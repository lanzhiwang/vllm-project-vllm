#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
disagg_encoder_proxy.py

[设计目的]
该代理服务是多模态 EPD 解耦的核心路由器. 用户只需要像往常一样向该 Proxy
发送 OpenAI 兼容的 API 请求, Proxy 内部会将复杂的 Vision 提取、LLM 文本首字预计算(Prefill)
以及流式自回归生成(Decode)拆分到不同的物理实例运行, 从而将不兼容的计算模式完美隔离开.

Proxy that routes OpenAI-compatible “/v1/chat/completions” requests to two
clusters:
  • encode  (multimodal feature extraction)
  • decode  (language-model inference)

For MM input we:
    1. Extract *every* image/audio item.
    2. Fire N concurrent requests to the encoder cluster
       (one request per item, with **all text removed**).
    3. Wait for all of them to succeed.
    4. Forward the *original* request to a decode server.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import uuid
from collections.abc import AsyncIterator

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

###############################################################################
# FastAPI app & global state
###############################################################################

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger("proxy")

app = FastAPI()
# [设计目的] 建立物理隔离的服务连接池.
# 分别维护连接到 Encoder、Prefill、Decode 物理集群的长连接会话, 防止高并发下频繁建立 TCP 连接带来的时延.
encode_session: aiohttp.ClientSession | None = None
prefill_session: aiohttp.ClientSession | None = None
decode_session: aiohttp.ClientSession | None = None

###############################################################################
# Utils
###############################################################################


MM_TYPES = {"image_url", "audio_url", "input_audio"}


def extract_mm_items(request_data: dict) -> list[dict]:
    """
    Return *all* image/audio items that appear anywhere in `messages`.

    [设计目的]
    快速扫描并剥离出整个请求消息历史(messages)中的所有多模态对象(图片、音频等).

    Each returned dict looks like:
        { "type": "image_url", "image_url": {...} }
    """
    items: list[dict] = []
    for msg in request_data.get("messages", []):
        content = msg.get("content")
        if not isinstance(content, list):
            continue

        for item in content:
            if item.get("type") in MM_TYPES:
                items.append(item)
    return items


async def fanout_encoder_primer(
    orig_request: dict,
    e_urls: list[str],
    req_id: str,
) -> None:
    """
    1. Build one request *per MM item* with all text removed.
    2. Send them concurrently to the encode cluster.
    3. Raise if any of them fails.

    [设计目的]
    并行触发多模态特征提取. 如果有 N 张图, Proxy 会将 N 张图拆分并并行派发给物理 Encoder 集群.

    [深层原理 - 为什么要把文本全部移除, 且 max_tokens 设为 1?]
    1. 文本剥离: Encoder 节点物理上只装载并执行多模态大模型的视觉部分(例如 ViT). 它不需要、也无法执行 LLM 文本计算.
    2. max_tokens=1: 强制 vLLM 在执行完多模态图像特征提取并写入 EC 共享缓存(Encoder Cache)后立即退出.
    3. 避免无效算力浪费: 如果不设 max_tokens=1 或不剥离文本, Encoder 节点会尝试对整段 Prompt 执行多模态自回归文本生成, 这与解耦设计完全相悖.
    """
    logger.info("[%s] Processing multimodal items...", req_id)

    mm_items = extract_mm_items(orig_request)
    if not mm_items:
        logger.info("[%s] No multimodal items, skipping encoder", req_id)
        # 没有多模态图像/音频, 直接跳过视觉提取节点
        return  # nothing to do

    logger.info("[%s] got %d multimodal items...", req_id, len(mm_items))

    tasks = []

    # [设计目的] 轮询(Round-Robin)分发负载.
    # 当单次请求包含多张大图(例如相册多轮对话)时, 将图片均匀打散到 Encoder 物理集群的多台实例上并行处理, 实现计算级负载均衡.
    # Round-robin over encode servers to distribute load a bit
    url_cycle = (e_urls[i % len(e_urls)] for i in range(len(mm_items)))

    for idx, (item, target_url) in enumerate(zip(mm_items, url_cycle)):
        # [设计逻辑] 生成可追踪的子请求 ID. 在分布式系统中, 这能极大地方便开发人员通过日志检索某张图在哪个节点上出错.
        # Derive a *child* request id:  <parent>:<index>:<random-short>
        child_req_id = f"{req_id}:{idx}:{uuid.uuid4().hex[:6]}"
        headers = {"x-request-id": child_req_id}

        # 构造一个纯净的视觉处理请求, 只包含单张图, 不含任何 LLM 文本 prompt
        encoder_req = {
            # You *may* need to keep additional fields
            "model": orig_request.get("model"),
            "messages": [
                {"role": "user", "content": [item]},
            ],
            # Only need 1 token so the server actually runs the encoder path
            "max_tokens": 1,
            "stream": False,
        }
        tasks.append(
            encode_session.post(
                f"{target_url}/v1/chat/completions",
                json=encoder_req,
                headers=headers,
            )
        )

    # [深层原理] 异步并发执行.
    # 多媒体数据的传输和 ViT 的前向传播需要耗费数十毫秒甚至数百毫秒. 使用 asyncio.gather 并发处理,
    # 可保证处理多图请求的时间瓶颈仅取决于单张图的最慢处理时间(O(1) 延迟开销), 而不是串行堆叠.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 快速失败响应机制(Fail-fast)
    # Fail fast if any sub-request failed
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(
                "[%s] Encoder request #%d raised exception: %s",
                req_id,
                idx,
                r,
                exc_info=r,
            )
            raise HTTPException(
                status_code=502, detail=f"Encoder request failed: {str(r)}"
            )
        if r.status != 200:
            try:
                detail = await r.text()
            except Exception:
                detail = "<unable to read body>"
            logger.error(
                "[%s] Encoder request #%d returned status %s: %s",
                req_id,
                idx,
                r.status,
                detail,
            )
            raise HTTPException(
                status_code=r.status,
                detail=f"Encoder request failed: {detail}",
            )

    logger.info(
        "[%s] All %d encoder requests completed successfully", req_id, len(mm_items)
    )


async def maybe_prefill(
    req_data: dict,
    p_url: str,
    req_id: str,
) -> dict:
    """
    - Do prefill-only task if p_url exist;
    - Return modified request data with kv transfer params (for nixl connector)
    - Else, skip and return the original request data for decode

    [设计目的]
    决定是执行 E->P->D(三阶段解耦)还是 E->PD(两阶段解耦).
    如果用户显式关闭了物理 Prefill 节点(p_url 为空), 则不进行任何干预, 直接原样下发给后续 PD 节点.
    """
    if p_url:
        logger.info("[%s] Processing through prefill: %s", req_id, p_url)

        # 驱动物理 Prefill 阶段进行文本首字计算
        prefill_response = await process_prefill_stage(req_data, p_url, req_id)

        # [深层原理 - 桥接控制信号]
        # Prefill 节点在物理显存中计算完本次 Prompt 的 KV Cache 后, 不会执行 Decode,
        # 而是将物理显存的虚拟指针、存储块(Block)地址映射以及网络直连协议等元数据, 打包封装在 `kv_transfer_params` 中返回给 Proxy.
        # for nixl connector to facilitate kv transfer...
        prefill_response_json = await prefill_response.json()
        kv_transfer_params = prefill_response_json.get("kv_transfer_params", {})
        if kv_transfer_params:
            # 将该传输参数动态注入请求体中, 以通知下流的 Decode 节点执行高速 RDMA 直接读取
            req_data["kv_transfer_params"] = kv_transfer_params

        return req_data
    else:
        return req_data


async def process_prefill_stage(
    req_data: dict,
    p_url: str,
    req_id: str,
) -> dict:
    """
    Process request through Prefill stage and return kv_transfer_params

    [深层原理 - 驱动离线 Prefill 计算并准备跨节点传输]
    1. 复制原请求: 保留模型设置和文本 prompt, 因为 Prefill 节点需要读取文本以及从 EC 存储中读取多模态图像 Embedding.
    2. 注入特定参数:
       - `do_remote_decode = True` & `do_remote_prefill = False`: 告知 Prefill 节点, “你只需要计算首字 KV 缓存并准备异步网络推送, 后续生成不要由你执行”.
    3. max_tokens=1: 同样强制 Prefill 节点在首字预热完毕并生成网络传输句柄后, 立即释放当前请求执行上下文.
    """
    logger.info("[%s] Sending prefill request to: %s", req_id, p_url)

    prefill_request = req_data.copy()
    prefill_request["kv_transfer_params"] = {
        "do_remote_decode": True,
        "do_remote_prefill": False,
        "remote_engine_id": None,
        "remote_block_ids": None,
        "remote_host": None,
        "remote_port": None,
    }
    prefill_request["stream"] = False
    prefill_request["max_tokens"] = 1
    if "max_completion_tokens" in prefill_request:
        prefill_request["max_completion_tokens"] = 1
    if "stream_options" in prefill_request:
        del prefill_request["stream_options"]

    headers = {"x-request-id": req_id}
    try:
        prefill_response = await prefill_session.post(
            f"{p_url}/v1/chat/completions", json=prefill_request, headers=headers
        )
        prefill_response.raise_for_status()

        if prefill_response.status != 200:
            error_text = await prefill_response.text()
            logger.error(
                "[%s] Prefill request failed with status %d: %s",
                req_id,
                prefill_response.status,
                error_text,
            )
            raise HTTPException(
                status_code=prefill_response.status,
                detail={"error": "Prefill request failed", "message": error_text},
            )
        logger.info("[%s] Prefill request completed successfully", req_id)

        return prefill_response

    except Exception as e:
        logger.error("Prefill processing failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Prefill processing error", "message": str(e)},
        ) from e


###############################################################################
# Middleware for request/response logging
###############################################################################


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests and responses

    [设计目的]
    全局 Trace 中间件. 在异步高并发代理中, 成百上千个请求的日志会完全交织在一起.
    引入唯一的 x-request-id 头能将整条分布式链路(Proxy -> E -> P -> D)的所有事件聚合排查.
    """
    req_id = request.headers.get("x-request-id", str(uuid.uuid4()))

    # Log incoming request
    logger.info(
        ">>> [%s] %s %s from %s",
        req_id,
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    try:
        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            "<<< [%s] %s %s completed with status %d",
            req_id,
            request.method,
            request.url.path,
            response.status_code,
        )

        return response
    except Exception as e:
        # Log errors
        logger.exception(
            "!!! [%s] %s %s failed with error: %s",
            req_id,
            request.method,
            request.url.path,
            str(e),
        )
        raise


###############################################################################
# FastAPI lifecycle
###############################################################################


@app.on_event("startup")
async def on_startup() -> None:
    """
    层原理 - 异步 HTTP 吞吐极限优化配置]
    1. limit=0: 禁用 aiohttp 内部的连接数上限限制. 在高并发微服务网关中, 如果限制连接池大小, 会导致大量并发请求在
       TCP 握手队列上排队(Head-of-Line Blocking), 从而极大地增加首字延迟(TTFT).
    2. force_close=False: 强制启用 HTTP Keep-Alive 连接复用, 杜绝每一次请求都重新发起 TCP 三次握手和 TLS 协商.
    """
    global encode_session, prefill_session, decode_session
    timeout = aiohttp.ClientTimeout(total=100_000)
    connector = aiohttp.TCPConnector(limit=0, force_close=False)
    encode_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    if app.state.p_urls:
        # only setup if prefill instance(s) exist
        prefill_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    decode_session = aiohttp.ClientSession(timeout=timeout, connector=connector)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    优雅地关闭连接池, 防止断开网络插槽(Socket)导致底层通信异常.
    """
    global encode_session, prefill_session, decode_session
    if encode_session:
        await encode_session.close()
    if prefill_session:
        await prefill_session.close()
    if decode_session:
        await decode_session.close()


###############################################################################
# Core forwarding
###############################################################################


async def forward_non_stream(
    req_data: dict, req_id: str, e_urls: list[str], p_url: str, d_url: str
) -> dict:
    """
    [设计目的] 协调非流式请求
    """
    try:
        # Step 1: 先提取原始请求中的所有视觉多媒体, 多播发给物理 Encoder 集群, 生成视觉 embedding 写入 EC
        # Step 1: Process through Encoder instance (if has MM input)
        await fanout_encoder_primer(req_data, e_urls, req_id)

        # Step 2: 驱动 Prefill 节点读取视觉特征, 并在物理卡上预热 prompt 并导出 KV Cache 元数据
        # Step 2: Process through Prefill instance
        req_data = await maybe_prefill(req_data, p_url, req_id)

        # Step 3: 向 Decode 节点发送最终的文本生成任务
        # 如果存在 Step 2, 此时 req_data 内已经封装了物理 KV 缓存跨节点读取的技术句柄.
        # Decode 节点在收到该请求后, 直接通过 Nixl 网卡通道零拷贝(Zero-copy)拉取 KV Cache 并执行自回归推理.
        # Step 3: Process through Decode instance
        logger.info("[%s] Forwarding to decode: %s", req_id, d_url)
        headers = {"x-request-id": req_id}

        # Non-streaming response
        async with decode_session.post(
            f"{d_url}/v1/chat/completions", json=req_data, headers=headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[%s] Error in forward_non_stream: %s", req_id, str(e))
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}") from e


async def forward_stream(
    req_data: dict, req_id: str, e_urls: list[str], p_url: str, d_url: str
) -> AsyncIterator[str]:
    """
    [设计目的] 协调高并发流式(Stream)请求.

    [深层原理 - 异步流式背压机制]
    虽然解耦了 Encoder 和 Prefill, 但流式请求(Token-by-token 输出)由 Decode 节点掌控.
    使用 AsyncIterator 包装 resp.content.iter_chunked 可以在不堵塞 Python 主线程的前提下,
    保持与 Decode 实例的高速流式数据块(chunks)中转, 直接将生成结果推回用户端.
    """
    try:
        # Step 1: Process through Encoder instance (if has MM input)
        await fanout_encoder_primer(req_data, e_urls, req_id)

        # Step 2: Process through Prefill instance
        req_data = await maybe_prefill(req_data, p_url, req_id)

        # Step 3: Process through Decode instance
        logger.info("[%s] Starting streaming from decode: %s", req_id, d_url)
        headers = {"x-request-id": req_id}

        # Streaming response
        async with decode_session.post(
            f"{d_url}/v1/chat/completions",
            json=req_data,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.content.iter_chunked(1024):
                if chunk:
                    # 使用 utf-8 容错解码(ignore), 防止流式响应发生断句字节截断时抛出致命异常
                    yield chunk.decode("utf-8", errors="ignore")

        logger.info("[%s] Streaming completed", req_id)

    except HTTPException:
        logger.exception("[%s] HTTPException in forward_stream", req_id)
        raise
    except Exception as e:
        logger.exception("[%s] Error in forward_stream: %s", req_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Proxy streaming error: {str(e)}"
        ) from e


###############################################################################
# Public routes
###############################################################################


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    [设计目的]
    OpenAI 兼容的标准微服务总网关. 外部客户端无法感知后端极其复杂的解耦实现, 在此抹平异构细节.
    """
    try:
        req_data = await request.json()
        req_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # 全量获取 Encoder 节点的端口, 用作 fan-out 多路并行派发
        e_urls = app.state.e_urls  # we want the full list for fan-out

        # [设计目的]
        # 对 Prefill 和 Decode 集群进行随机负载均衡(random.choice),
        # 极大地简化了微服务负载均衡器的部署, 实现了请求级的流量横向平铺.
        p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
        d_url = random.choice(app.state.d_urls)

        is_streaming = req_data.get("stream", False)

        if is_streaming:
            return StreamingResponse(
                forward_stream(req_data, req_id, e_urls, p_url, d_url),
                media_type="text/event-stream",
            )
        result = await forward_non_stream(req_data, req_id, e_urls, p_url, d_url)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in chat_completions endpoint: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Request processing error: {str(e)}"
        ) from e


@app.get("/v1/models")
async def list_models():
    """
    代理路由: 获取当前运行的模型. 直接向下游实例转发请求以实现接口一致.
    """
    async with decode_session.get(f"{app.state.d_urls[0]}/v1/models") as resp:
        resp.raise_for_status()
        return await resp.json()


@app.get("/health")
async def health_check():
    """
    [设计目的] 分布式集群联合健康状态监控.
    如果后端三个物理集群中有一个处于异常不可用状态, 则立刻对外界返回 503 (Service Unavailable),
    以触发诸如 Kubernetes 等容器管理平台的自动故障迁移(Failover).
    """
    async def healthy(urls):
        if not urls:
            return "empty"
        for u in urls:
            try:
                async with encode_session.get(f"{u}/health") as resp:
                    resp.raise_for_status()
            except Exception:
                return "unhealthy"
        return "healthy"

    # 并发查询各物理组件集群的健康状况
    e_status, p_status, d_status = await asyncio.gather(
        healthy(app.state.e_urls), healthy(app.state.p_urls), healthy(app.state.d_urls)
    )

    overall_healthy = all(
        status != "unhealthy" for status in (e_status, p_status, d_status)
    )

    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        {
            "proxy": "healthy",
            "encode_cluster": e_status,
            "prefill_cluster": p_status,
            "decode_cluster": d_status,
        },
        status_code=status_code,
    )


###############################################################################
# Simple profiler fan-out (unchanged except for sessions)
# 性能遥测数据采集
###############################################################################


async def _post_if_available(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
    headers: dict,
) -> dict | None:
    """
    POST `payload` to `url`.

    [设计目的]
    一个支持容错的遥测命令发送管道. 在未启用 profiling 的测试节点上直接静默忽略 404, 防止阻塞主体.

    Returns
    -------
    • The decoded JSON body on success (2xx)
    • None if the endpoint does not exist (404)
    • Raises for anything else.
    """
    try:
        resp = await session.post(url, json=payload, headers=headers)
        if resp.status == 404:  # profiling disabled on that server
            logger.warning("Profiling endpoint missing on %s", url)
            return None
        resp.raise_for_status()
        return await resp.json(content_type=None)
    except aiohttp.ClientResponseError as exc:
        # Pass 404 through the branch above, re-raise everything else
        if exc.status == 404:
            logger.warning("Profiling endpoint missing on %s", url)
            return None
        raise
    except Exception:
        # Network errors etc.: propagate
        raise


async def _profile_cmd(cmd: str, payload: dict, e_url: str, p_url: str, d_url: str):
    """
    Fire & forget to both clusters, tolerate 404.

    [深层原理] 多节点分布式性能追踪同步.
    多模态解耦架构极其复杂, 由于跨多节点传输, 传统的单机 PyTorch Profiler 只能看到单一环节, 无法看到端到端.
    此方法能够协调所有的物理实例, 在接收到 start 命令后同步对底层计算、通信(Nixl RDMA)进行 Trace 记录.
    """
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"}

    encode_task = _post_if_available(
        encode_session, f"{e_url}/{cmd}_profile", payload, headers
    )
    prefill_task = (
        _post_if_available(prefill_session, f"{p_url}/{cmd}_profile", payload, headers)
        if p_url is not None
        else asyncio.sleep(0)
    )
    decode_task = _post_if_available(
        decode_session, f"{d_url}/{cmd}_profile", payload, headers
    )

    encode_res, prefill_res, decode_res = await asyncio.gather(
        encode_task, prefill_task, decode_task
    )

    # If *all* clusters said “I don’t have that route”, surface an error
    if encode_res is prefill_res is decode_res is None:
        raise HTTPException(
            status_code=503,
            detail="Profiling endpoints are disabled on all clusters",
        )

    return {
        "encode": encode_res,  # may be None
        "prefill": prefill_res,  # may be None
        "decode": decode_res,  # may be None
    }


@app.post("/start_profile")
async def start_profile(request: Request):
    body = await request.json()
    # TODO: handle multi urls properly
    e_url = random.choice(app.state.e_urls)
    p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
    d_url = random.choice(app.state.d_urls)
    return await _profile_cmd("start", body, e_url, p_url, d_url)


@app.post("/stop_profile")
async def stop_profile(request: Request):
    body = await request.json()
    # TODO: handle multi urls properly
    e_url = random.choice(app.state.e_urls)
    p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
    d_url = random.choice(app.state.d_urls)
    return await _profile_cmd("stop", body, e_url, p_url, d_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--encode-servers-urls",
        required=True,
        help='Comma-separated encode URLs ("http://e1:8001,http://e2:8001")',
    )
    parser.add_argument(
        "--prefill-servers-urls",
        required=True,
        help=(
            'Comma-separated prefill URLs ("http://p1:8003,http://p2:8004") ',
            'to enable E->P->D, set "disable" or "none" to enable E->PD',
        ),
    )
    parser.add_argument(
        "--decode-servers-urls",
        required=True,
        help='Comma-separated decode URLs ("http://d1:8005,http://d2:8006")',
    )

    args = parser.parse_args()
    app.state.e_urls = [
        u.strip() for u in args.encode_servers_urls.split(",") if u.strip()
    ]
    app.state.d_urls = [
        u.strip() for u in args.decode_servers_urls.split(",") if u.strip()
    ]

    # [设计原理] 处理两阶段解耦和三阶段解耦的自适应路由.
    # handle prefill instances
    if args.prefill_servers_urls.lower() in ("disable", "none", ""):
        app.state.p_urls = []
        logger.info(
            "Disaggregated prefill phase explicitly disabled by user. Running E + PD..."
        )
    else:
        app.state.p_urls = [
            u.strip() for u in args.prefill_servers_urls.split(",") if u.strip()
        ]
        logger.info("Disaggregated prefill phase is enabled. Running E + P + D...")

    logger.info("Proxy listening on %s:%s", args.host, args.port)
    logger.info("Encode servers: %s", app.state.e_urls)
    logger.info("Prefill instances %s", app.state.p_urls)
    logger.info("Decode servers: %s", app.state.d_urls)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        # [设计原理] 采用高性能 uvloop 替换 Python 原生的 asyncio 事件循环, 提升高并发网络 I/O 的处理上限.
        loop="uvloop",
        access_log=True,
    )
