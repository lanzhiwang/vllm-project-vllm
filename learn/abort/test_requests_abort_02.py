import json
import time
import requests

# 远程访问
URL = "http://172.16.10.51:8090/v1/chat/completions"
MODEL_NAME = "Qwen2.5-7B-Instruct"


def test_requests_stream_abort():
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好. ",
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.7,
        "stream": True,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer my_secret_token_123",
    }

    print(f"[{time.strftime('%X')}] [requests] 发起流式长文本请求...")

    # 关键参数: stream=True
    response = requests.post(
        URL, json=payload, headers=headers, stream=True, timeout=60
    )

    count = 0
    try:
        # iter_lines 逐行读取 SSE 协议数据流 (以 "data: " 开头)
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")

                # 过滤 SSE 结束标志和非数据行
                if decoded_line.startswith("data: ") and decoded_line != "data: [DONE]":
                    data = json.loads(decoded_line[6:])
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        count += 1
                        print(delta, end="", flush=True)

                    # 收到 10 个 token 片段后主动中断
                    if count >= 10:
                        print(
                            f"\n\n[{time.strftime('%X')}] >>> [requests] 触发主动中断: 调用 response.close() <<<"
                        )
                        response.close()  # 关键点: 强制关闭 TCP 连接
                        break
    finally:
        response.close()

    print(f"[{time.strftime('%X')}] 客户端连接已完全释放, 进入 20 秒静默观察期...")
    print(">>> 请观察服务端 nvidia-smi / 日志中算力与运行队列是否已经降为 0 <<<")
    time.sleep(20)


if __name__ == "__main__":
    test_requests_stream_abort()
