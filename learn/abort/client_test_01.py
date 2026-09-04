import asyncio
import httpx
import time
import uuid

URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL_NAME = "Qwen2.5-7B-Instruct"


async def main():
    req_id = f"req-{uuid.uuid4().hex[:8]}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好. ",
            }
        ],
        "max_tokens": 4096,  # 故意设置极大 token 数
        "temperature": 0.7,
        "stream": True,
        "request_id": req_id,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer my_secret_token_123",
        "X-Request-Id": req_id,
    }

    print(f"[{time.strftime('%X')}] 发起长文本流式请求...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # 使用流式上下文管理器
        async with client.stream(
            "POST", URL, json=payload, headers=headers
        ) as response:
            count = 0
            async for chunk in response.aiter_lines():
                if chunk.strip():
                    count += 1
                    print(f"[{time.strftime('%X')}] 收到 Token 块 {count}...")

                    # 当接收到第 10 个 chunk 时, 主动跳出并关闭连接
                    if count >= 10:
                        print(
                            f"[{time.strftime('%X')}] >>> 客户端主动中断连接 (Abort) <<<"
                        )
                        break

    print(f"[{time.strftime('%X')}] 客户端连接已完全销毁. 进入等待观察期...")
    # 保持脚本休眠, 方便观察服务端在这期间是否还在偷跑计算
    await asyncio.sleep(20)


if __name__ == "__main__":
    asyncio.run(main())
