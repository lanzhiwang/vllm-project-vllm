import os
import sys
import time
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="my_secret_token_123",  # 如果方案二去掉了 api-key, 这里写 "EMPTY"
)


def test_hard_kill():
    print(f"[{time.strftime('%X')}] 发起流式请求...")
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
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            count += 1
            print(f"Token {count}: {delta}")
            if count >= 10:
                print(
                    f"[{time.strftime('%X')}] >>> 立即触发 os._exit(0) 强制销毁进程 <<<"
                )
                sys.stdout.flush()
                # 关键点: 直接让内核回收所有 socket fd 并发送 TCP RST
                os._exit(0)


if __name__ == "__main__":
    test_hard_kill()
