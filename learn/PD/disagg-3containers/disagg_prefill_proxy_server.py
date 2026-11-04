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
import socket
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


def get_default_host_ip() -> str:
    """与 vLLM 底层 get_ip() 逻辑完全对齐的 IP 获取函数"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return socket.gethostbyname(socket.gethostname())


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
        help="后端 vLLM 实例用于底层 NCCL/ZMQ P2P 传输的全局默认 IP",
    )
    parser.add_argument(
        "--prefill-kv-host",
        type=str,
        default=None,
        help="Prefill 实例专属 NCCL 通信物理 IP (若不指定则回退到 --kv-host)",
    )
    parser.add_argument(
        "--decode-kv-host",
        type=str,
        default=None,
        help="Decode 实例专属 NCCL 通信物理 IP (若不指定则回退到 --kv-host)",
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

    # 详细打印所有从命令行/环境变量解析得到的启动参数
    logger.info("📋 成功解析启动参数 (Parsed CLI Arguments):")
    for arg_name, arg_val in vars(args).items():
        logger.info("  - %-18s : %s", arg_name, arg_val)

    # 初始化 aiohttp 全局客户端超时对象 (主要作用于 Decode 阶段的长文本输出)
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)

    # 规范化后端 URL, 去除末尾斜杠, 防止与请求子路径拼接产生双斜杠导致 404
    PREFILL_BASE = args.prefill_url.rstrip("/")
    DECODE_BASE = args.decode_url.rstrip("/")

    # ==========================================================================
    # [核心避坑要点 1: 通信套接字物理寻址对齐]
    # PREFILL_KV_ADDR 和 DECODE_KV_ADDR 必须与容器启动命令中传给 vllm serve 的
    # "kv_ip" 及 "kv_port" 严格一致.
    # ==========================================================================

    # 如果没配或者配了 auto, 自动探测
    detected_host = (
        args.kv_host
        if (args.kv_host and args.kv_host != "auto")
        else get_default_host_ip()
    )
    prefill_host = args.prefill_kv_host or detected_host
    decode_host = args.decode_kv_host or detected_host

    PREFILL_KV_ADDR = f"{prefill_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{decode_host}:{args.decode_kv_port}"

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
    logger.info("  - X-KV-Target 目标路由标识    : %s", KV_TARGET)
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
            logger.debug("🔑 下游请求头已注入 Authorization 凭证")
        else:
            logger.debug("ℹ️ 未检测到 OPENAI_API_KEY 环境变量, 跳过 Authorization 注入")
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
        logger.debug(
            "[%s] 📦 Prefill 请求参数摘要: max_tokens=%s, stream=%s, model=%s",
            req_tag,
            payload.get("max_tokens"),
            payload.get("stream"),
            payload.get("model"),
        )
        logger.debug(
            "[%s] 🏷️ Prefill 请求专属请求头: X-Request-Id=%s, X-KV-Target=%s",
            req_tag,
            headers.get("X-Request-Id"),
            headers.get("X-KV-Target"),
        )

        try:
            prefill_timeout = aiohttp.ClientTimeout(total=180)
            logger.debug(
                "[%s] 🌐 正在初始化 Prefill HTTP ClientSession (Timeout=180s)...",
                req_tag,
            )
            async with aiohttp.ClientSession(timeout=prefill_timeout) as session:
                logger.debug(
                    "[%s] 📤 正在向 Prefill 节点推送 HTTP POST 数据包...", req_tag
                )
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    logger.debug(
                        "[%s] 📥 Prefill 节点返回 HTTP 响应状态码: %d",
                        req_tag,
                        resp_status,
                    )

                    if resp_status != 200:
                        err_text = await resp.text()
                        logger.error(
                            "[%s] ❌ [Prefill 失败] HTTP %d: %s",
                            req_tag,
                            resp_status,
                            err_text,
                        )
                        return

                    logger.debug(
                        "[%s] ⏳ 开始读取 Prefill 完整响应体以确认 KV Cache 推送完毕...",
                        req_tag,
                    )
                    body_bytes = await resp.read()
                    elapsed = time.perf_counter() - start_ts
                    logger.info(
                        "[%s] ⬅️ [Prefill 完成] 耗时: %.3f 秒, 响应体大小: %d 字节, KV 已推送至 Decode",
                        req_tag,
                        elapsed,
                        len(body_bytes),
                    )
        except asyncio.TimeoutError:
            logger.error(
                "[%s] ❌ [Prefill 超时] 请求耗时超过 180 秒硬超时限制, 可能卡在 NCCL 发送环路中",
                req_tag,
            )
        except aiohttp.ClientConnectorError as exc:
            logger.error(
                "[%s] ❌ [Prefill 连接拒绝] 无法连接到 %s, 错误: %s", req_tag, url, exc
            )
        except Exception as exc:
            logger.error("[%s] ❌ [Prefill 异常]: %s", req_tag, exc, exc_info=True)

    async def _stream_decode(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        req_tag: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        [阶段 2: Decode 执行与流式推流生成器]
        向 Decode 实例发起异步 HTTP 请求.
        """
        url = f"{DECODE_BASE}{request_path}"
        start_ts = time.perf_counter()
        first_chunk_ts = None
        chunk_count = 0
        total_bytes = 0

        logger.info(
            "[%s] ➡️ [Decode 接入] 发送至 Decode 节点等待 KV 并流式生成: %s",
            req_tag,
            url,
        )
        logger.debug(
            "[%s] 📦 Decode 原始参数摘要: max_tokens=%s, stream=%s, model=%s",
            req_tag,
            payload.get("max_tokens"),
            payload.get("stream"),
            payload.get("model"),
        )
        logger.debug(
            "[%s] 🏷️ Decode 请求携带的 X-Request-Id: %s",
            req_tag,
            headers.get("X-Request-Id"),
        )

        try:
            logger.debug(
                "[%s] 🌐 正在初始化 Decode HTTP ClientSession (Timeout=%.1fs)...",
                req_tag,
                args.timeout,
            )
            async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
                logger.debug(
                    "[%s] 📤 正在向 Decode 节点发起 HTTP POST 请求...", req_tag
                )
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    resp_content_type = resp.headers.get("Content-Type", "unknown")
                    logger.debug(
                        "[%s] 📥 Decode 节点已响应: HTTP %d, Content-Type: %s",
                        req_tag,
                        resp_status,
                        resp_content_type,
                    )

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

                    logger.info(
                        "[%s] 🔄 [Decode 连接建立] 开始以流式方式接收 Token...", req_tag
                    )

                    async for chunk in resp.content.iter_chunked(1024):
                        if not chunk:
                            logger.debug("[%s] ⚠️ 收到空的流式数据块, 跳过", req_tag)
                            continue

                        now = time.perf_counter()
                        if first_chunk_ts is None:
                            first_chunk_ts = now
                            ttft = first_chunk_ts - start_ts
                            logger.info(
                                "[%s] ⚡ [首 Token 产生] TTFT (首字延迟): %.3f 秒, 首块大小: %d 字节",
                                req_tag,
                                ttft,
                                len(chunk),
                            )
                        else:
                            logger.debug(
                                "[%s] 📦 接收 Token 流数据块 #%d, 大小: %d 字节",
                                req_tag,
                                chunk_count + 1,
                                len(chunk),
                            )

                        chunk_count += 1
                        total_bytes += len(chunk)
                        yield chunk

                    total_elapsed = time.perf_counter() - start_ts
                    logger.info(
                        "[%s] ⬅️ [Decode 传输结束] 成功! 总耗时: %.3f 秒, 数据块: %d, 大小: %.2f KB, 平均速率: %.2f KB/s",
                        req_tag,
                        total_elapsed,
                        chunk_count,
                        total_bytes / 1024.0,
                        (
                            (total_bytes / 1024.0) / total_elapsed
                            if total_elapsed > 0
                            else 0.0
                        ),
                    )

        except asyncio.TimeoutError:
            logger.error(
                "[%s] ❌ [Decode 超时] 超过全局超时 %.1f 秒限制", req_tag, args.timeout
            )
            yield b'{"error": "Decode backend timeout"}'
        except aiohttp.ClientConnectorError as exc:
            logger.error(
                "[%s] ❌ [Decode 无法连接] 地址: %s, 异常: %s", req_tag, url, exc
            )
            yield json.dumps(
                {"error": f"Decode connection refused: {str(exc)}"}
            ).encode("utf-8")
        except Exception as exc:
            logger.error("[%s] ❌ [Decode 连接异常]: %s", req_tag, exc, exc_info=True)
            yield json.dumps({"error": f"Decode connection error: {str(exc)}"}).encode(
                "utf-8"
            )

    async def process_request() -> Response:
        """主流程编排控制管道"""
        request_start_time = time.perf_counter()
        req_tag = f"Req-{uuid.uuid4().hex[:8]}"

        req_path = request.path
        req_method = request.method
        logger.debug(
            "[%s] 🔍 开始捕获客户端请求元数据: %s %s", req_tag, req_method, req_path
        )

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
        temperature = original_request_data.get("temperature", "default")

        prompt_preview = ""
        if "prompt" in original_request_data:
            p = str(original_request_data["prompt"])
            prompt_preview = (p[:50] + "...") if len(p) > 50 else p
        elif "messages" in original_request_data:
            msgs = original_request_data["messages"]
            prompt_preview = f"Messages(count={len(msgs)})"

        logger.info(
            "[%s] 📥 接收请求 -> 路由: %s, 模型: %s, max_tokens: %s, stream: %s, temperature: %s, 提示摘要: [%s]",
            req_tag,
            req_path,
            model,
            max_tokens,
            stream,
            temperature,
            prompt_preview,
        )

        # 步骤 1: 构造 Prefill 专属请求体
        logger.debug(
            "[%s] 🛠️ [步骤 1/3] 开始克隆并改写 Prefill 专属 Payload...", req_tag
        )
        prefill_request = original_request_data.copy()
        prefill_request["max_tokens"] = 1
        if "max_completion_tokens" in prefill_request:
            prefill_request["max_completion_tokens"] = 1
            logger.debug("[%s] 强制将 max_completion_tokens 重写为 1", req_tag)
        prefill_request["stream"] = False
        logger.debug(
            "[%s] 强制将 Prefill 的 stream 参数重写为 False (禁止 SSE 悬挂)", req_tag
        )

        # 步骤 2: 构造底层 NCCL 拓扑寻址 Request-ID
        logger.debug(
            "[%s] 🛠️ [步骤 2/3] 正在构造 NCCL P2P 物理寻址 Request-ID...", req_tag
        )
        unique_token = uuid.uuid4().hex
        full_request_id = (
            f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_"
            f"{DECODE_KV_ADDR}_{unique_token}"
        )
        headers = _build_headers(full_request_id)
        logger.debug("[%s] 🔑 生成的 P2P 寻址 Request-ID: %s", req_tag, full_request_id)

        # 步骤 3: 激活并发流水线
        logger.info("[%s] 🚀 [阶段 1] 激活 Prefill 节点计算与 KV 传输...", req_tag)
        prefill_task = asyncio.create_task(
            _run_prefill_task(req_path, prefill_request, headers, req_tag)
        )
        logger.debug(
            "[%s] 协程任务已放入 asyncio 事件循环: TaskID=%s", req_tag, id(prefill_task)
        )

        logger.debug(
            "[%s] ⏱️ 正在执行微时差让步 (sleep 0.05s) 以确保 Prefill ZMQ 服务端完成广播...",
            req_tag,
        )
        await asyncio.sleep(0.05)
        logger.debug("[%s] ⏱️ 微时差让步结束, 开始激活 Decode 阶段", req_tag)

        logger.info("[%s] 🚀 [阶段 2] 接入 Decode 节点管道...", req_tag)

        async def response_stream():
            logger.debug(
                "[%s] 🌊 客户端响应流开始消费 (response_stream iterator activated)",
                req_tag,
            )
            try:
                async for chunk in _stream_decode(
                    req_path, original_request_data, headers, req_tag
                ):
                    yield chunk
            except Exception as stream_err:
                logger.error(
                    "[%s] 💥 response_stream 迭代异常: %s",
                    req_tag,
                    stream_err,
                    exc_info=True,
                )
                raise
            finally:
                if not prefill_task.done():
                    logger.warning(
                        "[%s] 🧹 数据推流已结束但 Prefill 任务尚未完成, 正在触发主动取消...",
                        req_tag,
                    )
                    prefill_task.cancel()
                    try:
                        await prefill_task
                    except asyncio.CancelledError:
                        logger.debug("[%s] ✅ Prefill 协程已成功取消", req_tag)
                    except Exception as clean_err:
                        logger.error(
                            "[%s] ⚠️ 取消 Prefill 协程时捕获异常: %s",
                            req_tag,
                            clean_err,
                        )
                else:
                    logger.debug(
                        "[%s] ✅ 响应流结束, Prefill 任务已正常完毕 (Task Status: Done)",
                        req_tag,
                    )

        logger.debug("[%s] 📦 正在封装 Quart Streaming Response...", req_tag)
        response = await make_response(response_stream())
        response.timeout = None
        logger.debug(
            "[%s] 🛡️ 已禁用 Quart Response Timeout (response.timeout=None)", req_tag
        )

        elapsed_setup = time.perf_counter() - request_start_time
        logger.info(
            "[%s] 🔗 双向流水线就绪 (调度层握手耗时: %.3f 秒)",
            req_tag,
            elapsed_setup,
        )
        return response

    # 路由注册与服务透传
    @app.route("/v1/completions", methods=["POST"])
    @app.route("/v1/chat/completions", methods=["POST"])
    async def handle_request():
        req_start = time.perf_counter()
        logger.debug("🌐 [HTTP 入口] 收到路由命中: %s %s", request.method, request.path)
        try:
            resp = await process_request()
            logger.debug(
                "🌐 [HTTP 出口] 成功生成响应对象: %s %s (耗时: %.3fs)",
                request.method,
                request.path,
                time.perf_counter() - req_start,
            )
            return resp
        except asyncio.CancelledError:
            logger.warning(
                "⚠️ 客户端主动中断连接 (Request Cancelled by Client): %s", request.path
            )
            return Response(b'{"error": "Request cancelled"}', status=503)
        except Exception as exc:
            logger.exception("💥 Proxy 处理异常: %s", str(exc))
            return Response(
                json.dumps({"error": f"Internal proxy error: {str(exc)}"}),
                status=500,
                content_type="application/json",
            )

    @app.route("/v1/models", methods=["GET"])
    async def handle_models():
        target_url = f"{DECODE_BASE}/v1/models"
        logger.debug(
            "🔍 收到模型探活请求 GET /v1/models, 准备穿透请求 Decode: %s", target_url
        )
        start_ts = time.perf_counter()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(target_url) as resp:
                    data = await resp.read()
                    elapsed = time.perf_counter() - start_ts
                    logger.debug(
                        "✅ Decode /v1/models 返回状态: %d, 大小: %d 字节, 耗时: %.3fs",
                        resp.status,
                        len(data),
                        elapsed,
                    )
                    return Response(
                        data, status=resp.status, content_type="application/json"
                    )
        except Exception as e:
            logger.error("❌ 转发 /v1/models 请求失败: %s", e)
            return Response(json.dumps({"error": str(e)}), status=500)

    # 启动 ASGI 服务
    logger.info("🎬 Quart ASGI 服务已进入事件循环, 监听端口 %d...", args.port)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
