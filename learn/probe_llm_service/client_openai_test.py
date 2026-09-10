import json
import uuid
import httpx
from openai import OpenAI, APIConnectionError


# 利用 httpx 的事件钩子实现请求/响应的完整日志打印
def log_request(request: httpx.Request):
    print("\n" + "=" * 35 + " [Client] 发出 HTTP 请求 " + "=" * 35)
    print(f"{request.method} {request.url}")
    print("----- 发送请求头 (Client Request Headers) -----")
    for k, v in request.headers.items():
        print(f"  {k}: {v}")
    if request.content:
        print("----- 发送请求体 (Client Request Body) -----")
        try:
            print(
                json.dumps(
                    json.loads(request.content.decode()), indent=4, ensure_ascii=False
                )
            )
        except Exception:
            print(request.content.decode(errors="ignore"))
    print("=" * 90 + "\n")


def log_response(response: httpx.Response):
    print("\n" + "=" * 35 + " [Client] 收到 HTTP 首包响应 " + "=" * 35)
    print(
        f"HTTP/{response.http_version} {response.status_code} {response.reason_phrase}"
    )
    print("----- 响应头 (Client Response Headers) -----")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    print("=" * 90 + "\n")
    print(">>> 开始流式 Token 接收: ")


# 构造带有调试探针的 HTTP 客户端
http_client = httpx.Client(
    event_hooks={"request": [log_request], "response": [log_response]}, timeout=60.0
)

# 初始化 OpenAI SDK
client = OpenAI(
    base_url="http://127.0.0.1:8091/v1",
    api_key="my_secret_token_123",
    http_client=http_client,
)


def run_test():
    received_tokens = []
    finish_reason_received = None
    stream_aborted_by_transport = False

    req_id = f"req-{uuid.uuid4().hex[:16]}"

    try:
        response = client.chat.completions.create(
            model="Qwen2.5-7B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": "请详细写一篇关于量子计算的2000字综述, 包含三个核心发展方向.",
                }
            ],
            stream=True,
            temperature=0.7,
            # 同时注入标准 X-Request-Id 与自定义 X-Client-Request-Id
            extra_headers={
                "X-Request-Id": str(req_id),
                "X-Client-Request-Id": str(req_id),
            },
        )

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                delta = choice.delta.content or ""
                received_tokens.append(delta)
                print(delta, flush=True)

                if choice.finish_reason is not None:
                    finish_reason_received = choice.finish_reason

    except APIConnectionError as e:
        stream_aborted_by_transport = True
        print(
            f"\n\n\033[1;31m[Layer 4/7 捕获] 成功捕获连接层断开异常: {type(e).__name__} -> {e}\033[0m"
        )
    except Exception as e:
        stream_aborted_by_transport = True
        print(f"\n\n\033[1;31m[未知异常] 捕获: {type(e).__name__} -> {e}\033[0m")

    # ================= 完整性业务判定 =================
    print("\n" + "=" * 50)
    print("[客户端断流完整性校验结果]")
    print(f"1. 追踪 ID (req_id): {req_id}")
    print(f"2. 传输层发生截断/异常: {stream_aborted_by_transport}")
    print(f"3. 最终收到 finish_reason: {finish_reason_received}")
    print(f"4. 累计接收片段数: {len(received_tokens)}")

    if finish_reason_received is None:
        print(
            "\033[1;31m❌ [报警] 触发 Broken Stream 异常告警: 流未收到正常的 finish_reason 就中断了! \033[0m"
        )
        print(
            "   -> 客户端判定: 输出不完整, 应触发重试或向业务层抛出 IncompleteGenerationError"
        )
    else:
        print("\033[1;32m✅ [正常] 流式生成完整结束. \033[0m")


if __name__ == "__main__":
    run_test()
