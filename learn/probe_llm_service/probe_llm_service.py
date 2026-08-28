import json
import time
import requests

# ==================== 配置区域 ====================
BASE_URL = "https://api.gpugeek.com/v1/chat/completions"
API_KEY = "d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o"
MODEL_NAME = "Vendor3/DeepSeek-V4-Flash"

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ==================== 1. 性能探测 (TTFT & Throughput) ====================


def test_streaming_performance(prompt="你好, 请用200字介绍量子计算的基本原理", runs=2):
    """
    整个流式响应的完整生命周期分为 6 个阶段:
    1. 握手与角色声明: `delta: {"role": "assistant", ...}`
    2. 思考链推理阶段 (Reasoning): `delta: {"reasoning_content": "..."}`
    3. 正式回答生成阶段 (Content): `delta: {"content": "..."}`
    4. 生成结束标记: `finish_reason: "stop"`
    5. Token 与耗时统计元数据: `choices: []`, 包含 `usage` 与 `metrics`
    6. SSE 终止信号: `data: [DONE]`

    流式测试: 精确解析 Reasoning、Content、Usage 以及 data: [DONE]
    """
    print("\n" + "=" * 50)
    print(f"🚀 开始测试流式性能 (TTFT & TPOT) - 共测试 {runs} 轮")
    print("=" * 50)

    ttft_list = []
    total_time_list = []

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }

    for i in range(1, runs + 1):
        print(f"\n--- [Round {i}] 开始请求 ---")
        start_time = time.perf_counter()

        first_token_time = None  # 首 Token (含 Reasoning)
        first_content_time = None  # 首个正式回答 Token

        chunk_count = 0
        received_text = ""
        received_reasoning = ""
        server_usage = None
        server_metrics = None
        received_done_signal = False

        try:
            with requests.post(
                BASE_URL, headers=HEADERS, json=payload, stream=True, timeout=60
            ) as resp:
                if resp.status_code != 200:
                    print(
                        f"❌ 第 {i} 轮失败, HTTP 状态码: {resp.status_code}, 内容: {resp.text}"
                    )
                    continue

                for line in resp.iter_lines():
                    # print(f"test_streaming_performance line: {line}")
                    """
                    {
                        "id": "cds_0e09bffa-4b14-4759-9177-bfc76158a9fc",
                        "object": "chat.completion.chunk",
                        "created": 1787552608,
                        "model": "Vendor3/DeepSeek-V4-Flash",
                        "choices": [
                            {
                                "finish_reason": null,
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "content": null,
                                    "reasoning_content": "\xe7\x94\xa8\xe6\x88\xb7"
                                }
                            }
                        ],
                        "usage": null,
                        "metrics": null
                    }

                    {
                        "id": "cds_eb13e70a-0ae0-9373-9a75-d83c83ba346d",
                        "object": "chat.completion.chunk",
                        "created": 1787552616,
                        "model": "Vendor3/DeepSeek-V4-Flash",
                        "choices": [
                            {
                                "finish_reason": null,
                                "index": 0,
                                "delta": {
                                    "content": null,
                                    "reasoning_content": "\xe8\xbf\x99\xe6\xa0\xb7\xe7\xbb\x93\xe6\x9e\x84\xe6\xaf\x94\xe8\xbe\x83\xe6\xb8\x85\xe6\x99\xb0\xe3\x80\x82"
                                }
                            }
                        ],
                        "usage": null,
                        "metrics": null
                    }


                    {
                        "id": "cds_eb13e70a-0ae0-9373-9a75-d83c83ba346d",
                        "object": "chat.completion.chunk",
                        "created": 1787552616,
                        "model": "Vendor3/DeepSeek-V4-Flash",
                        "choices": [
                            {
                                "finish_reason": null,
                                "index": 0,
                                "delta": {
                                    "content": "\xe9\x87\x8f\xe5\xad\x90\xe8\xae\xa1\xe7\xae\x97\xe7\x9a\x84\xe6\xa0\xb8\xe5\xbf\x83\xe6\x98\xaf\xe5\x88\xa9\xe7\x94\xa8"
                                }
                            }
                        ],
                        "usage": null,
                        "metrics": null
                    }

                    {
                        "id": "cds_eb13e70a-0ae0-9373-9a75-d83c83ba346d",
                        "object": "chat.completion.chunk",
                        "created": 1787552616,
                        "model": "Vendor3/DeepSeek-V4-Flash",
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "index": 0,
                                "delta": {
                                    "content": ""
                                }
                            }
                        ],
                        "usage": null,
                        "metrics": null
                    }
                    {
                        "id": "cds_eb13e70a-0ae0-9373-9a75-d83c83ba346d",
                        "object": "chat.completion.chunk",
                        "created": 1787552616,
                        "model": "Vendor3/DeepSeek-V4-Flash",
                        "choices": [

                        ],
                        "usage": {
                            "prompt_tokens": 16,
                            "completion_tokens": 353,
                            "total_tokens": 369,
                            "prompt_tokens_details": {
                                "cache_creation": {

                                }
                            }
                        },
                        "metrics": {
                            "input_token_count": 16,
                            "output_token_count": 353,
                            "predict_time": 4.844539691
                        }
                    }

                    data: [DONE]
                    """
                    if not line:
                        continue

                    line_str = line.decode("utf-8")

                    # 1. 拦截 SSE 终止信号
                    if line_str.strip() == "data: [DONE]":
                        received_done_signal = True
                        print(f"📥 成功接收终止标记: data: [DONE]")
                        break

                    if line_str.startswith("data: "):
                        data_str = line_str[6:].strip()
                        try:
                            chunk_data = json.loads(data_str)
                            chunk_count += 1

                            # 2. 检查是否有 Usage / Metrics 元数据包 (choices 此时通常为空)
                            if "usage" in chunk_data and chunk_data["usage"]:
                                server_usage = chunk_data["usage"]
                            if "metrics" in chunk_data and chunk_data["metrics"]:
                                server_metrics = chunk_data["metrics"]

                            # 3. 防御性读取 choices
                            choices = chunk_data.get("choices", [])
                            if not choices:
                                # 元数据 chunk, 直接跳过 delta 解析
                                continue

                            delta = choices[0].get("delta", {})

                            # 捕获第一个 Token 响应时间 (TTFT)
                            if first_token_time is None and (
                                delta.get("content") or delta.get("reasoning_content")
                            ):
                                first_token_time = time.perf_counter()

                            # 捕获第一个正式文本 Token 响应时间 (TTFAT)
                            if first_content_time is None and delta.get("content"):
                                first_content_time = time.perf_counter()

                            if delta.get("reasoning_content"):
                                received_reasoning += delta["reasoning_content"]
                            if delta.get("content"):
                                received_text += delta["content"]

                        except json.JSONDecodeError:
                            print(f"⚠️ JSON 解析跳过: {data_str}")

                end_time = time.perf_counter()

                # 统计计算
                total_duration = end_time - start_time
                ttft = (
                    (first_token_time - start_time)
                    if first_token_time
                    else total_duration
                )
                ttfat = (
                    (first_content_time - start_time)
                    if first_content_time
                    else total_duration
                )

                # Token 数量优先采用服务端真实数据
                if server_usage:
                    in_tokens = server_usage.get("prompt_tokens", 0)
                    out_tokens = server_usage.get("completion_tokens", 0)
                else:
                    in_tokens = len(prompt)
                    out_tokens = int(len(received_text + received_reasoning) / 1.5)

                # 计算生成阶段吞吐
                gen_duration = total_duration - ttft
                actual_tps = (out_tokens / gen_duration) if gen_duration > 0 else 0

                ttft_list.append(ttft)
                total_time_list.append(total_duration)

                print(f"\n📊 [Round {i} 结果汇总]:")
                print(f"  • 首 Token 延迟 (TTFT - 包含思维链): {ttft*1000:.2f} ms")
                print(f"  • 首个正式回答延迟 (TTFAT): {ttfat*1000:.2f} ms")
                print(f"  • 客户端全流程耗时: {total_duration:.3f} s")
                if server_metrics:
                    print(
                        f"  • 服务端纯推理耗时 (predict_time): {server_metrics.get('predict_time')} s"
                    )
                print(f"  • Token 统计 (In / Out): {in_tokens} / {out_tokens}")
                print(f"  • 解码吞吐速度: {actual_tps:.2f} tokens/s")
                print(
                    f"  • 是否收到 [DONE] 信号: {'✅ 是' if received_done_signal else '❌ 否'}"
                )
                print(
                    f"  • 思维链长度: {len(received_reasoning)} 字符 | 正文长度: {len(received_text)} 字符"
                )

        except Exception as e:
            print(f"❌ 第 {i} 轮请求发生异常: {type(e).__name__}: {e}")

    if ttft_list:
        print("\n" + "=" * 50)
        print(f"📈 [流式多轮基准总结]")
        print(f"  • 平均 TTFT: {sum(ttft_list)/len(ttft_list)*1000:.2f} ms")
        print(f"  • 平均总耗时: {sum(total_time_list)/len(total_time_list):.2f} s")
        print("=" * 50)


# ==================== 2. 非流式全量性能测试 ====================


def test_non_streaming_performance(prompt="你好, 请介绍一下自己", runs=2):
    print("\n" + "=" * 50)
    print(f"⏱️ 开始测试非流式全量请求 - 共测试 {runs} 轮")
    print("=" * 50)

    payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}

    for i in range(1, runs + 1):
        client_start = time.perf_counter()
        try:
            resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
            client_total_time = time.perf_counter() - client_start

            if resp.status_code == 200:
                data = resp.json()
                # print(f"test_non_streaming_performance data: {data}")
                """
                {
                    'id': 'cds_5cf051a2-08e0-4b18-9b25-bffdaff29d60',
                    'object': 'chat.completion',
                    'created': 1787553874,
                    'model': 'Vendor3/DeepSeek-V4-Flash',
                    'choices': [
                        {
                            'finish_reason': 'stop',
                            'index': 0,
                            'message': {
                                'role': 'assistant',
                                'content': '你好呀! 很高兴认识你! 😊\n\n我是DeepSeek, 由深度求索公司创造的AI助手. ',
                                'reasoning_content': '好的, 用户让我介绍一下自己. 这是一个很常见的开场问题, 用户可能是第一次接触我, 想了解我的基本情况和能力范围'
                            }
                        }
                    ],
                    'usage': {
                        'prompt_tokens': 10,
                        'completion_tokens': 477,
                        'total_tokens': 487,
                        'prompt_tokens_details': {
                            'cache_creation': {}
                        }
                    },
                    'metrics': {
                        'input_token_count': 10,
                        'output_token_count': 477,
                        'predict_time': 5.637811931
                    }
                }
                """
                usage = data.get("usage", {})
                metrics = data.get("metrics", {})
                predict_time = metrics.get("predict_time", 0)
                in_tokens = usage.get("prompt_tokens", 0)
                out_tokens = usage.get("completion_tokens", 0)

                network_overhead = (
                    client_total_time - float(predict_time) if predict_time else 0
                )

                print(
                    f"  [Round {i}] 客户端总耗时: {client_total_time:.3f}s | "
                    f"服务端纯推理耗时: {predict_time}s | 网络+网关开销: {network_overhead:.3f}s | "
                    f"Tokens (In/Out): {in_tokens}/{out_tokens}"
                )
            else:
                print(f"❌ [Round {i}] 请求失败: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"❌ [Round {i}] 网络异常: {e}")


# ==================== 3. 异常注入探测 ====================


def test_error_scenarios():
    print("\n" + "=" * 50)
    print("🛡️ 开始系统性异常与错误场景探测")
    print("=" * 50)

    test_cases = [
        (
            "1. 鉴权失败测试",
            {"Authorization": "Bearer bad_key"},
            {"model": MODEL_NAME, "messages": [{"role": "user", "content": "hi"}]},
        ),
        (
            "2. 模型不存在测试",
            HEADERS,
            {
                "model": "Non-Existent-Model",
                "messages": [{"role": "user", "content": "hi"}],
            },
        ),
        ("3. Messages 为空列表", HEADERS, {"model": MODEL_NAME, "messages": []}),
        (
            "4. 非法 Temperature 越界",
            HEADERS,
            {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 99.0,
            },
        ),
        (
            "5. Max Tokens 极大值溢出",
            HEADERS,
            {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 100000000,
            },
        ),
    ]

    for name, h, p in test_cases:
        print(f"\n🧪 [测试项] {name}")
        try:
            resp = requests.post(BASE_URL, headers=h, json=p, timeout=10)
            print(f"   👉 响应状态码: {resp.status_code}")
            print(f"   👉 响应 Body: {resp.text[:200]}")
        except Exception as e:
            print(f"   ⚠️ 请求异常: {e}")


# ==================== 主入口 ====================

if __name__ == "__main__":
    print(f"🎯 探测目标: {BASE_URL}")
    print(f"🤖 目标模型: {MODEL_NAME}")

    # 1. 运行修复后的流式测试
    test_streaming_performance(runs=3)

    # 2. 运行非流式全量测试
    test_non_streaming_performance(runs=3)

    # 3. 运行异常注入探测
    test_error_scenarios()
