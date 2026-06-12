# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import argparse
import asyncio
import logging
import os
import time
import uuid
from urllib.parse import urlparse

import aiohttp

# Quart 是一个支持 asyncio 的异步 Python Web 框架, 其 API 与 Flask 完全一致.
# 在 LLM 推理场景中, 由于需要进行高并发的长连接(SSE 流式输出)处理,
# 使用同步的 Flask 会阻塞线程池, 而 Quart 能够利用非阻塞 I/O 实现高并发.
from quart import Quart, Response, make_response, request

# 配置日志系统, 用于监控 P/D 两个阶段的延迟和状态
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """parse command line arguments"""
    parser = argparse.ArgumentParser(description="vLLM P/D disaggregation proxy server")

    # Add args
    # 超时设置: 默认 6 小时. 由于 LLM 生成长文本或排队可能耗时较长, 需要调高 HTTP 超时限制.
    parser.add_argument(
        "--timeout",
        type=float,
        default=6 * 60 * 60,
        help="Timeout for backend service requests in seconds (default: 21600)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    # 分离的两个 vLLM 服务端地址
    parser.add_argument(
        "--prefill-url",
        type=str,
        default="http://localhost:8100",
        help="Prefill service base URL (protocol + host[:port])",
    )
    parser.add_argument(
        "--decode-url",
        type=str,
        default="http://localhost:8200",
        help="Decode service base URL (protocol + host[:port])",
    )
    # 用于传输 KV Cache 数据的物理网络地址和端口.
    # 这里的端口(14579 和 14580)是 vLLM 底层传输 Connector(如 P2pNcclConnector)建立通信的物理套接字.
    parser.add_argument(
        "--kv-host",
        type=str,
        default="localhost",
        help="Hostname or IP used by KV transfer (default: localhost)",
    )
    parser.add_argument(
        "--prefill-kv-port",
        type=int,
        default=14579,
        help="Prefill KV port (default: 14579)",
    )
    parser.add_argument(
        "--decode-kv-port",
        type=int,
        default=14580,
        help="Decode KV port (default: 14580)",
    )

    return parser.parse_args()


def main():
    """parse command line arguments"""
    args = parse_args()

    # Initialize configuration using command line parameters
    # 初始化 aiohttp 的全局超时配置
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)
    PREFILL_SERVICE_URL = args.prefill_url
    DECODE_SERVICE_URL = args.decode_url
    PORT = args.port

    # 组装 Prefill 和 Decode 实例的数据通信网络端点(Socket 级别)
    PREFILL_KV_ADDR = f"{args.kv_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{args.kv_host}:{args.decode_kv_port}"

    logger.info(
        "Proxy resolved KV addresses -> prefill: %s, decode: %s",
        PREFILL_KV_ADDR,
        DECODE_KV_ADDR,
    )

    app = Quart(__name__)

    # 将配置存入 Quart 的 app.config 中, 避免使用全局变量, 利于多线程/协程安全访问.
    # Attach the configuration object to the application instance so helper
    # coroutines can read the resolved backend URLs and timeouts without using
    # globals.
    app.config.update(
        {
            "AIOHTTP_TIMEOUT": AIOHTTP_TIMEOUT,
            "PREFILL_SERVICE_URL": PREFILL_SERVICE_URL,
            "DECODE_SERVICE_URL": DECODE_SERVICE_URL,
            "PREFILL_KV_ADDR": PREFILL_KV_ADDR,
            "DECODE_KV_ADDR": DECODE_KV_ADDR,
        }
    )

    def _normalize_base_url(url: str) -> str:
        """
        Remove any trailing slash so path joins behave predictably.

        去除 URL 结尾的斜杠, 防止拼接路径时出现双斜杠(//)导致 HTTP 404 错误
        """
        return url.rstrip("/")

    def _get_host_port(url: str) -> str:
        """
        Return the hostname:port portion for logging and KV headers.

        提取 'IP:Port'. 这将被注入到 HTTP 协议头的 X-KV-Target 中,
        提示 Prefill 节点该将 KV 传输到哪个目的地址.
        """
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port
        if port is None:
            port = 80 if parsed.scheme == "http" else 443
        return f"{host}:{port}"

    PREFILL_BASE = _normalize_base_url(PREFILL_SERVICE_URL)
    DECODE_BASE = _normalize_base_url(DECODE_SERVICE_URL)
    KV_TARGET = _get_host_port(DECODE_SERVICE_URL)

    def _build_headers(request_id: str) -> dict[str, str]:
        """
        Construct the headers expected by vLLM's P2P disagg connector.

        构建发送给后端 vLLM 的 HTTP 请求头.
        - X-Request-Id: 极重要, 不仅是追踪号, 还暗含了 P2P 节点的寻址元数据.
        - X-KV-Target: 告知 Prefill 节点 KV Cache 最终输出的目的 HTTP 地址.
        """
        headers: dict[str, str] = {"X-Request-Id": request_id, "X-KV-Target": KV_TARGET}
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def _run_prefill(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
    ):
        """
        [Prefill 阶段控制]
        向 Prefill 实例发起请求, 令其对 Prompt 计算 Attention, 并触发底层网络将 KV 发送出去.
        """
        url = f"{PREFILL_BASE}{request_path}"
        start_ts = time.perf_counter()
        logger.info("[prefill] start request_id=%s url=%s", request_id, url)
        try:
            # 采用异步 aiohttp.ClientSession 避免网络 I/O 阻塞主循环进程
            async with (
                aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session,
                session.post(url=url, json=payload, headers=headers) as resp,
            ):
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(
                        f"Prefill backend error {resp.status}: {error_text}"
                    )
                # 使用 await resp.read() 读完全部响应体, 确保连接完全释放, 并且 Prefill 节点的计算和 KV 发送动作已彻底完成
                await resp.read()
                logger.info(
                    "[prefill] done request_id=%s status=%s elapsed=%.2fs",
                    request_id,
                    resp.status,
                    time.perf_counter() - start_ts,
                )
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Prefill service timeout at {url}") from exc
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Prefill service unavailable at {url}") from exc

    async def _stream_decode(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
    ):
        """
        [Decode 阶段控制]
        从已经接收到 KV Cache 的 Decode 节点获取流式生成的 Token.
        该函数是一个异步生成器(async generator).
        """
        url = f"{DECODE_BASE}{request_path}"
        # Stream tokens from the decode service once the prefill stage has
        # materialized KV caches on the target workers.
        logger.info("[decode] start request_id=%s url=%s", request_id, url)
        try:
            # 同样采用 aiohttp 异步请求, 以便实时流式地读取 Decode 节点返回的数据块
            async with (
                aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session,
                session.post(url=url, json=payload, headers=headers) as resp,
            ):
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        "Decode backend error %s - %s", resp.status, error_text
                    )
                    err_msg = (
                        '{"error": "Decode backend error ' + str(resp.status) + '"}'
                    )
                    yield err_msg.encode()
                    return
                logger.info(
                    "[decode] streaming response request_id=%s status=%s",
                    request_id,
                    resp.status,
                )
                # 核心非阻塞流式: 迭代以 1024 字节为单位的数据块, 实时将其 yield 回给 Quart 框架
                async for chunk_bytes in resp.content.iter_chunked(1024):
                    yield chunk_bytes
                logger.info("[decode] finished streaming request_id=%s", request_id)
        except asyncio.TimeoutError:
            logger.error("Decode service timeout at %s", url)
            yield b'{"error": "Decode service timeout"}'
        except aiohttp.ClientError as exc:
            logger.error("Decode service error at %s: %s", url, exc)
            yield b'{"error": "Decode service unavailable"}'

    async def process_request():
        """
        Process a single request through prefill and decode stages

        [请求编排主干逻辑]
        将客户端单次请求分步送往 Prefill 节点和 Decode 节点.
        """
        try:
            # 异步解析客户端传过来的 JSON 请求负载
            original_request_data = await request.get_json()

            # -------------------------------------------------------------
            # 步骤 1: 构造 Prefill 请求(截断为 1 Token 生成)
            # -------------------------------------------------------------
            # Create prefill request (max_tokens=1)
            prefill_request = original_request_data.copy()
            # 强制设置只生成 1 个 Token(或配置 max_completion_tokens)
            # 目的: 让 Prefill 节点仅计算 Prompt 的注意力键值, 产生 KV Cache 并触发 P2P 传输,
            # 之后立即结束该请求, 防止 Prefill 节点做后续的自回归解码.
            prefill_request["max_tokens"] = 1
            if "max_completion_tokens" in prefill_request:
                prefill_request["max_completion_tokens"] = 1

            # -------------------------------------------------------------
            # 步骤 2: 构造特定的 Request ID (编排设计的精髓)
            # -------------------------------------------------------------
            # 我们将 Prefill 节点和 Decode 节点的物理 KV 传输套接字编码进 Request ID 中.
            # vLLM 的底层通信网络组件(如 P2pNcclConnector)会解析此 Request ID.
            # 从而, 在没有全局路由表的情况下, Prefill 的 GPU 能够直接动态得知: 该将此请求对应的
            # KV Cache 发送到哪一个 Decode 节点的 IP 端口(DECODE_KV_ADDR).
            # Execute prefill stage
            # The request id encodes both KV socket addresses so the backend can
            # shuttle tensors directly via NCCL once the prefill response
            # completes.
            request_id = (
                f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_"
                f"{DECODE_KV_ADDR}_{uuid.uuid4().hex}"
            )

            headers = _build_headers(request_id)

            # -------------------------------------------------------------
            # 步骤 3: 串行执行控制面转发
            # -------------------------------------------------------------
            # 1. 触发 Prefill
            await _run_prefill(request.path, prefill_request, headers, request_id)

            # 2. 触发 Decode(传入未经修改的原始请求, 如原 max_tokens=256)
            # Decode 节点收到该 request_id 时, 会先通过内部底层连接拦截并加载 Prefill 发过来的 KV 缓存,
            # 然后直接进行自回归计算, 吐出剩下的 Token.
            # Execute decode stage and stream response
            # Pass the unmodified user request so the decode phase can continue
            # sampling with the already-populated KV cache.
            generator = _stream_decode(
                request.path, original_request_data, headers, request_id
            )

            # 使用 Quart 包装异步生成器为流式 HTTP 响应
            response = await make_response(generator)

            # 必须禁用 Quart 的响应超时设置, 否则长时间的 LLM 推理生成连接会由于没有新的 HTTP 请求而被中间切断.
            response.timeout = None  # Disable timeout for streaming response
            return response

        except Exception:
            logger.exception("Error processing request")
            return Response(
                response=b'{"error": "Internal server error"}',
                status=500,
                content_type="application/json",
            )

    @app.route("/v1/completions", methods=["POST"])
    async def handle_request():
        """
        Handle incoming API requests with concurrency and rate limiting

        对外部客户端暴露的统一 OpenAI 标准接口路由
        """
        try:
            return await process_request()
        except asyncio.CancelledError:
            # 必须捕获协程取消异常. 当客户端(浏览器/SDK)中途断开连接时,
            # asyncio 会向该协程发出 CancelledError, 我们需要记录并进行优雅的资源回收.
            logger.warning("Request cancelled")
            return Response(
                response=b'{"error": "Request cancelled"}',
                status=503,
                content_type="application/json",
            )

    # 启动 Quart 服务器, 开始监听来自客户端的流量
    # Start the Quart server with host can be set to 0.0.0.0
    app.run(port=PORT)


if __name__ == "__main__":
    main()
