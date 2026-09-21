# SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import logging
import os
import time
import uuid
from urllib.parse import urlparse

import aiohttp
from quart import Quart, Response, make_response, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DisaggProxy] %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="vLLM P/D disaggregation proxy server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Proxy 监听地址",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Proxy 对外暴露端口",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=21600,
        help="后端超时时间(秒)",
    )
    parser.add_argument(
        "--prefill-url",
        type=str,
        default="http://127.0.0.1:8100",
        help="Prefill 实例地址",
    )
    parser.add_argument(
        "--decode-url",
        type=str,
        default="http://127.0.0.1:8200",
        help="Decode 实例地址",
    )
    parser.add_argument(
        "--kv-host",
        type=str,
        default="127.0.0.1",
        help="KV P2P 传输 Host/IP",
    )
    parser.add_argument(
        "--prefill-kv-port",
        type=int,
        default=14579,
        help="Prefill 实例 KV 传输端口",
    )
    parser.add_argument(
        "--decode-kv-port",
        type=int,
        default=14580,
        help="Decode 实例 KV 传输端口",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)
    PREFILL_SERVICE_URL = args.prefill_url
    DECODE_SERVICE_URL = args.decode_url

    PREFILL_KV_ADDR = f"{args.kv_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{args.kv_host}:{args.decode_kv_port}"

    logger.info(f"Target Prefill HTTP: {PREFILL_SERVICE_URL}, KV: {PREFILL_KV_ADDR}")
    logger.info(f"Target Decode HTTP : {DECODE_SERVICE_URL}, KV: {DECODE_KV_ADDR}")

    app = Quart(__name__)

    def _normalize_base_url(url: str) -> str:
        return url.rstrip("/")

    def _get_host_port(url: str) -> str:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (80 if parsed.scheme == "http" else 443)
        return f"{host}:{port}"

    PREFILL_BASE = _normalize_base_url(PREFILL_SERVICE_URL)
    DECODE_BASE = _normalize_base_url(DECODE_SERVICE_URL)
    KV_TARGET = _get_host_port(DECODE_SERVICE_URL)

    def _build_headers(request_id: str) -> dict[str, str]:
        headers = {"X-Request-Id": request_id, "X-KV-Target": KV_TARGET}
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def _run_prefill(
        request_path: str, payload: dict, headers: dict[str, str], request_id: str
    ):
        url = f"{PREFILL_BASE}{request_path}"
        start_ts = time.perf_counter()
        async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
            async with session.post(url=url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"Prefill backend returned {resp.status}: {text}"
                    )
                await resp.read()
                logger.info(
                    f"[prefill] req_id={request_id} finished in {time.perf_counter() - start_ts:.3f}s"
                )

    async def _stream_decode(
        request_path: str, payload: dict, headers: dict[str, str], request_id: str
    ):
        url = f"{DECODE_BASE}{request_path}"
        async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
            async with session.post(url=url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Decode error {resp.status}: {text}")
                    yield f'{{"error": "Decode error {resp.status}"}}'.encode()
                    return
                async for chunk_bytes in resp.content.iter_chunked(1024):
                    yield chunk_bytes

    async def process_request():
        original_request_data = await request.get_json()
        prefill_request = original_request_data.copy()
        prefill_request["max_tokens"] = 1
        if "max_completion_tokens" in prefill_request:
            prefill_request["max_completion_tokens"] = 1

        request_id = f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_{DECODE_KV_ADDR}_{uuid.uuid4().hex}"
        headers = _build_headers(request_id)

        # 阶段 1: Prefill 生成 KV Cache 并通过 NCCL P2P 发送
        await _run_prefill(request.path, prefill_request, headers, request_id)

        # 阶段 2: Decode 节点接力加载 KV Cache 并完成后续 Token 解码
        generator = _stream_decode(
            request.path, original_request_data, headers, request_id
        )

        response = await make_response(generator)
        response.timeout = None
        return response

    @app.route("/v1/completions", methods=["POST"])
    @app.route("/v1/chat/completions", methods=["POST"])
    async def handle_request():
        try:
            return await process_request()
        except asyncio.CancelledError:
            logger.warning("Request cancelled by client")
            return Response(
                b'{"error": "Request cancelled"}',
                status=503,
                content_type="application/json",
            )
        except Exception:
            logger.exception("Error processing request")
            return Response(
                b'{"error": "Internal server error"}',
                status=500,
                content_type="application/json",
            )

    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
