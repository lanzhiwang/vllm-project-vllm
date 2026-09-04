import time
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="my_secret_token_123")


def test_openai_stream_abort():
    print(f"[{time.strftime('%X')}] 发起 OpenAI SDK 流式请求...")

    stream = client.chat.completions.create(
        model="Qwen2.5-7B-Instruct",
        messages=[
            {
                "role": "user",
                "content": "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好.",
            }
        ],
        max_tokens=4096,
        stream=True,
    )

    count = 0
    try:
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                count += 1
                print(f"收到第 {count} 个 token: {delta}")
                if count >= 10:
                    print(
                        f"\n[{time.strftime('%X')}] >>> 触发强制中断 stream.close() <<<"
                    )
                    stream.close()  # 关闭 HTTP 流
                    break
    except Exception as e:
        print(f"异常: {e}")

    print(f"[{time.strftime('%X')}] 进入 15 秒观察期...")
    time.sleep(15)


if __name__ == "__main__":
    test_openai_stream_abort()
