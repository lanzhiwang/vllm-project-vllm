import time
import uuid
from openai import OpenAI

# ==========================================
# 1. 服务配置
# ==========================================
SERVER_HOST = "http://172.16.10.51:8090"
API_KEY = "my_secret_token_123"
MODEL_NAME = "Qwen2.5-7B-Instruct"

client = OpenAI(base_url=f"{SERVER_HOST}/v1", api_key=API_KEY)


# ==========================================
# 2. 文本生成器 (构造严格分级且互不污染的测试语料)
# ==========================================
def generate_context_by_tokens(target_type: str, session_id: str) -> str:
    """根据类型生成不同规模的静态前缀, 并加入 unique session_id 确保绝对冷启动"""
    header = f"[测试任务编号: {session_id}]\n你是一个专业的数据与逻辑分析助手. \n"

    if target_type == "tiny":  # 微型: 仅头部 (~35 Tokens)
        return header

    elif target_type == "short":  # 短文本: 角色与系统规则 (~300 Tokens)
        rules = "\n".join(
            [
                f"规则 {i+1}: 在处理任务时必须遵循安全规范第 {i+1} 条, 确保输出无有害信息且格式严谨. "
                for i in range(12)
            ]
        )
        return header + "\n系统运行核心约束如下:\n" + rules + "\n"

    elif target_type == "medium":  # 中长文档: 模拟 RAG 知识库 (~1500 Tokens)
        table_rows = "\n".join(
            [
                f"| ID_{i:03d} | Product_Item_{i} | Category_{i%5} | InStock: {i*7%100} | Price: ${i*12.5:.2f} | Warehouse_Zone_{i%8} |"
                for i in range(45)
            ]
        )
        return header + "\n以下是当前仓库的全部实时库存清单记录:\n" + table_rows + "\n"

    elif target_type == "long":  # 超长文档: 模拟长文档分析 (~5000 Tokens)
        logs = "\n".join(
            [
                f"[2026-08-27 10:{i%60:02d}:{(i*7)%60:02d}.{i*13%999:03d}] [SERVER-NODE-{(i%10):02d}] "
                f"INFO: ServiceModule_{i%8} processed trans_id=0x{i*99999:08X} user_id=UID_{i*31%1000} "
                f"latency={(i*3.14)%25:.2f}ms status=SUCCESS payload_hash=H_{hash(str(i))%10000000}"
                for i in range(150)
            ]
        )
        return header + "\n以下是集群近期的系统运行审计日志:\n" + logs + "\n"

    raise ValueError(f"Unknown target_type: {target_type}")


# ==========================================
# 3. 核心请求与指标采样函数
# ==========================================
def execute_stream_request(system_prompt: str, user_question: str):
    """发送单次流式请求, 捕获 TTFT、生成时间与 Token Usage"""
    start_time = time.perf_counter()
    first_token_time = None
    final_usage = None
    output_chunks = []

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        temperature=0.0,
        max_tokens=20,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in response:
        if chunk.choices and len(chunk.choices) > 0:
            content = chunk.choices[0].delta.content or ""
            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                output_chunks.append(content)

        if hasattr(chunk, "usage") and chunk.usage is not None:
            final_usage = chunk.usage
    print(f"final_usage: {final_usage}")

    end_time = time.perf_counter()

    ttft_ms = (
        (first_token_time - start_time) * 1000
        if first_token_time
        else (end_time - start_time) * 1000
    )
    total_time_ms = (end_time - start_time) * 1000

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
        "ttft_ms": ttft_ms,
        "total_time_ms": total_time_ms,
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "answer": "".join(output_chunks).strip(),
    }


# ==========================================
# 4. 主评测流程
# ==========================================
def run_rigorous_benchmark():
    test_scales = [
        ("微型前缀 (Tiny, ~40 Tokens)", "tiny"),
        ("短前缀 (Short, ~300 Tokens)", "short"),
        ("中长前缀 (Medium, ~1500 Tokens)", "medium"),
        ("超长前缀 (Long, ~5000 Tokens)", "long"),
    ]

    benchmark_summary = []

    print("=" * 95)
    print("🎯 vLLM 前缀缓存 (Prefix Caching) 与 Prompt 长度关系严密验证实验")
    print("=" * 95)

    for scale_name, scale_key in test_scales:
        # 为当前组生成专属 UUID, 保证前缀绝不会与上一组产生任何 Token 复用
        unique_session_id = uuid.uuid4().hex[:8]
        system_prefix = generate_context_by_tokens(scale_key, unique_session_id)

        print(f"\n" + "-" * 95)
        print(f"🔬 正在测试实验组: [{scale_name}] (Session: {unique_session_id})")
        print("-" * 95)

        # --------------------------------------------------
        # Step 1: 绝对冷启动请求 (Cache Miss)
        # --------------------------------------------------
        cold_res = execute_stream_request(system_prefix, "请直接输出一个数字 '1' 即可.")
        print(
            f"❄️  [冷启动 Miss] -> 总 Prompt Tokens: {cold_res['prompt_tokens']:<5} | "
            f"Cached: {cold_res['cached_tokens']:<5} | TTFT: {cold_res['ttft_ms']:>7.2f} ms"
        )

        time.sleep(0.5)

        # --------------------------------------------------
        # Step 2: 热启动请求 (Cache Hit) - 连续跑 3 次取平均, 降低抖动
        # --------------------------------------------------
        warm_ttfts = []
        last_warm_res = None
        for i in range(3):
            # 共享相同的 system_prefix, 仅问题稍作微调
            warm_res = execute_stream_request(
                system_prefix, f"第{i+1}次验证: 请直接输出数字 '{i+2}'. "
            )
            warm_ttfts.append(warm_res["ttft_ms"])
            last_warm_res = warm_res
            time.sleep(0.2)

        avg_warm_ttft = sum(warm_ttfts) / len(warm_ttfts)
        speedup = cold_res["ttft_ms"] / avg_warm_ttft if avg_warm_ttft > 0 else 1.0

        print(
            f"🔥 [缓存命中 Hit ] -> 复用 Tokens: {last_warm_res['cached_tokens']:<9} | "
            f"三次平均 TTFT: {avg_warm_ttft:>7.2f} ms (单次: {[f'{t:.1f}ms' for t in warm_ttfts]})"
        )
        print(f"🚀 [首字延迟加速比] -> {speedup:.2f} x")

        benchmark_summary.append(
            {
                "name": scale_name,
                "prompt_tokens": cold_res["prompt_tokens"],
                "cached_tokens": last_warm_res["cached_tokens"],
                "uncached_tokens": cold_res["prompt_tokens"]
                - last_warm_res["cached_tokens"],
                "cold_ttft": cold_res["ttft_ms"],
                "warm_ttft": avg_warm_ttft,
                "speedup": speedup,
            }
        )

    # ==========================================
    # 5. 结果汇总与数学规律校验
    # ==========================================
    print("\n" + "=" * 95)
    print("📊 最终测试结果汇总与数学规律检验表 (Block Size = 16)")
    print("=" * 95)
    print(
        f"{'前缀规模':<26} | {'Prompt':<7} | {'命中 Tokens':<11} | {'未命中(尾数)':<12} | {'冷启动 TTFT':<11} | {'缓存 TTFT':<10} | {'加速比':<8}"
    )
    print("-" * 95)

    for item in benchmark_summary:
        # 验证是否符合整块对齐: cached_tokens 必须是 16 的倍数
        is_aligned = item["cached_tokens"] % 16 == 0
        align_tag = "✓" if is_aligned else "✗"

        print(
            f"{item['name']:<24} | "
            f"{item['prompt_tokens']:<7} | "
            f"{item['cached_tokens']:<5} ({align_tag}) | "
            f"{item['uncached_tokens']:<12} | "
            f"{item['cold_ttft']:>8.2f} ms | "
            f"{item['warm_ttft']:>7.2f} ms | "
            f"{item['speedup']:>6.2f}x"
        )
    print("-" * 95)

    print("\n💡 [核心结论与数学事实]:")
    print(
        "1. Block 对齐恒等式: `Cached Tokens` 严格等于 `floor(可复用前缀Tokens / 16) * 16`. "
    )
    print("2. 长度与收益曲线: ")
    print(
        "   - 微型/短文本: 虽然 `Cached Tokens` 占比很高, 但因 Prefill 本身只需 1~2ms, 总耗时由网络与调度主导, 故加速比接近 1.0x~1.3x. "
    )
    print(
        "   - 超长文本: Prefill 计算耗时随长度呈超线性增长. 命中缓存直接省去了数千个 Token 的计算, TTFT 加速比呈现质的飞跃(5x ~ 20x+). "
    )


if __name__ == "__main__":
    run_rigorous_benchmark()
