import json

from aiohttp import web, ClientSession, ClientTimeout

# 指向你目前宿主机上映射的 vLLM 端口
UPSTREAM_VLLM_URL = "http://172.16.10.51:8090"
PROXY_PORT = 8091
FAIL_AFTER_CHUNKS = 5  # 在输出第 5 个 Chunk 后强制断开


async def proxy_handler(request: web.Request):
    target_url = f"{UPSTREAM_VLLM_URL}{request.rel_url}"
    body = await request.read()

    # 1. 打印客户端发来的请求详情
    print("\n" + "=" * 35 + " [Proxy] 收到下游客户端请求 " + "=" * 35)
    print(f"URL: {request.method} {request.rel_url} (来自: {request.remote})")
    print("----- 请求头 (Request Headers) -----")
    for k, v in request.headers.items():
        # 高亮展示 request id 相关头
        print(f"  {k}: {v}")

    print("----- 请求体 (Request Body) -----")
    try:
        body_json = json.loads(body.decode("utf-8"))
        print(json.dumps(body_json, indent=4, ensure_ascii=False))
    except Exception:
        print(body.decode("utf-8", errors="ignore"))

    # 清理逐跳请求头, 重新打包转发给上游
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "transfer-encoding")
    }

    print("=" * 90)
    print(f"正在将请求转发至上游 vLLM: {target_url} ...")

    timeout = ClientTimeout(total=120)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.request(
                method=request.method, url=target_url, headers=headers, data=body
            ) as upstream_resp:
                # 2. 打印上游 vLLM 返回的响应详情
                print("\n" + "=" * 35 + " [Proxy] 收到上游 vLLM 响应 " + "=" * 35)
                print(f"Status: {upstream_resp.status} {upstream_resp.reason}")
                print("----- 响应头 (Upstream Headers) -----")
                for k, v in upstream_resp.headers.items():
                    print(f"  {k}: {v}")
                print("=" * 90 + "\n")

                # 建立与客户端的流式回传
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

                    # 打印 Chunk 日志
                    print(
                        f"[SSE Chunk #{chunk_count}] 大小: {len(chunk)} 字节 | 片段预览: {raw_text.strip()}..."
                    )

                    # 达到指定阈值, 实施故障注入
                    if chunk_count > FAIL_AFTER_CHUNKS:
                        print("\n" + "!" * 30 + " [故障注入触发] " + "!" * 30)
                        print(
                            f"⚡ 已转发 {chunk_count-1} 个 Chunk, 阈值达到! 立即强制斩断 TCP 传输 (TCP RST)!"
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
        f"混沌代理已启动: 监听端口 0.0.0.0:{PROXY_PORT} -> 转发至 {UPSTREAM_VLLM_URL}"
    )
    web.run_app(app, host="0.0.0.0", port=PROXY_PORT)
