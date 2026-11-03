# SPDX-License-Identifier: Apache-2.0
"""
================================================================================
模块名称: disagg_prefill_proxy_server.py
模块职责: vLLM 预填充与解码分离 (Disaggregated Prefill & Decode, P/D 分离) 控制面协调调度代理
技术框架: Quart (基于 asyncio 的异步 ASGI Web 框架) + aiohttp (异步高性能 HTTP Client)
================================================================================

[一、核心架构背景与业务痛点]
在传统的单实例或纯数据并行 LLM 服务中, 计算密集的 Prefill 阶段(对输入所有 Prompt Token 并行
计算 Self-Attention)与显存带宽受限的 Decode 阶段(逐个串行自回归生成 Token)在同一张 GPU 上交替执行:
1. 资源抢占: Prefill 突发流量会霸占 Tensor Core, 导致正在平稳吐字的 Decode 请求被迫等待, 引起严重
   的帧生成延迟 (Inter-Token Latency, ITL) 抖动.
2. 推理气泡: 为了凑批 (Batching), 调度器不得不频繁暂停处于自回归阶段的请求以混合执行 Prefill, 产生
   严重的显卡空转与计算气泡 (Inference Bubbles).

[二、本 Proxy 调度中枢的核心职责]
1. 统一流量网关: 对外暴露完全兼容 OpenAI 标准规范的 API 接口 (/v1/chat/completions 和 /v1/completions).
2. 请求双向分发与改写 (Split-and-Rewrite):
   - Prefill 端: 克隆请求体, 强制注入 `max_tokens=1` 和 `stream=False`, 逼迫其完成 Prompt 的全量前向
     计算并触发底层 KV 推送, 随后立即返回释放算力.
   - Decode 端: 保持原请求参数(保留完整 `max_tokens` 和原始 `stream` 策略), 负责自回归解码.
3. 拓扑寻址穿透 (P2P Addressing Injection):
   - 将底层两端监听的真实物理套接字 (IP:Port) 直接编码至 `X-Request-Id` 内部.
   - vLLM 内部的 P2pNcclConnector 会解析该 ID, 免除外部集中式注册中心 (如 Redis/Consul), 直接触发 GPU
     间的 NVLink / PCIe P2P 直连传输.
4. 微时差双向流水线编排 (Pipelined Rendezvous):
   - 彻底打破"先等 Prefill 算完再调 Decode"引发的 NCCL 阻塞死锁, 实现毫秒级协同触发.
================================================================================
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from typing import AsyncGenerator
from urllib.parse import urlparse

import aiohttp
from quart import Quart, Response, make_response, request

# ==============================================================================
# 日志配置: 统一时间戳精确到毫秒, 多协程场景下配合 Req-ID 实现分布式全链路追踪
# ==============================================================================
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(process)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("vLLM-Disagg-Proxy")


def parse_args():
    """解析命令行参数, 支持从容器环境变量或外部启动脚本灵活覆盖通讯拓扑"""
    parser = argparse.ArgumentParser(
        description="vLLM P/D 分离代理调度服务 (Disaggregated Proxy Server)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Proxy 自身对外监听绑定的 IP 地址 (容器化场景下必须为 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Proxy 自身对外暴露的 HTTP API 服务端口",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3600.0,
        help="与后端 Decode 实例交互的全局 HTTP 超时上限 (秒), 超长文本生成需调高",
    )
    parser.add_argument(
        "--prefill-url",
        type=str,
        default="http://127.0.0.1:8100",
        help="Prefill 实例 HTTP 根地址 (KV Producer 节点)",
    )
    parser.add_argument(
        "--decode-url",
        type=str,
        default="http://127.0.0.1:8200",
        help="Decode 实例 HTTP 根地址 (KV Consumer 节点)",
    )
    parser.add_argument(
        "--kv-host",
        type=str,
        default="127.0.0.1",
        help="后端 vLLM 实例用于底层 NCCL/ZMQ P2P 传输的物理网卡 IP (容器场景下必须传入真实内网 IP)",
    )
    parser.add_argument(
        "--prefill-kv-port",
        type=int,
        default=14579,
        help="Prefill 实例暴露的底层 NCCL/ZMQ 通信 Bootstrap 端口",
    )
    parser.add_argument(
        "--decode-kv-port",
        type=int,
        default=14580,
        help="Decode 实例暴露的底层 NCCL/ZMQ 通信 Bootstrap 端口",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 初始化 aiohttp 全局客户端超时对象 (主要作用于 Decode 阶段的长文本输出)
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)

    # 规范化后端 URL, 去除末尾斜杠, 防止与请求子路径拼接产生双斜杠导致 404
    PREFILL_BASE = args.prefill_url.rstrip("/")
    DECODE_BASE = args.decode_url.rstrip("/")

    # ==========================================================================
    # [核心避坑要点 1: 通信套接字物理寻址对齐]
    # PREFILL_KV_ADDR 和 DECODE_KV_ADDR 必须与 entrypoint.sh 中传给 vllm serve 的
    # "kv_ip" 及 "kv_port" 严格一致. 若这里传入 127.0.0.1 而后端监听在 10.41.0.2,
    # 底层 ZMQ 连接将失败, 进而导致两端 NCCL 握手陷入永久静默死锁.
    # ==========================================================================
    PREFILL_KV_ADDR = f"{args.kv_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{args.kv_host}:{args.decode_kv_port}"

    parsed_decode = urlparse(DECODE_BASE)
    kv_target_port = parsed_decode.port or (
        80 if parsed_decode.scheme == "http" else 443
    )
    KV_TARGET = f"{parsed_decode.hostname or '127.0.0.1'}:{kv_target_port}"

    logger.info("=" * 70)
    logger.info("🚀 启动 vLLM P/D 分离并发协调代理服务 (Disaggregated Proxy)")
    logger.info("  - 统一网关监听地址           : %s:%d", args.host, args.port)
    logger.info("  - Prefill 阶段后端 HTTP 接口  : %s", PREFILL_BASE)
    logger.info("  - Decode 阶段后端 HTTP 接口   : %s", DECODE_BASE)
    logger.info("  - Prefill 物理通讯端点 (ZMQ) : %s", PREFILL_KV_ADDR)
    logger.info("  - Decode 物理通讯端点 (ZMQ)  : %s", DECODE_KV_ADDR)
    logger.info("  - 后端请求全局超时限制        : %.1f 秒", args.timeout)
    logger.info("=" * 70)

    # 实例化 Quart 应用 (支持完全非阻塞的协程流式转发, 兼具 Flask 的轻量语法)
    app = Quart(__name__)

    def _build_headers(request_id: str) -> dict[str, str]:
        """构建注入了拓扑寻址协议的下游 HTTP 请求头
        - X-Request-Id: 最关键的载体, 编码了 P2P 两端的通信套接字及全生命周期唯一的 UUID.
        - X-KV-Target: 告知 Prefill 节点将计算出的 KV Cache 最终输出的目的端.
        """
        headers: dict[str, str] = {
            "X-Request-Id": request_id,
            "X-KV-Target": KV_TARGET,
            "Content-Type": "application/json",
        }
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def _run_prefill_task(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        req_tag: str,
    ) -> None:
        """
        [阶段 1: Prefill 执行控制协程]
        向 Prefill 实例发起异步 HTTP 请求.

        [底层通信机制与注意事项]:
        1. max_tokens=1 拦截: Prefill 节点仅计算 Prompt 注意力并生成第一个 Token,
           同时通过 P2pNcclConnector 将其 Attention 键值推入底层环形队列.
        2. stream=False 拦截 (关键): 必须关闭流式传输. 若保留流式, Prefill 实例将保持
           Server-Sent Events 长连接直至首个 Token 彻底析出, 极易导致网络悬挂.
        3. await resp.read(): 读完整包即确认 Prefill 实例已完成首步前向计算,
           并将全部 KV 数据通过 NCCL/NVLink 压入了 Decode 节点的 GPU Buffer 中.
        """
        url = f"{PREFILL_BASE}{request_path}"
        start_ts = time.perf_counter()
        logger.info("[%s] ➡️ [Prefill 触发] 发送至 Prefill 节点: %s", req_tag, url)

        try:
            # 独立短超时 Session: Prefill 仅计算首 Token, 理论耗时极短 (几十毫秒到数秒)
            # 设置 180 秒硬超时, 若发生意外能尽早熔断, 防止连接池耗尽
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=180)
            ) as session:
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    if resp_status != 200:
                        err_text = await resp.text()
                        logger.error(
                            "[%s] ❌ [Prefill 失败] HTTP %d: %s",
                            req_tag,
                            resp_status,
                            err_text,
                        )
                        return

                    # 等待底层彻底推流结束并读取回包
                    await resp.read()
                    logger.info(
                        "[%s] ⬅️ [Prefill 完成] 耗时: %.3f 秒, KV Cache 已入库推至 Decode 显存",
                        req_tag,
                        time.perf_counter() - start_ts,
                    )
        except Exception as exc:
            # Prefill 失败不中断主流程抛错, 交给 Decode 端去触发兜底策略 (如 fallback 回本地计算)
            logger.error("[%s] ❌ [Prefill 异常]: %s", req_tag, exc)

    async def _stream_decode(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        req_tag: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        [阶段 2: Decode 执行与流式推流生成器]
        向 Decode 实例发起异步 HTTP 请求.

        [底层机制与注意事项]:
        1. 带有相同 X-Request-Id 的请求到达 Decode 节点.
        2. Decode 节点通过 P2pNcclConnector 查找本地接收 Buffer:
           若命中匹配的 Request ID, 直接跳过耗时的 Prefill 前向计算, 加载已有 KV,
           立即启动低延迟的自回归解码.
        3. 以二进制数据块 (iter_chunked) 逐块接收并直接推流 (yield) 吐回客户端,
           天然兼容普通 JSON 输出与 SSE (Server-Sent Events) 流式打字机效果.
        """
        url = f"{DECODE_BASE}{request_path}"
        start_ts = time.perf_counter()
        first_chunk_ts = None
        chunk_count = 0
        total_bytes = 0

        logger.info("[%s] ➡️ [Decode 接入] 发送至 Decode 节点等待 KV 并流式生成: %s", req_tag, url)

        try:
            async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    if resp_status != 200:
                        err_text = await resp.text()
                        logger.error(
                            "[%s] ❌ [Decode 失败] HTTP %d: %s",
                            req_tag,
                            resp_status,
                            err_text,
                        )
                        yield json.dumps(
                            {"error": f"Decode backend error {resp_status}: {err_text}"}
                        ).encode("utf-8")
                        return

                    logger.info("[%s] 🔄 [Decode 连接建立] 状态码: 200, 开始迭代传输 Token...", req_tag)

                    # 逐块异步迭代读取二进制流 (1KB 块缓冲, 平衡吞吐与流式首字抖动)
                    async for chunk in resp.content.iter_chunked(1024):
                        if not chunk:
                            continue

                        now = time.perf_counter()
                        if first_chunk_ts is None:
                            first_chunk_ts = now
                            logger.info(
                                "[%s] ⚡ [首 Token 产生] TTFT (首字延迟): %.3f 秒",
                                req_tag,
                                first_chunk_ts - start_ts,
                            )

                        chunk_count += 1
                        total_bytes += len(chunk)
                        yield chunk

                    logger.info(
                        "[%s] ⬅️ [Decode 传输结束] 成功! 总耗时: %.3f 秒, 数据块: %d, 传输量: %.2f KB",
                        req_tag,
                        time.perf_counter() - start_ts,
                        chunk_count,
                        total_bytes / 1024.0,
                    )

        except Exception as exc:
            logger.error("[%s] ❌ [Decode 连接异常]: %s", req_tag, exc)
            yield json.dumps({"error": f"Decode connection error: {str(exc)}"}).encode("utf-8")

    async def process_request() -> Response:
        """
        [主流程编排控制管道]
        实现外部单次 HTTP 请求到底层 P/D 双节点流水线的无缝解耦与并发撮合.
        """
        request_start_time = time.perf_counter()
        req_tag = f"Req-{uuid.uuid4().hex[:8]}"

        # ======================================================================
        # [核心避坑要点 2: 脱离 Quart 上下文生命周期]
        # 必须在进入任何异步生成器 (response_stream) 之前, 将 request.path、
        # request.get_json() 等一切属性彻底提取为局部变量!
        # 原因: Quart 的 request 属于 LocalProxy (基于 ContextVar). 当当前视图函数
        # process_request() 返回 Response 对象时, HTTP 接收上下文被回收.
        # 如果在延迟执行的生成器内部去读取 `request.path`, 会当场抛出异常:
        # `RuntimeError: Not within a request context` 导致 ASGI 框架彻底崩溃.
        # ======================================================================
        req_path = request.path

        try:
            original_request_data = await request.get_json()
            if not isinstance(original_request_data, dict):
                raise ValueError("请求负载必须为有效的 JSON 对象")
        except Exception as e:
            logger.warning("[%s] ⚠️ 收到无效的请求体: %s", req_tag, str(e))
            return Response(
                json.dumps({"error": f"Invalid JSON: {str(e)}"}),
                status=400,
                content_type="application/json",
            )

        model = original_request_data.get("model", "unknown")
        max_tokens = original_request_data.get("max_tokens", "default")
        stream = original_request_data.get("stream", False)

        logger.info(
            "[%s] 📥 接收请求 -> 路由: %s, 模型: %s, max_tokens: %s, stream: %s",
            req_tag,
            req_path,
            model,
            max_tokens,
            stream,
        )

        # ----------------------------------------------------------------------
        # 步骤 1: 构造 Prefill 专属请求体
        # ----------------------------------------------------------------------
        prefill_request = original_request_data.copy()
        # 强制只让 Prefill 节点算 1 个 Token, 完成 Attention 矩阵计算后立即脱手
        prefill_request["max_tokens"] = 1
        if "max_completion_tokens" in prefill_request:
            prefill_request["max_completion_tokens"] = 1
        # [关键]Prefill 必须强制非流式, 确保 HTTP 连接不会因为 SSE 事件流而长期悬挂
        prefill_request["stream"] = False

        # ----------------------------------------------------------------------
        # 步骤 2: 构造底层 NCCL 拓扑寻址 Request-ID
        # ----------------------------------------------------------------------
        # [核心避坑要点 3: 必须确保两端 Request-ID 字符串绝对一致]
        # vLLM V1 必须配置环境变量 VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=1.
        # 只有该变量开启, 后端引擎才不会自动往外部 ID 后面拼接随机生成的后缀,
        # 保证 Prefill 发送的 Tensor Key 与 Decode 接收的 Tensor Key 完美吻合.
        unique_token = uuid.uuid4().hex
        full_request_id = (
            f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_"
            f"{DECODE_KV_ADDR}_{unique_token}"
        )
        headers = _build_headers(full_request_id)

        # ----------------------------------------------------------------------
        # 步骤 3: [核心并发流水线机制]打破串行死锁
        # ----------------------------------------------------------------------
        # [核心通信原理解析]:
        # NCCL P2P (ncclSend / ncclRecv) 本质上是阻塞型/协同型的通讯操作.
        # 若采用严格串行调度 (先 await Prefill 完成, 再发 Decode):
        # Prefill 节点的 GPU 在执行完前向后调用 ncclSend, 在 Stream 上阻塞等待对端对齐;
        # 而由于没有调用 Decode, Decode 端没有收到请求, 根本不会调用 ncclRecv;
        # 最终导致 Prefill 永远不返回 200, 形成了三方死锁!
        #
        # [正确解法]:
        # 1. 先通过 asyncio.create_task 后台拉起 Prefill 任务;
        # 2. 给予极短 (0.05 秒) 异步让步, 确保 Prefill 建立连接并在 ZMQ 信道广播元数据;
        # 3. 紧接着拉起 Decode 任务, 让 Decode 立即在 EngineCore 注册并挂起等待 KV (ncclRecv 就绪);
        # 4. 两端同时在物理 Stream 上握手成功, KV Cache 瞬间直传完成并流式推回客户端!
        logger.info("[%s] 🚀 [阶段 1] 激活 Prefill 节点计算与 KV 传输...", req_tag)
        prefill_task = asyncio.create_task(
            _run_prefill_task(req_path, prefill_request, headers, req_tag)
        )

        # 微秒级异步让步, 消解分布式时序竞争
        await asyncio.sleep(0.05)

        logger.info("[%s] 🚀 [阶段 2] 接入 Decode 节点管道...", req_tag)
        async def response_stream():
            try:
                async for chunk in _stream_decode(
                    req_path, original_request_data, headers, req_tag
                ):
                    yield chunk
            finally:
                # 客户端断连或流结束时的清理逻辑: 若客户端中途取消, 立即掐死后台的 Prefill 任务释放 GPU
                if not prefill_task.done():
                    prefill_task.cancel()

        # 创建 Quart 响应流
        response = await make_response(response_stream())
        # 核心设置: 禁用 ASGI 内部超时切断, 防止长文本大模型自回归慢导致连接被代理切断
        response.timeout = None

        logger.info(
            "[%s] 🔗 双向流水线就绪 (调度层握手耗时: %.3f 秒)",
            req_tag,
            time.perf_counter() - request_start_time,
        )
        return response

    # ==========================================================================
    # 路由注册与服务透传
    # ==========================================================================
    @app.route("/v1/completions", methods=["POST"])
    @app.route("/v1/chat/completions", methods=["POST"])
    async def handle_request():
        try:
            return await process_request()
        except asyncio.CancelledError:
            # 客户端主动断开网络 (如关闭页面或 Ctrl+C)
            logger.warning("⚠️ 客户端主动中断连接 (Request Cancelled)")
            return Response(b'{"error": "Request cancelled"}', status=503)
        except Exception as exc:
            logger.exception("💥 Proxy 处理异常: %s", str(exc))
            return Response(
                json.dumps({"error": f"Internal proxy error: {str(exc)}"}),
                status=500,
                content_type="application/json",
            )

    # 健康检查与模型列表透传 (直接穿透给 Decode 节点)
    @app.route("/v1/models", methods=["GET"])
    async def handle_models():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{DECODE_BASE}/v1/models") as resp:
                    data = await resp.read()
                    return Response(data, status=resp.status, content_type="application/json")
        except Exception as e:
            return Response(json.dumps({"error": str(e)}), status=500)

    # 启动 ASGI 服务
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
