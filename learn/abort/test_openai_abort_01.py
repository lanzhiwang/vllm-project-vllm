import time
from openai import OpenAI

# vLLM 默认 API 地址, api_key 任意填写非空字符串即可
client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="my_secret_token_123")

MODEL_NAME = "Qwen2.5-7B-Instruct"


def test_openai_stream_abort():
    print(f"[{time.strftime('%X')}] [OpenAI SDK] 发起流式长文本请求...")

    # 启用流式输出 stream=True
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好. ",
            }
        ],
        max_tokens=4096,  # 极大 Token 数
        temperature=0.7,
        stream=True,
    )

    count = 0
    try:
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                count += 1
                print(delta, end="", flush=True)

                # 收到 10 个 token 片段后主动中断
                if count >= 10:
                    print(
                        f"\n\n[{time.strftime('%X')}] >>> [OpenAI SDK] 触发主动中断: 调用 stream.close() <<<"
                    )
                    stream.close()  # 关键点: 显式关闭底层 HTTP 流连接
                    break
    except Exception as e:
        print(f"\n捕获异常: {e}")

    print(f"[{time.strftime('%X')}] 客户端连接已关闭, 进入 20 秒静默观察期...")
    print(">>> 请观察服务端 nvidia-smi / 日志中算力与运行队列是否已经降为 0 <<<")
    time.sleep(20)


if __name__ == "__main__":
    test_openai_stream_abort()
