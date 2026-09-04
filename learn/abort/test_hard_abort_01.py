import json
import socket
import struct
import time
import requests

URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL_NAME = "Qwen2.5-7B-Instruct"


def test_hard_abort():
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "请详细写一篇关于人类探索宇宙历史的万字长文, 越详细越好.",
            }
        ],
        "max_tokens": 4096,
        "stream": True,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer my_secret_token_123",
    }

    print(f"[{time.strftime('%X')}] 发起请求...")
    response = requests.post(
        URL, json=payload, headers=headers, stream=True, timeout=60
    )

    count = 0
    raw_socket = None

    try:
        # 获取底层原生 TCP socket 对象
        raw_socket = response.raw._fp.fp.raw._sock
    except Exception:
        pass

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode("utf-8")
            if decoded_line.startswith("data: ") and decoded_line != "data: [DONE]":
                count += 1
                print(f"Token count: {count}")

                if count >= 10:
                    print(
                        f"\n[{time.strftime('%X')}] >>> 触发底层 Socket 强制硬切断 (TCP RST) <<<"
                    )
                    if raw_socket:
                        # 设置 SO_LINGER 超时为 0 秒, 强制发送 TCP RST 包而不是正常 FIN
                        raw_socket.setsockopt(
                            socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)
                        )
                        raw_socket.close()
                    response.close()
                    break

    print(f"[{time.strftime('%X')}] 观察服务端日志是否在第 10~15 个 Iteration 停止...")
    time.sleep(15)


if __name__ == "__main__":
    test_hard_abort()
