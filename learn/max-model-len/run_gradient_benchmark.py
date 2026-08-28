import time
from openai import OpenAI

SERVER_HOST = "http://172.16.10.51:8090"
API_KEY = "my_secret_token_123"
MODEL_NAME = "Qwen2.5-7B-Instruct"

client = OpenAI(base_url=f"{SERVER_HOST}/v1", api_key=API_KEY)


def send_test_request(prefix: str, question: str):
    """发送请求并获取 TTFT、Prompt Tokens 以及 Cached Tokens"""
    full_prompt = prefix + question
    start_time = time.perf_counter()
    first_token_time = None
    final_usage = None

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.0,
        max_tokens=30,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in response:
        print("chunk: " + chunk.model_dump_json(indent=4))
        print(f"---")
        if chunk.choices and len(chunk.choices) > 0:
            if chunk.choices[0].delta.content and first_token_time is None:
                first_token_time = time.perf_counter()
        if hasattr(chunk, "usage") and chunk.usage is not None:
            final_usage = chunk.usage
    print(f"final_usage: {final_usage}")

    ttft_ms = (
        (first_token_time - start_time) * 1000
        if first_token_time
        else (time.perf_counter() - start_time) * 1000
    )
    prompt_tokens = getattr(final_usage, "prompt_tokens", 0) if final_usage else 0
    cached_tokens = 0
    if (
        final_usage
        and hasattr(final_usage, "prompt_tokens_details")
        and final_usage.prompt_tokens_details
    ):
        cached_tokens = (
            getattr(final_usage.prompt_tokens_details, "cached_tokens", 0) or 0
        )

    return {
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "ttft_ms": ttft_ms,
    }


def run_gradient_benchmark():
    # 构造 4 个不同长度的前缀
    prefix_suites = {
        "极短前缀 (<16 Tokens)": ("请直接回答: "),
        "较短前缀 (~45 Tokens)": (
            "你是一个专业的智能助手, 必须严格遵守客观、简明、准确的原则回答问题, "
            "不要有多余的废话和客套, 直接输出答案: \n\n"
        ),
        "中等前缀 (~400 Tokens)": (
            "以下是某软件系统的通用配置参考信息: \n"
            + "\n".join(
                [
                    f"- ConfigKey_{i}: SettingValue_Option_{i * 17 % 100}"
                    for i in range(40)
                ]
            )
            + "\n请根据以上上下文回答: "
        ),
        "超长前缀 (~2000 Tokens)": (
            "以下是某大型跨国企业的核心员工数据库档案表: \n\n"
            "| ID | Name | Age | Department | Role | Email | Country |\n"
            + "\n".join(
                [
                    f"| {i} | Staff_{i} | {20 + i % 30} | Tech | Engineer | staff{i}@corp.com | City_{i} |"
                    for i in range(80)
                ]
            )
            + "\n\n请根据上述员工全量信息回答: "
        ),
    }

    results = []

    print("=" * 85)
    print("🚀 开始 Prompt 长度与 Prefix Caching 关联性梯度验证")
    print("=" * 85)

    for label, prefix in prefix_suites.items():
        print(f"\n🧪 正在测试: [{label}] ...")

        print(f"第 1 次请求: Cold Start (Cache Miss)")
        r1 = send_test_request(prefix, "")
        time.sleep(0.5)

        print(f"第 2 次请求: Warm Start (Cache Hit - 相同前缀, 不同问题)")
        r2 = send_test_request(prefix, "")

        speedup = r1["ttft_ms"] / r2["ttft_ms"] if r2["ttft_ms"] > 0 else 1.0

        results.append(
            {
                "group": label,
                "prompt_tokens": r1["prompt_tokens"],
                "cached_tokens": r2["cached_tokens"],
                "cold_ttft": r1["ttft_ms"],
                "warm_ttft": r2["ttft_ms"],
                "speedup": speedup,
            }
        )

    # 输出结构化对比分析表
    print("\n" + "=" * 85)
    print(
        f"{'前缀分组':<22} | {'总 Tokens':<10} | {'命中 Tokens':<12} | {'冷启动 TTFT':<12} | {'缓存 TTFT':<12} | {'加速比':<8}"
    )
    print("-" * 85)
    for res in results:
        print(
            f"{res['group']:<20} | "
            f"{res['prompt_tokens']:<10} | "
            f"{res['cached_tokens']:<12} | "
            f"{res['cold_ttft']:>8.2f} ms | "
            f"{res['warm_ttft']:>8.2f} ms | "
            f"{res['speedup']:>6.2f}x"
        )
    print("=" * 85)


if __name__ == "__main__":
    run_gradient_benchmark()
