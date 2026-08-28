import json
import time
import requests

# ==================== 配置区域 ====================
BASE_URL = "https://api.gpugeek.com/v1/chat/completions"
API_KEY = "d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o"
MODEL_NAME = "Vendor3/DeepSeek-V4-Flash"

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 构造一段约 2000+ tokens 的背景长文本 (确保达到缓存激活门槛)
SHARED_PREFIX_TEXT = "[技术文档背景资料]\n" + (
    "分布式大模型推理系统通常采用流水线并行、张量并行和序列并行. KV Cache 管理是推理优化的核心."
    "PagedAttention 将物理显存切分成固定大小的 Block 从而减少内存碎片."
    "Prefix Caching 则允许跨请求复用已计算的前缀 KV Cache, 极大加速多轮对话与长上下文的 Prefill 耗时.\n"
    * 45
)

CONTROL_PREFIX_TEXT = "[历史与天文学背景资料]\n" + (
    "太阳系的行星轨道呈现微小的椭圆偏心率, 开普勒三大定律奠定了近代天体力学的基础."
    "在恒星演化末期, 大质量恒星会经历超新星爆发并可能坍缩为中子星或黑洞.\n" * 45
)


def send_chat_completion(prefix: str, question: str, stream: bool = True):
    """
    发送测试请求, 测量 TTFT、总耗时, 并安全提取返回的缓存元数据与服务端指标
    """
    print(f"send_chat_completion prefix: {prefix[:30]}")
    print(f"send_chat_completion question: {question}")
    print(f"send_chat_completion stream: {stream}")

    messages = [
        {"role": "system", "content": prefix},
        {"role": "user", "content": question},
    ]
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 10,  # 限制输出极短, 使整体耗时主要由 Prefill 决定
        "temperature": 0.0,  # 固定随机性
        "stream": stream,
        "stream_options": {"include_usage": True},  # 显式要求在流式末尾返回 usage
    }

    start_time = time.perf_counter()
    first_token_time = None
    full_response_text = ""
    prompt_tokens = 0
    cached_tokens = 0
    predict_time = None
    prompt_tokens_details = {}

    if stream:
        resp = requests.post(
            BASE_URL, headers=HEADERS, json=payload, stream=True, timeout=60
        )
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

        for line in resp.iter_lines():
            print(f"send_chat_completion line: {line}")
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)

                    # 1. 安全提取 choices (处理 choices 为 [] 的 usage chunk)
                    choices = chunk.get("choices", [])
                    if choices and len(choices) > 0:
                        delta = choices[0].get("delta", {})
                        # 捕获首 token (包括 reasoning_content 或普通 content)
                        if first_token_time is None and (
                            delta.get("content") or delta.get("reasoning_content")
                        ):
                            first_token_time = time.perf_counter()
                        if delta.get("content"):
                            full_response_text += delta["content"]

                    # 2. 提取 usage 统计信息
                    if "usage" in chunk and chunk["usage"]:
                        usage = chunk["usage"]
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        prompt_tokens_details = usage.get("prompt_tokens_details", {})
                        cached_tokens = (
                            prompt_tokens_details.get("cached_tokens")
                            or prompt_tokens_details.get("cache_read_input_tokens")
                            or 0
                        )

                    # 3. 提取服务端 metrics (如果有)
                    if "metrics" in chunk and chunk["metrics"]:
                        metrics = chunk["metrics"]
                        predict_time = metrics.get("predict_time")

                except json.JSONDecodeError:
                    pass
        end_time = time.perf_counter()

    else:
        # 非流式请求路径
        resp = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=60)
        end_time = time.perf_counter()
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        print(f"send_chat_completion data: {data}")

        usage = data.get("usage", {})
        metrics = data.get("metrics", {})
        predict_time = metrics.get("predict_time")
        prompt_tokens = usage.get("prompt_tokens", 0)
        prompt_tokens_details = usage.get("prompt_tokens_details", {})
        cached_tokens = (
            prompt_tokens_details.get("cached_tokens")
            or prompt_tokens_details.get("cache_read_input_tokens")
            or 0
        )

    client_total_time = end_time - start_time
    ttft = (first_token_time - start_time) if first_token_time else client_total_time

    return {
        "ttft_ms": ttft * 1000,
        "total_time_s": client_total_time,
        "predict_time_s": predict_time,
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "prompt_tokens_details": prompt_tokens_details,
    }


def verify_prefix_caching():
    print("=" * 70)
    print("🔍 正在启动 LLM 前缀缓存 (Prefix Caching / Prompt Cache) 验证程序")
    print(f"🎯 测试目标: {BASE_URL}")
    print(f"🤖 目标模型: {MODEL_NAME}")
    print("=" * 70)

    results = []

    # 1. 第一次请求: 冷启动 / 缓存创建 (Cache Miss & Creation)
    print("\n[Step 1] 发送长前缀冷启动请求 (Cache Miss)...")
    res1 = send_chat_completion(SHARED_PREFIX_TEXT, "请用一句话总结上述技术内容: ")
    results.append(("1. Cold Request (Miss/Build)", res1))
    print(
        f"   👉 TTFT: {res1['ttft_ms']:.2f} ms | 总耗时: {res1['total_time_s']:.3f} s"
    )
    print(f"   👉 缓存详情字段: {res1['prompt_tokens_details']}")

    # 稍作停顿, 确保服务端 KV Cache 写入与索引更新完成
    time.sleep(1.0)

    # 2. 第二次请求: 相同前缀 + 略微不同的提问 (预期命中 Cache Hit)
    print("\n[Step 2] 发送完全相同长前缀的测试请求 (Cache Hit)...")
    res2 = send_chat_completion(SHARED_PREFIX_TEXT, "请简述 KV Cache 的主要作用: ")
    results.append(("2. Warm Request (Hit Target)", res2))
    print(
        f"   👉 TTFT: {res2['ttft_ms']:.2f} ms | 总耗时: {res2['total_time_s']:.3f} s"
    )
    print(f"   👉 缓存详情字段: {res2['prompt_tokens_details']}")

    # 3. 第三次请求: 再次命中验证 (连续命中稳定性)
    print("\n[Step 3] 再次发送相同长前缀的复测请求 (Cache Hit Repeat)...")
    res3 = send_chat_completion(SHARED_PREFIX_TEXT, "文档提到了哪几种并行方式?")
    results.append(("3. Warm Request 2 (Repeat Hit)", res3))
    print(
        f"   👉 TTFT: {res3['ttft_ms']:.2f} ms | 总耗时: {res3['total_time_s']:.3f} s"
    )
    print(f"   👉 缓存详情字段: {res3['prompt_tokens_details']}")

    # 4. 第四次请求: 对照组, 全新等长前缀 (预期重新变慢 Cache Miss)
    print("\n[Step 4] 发送全新对照组长前缀 (Control Miss)...")
    res4 = send_chat_completion(CONTROL_PREFIX_TEXT, "请简要概括天文学资料: ")
    results.append(("4. Control Request (New Miss)", res4))
    print(
        f"   👉 TTFT: {res4['ttft_ms']:.2f} ms | 总耗时: {res4['total_time_s']:.3f} s"
    )
    print(f"   👉 缓存详情字段: {res4['prompt_tokens_details']}")

    # ==================== 分析与诊断报告 ====================
    print("\n" + "=" * 70)
    print("📊 验证结果与指标对比报告")
    print("=" * 70)
    print(f"results: {results}")
    print(
        f"{'测试阶段':<30} | {'TTFT (ms)':<12} | {'总耗时 (s)':<10} | {'Cached Tokens':<15}"
    )
    print("-" * 70)
    for name, r in results:
        cached_info = (
            str(r["cached_tokens"])
            if r["cached_tokens"]
            else json.dumps(r["prompt_tokens_details"])
        )
        print(
            f"{name:<30} | {r['ttft_ms']:<12.2f} | {r['total_time_s']:<10.3f} | {cached_info:<15}"
        )
    print("-" * 70)

    # 计算加速比
    cold_ttft = res1["ttft_ms"]
    warm_ttft = res2["ttft_ms"]
    speedup_ratio = (cold_ttft - warm_ttft) / cold_ttft if cold_ttft > 0 else 0

    print("\n💡 [分析结论]")

    # 判据 1: 元数据中存在确切命中记录
    has_explicit_cache_metadata = (
        res2["cached_tokens"] > 0
        or res2["prompt_tokens_details"].get("cached_tokens", 0) > 0
        or res2["prompt_tokens_details"].get("cache_read_input_tokens", 0) > 0
    )

    # 判据 2: TTFT 下降显著 (一般前缀缓存命中时 TTFT 下降幅度 > 35%)
    has_latency_drop = (speedup_ratio > 0.35) and (
        res2["ttft_ms"] < res4["ttft_ms"] * 0.7
    )

    if has_explicit_cache_metadata:
        print(
            f"✅ [确定开启] 服务端返回了明确的缓存命中数据: cached_tokens = {res2['cached_tokens']}"
        )
    elif has_latency_drop:
        print(
            f"✅ [确定开启 (性能特征命中)] 冷请求 TTFT 为 {cold_ttft:.1f}ms, 热请求 TTFT 为 {warm_ttft:.1f}ms, "
            f"延迟下降了 {speedup_ratio*100:.1f}%, 对照组恢复至 {res4['ttft_ms']:.1f}ms. "
        )
        print(
            "   (说明: 虽然网关未透传 cached_tokens 具体数字, 但底层推理引擎已实际执行了前缀缓存加速.)"
        )
    else:
        print(
            f"❌ [未开启或未命中] 冷请求 TTFT ({cold_ttft:.1f}ms) 与热请求 TTFT ({warm_ttft:.1f}ms) 无显著差异 (下降 {speedup_ratio*100:.1f}%). "
        )
        print("   可能原因:")
        print(
            "   1. 推理引擎后端未启用 Prefix Caching(例如 vLLM 缺少 `--enable-prefix-caching`). "
        )
        print(
            "   2. 多 Worker 实例负载均衡时缺少会话保持(Sticky Routing), 热请求落到了其他节点. "
        )


if __name__ == "__main__":
    verify_prefix_caching()

"""
$ python verify_prefix_caching.py
======================================================================
🔍 正在启动 LLM 前缀缓存 (Prefix Caching / Prompt Cache) 验证程序
🎯 测试目标: https://api.gpugeek.com/v1/chat/completions
🤖 目标模型: Vendor3/DeepSeek-V4-Flash
======================================================================

[Step 1] 发送长前缀冷启动请求 (Cache Miss)...
send_chat_completion prefix: [技术文档背景资料]
分布式大模型推理系统通常采用流水线并行
send_chat_completion question: 请用一句话总结上述技术内容:
send_chat_completion stream: True
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"\xe6\x88\x91\xe4\xbb\xac"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe8\xa2\xab\xe8\xa6\x81\xe6\xb1\x82\xe7\x94\xa8"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe4\xb8\x80\xe5\x8f\xa5\xe8\xaf\x9d\xe6\x80\xbb\xe7\xbb\x93\xe4\xb8\x8a\xe8\xbf\xb0"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe6\x8a\x80\xe6\x9c\xaf\xe5\x86\x85\xe5\xae\xb9"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":"length","index":0,"delta":{"content":null,"reasoning_content":"\xe3\x80\x82"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_ea8e278c-e8c7-4858-9796-7c96d9a55ccb","object":"chat.completion.chunk","created":1787561102,"model":"Vendor3/DeepSeek-V4-Flash","choices":[],"usage":{"prompt_tokens":3484,"completion_tokens":11,"total_tokens":3495,"prompt_tokens_details":{"cache_creation":{},"cached_tokens":3072}},"metrics":{"input_token_count":3484,"output_token_count":11,"predict_time":4.071713039}}'
send_chat_completion line: b''
send_chat_completion line: b'data: [DONE]'
   👉 TTFT: 4474.80 ms | 总耗时: 4.475 s
   👉 缓存详情字段: {'cache_creation': {}, 'cached_tokens': 3072}

[Step 2] 发送完全相同长前缀的测试请求 (Cache Hit)...
send_chat_completion prefix: [技术文档背景资料]
分布式大模型推理系统通常采用流水线并行
send_chat_completion question: 请简述 KV Cache 的主要作用:
send_chat_completion stream: True
send_chat_completion line: b'data: {"id":"cds_69692948-16bc-41c9-8f87-74b31e61e141","object":"chat.completion.chunk","created":1787561104,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"\xe6\x88\x91\xe4\xbb\xac"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69692948-16bc-41c9-8f87-74b31e61e141","object":"chat.completion.chunk","created":1787561104,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe8\xa2\xab\xe8\xa6\x81\xe6\xb1\x82\\""}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69692948-16bc-41c9-8f87-74b31e61e141","object":"chat.completion.chunk","created":1787561104,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe8\xaf\xb7\xe7\xae\x80\xe8\xbf\xb0 KV"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69692948-16bc-41c9-8f87-74b31e61e141","object":"chat.completion.chunk","created":1787561104,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":"length","index":0,"delta":{"content":null,"reasoning_content":" Cache \xe7\x9a\x84\xe4\xb8\xbb\xe8\xa6\x81"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69692948-16bc-41c9-8f87-74b31e61e141","object":"chat.completion.chunk","created":1787561104,"model":"Vendor3/DeepSeek-V4-Flash","choices":[],"usage":{"prompt_tokens":3484,"completion_tokens":11,"total_tokens":3495,"prompt_tokens_details":{"cache_creation":{},"cached_tokens":3072}},"metrics":{"input_token_count":3484,"output_token_count":11,"predict_time":0.994324766}}'
send_chat_completion line: b''
send_chat_completion line: b'data: [DONE]'
   👉 TTFT: 1354.04 ms | 总耗时: 1.355 s
   👉 缓存详情字段: {'cache_creation': {}, 'cached_tokens': 3072}

[Step 3] 再次发送相同长前缀的复测请求 (Cache Hit Repeat)...
send_chat_completion prefix: [技术文档背景资料]
分布式大模型推理系统通常采用流水线并行
send_chat_completion question: 文档提到了哪几种并行方式?
send_chat_completion stream: True
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"\xe6\x88\x91\xe4\xbb\xac"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe8\xa2\xab\xe9\x97\xae\xe5\x88\xb0"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xef\xbc\x9a\\"\xe6\x96\x87\xe6\xa1\xa3\xe6\x8f\x90\xe5\x88\xb0\xe4\xba\x86"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe5\x93\xaa\xe5\x87\xa0\xe7\xa7\x8d\xe5\xb9\xb6\xe8\xa1\x8c"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":"length","index":0,"delta":{"content":null,"reasoning_content":"\xe6\x96\xb9\xe5\xbc\x8f"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_69438526-0691-4244-9d7a-98b3e19652ac","object":"chat.completion.chunk","created":1787561106,"model":"Vendor3/DeepSeek-V4-Flash","choices":[],"usage":{"prompt_tokens":3482,"completion_tokens":11,"total_tokens":3493,"prompt_tokens_details":{"cache_creation":{},"cached_tokens":3072}},"metrics":{"input_token_count":3482,"output_token_count":11,"predict_time":0.927445393}}'
send_chat_completion line: b''
send_chat_completion line: b'data: [DONE]'
   👉 TTFT: 1375.96 ms | 总耗时: 1.377 s
   👉 缓存详情字段: {'cache_creation': {}, 'cached_tokens': 3072}

[Step 4] 发送全新对照组长前缀 (Control Miss)...
send_chat_completion prefix: [历史与天文学背景资料]
太阳系的行星轨道呈现微小的椭圆偏心
send_chat_completion question: 请简要概括天文学资料:
send_chat_completion stream: True
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":null,"reasoning_content":"\xe6\x88\x91\xe4\xbb\xac"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe8\xa6\x81\xe6\xb1\x82"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe7\xae\x80\xe8\xa6\x81"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"content":null,"reasoning_content":"\xe6\xa6\x82\xe6\x8b\xac\xe5\xa4\xa9\xe6\x96\x87\xe5\xad\xa6\xe8\xb5\x84\xe6\x96\x99"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":"length","index":0,"delta":{"content":null,"reasoning_content":"\xe3\x80\x82\xe7\xbb\x99\xe5\x87\xba\xe7\x9a\x84\xe8\xb5\x84\xe6\x96\x99"}}],"usage":null,"metrics":null}'
send_chat_completion line: b''
send_chat_completion line: b'data: {"id":"cds_119bb279-0892-4ccc-a21f-6c2d5fe97e8d","object":"chat.completion.chunk","created":1787561107,"model":"Vendor3/DeepSeek-V4-Flash","choices":[],"usage":{"prompt_tokens":2180,"completion_tokens":11,"total_tokens":2191,"prompt_tokens_details":{"cache_creation":{},"cached_tokens":2048}},"metrics":{"input_token_count":2180,"output_token_count":11,"predict_time":0.997202438}}'
send_chat_completion line: b''
send_chat_completion line: b'data: [DONE]'
   👉 TTFT: 1357.49 ms | 总耗时: 1.358 s
   👉 缓存详情字段: {'cache_creation': {}, 'cached_tokens': 2048}

======================================================================
📊 验证结果与指标对比报告
======================================================================
results: [
    ('1. Cold Request (Miss/Build)', {
        'ttft_ms': 4474.800673000118,
        'total_time_s': 4.475171535000072,
        'predict_time_s': 4.071713039,
        'prompt_tokens': 3484,
        'cached_tokens': 3072,
        'prompt_tokens_details': {'cache_creation': {}, 'cached_tokens': 3072}
    }),
    ('2. Warm Request (Hit Target)', {
        'ttft_ms': 1354.0445650000947,
        'total_time_s': 1.3545432220000748,
        'predict_time_s': 0.994324766,
        'prompt_tokens': 3484,
        'cached_tokens': 3072,
        'prompt_tokens_details': {'cache_creation': {}, 'cached_tokens': 3072}
    }),
    ('3. Warm Request 2 (Repeat Hit)', {
        'ttft_ms': 1375.9634330001518,
        'total_time_s': 1.3765332450000187,
        'predict_time_s': 0.927445393,
        'prompt_tokens': 3482,
        'cached_tokens': 3072,
        'prompt_tokens_details': {'cache_creation': {}, 'cached_tokens': 3072}
    }),
    ('4. Control Request (New Miss)', {
        'ttft_ms': 1357.4872619999496,
        'total_time_s': 1.3579596679999213,
        'predict_time_s': 0.997202438,
        'prompt_tokens': 2180,
        'cached_tokens': 2048,
        'prompt_tokens_details': {'cache_creation': {}, 'cached_tokens': 2048}
    })
]
测试阶段                           | TTFT (ms)    | 总耗时 (s)    | Cached Tokens
----------------------------------------------------------------------
1. Cold Request (Miss/Build)   | 4474.80      | 4.475      | 3072
2. Warm Request (Hit Target)   | 1354.04      | 1.355      | 3072
3. Warm Request 2 (Repeat Hit) | 1375.96      | 1.377      | 3072
4. Control Request (New Miss)  | 1357.49      | 1.358      | 2048
----------------------------------------------------------------------

💡 [分析结论]
✅ [确定开启] 服务端返回了明确的缓存命中数据: cached_tokens = 3072
$
"""
