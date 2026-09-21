# SPDX-License-Identifier: Apache-2.0
"""vLLM 预填充与解码分离 (Disaggregated Prefill & Decode, P/D 分离) 协调代理服务器 (Proxy Server)

[核心架构背景与设计原理]
在传统的单实例 LLM 服务中, 计算密集的 Prefill 阶段(对输入 Prompt 并行计算 Attention)
与显存带宽受限的 Decode 阶段(逐个自回归串行生成 Token)相互争抢计算单元与显存带宽,
容易产生严重的推理气泡(Bubbles)和首字延迟(TTFT)抖动.

本 Proxy 的职责是作为外部客户端与后端两个异构 vLLM 实例之间的"控制面调度中枢":
1. 流量入口: 统一暴露符合 OpenAI 规范的 HTTP 接口 (/v1/completions 和 /v1/chat/completions).
2. 请求改写: 收到请求后克隆一份, 强制指定 `max_tokens=1` 发送给 Prefill 实例.
3. 拓扑寻址注入: 在 Request-ID 中编码两端的物理传输套接字, 触发底层 GPU 间的 NVLink/PCIe P2P KV Cache 直传.
4. 解码流转发: Prefill 阶段完成瞬间, 将原始完整请求发往 Decode 实例, 并将自回归生成的 Token 流式推回给客户端.
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
# 日志配置: 统一时间戳与模块名格式, 确保在多并发协程场景下日志清晰有序
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] [%(process)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("vLLM-Disagg-Proxy")


def parse_args():
    """解析命令行参数, 支持从容器环境或外部命令行灵活覆盖后端地址与端口配置"""
    parser = argparse.ArgumentParser(
        description="vLLM P/D 分离代理调度服务",
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
        default=21600.0,
        help="与后端 Prefill/Decode 实例交互的全局 HTTP 超时上限 (秒), 长文本生成需调高",
    )
    parser.add_argument(
        "--prefill-url",
        type=str,
        default="http://localhost:8100",
        help="Prefill 阶段后端的 HTTP 根路径 (KV Producer 实例)",
    )
    parser.add_argument(
        "--decode-url",
        type=str,
        default="http://localhost:8200",
        help="Decode 阶段后端的 HTTP 根路径 (KV Consumer 实例)",
    )
    parser.add_argument(
        "--kv-host",
        type=str,
        default="127.0.0.1",
        help="后端 vLLM 实例用于底包 NCCL 传输物理通信的 Host/IP 地址",
    )
    parser.add_argument(
        "--prefill-kv-port",
        type=int,
        default=14579,
        help="Prefill 实例暴露的底层 NCCL/P2P 通信 Bootstrap 端口",
    )
    parser.add_argument(
        "--decode-kv-port",
        type=int,
        default=14580,
        help="Decode 实例暴露的底层 NCCL/P2P 通信 Bootstrap 端口",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 初始化 aiohttp 全局超时对象, 防止网络悬挂
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)

    PREFILL_SERVICE_URL = args.prefill_url
    DECODE_SERVICE_URL = args.decode_url

    # 构造底层 GPU 通信协议的端点字符串 (IP:Port)
    PREFILL_KV_ADDR = f"{args.kv_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{args.kv_host}:{args.decode_kv_port}"

    logger.info("=" * 70)
    logger.info("🚀 启动 vLLM P/D 分离代理调度服务器 (Disagg Proxy Server)")
    logger.info("  - 监听地址 (Proxy Port)     : %s:%d", args.host, args.port)
    logger.info("  - Prefill 节点 HTTP 地址     : %s", PREFILL_SERVICE_URL)
    logger.info("  - Decode 节点 HTTP 地址      : %s", DECODE_SERVICE_URL)
    logger.info("  - Prefill 物理 KV 通信套接字 : %s", PREFILL_KV_ADDR)
    logger.info("  - Decode 物理 KV 通信套接字  : %s", DECODE_KV_ADDR)
    logger.info("  - 全局后端请求超时限制       : %.1f 秒", args.timeout)
    logger.info("=" * 70)

    # 实例化 Quart 应用 (ASGI 异步 Web 框架, 完美兼容 Flask 路由语法但支持真正协程非阻塞)
    app = Quart(__name__)

    def _normalize_base_url(url: str) -> str:
        """格式化 URL, 移除末尾斜杠, 防止与请求子路径拼接产生双斜杠导致 404"""
        return url.rstrip("/")

    def _get_host_port(url: str) -> str:
        """从完整的 URL 中解析出 host:port 字符串, 用于注入 X-KV-Target 请求头"""
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (80 if parsed.scheme == "http" else 443)
        return f"{host}:{port}"

    PREFILL_BASE = _normalize_base_url(PREFILL_SERVICE_URL)
    DECODE_BASE = _normalize_base_url(DECODE_SERVICE_URL)
    KV_TARGET = _get_host_port(DECODE_SERVICE_URL)

    def _build_headers(request_id: str) -> dict[str, str]:
        """构建向下游转发的专属 HTTP 请求头
        - X-Request-Id: 核心元数据载体, 携带底层点对点 P2P 通信的连接寻址信息.
        - X-KV-Target: 告知 Prefill 节点其计算生成的 KV Cache 最终输出的目的端.
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

    async def _run_prefill(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
        req_tag: str,
    ) -> None:
        """[阶段 1: Prefill 执行控制]
        向 Prefill 实例发起异步 HTTP 请求.
        目的: 令 Prefill GPU 计算输入文本全部 Prompt 的 Attention 键值并生成 KV Cache.
        底层逻辑: 该实例中的 P2pNcclConnector 会通过网络/NVLink 将 KV 直接拷贝到 Decode 节点的显存中.
        """
        url = f"{PREFILL_BASE}{request_path}"
        start_ts = time.perf_counter()

        logger.info(
            "[%s] ➡️ [阶段 1/2: Prefill 发起] 正在请求 Prefill 节点: %s (max_tokens 强制设为 1)",
            req_tag,
            url,
        )

        try:
            async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    if resp_status != 200:
                        err_text = await resp.text()
                        logger.error(
                            "[%s] ❌ [阶段 1/2: Prefill 失败] HTTP 状态码: %d, 错误详情: %s",
                            req_tag,
                            resp_status,
                            err_text,
                        )
                        raise RuntimeError(
                            f"Prefill backend error (HTTP {resp_status}): {err_text}"
                        )

                    # 核心机制: 使用 await resp.read() 确保读取完整响应体,
                    # 只有 Prefill 节点完全执行完并触发底层发送动作后, 该连接才会彻底结束并返回
                    await resp.read()
                    elapsed = time.perf_counter() - start_ts
                    logger.info(
                        "[%s] ⬅️ [阶段 1/2: Prefill 完毕] 成功! 耗时: %.3f 秒 (KV Cache 已通过 P2pNccl 推送给 Decode)",
                        req_tag,
                        elapsed,
                    )

        except asyncio.TimeoutError as exc:
            logger.error("[%s] ❌ [阶段 1/2: Prefill 超时] 请求耗时超过限制", req_tag)
            raise RuntimeError(f"Prefill 服务在 {url} 发生超时") from exc
        except aiohttp.ClientError as exc:
            logger.error("[%s] ❌ [阶段 1/2: Prefill 无法连接] 错误: %s", req_tag, exc)
            raise RuntimeError(f"Prefill 服务在 {url} 不可用") from exc

    async def _stream_decode(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
        req_tag: str,
    ) -> AsyncGenerator[bytes, None]:
        """[阶段 2: Decode 执行与流式返回]
        向 Decode 实例发起异步 HTTP 请求.
        目的: Decode 节点收到带有相同 request_id 的请求时, 先从本地已接收到的 KV Cache 缓冲区定位并加载数据,
              随后仅进行低延迟的自回归 Token 解码, 并通过 HTTP SSE 数据块实时推流返回.
        """
        url = f"{DECODE_BASE}{request_path}"
        start_ts = time.perf_counter()
        first_chunk_ts = None
        chunk_count = 0
        total_bytes = 0

        logger.info(
            "[%s] ➡️ [阶段 2/2: Decode 发起] 正在请求 Decode 节点: %s (恢复原始生成参数)",
            req_tag,
            url,
        )

        try:
            async with aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session:
                async with session.post(url=url, json=payload, headers=headers) as resp:
                    resp_status = resp.status
                    if resp_status != 200:
                        err_text = await resp.text()
                        logger.error(
                            "[%s] ❌ [阶段 2/2: Decode 失败] HTTP 状态码: %d, 错误详情: %s",
                            req_tag,
                            resp_status,
                            err_text,
                        )
                        err_payload = json.dumps(
                            {"error": f"Decode backend error {resp_status}: {err_text}"}
                        )
                        yield err_payload.encode("utf-8")
                        return

                    logger.info(
                        "[%s] 🔄 [阶段 2/2: Decode 连接建立] 状态码: 200, 开始以流式方式接收 Token...",
                        req_tag,
                    )

                    # 逐块异步迭代读取二进制流(支持 SSE 格式的 Server-Sent Events)
                    async for chunk in resp.content.iter_chunked(1024):
                        if not chunk:
                            continue

                        now = time.perf_counter()
                        if first_chunk_ts is None:
                            first_chunk_ts = now
                            ttft = first_chunk_ts - start_ts
                            logger.info(
                                "[%s] ⚡ [阶段 2/2: 首次 Token 吐出] 首块到达耗时 (TTFT): %.3f 秒",
                                req_tag,
                                ttft,
                            )

                        chunk_count += 1
                        total_bytes += len(chunk)
                        yield chunk

                    total_elapsed = time.perf_counter() - start_ts
                    logger.info(
                        "[%s] ⬅️ [阶段 2/2: Decode 传输结束] 成功! 总耗时: %.3f 秒, 数据块数: %d, 传输量: %.2f KB",
                        req_tag,
                        total_elapsed,
                        chunk_count,
                        total_bytes / 1024.0,
                    )

        except asyncio.TimeoutError:
            logger.error("[%s] ❌ [阶段 2/2: Decode 超时] 请求耗时超过限制", req_tag)
            yield b'{"error": "Decode service timeout"}'
        except aiohttp.ClientError as exc:
            logger.error("[%s] ❌ [阶段 2/2: Decode 连接异常] 错误: %s", req_tag, exc)
            yield b'{"error": "Decode service connection error"}'

    async def process_request() -> Response:
        """[请求处理主编排管道]
        负责将外部单次 REST 请求转化为底层多阶段流式编排调用
        """
        request_start_time = time.perf_counter()
        raw_uuid = uuid.uuid4().hex[:8]  # 生成 8 位短 UUID 用于日志标识
        req_tag = f"Req-{raw_uuid}"

        # 1. 尝试解析输入 JSON 负载
        try:
            original_request_data = await request.get_json()
            if not isinstance(original_request_data, dict):
                raise ValueError("Payload 必须为有效的 JSON 对象")
        except Exception as e:
            logger.warning("[%s] ⚠️ 收到无效的请求体: %s", req_tag, str(e))
            return Response(
                json.dumps({"error": f"Invalid JSON body: {str(e)}"}),
                status=400,
                content_type="application/json",
            )

        # 提取请求特征以丰富日志
        model = original_request_data.get("model", "unknown")
        max_tokens = original_request_data.get("max_tokens", "default")
        stream = original_request_data.get("stream", False)
        prompt_preview = ""
        if "prompt" in original_request_data:
            p = str(original_request_data["prompt"])
            prompt_preview = (p[:40] + "...") if len(p) > 40 else p
        elif "messages" in original_request_data:
            prompt_preview = f"Messages(count={len(original_request_data['messages'])})"

        logger.info(
            "[%s] 📥 接收到外部客户端请求 -> 路由: %s, 模型: %s, 请求最大Token: %s, 流式: %s, 提示摘要: [%s]",
            req_tag,
            request.path,
            model,
            max_tokens,
            stream,
            prompt_preview,
        )

        # ----------------------------------------------------------------------
        # 步骤 1: 构造 Prefill 专属请求
        # ----------------------------------------------------------------------
        # 深度复制一份请求, 避免修改原始参数
        prefill_request = original_request_data.copy()
        # 核心拦截逻辑: 强制将 max_tokens 改写为 1.
        # 目的: 让 Prefill 实例仅计算 Prompt 的键值对并触发 P2P 传输, 立即退出, 坚决不进行自回归计算
        prefill_request["max_tokens"] = 1
        if "max_completion_tokens" in prefill_request:
            prefill_request["max_completion_tokens"] = 1

        # ----------------------------------------------------------------------
        # 步骤 2: 构造特殊编码的 Request-ID (P/D 通信寻址核心协议)
        # ----------------------------------------------------------------------
        # 该特殊的 request_id 将两端的底层物理网络地址打包在一起.
        # 内部的 P2pNcclConnector 会解析这个字符串, 使得无需引入外部 Redis 或协调注册中心,
        # Prefill 实例便可直接得知应该向哪一个 Decode 实例地址 (DECODE_KV_ADDR) 投递 KV Cache.
        full_request_id = (
            f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_"
            f"{DECODE_KV_ADDR}_{uuid.uuid4().hex}"
        )
        headers = _build_headers(full_request_id)

        logger.debug("[%s] 生成的 P2P 寻址 Request-ID: %s", req_tag, full_request_id)

        # ----------------------------------------------------------------------
        # 步骤 3: 串行触发 Prefill 与 Decode 两个阶段
        # ----------------------------------------------------------------------
        # 先执行 Prefill (阻塞等待计算与传输完成)
        await _run_prefill(
            request.path, prefill_request, headers, full_request_id, req_tag
        )

        # 再触发 Decode 流 (流式异步生成器)
        generator = _stream_decode(
            request.path, original_request_data, headers, full_request_id, req_tag
        )

        # 将异步生成器封装为 Quart 的流式 HTTP 响应
        response = await make_response(generator)
        # 关键配置: 必须禁用超时, 防止在大模型长文本输出或长时间暂停时被 Web 框架强制斩断
        response.timeout = None

        logger.info(
            "[%s] 🔗 已建立与客户端的流式输出管道 (调度层就绪耗时: %.3f 秒)",
            req_tag,
            time.perf_counter() - request_start_time,
        )
        return response

    # ==========================================================================
    # 路由注册: 兼容标准 OpenAI 补全与对话补全接口
    # ==========================================================================
    @app.route("/v1/completions", methods=["POST"])
    @app.route("/v1/chat/completions", methods=["POST"])
    async def handle_request():
        try:
            return await process_request()
        except asyncio.CancelledError:
            # 客户端异常中断 (如主动断开网络连接或关闭浏览器)
            logger.warning("⚠️ 客户端主动断开了当前 HTTP 连接 (Request Cancelled)")
            return Response(
                b'{"error": "Request cancelled by client"}',
                status=503,
                content_type="application/json",
            )
        except Exception as exc:
            logger.exception(
                "💥 调度请求处理过程中发生未捕获的严重内部异常: %s", str(exc)
            )
            return Response(
                json.dumps({"error": f"Internal server error: {str(exc)}"}).encode(
                    "utf-8"
                ),
                status=500,
                content_type="application/json",
            )

    # 启动 ASGI 服务
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
