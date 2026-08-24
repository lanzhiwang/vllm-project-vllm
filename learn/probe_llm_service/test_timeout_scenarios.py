import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from requests.exceptions import ReadTimeout, Timeout

# ==================== 1. 配置参数 ====================
REAL_BASE_URL = "https://api.gpugeek.com/v1/chat/completions"
REAL_API_KEY = "d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o"
REAL_MODEL = "Vendor3/DeepSeek-V4-Flash"

MOCK_PORT = 9998
MOCK_BASE_URL = f"http://127.0.0.1:{MOCK_PORT}/v1/chat/completions"


# ==================== 2. 本地故障注入 Mock 服务 ====================


class FaultInjectionHandler(BaseHTTPRequestHandler):
    """模拟服务端异常挂死、断流等场景"""

    def log_message(self, format, *args):
        pass  # 屏蔽默认访问日志, 保持终端整洁

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        # 根据请求内容判断要注入哪种故障
        if "sim_prefill_hang" in body:
            # 场景 A: 接收到请求后, 服务端彻底卡死, 不发任何数据(模拟 Prefill 死锁)
            time.sleep(30)
            self.send_response(200)
            self.end_headers()

        elif "sim_mid_stream_hang" in body:
            # 场景 B: 正常建立 SSE 流, 吐出 2 个 chunk 后突然挂死, 不再发数据也不关连接
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            chunk1 = 'data: {"choices":[{"delta":{"content":"你好! 这是前几个正常的Token..."}}]}\n\n'
            self.wfile.write(chunk1.encode("utf-8"))
            self.wfile.flush()

            time.sleep(0.5)
            chunk2 = (
                'data: {"choices":[{"delta":{"content":"系统正在深度推理中..."}}]}\n\n'
            )
            self.wfile.write(chunk2.encode("utf-8"))
            self.wfile.flush()

            # 💥 故障注入: 模拟 GPU Worker 突然挂起, 静默 30 秒
            time.sleep(30)


def start_mock_server():
    server = HTTPServer(("127.0.0.1", MOCK_PORT), FaultInjectionHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ==================== 3. 各种超时场景测试用例 ====================


def test_case_1_real_service_strict_timeout():
    """
    [场景 1]真实服务探测: 客户端设置极度严格的 Read Timeout (如 0.08s)
    验证客户端是否能在首 Token 产生前主动抛出 ReadTimeout, 并释放连接
    """
    print("\n" + "=" * 65)
    print("🧪 [测试 1] 真实服务首 Token 超时保护验证 (Strict TTFT Timeout)")
    print("=" * 65)

    headers = {
        "Authorization": f"Bearer {REAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": REAL_MODEL,
        "messages": [{"role": "user", "content": "请写一篇关于量子力学的长文"}],
        "stream": True,
    }

    strict_timeout = (3.0, 0.08)
    start_time = time.perf_counter()
    try:
        print(f"👉 发起请求, 设置 Client Read Timeout = {strict_timeout[1]}s...")
        resp = requests.post(
            REAL_BASE_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=strict_timeout,
        )

        for line in resp.iter_lines():
            pass

        print("❌ 未触发超时(说明模型响应极快或超时时间设大了)")
    except ReadTimeout as e:
        elapsed = time.perf_counter() - start_time
        print(f"✅ 成功捕获 ReadTimeout 异常!")
        print(f"   ⏱️ 客户端在等待 {elapsed:.3f}s 无数据后果断切断连接")
        print(f"   📋 异常类型: {type(e).__name__}")
    except Exception as e:
        print(f"⚠️ 捕获到其他异常: {type(e).__name__}: {e}")


def test_case_2_mock_prefill_hang():
    """
    [场景 2]模拟服务端死锁: 服务端接受连接但 0 字节返回
    验证客户端在设定 2.0s 超时下能否准时熔断
    """
    print("\n" + "=" * 65)
    print("🧪 [测试 2] 模拟服务端 Prefill 完全卡死 (0 字节返回)")
    print("=" * 65)

    payload = {"prompt": "sim_prefill_hang"}
    client_timeout = (2.0, 2.0)

    start_time = time.perf_counter()
    try:
        print(f"👉 发送请求到假死服务端, 客户端超时阈值: {client_timeout[1]}s...")
        resp = requests.post(
            MOCK_BASE_URL, json=payload, stream=True, timeout=client_timeout
        )
        for line in resp.iter_lines():
            pass
    except ReadTimeout:
        elapsed = time.perf_counter() - start_time
        print(f"✅ 客户端安全熔断!")
        print(f"   ⏱️ 耗时 {elapsed:.3f}s 触发 ReadTimeout, 避免了线程永久挂起")
    except Exception as e:
        print(f"❌ 捕获异常: {e}")


def test_case_3_mock_mid_stream_hang():
    """
    [场景 3]模拟流式传输中途断流(Token 吐到一半卡住)
    验证在 SSE 接收过程中, 单个 Chunk 间隔超时是否能被 requests 准确识别
    """
    print("\n" + "=" * 65)
    print("🧪 [测试 3] 模拟流式传输中途断流 (Mid-stream Silent Hang)")
    print("=" * 65)

    payload = {"prompt": "sim_mid_stream_hang"}
    chunk_timeout = (2.0, 2.0)

    start_time = time.perf_counter()
    received_chunks = []

    try:
        print(f"👉 开始流式接收, 设置单 Chunk 间隔超时 = {chunk_timeout[1]}s...")
        resp = requests.post(
            MOCK_BASE_URL, json=payload, stream=True, timeout=chunk_timeout
        )

        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                received_chunks.append(line_str)
                print(f"   📥 收到数据片段: {line_str[:50]}...")

    except ReadTimeout:
        elapsed = time.perf_counter() - start_time
        print(f"✅ 成功捕获流式中途断流异常 (ReadTimeout)! ")
        print(f"   📥 中断前已接收的 Chunk 数: {len(received_chunks)}")
        print(f"   ⏱️ 从开始到最终超时总耗时: {elapsed:.3f}s")
        print(
            "   💡 结论: `requests` 的 `read_timeout` 在流式模式下是作用于[每一个 Chunk 的到达间隔], 能有效防止中途挂死."
        )
    except Exception as e:
        print(f"❌ 未按预期捕获: {type(e).__name__}: {e}")


# ==================== 4. 生产级具备超时守护与安全解析的流式读取器 ====================


def robust_stream_reader_demo():
    """
    [生产实践]安全防御型 SSE 解析 + 超时重试客户端示范
    """
    print("\n" + "=" * 65)
    print("🛡️ [生产模式] 健壮的流式客户端示范 (含安全解析与异常防护)")
    print("=" * 65)

    headers = {
        "Authorization": f"Bearer {REAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": REAL_MODEL,
        "messages": [{"role": "user", "content": "请输出1到5五个数字"}],
        "max_tokens": 100,
        "stream": True,
    }

    # 推荐配置: 连接超时 3.0s, 每 Chunk 间隔超时上限 10.0s
    STREAM_TIMEOUT = (3.0, 10.0)

    max_retries = 2
    for attempt in range(1, max_retries + 1):
        print(f"\n🚀 第 {attempt} 次尝试发起请求...")
        t0 = time.perf_counter()

        has_printed_reasoning_header = False
        has_printed_content_header = False

        try:
            with requests.post(
                REAL_BASE_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=STREAM_TIMEOUT,
            ) as resp:
                if resp.status_code != 200:
                    print(f"⚠️ 服务端返回错误状态码: {resp.status_code} - {resp.text}")
                    break

                for line in resp.iter_lines(chunk_size=None):
                    if not line:
                        continue
                    line_str = line.decode("utf-8")
                    if line_str.startswith("data: "):
                        data_str = line_str[6:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        # ✅ 安全获取 choices 列表 (防止 choices 为空列表时报 list index out of range)
                        choices = chunk.get("choices") or []
                        if not choices:
                            # 可能是末尾附带的 usage/metrics 数据块，安全跳过或提取
                            continue

                        delta = choices[0].get("delta", {})

                        # 兼容处理思考过程 (reasoning_content) 与 正式回答 (content)
                        reasoning_piece = delta.get("reasoning_content")
                        content_piece = delta.get("content")

                        if reasoning_piece:
                            if not has_printed_reasoning_header:
                                print("\n🧠 [思考过程]: ", end="", flush=True)
                                has_printed_reasoning_header = True
                            print(reasoning_piece, end="", flush=True)

                        if content_piece:
                            if not has_printed_content_header:
                                print("\n\n💬 [正式回复]: ", end="", flush=True)
                                has_printed_content_header = True
                            print(content_piece, end="", flush=True)

            print(f"\n\n✅ 接收完成! 总耗时: {time.perf_counter() - t0:.2f}s")
            break

        except (ReadTimeout, Timeout) as e:
            print(
                f"\n⚠️ [超时告警] 服务端在 {STREAM_TIMEOUT[1]}s 内未推送新数据, 连接已断开! (原因: {e})"
            )
            if attempt < max_retries:
                print("🔄 正在执行重试...")
                time.sleep(1.0)
            else:
                print("❌ 达到最大重试次数, 执行降级逻辑.")
        except Exception as e:
            print(f"\n❌ 发生未预期的客户端异常: {type(e).__name__}: {e}")
            break


# ==================== 主入口 ====================

if __name__ == "__main__":
    # 启动本地故障注入 Mock 服务
    mock_server = start_mock_server()
    time.sleep(0.5)

    try:
        # 1. 真实环境超低阈值超时测试
        test_case_1_real_service_strict_timeout()

        # 2. 模拟 Prefill 完全卡死测试
        test_case_2_mock_prefill_hang()

        # 3. 模拟流式中途静默断流测试
        test_case_3_mock_mid_stream_hang()

        # 4. 生产级健壮代码演示
        robust_stream_reader_demo()

    finally:
        mock_server.shutdown()
        print("\n" + "=" * 65)
        print("🏁 超时测试套件执行完毕.")
        print("=" * 65)
