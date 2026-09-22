import json
import os
from aiohttp import ClientSession, ClientTimeout, web

UPSTREAM_VLLM_URL = os.getenv("UPSTREAM_VLLM_URL", "http://127.0.0.1:8000")
PROXY_PORT = int(os.getenv("PROXY_PORT", "8001"))
FAIL_AFTER_CHUNKS = int(os.getenv("FAIL_AFTER_CHUNKS", "5"))


async def proxy_handler(request: web.Request):
    target_url = f"{UPSTREAM_VLLM_URL}{request.rel_url}"
    body = await request.read()

    print("\n" + "=" * 35 + " [Chaos Proxy] 收到下游客户端请求 " + "=" * 35)
    print(f"URL: {request.method} {request.rel_url} (来自: {request.remote})")
    print("----- 请求头 (Request Headers) -----")
    for k, v in request.headers.items():
        print(f"  {k}: {v}")

    print("----- 请求体 (Request Body) -----")
    try:
        body_json = json.loads(body.decode("utf-8"))
        print(json.dumps(body_json, indent=4, ensure_ascii=False))
    except Exception:
        print(body.decode("utf-8", errors="ignore"))

    # 清理逐跳请求头
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "transfer-encoding")
    }

    print("=" * 90)
    print(f"正在将请求转发至上游 vLLM: {target_url} ...")

    timeout = ClientTimeout(total=180)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
            ) as upstream_resp:
                print("\n" + "=" * 35 + " [Chaos Proxy] 收到上游 vLLM 响应 " + "=" * 35)
                print(f"Status: {upstream_resp.status} {upstream_resp.reason}")
                print("=" * 90 + "\n")

                downstream_resp = web.StreamResponse(
                    status=upstream_resp.status,
                    reason=upstream_resp.reason,
                    headers=upstream_resp.headers,
                )
                await downstream_resp.prepare(request)

                chunk_count = 0
                async for chunk in upstream_resp.content.iter_any():
                    chunk_count += 1
                    raw_text = chunk.decode("utf-8", errors="ignore")
                    print(
                        f"[SSE Chunk #{chunk_count}] 大小: {len(chunk)} 字节 | 预览: {raw_text.strip()[:60]}..."
                    )

                    # 达到指定阈值且属于流式输出时中断
                    if FAIL_AFTER_CHUNKS > 0 and chunk_count > FAIL_AFTER_CHUNKS:
                        print("\n" + "!" * 30 + " [传输层故障注入触发] " + "!" * 30)
                        print(
                            f"⚡ 已转发 {chunk_count - 1} 个 Chunk, 达到阈值! 立即强制斩断 TCP 传输 (TCP Abort/RST)!"
                        )
                        print("!" * 80 + "\n")
                        if request.transport:
                            request.transport.abort()
                        return downstream_resp

                    await downstream_resp.write(chunk)

                await downstream_resp.write_eof()
                return downstream_resp

        except Exception as e:
            print(f"[Chaos Proxy] 异常: {e}", exc_info=True)
            raise


app = web.Application()
app.router.add_route("*", "/{path:.*}", proxy_handler)

if __name__ == "__main__":
    print(
        f"[Chaos Proxy] 启动中: 监听 0.0.0.0:{PROXY_PORT} -> 转发至 {UPSTREAM_VLLM_URL}"
    )
    print(
        f"[Chaos Proxy] 截断阈值: 每轮流式传输将在第 {FAIL_AFTER_CHUNKS} 个 Chunk 后直接 Reset 连接"
    )
    web.run_app(app, host="0.0.0.0", port=PROXY_PORT)
