import time
import requests
from openai import OpenAI

# ==========================================
# 1. 服务端连接配置
# ==========================================
SERVER_HOST = "http://172.16.10.51:8090"
API_KEY = "my_secret_token_123"
MODEL_NAME = "Qwen2.5-7B-Instruct"

client = OpenAI(base_url=f"{SERVER_HOST}/v1", api_key=API_KEY)


# ==========================================
# 2. 构造对比 Prompt (超长前缀 vs 较短前缀)
# ==========================================
# (A) 超长共享前缀: 30个人员信息 Markdown 表格 (约 1500+ Tokens)
LONG_PREFIX_TABLE = (
    "你是一个精通表格数据分析的专业助手. 以下是公司全体核心员工的档案记录表: \n\n"
    "| ID  | Name          | Age | Occupation | Country     | Email                  | Phone Number | Address                         |\n"
    "| --- | ------------- | --- | ---------- | ----------- | ---------------------- | ------------ | ------------------------------- |\n"
    "| 1   | John Doe      | 29  | Engineer   | USA         | john.doe@example.com   | 555-1234     | 123 Elm St, Springfield, IL     |\n"
    "| 2   | Jane Smith    | 34  | Doctor     | Canada      | jane.smith@example.com | 555-5678     | 456 Oak St, Toronto, ON         |\n"
    "| 3   | Alice Johnson | 27  | Teacher    | UK          | alice.j@example.com    | 555-8765     | 789 Pine St, London, UK         |\n"
    "| 4   | Bob Brown     | 45  | Artist     | Australia   | bob.b@example.com      | 555-4321     | 321 Maple St, Sydney, NSW       |\n"
    "| 5   | Carol White   | 31  | Scientist  | New Zealand | carol.w@example.com    | 555-6789     | 654 Birch St, Wellington, NZ    |\n"
    "| 6   | Dave Green    | 28  | Lawyer     | Ireland     | dave.g@example.com     | 555-3456     | 987 Cedar St, Dublin, IE        |\n"
    "| 7   | Emma Black    | 40  | Musician   | USA         | emma.b@example.com     | 555-1111     | 246 Ash St, New York, NY        |\n"
    "| 8   | Frank Blue    | 37  | Chef       | Canada      | frank.b@example.com    | 555-2222     | 135 Spruce St, Vancouver, BC    |\n"
    "| 9   | Grace Yellow  | 50  | Engineer   | UK          | grace.y@example.com    | 555-3333     | 864 Fir St, Manchester, UK      |\n"
    "| 10  | Henry Violet  | 32  | Artist     | Australia   | henry.v@example.com    | 555-4444     | 753 Willow St, Melbourne, VIC   |\n"
    "| 11  | Irene Orange  | 26  | Scientist  | New Zealand | irene.o@example.com    | 555-5555     | 912 Poplar St, Auckland, NZ     |\n"
    "| 12  | Jack Indigo   | 38  | Teacher    | Ireland     | jack.i@example.com     | 555-6666     | 159 Elm St, Cork, IE            |\n"
    "| 13  | Karen Red     | 41  | Lawyer     | USA         | karen.r@example.com    | 555-7777     | 357 Cedar St, Boston, MA        |\n"
    "| 14  | Leo Brown     | 30  | Chef       | Canada      | leo.b@example.com      | 555-8888     | 246 Oak St, Calgary, AB         |\n"
    "| 15  | Mia Green     | 33  | Musician   | UK          | mia.g@example.com      | 555-9999     | 975 Pine St, Edinburgh, UK      |\n"
    "| 16  | Noah Yellow   | 29  | Doctor     | Australia   | noah.y@example.com     | 555-0000     | 864 Birch St, Brisbane, QLD     |\n"
    "| 17  | Olivia Blue   | 35  | Engineer   | New Zealand | olivia.b@example.com   | 555-1212     | 753 Maple St, Hamilton, NZ      |\n"
    "| 18  | Peter Black   | 42  | Artist     | Ireland     | peter.b@example.com    | 555-3434     | 912 Fir St, Limerick, IE        |\n"
    "| 19  | Quinn White   | 28  | Scientist  | USA         | quinn.w@example.com    | 555-5656     | 159 Willow St, Seattle, WA      |\n"
    "| 20  | Rachel Red    | 31  | Teacher    | Canada      | rachel.r@example.com   | 555-7878     | 357 Poplar St, Ottawa, ON       |\n"
    "| 21  | Steve Green   | 44  | Lawyer     | UK          | steve.g@example.com    | 555-9090     | 753 Elm St, Birmingham, UK      |\n"
    "| 22  | Tina Blue     | 36  | Musician   | Australia   | tina.b@example.com     | 555-1213     | 864 Cedar St, Perth, WA         |\n"
    "| 23  | Umar Black    | 39  | Chef       | New Zealand | umar.b@example.com     | 555-3435     | 975 Spruce St, Christchurch, NZ |\n"
    "| 24  | Victor Yellow | 43  | Engineer   | Ireland     | victor.y@example.com   | 555-5657     | 246 Willow St, Galway, IE       |\n"
    "| 25  | Wendy Orange  | 27  | Artist     | USA         | wendy.o@example.com    | 555-7879     | 135 Elm St, Denver, CO          |\n"
    "| 26  | Xavier Green  | 34  | Scientist  | Canada      | xavier.g@example.com   | 555-9091     | 357 Oak St, Montreal, QC        |\n"
    "| 27  | Yara Red      | 41  | Teacher    | UK          | yara.r@example.com     | 555-1214     | 975 Pine St, Leeds, UK          |\n"
    "| 28  | Zack Blue     | 30  | Lawyer     | Australia   | zack.b@example.com     | 555-3436     | 135 Birch St, Adelaide, SA      |\n"
    "| 29  | Amy White     | 33  | Musician   | New Zealand | amy.w@example.com      | 555-5658     | 159 Maple St, Wellington, NZ    |\n"
    "| 30  | Ben Black     | 38  | Chef       | Ireland     | ben.b@example.com      | 555-7870     | 246 Fir St, Waterford, IE       |\n\n"
)

# (B) 较短共享前缀: 常见系统级 System Prompt (约 45 Tokens)
SHORT_PREFIX_SYSTEM = (
    "你是一个严谨且乐于助人的专业AI助手. 在回答用户提出的常识或学科问题时,"
    "请务必保持客观、精炼、准确, 直接给出核心答案, 不要有多余的寒暄与废话.\n\n"
)


# ==========================================
# 3. 核心请求函数 (捕获流式 Usage, Cached Tokens & 延迟)
# ==========================================
def query_with_streaming_metrics(prompt: str, query_label: str):
    """
    通过 stream=True 配合 stream_options={"include_usage": True} 模式发送请求:
    1. 测量 TTFT (首字延迟) 和 TPOT (单 Token 解码延迟)
    2. 从最后一个数据 Chunk 提取 Usage (prompt_tokens, cached_tokens, completion_tokens)
    """
    print(f"\n" + "-" * 70)
    print(f"🚀 发送请求: [{query_label}]")
    print("-" * 70)

    start_time = time.perf_counter()
    first_token_time = None
    full_response = []
    final_usage = None

    # 启用流式传输, 并通过 stream_options 要求服务端返回最终 usage 统计
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=60,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in response:
        # 1. 抓取流式生成的文本内容
        print("chunk: " + chunk.model_dump_json(indent=4))
        print(f"---")

        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                full_response.append(delta)

        # 2. 抓取流式末尾附加的 usage 信息
        if hasattr(chunk, "usage") and chunk.usage is not None:
            final_usage = chunk.usage

    end_time = time.perf_counter()

    # 延迟度量计算
    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
    total_time_ms = (end_time - start_time) * 1000
    answer_text = "".join(full_response).strip()

    # Usage 与 Token 缓存指标提取
    prompt_tokens = getattr(final_usage, "prompt_tokens", 0) if final_usage else 0
    completion_tokens = (
        getattr(final_usage, "completion_tokens", 0)
        if final_usage
        else len(full_response)
    )

    # 提取 cached_tokens (vLLM 在 prompt_tokens_details 中返回)
    cached_tokens = 0
    if (
        final_usage
        and hasattr(final_usage, "prompt_tokens_details")
        and final_usage.prompt_tokens_details
    ):
        cached_tokens = (
            getattr(final_usage.prompt_tokens_details, "cached_tokens", 0) or 0
        )

    uncached_tokens = max(0, prompt_tokens - cached_tokens)
    cache_hit_rate_req = (
        (cached_tokens / prompt_tokens * 100) if prompt_tokens > 0 else 0.0
    )

    # 打印详细结果
    print(f"📝 [模型回答]: {answer_text}")
    print(
        f"⏱️ [耗时指标]: TTFT (首字延迟) = {ttft_ms:.2f} ms | 总响应耗时 = {total_time_ms:.2f} ms"
    )

    if final_usage:
        print(f"📊 [Token Usage 详情]:")
        print(f"   ├─ Prompt Tokens (输入总数): {prompt_tokens}")
        print(f"   ├─ Cached Tokens (复用缓存数): {cached_tokens}  <-- [关键判定依据]")
        print(f"   ├─ Uncached Tokens (实际Prefill): {uncached_tokens}")
        print(f"   ├─ Completion Tokens (生成数): {completion_tokens}")
        print(f"   └─ 本次请求前缀缓存命中率: {cache_hit_rate_req:.1f}%")
        if cached_tokens > 0:
            print(
                f"   ✅ [确凿证据]: vLLM 成功跳过了 {cached_tokens} 个 Token 的 Prefill 计算, 直接读取显存 KV Cache!"
            )
        else:
            print(
                f"   ❄️ [冷启动]: 没有命中缓存 (cached_tokens = 0), 执行了全量 Prefill 计算."
            )
    else:
        print(
            "⚠️ [警告] 未能从数据流中获取 Usage. 请确认 vLLM 是否支持或已开启 `--enable-prompt-tokens-details`. "
        )

    return {
        "label": query_label,
        "ttft_ms": ttft_ms,
        "total_time_ms": total_time_ms,
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached_tokens,
        "cache_hit_rate_req": cache_hit_rate_req,
        "answer": answer_text,
    }


# ==========================================
# 4. 辅助函数: 从 Prometheus 指标端点获取统计
# ==========================================
def get_vllm_prometheus_metrics():
    """抓取 vLLM /metrics 提取前缀缓存命中率及显存缓存使用率"""
    metrics = {"prefix_cache_hit_rate": "N/A", "gpu_cache_usage_factor": "N/A"}
    try:
        res = requests.get(f"{SERVER_HOST}/metrics", timeout=3)
        if res.status_code == 200:
            for line in res.text.splitlines():
                if line.startswith("#"):
                    continue
                if "prefix_cache_hit_rate" in line:
                    metrics["prefix_cache_hit_rate"] = line.split()[-1]
                elif "gpu_cache_usage_factor" in line:
                    metrics["gpu_cache_usage_factor"] = line.split()[-1]
    except Exception as e:
        metrics["error"] = str(e)
    return metrics


# ==========================================
# 5. 主执行逻辑: 长短 Prompt 全流程对比实验
# ==========================================
def main():
    print("=" * 80)
    print("🎯 vLLM Automatic Prefix Caching (APC) 全面验证与长度对比实验")
    print("=" * 80)

    # -------------------------------------------------------------
    # 实验组 1: 超长 Prompt (约 1500+ Tokens) 验证
    # -------------------------------------------------------------
    print("\n" + "#" * 80)
    print("🧪 实验一: 超长前缀测试 (约 1500+ Tokens 表格)")
    print("#" * 80)

    long_q1 = LONG_PREFIX_TABLE + "问题: 请问 John Doe 的年龄和职业是什么? 请简明回答:"
    long_res1 = query_with_streaming_metrics(
        long_q1, "长 Prompt - 第 1 次请求 (Cold Start / Cache Miss)"
    )

    time.sleep(1)  # 留出 1 秒给 vLLM 更新缓存索引

    long_q2 = (
        LONG_PREFIX_TABLE + "问题: 请问 Zack Blue 的职业和所在国家是什么? 请简明回答:"
    )
    long_res2 = query_with_streaming_metrics(
        long_q2, "长 Prompt - 第 2 次请求 (Shared Prefix / Cache Hit)"
    )

    # -------------------------------------------------------------
    # 实验组 2: 较短 Prompt (约 45 Tokens) 验证
    # -------------------------------------------------------------
    print("\n" + "#" * 80)
    print("🧪 实验二: 较短前缀测试 (约 45 Tokens 系统指令)")
    print("#" * 80)

    short_q1 = SHORT_PREFIX_SYSTEM + "问题: 太阳系中体积最大的行星是哪一颗?"
    short_res1 = query_with_streaming_metrics(
        short_q1, "短 Prompt - 第 1 次请求 (Cold Start / Cache Miss)"
    )

    time.sleep(1)

    short_q2 = SHORT_PREFIX_SYSTEM + "问题: 光在真空中传播的速度大约是多少每秒?"
    short_res2 = query_with_streaming_metrics(
        short_q2, "短 Prompt - 第 2 次请求 (Shared Prefix / Cache Hit)"
    )

    # -------------------------------------------------------------
    # 实验组 3: 汇总对比与技术指标分析
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("📈 实验对比汇总表")
    print("=" * 80)

    long_speedup = (
        (long_res1["ttft_ms"] / long_res2["ttft_ms"]) if long_res2["ttft_ms"] > 0 else 0
    )
    short_speedup = (
        (short_res1["ttft_ms"] / short_res2["ttft_ms"])
        if short_res2["ttft_ms"] > 0
        else 0
    )

    print(f"{'对比维度':<22} | {'[长 Prompt 实验组]':<25} | {'[短 Prompt 实验组]':<25}")
    print("-" * 80)
    print(
        f"{'Prompt 总 Token 数':<20} | {str(long_res1['prompt_tokens']):<27} | {str(short_res1['prompt_tokens']):<27}"
    )
    print(
        f"{'二次请求 Cached Tokens':<18} | {str(long_res2['cached_tokens']):<27} | {str(short_res2['cached_tokens']):<27}"
    )
    print(
        f"{'前缀缓存命中比例':<20} | {f'{long_res2['cache_hit_rate_req']:.1f}%':<27} | {f'{short_res2['cache_hit_rate_req']:.1f}%':<27}"
    )
    print(
        f"{'首次 TTFT (无缓存)':<20} | {f'{long_res1['ttft_ms']:.2f} ms':<27} | {f'{short_res1['ttft_ms']:.2f} ms':<27}"
    )
    print(
        f"{'二次 TTFT (命中缓存)':<20} | {f'{long_res2['ttft_ms']:.2f} ms':<27} | {f'{short_res2['ttft_ms']:.2f} ms':<27}"
    )
    print(
        f"{'🚀 TTFT 加速比':<20} | {f'{long_speedup:.2f} x 提升':<27} | {f'{short_speedup:.2f} x 提升':<27}"
    )
    print("-" * 80)

    # 抓取服务端全局指标
    server_metrics = get_vllm_prometheus_metrics()
    print(f"🌐 [vLLM 服务端全局 Prometheus 状态]")
    print(
        f"   ├─ 前缀缓存命中率 (prefix_cache_hit_rate): {server_metrics.get('prefix_cache_hit_rate', 'N/A')}"
    )
    print(
        f"   └─ GPU KV Cache 使用率 (gpu_cache_usage) : {server_metrics.get('gpu_cache_usage_factor', 'N/A')}"
    )
    print("=" * 80)

    # -------------------------------------------------------------
    # 核心原理解释与总结输出
    # -------------------------------------------------------------
    print("\n💡 [高级架构师技术解析: 前缀缓存与 Prompt 长度的关系]")
    print(
        "1. 缓存生效判定依据:\n"
        "   - 通过响应流中的 `usage.prompt_tokens_details.cached_tokens` 可以 100% 确定是否复用了 KV Cache.\n"
        "   - 若 `cached_tokens > 0`, 代表该数量的 Token 未参与 Prefill 矩阵乘法, 而是直接从 GPU 物理显存块(Block)复用.\n\n"
        "2. 前缀缓存与 Prompt 长度的关系与机制约束:\n"
        "   - Block 对齐限制(离散化分块):\n"
        "     vLLM 以 `block_size`(默认为 16 个 Token)为基本单位进行哈希管理. 只有凑满整块的 Token 才会进入 Radix Tree.\n"
        "     * 若 Prompt 长度极短(< 16 Tokens), `cached_tokens` 会始终为 0, 前缀缓存无法生效!\n"
        "     * 若 Prompt 长度为 45 Tokens, 最多只能缓存 `floor(45/16)*16 = 32` 个 Tokens, 剩余不满一整块的末尾 Token 必须重新 Prefill.\n"
        "   - 延迟加速效益与 Prompt 长度呈强正相关:\n"
        "     * 超长 Prompt: Prefill 计算复杂度为 O(N^2), 耗时极长. 命中缓存后省去了数千个 Token 的重算, TTFT 加速极其显著(通常可达 3x ~ 10x+).\n"
        "     * 极短 Prompt: Prefill 本身耗时仅需几毫秒, 此时性能瓶颈在于 API 框架调度、CUDA Kernel 启动以及网络 I/O, 因此 TTFT 加速比可能并不明显(1.0x ~ 1.5x 左右), 但底层 `cached_tokens` 依然真实生效."
    )


if __name__ == "__main__":
    main()


"""
================================================================================
🎯 vLLM Automatic Prefix Caching (APC) 全面验证与长度对比实验
================================================================================

################################################################################
🧪 实验一: 超长前缀测试 (约 1500+ Tokens 表格)
################################################################################

----------------------------------------------------------------------
🚀 发送请求: [长 Prompt - 第 1 次请求 (Cold Start / Cache Miss)]
----------------------------------------------------------------------
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": "assistant",
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 1634,
        "total_tokens": 1634,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    },
    "prompt_token_ids": null,
    "prompt_text": null
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "John",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 1,
        "prompt_tokens": 1634,
        "total_tokens": 1635,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": " Doe",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 2,
        "prompt_tokens": 1634,
        "total_tokens": 1636,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": " 的",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 3,
        "prompt_tokens": 1634,
        "total_tokens": 1637,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "年龄",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 4,
        "prompt_tokens": 1634,
        "total_tokens": 1638,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 5,
        "prompt_tokens": 1634,
        "total_tokens": 1639,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": " ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 6,
        "prompt_tokens": 1634,
        "total_tokens": 1640,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "2",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 7,
        "prompt_tokens": 1634,
        "total_tokens": 1641,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "9",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 8,
        "prompt_tokens": 1634,
        "total_tokens": 1642,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 9,
        "prompt_tokens": 1634,
        "total_tokens": 1643,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 10,
        "prompt_tokens": 1634,
        "total_tokens": 1644,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": " 岁",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 11,
        "prompt_tokens": 1634,
        "total_tokens": 1645,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": ", ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 12,
        "prompt_tokens": 1634,
        "total_tokens": 1646,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "职业",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 13,
        "prompt_tokens": 1634,
        "total_tokens": 1647,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 14,
        "prompt_tokens": 1634,
        "total_tokens": 1648,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": " Engineer",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 15,
        "prompt_tokens": 1634,
        "total_tokens": 1649,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": ". ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 16,
        "prompt_tokens": 1634,
        "total_tokens": 1650,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "stop_reason": null,
            "token_ids": null
        }
    ],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 17,
        "prompt_tokens": 1634,
        "total_tokens": 1651,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bb8abda6fe4b5a43",
    "choices": [],
    "created": 1787893902,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": "vllm-0.22.0-85f39604",
    "usage": {
        "completion_tokens": 17,
        "prompt_tokens": 1634,
        "total_tokens": 1651,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
📝 [模型回答]: John Doe 的年龄是 29 岁, 职业是 Engineer.
⏱️ [耗时指标]: TTFT (首字延迟) = 2548.56 ms | 总响应耗时 = 2559.44 ms
📊 [Token Usage 详情]:
   ├─ Prompt Tokens (输入总数): 1634
   ├─ Cached Tokens (复用缓存数): 0  <-- [关键判定依据]
   ├─ Uncached Tokens (实际Prefill): 1634
   ├─ Completion Tokens (生成数): 17
   └─ 本次请求前缀缓存命中率: 0.0%
   ❄️ [冷启动]: 没有命中缓存 (cached_tokens = 0), 执行了全量 Prefill 计算.

----------------------------------------------------------------------
🚀 发送请求: [长 Prompt - 第 2 次请求 (Shared Prefix / Cache Hit)]
----------------------------------------------------------------------
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": "assistant",
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 1635,
        "total_tokens": 1635,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    },
    "prompt_token_ids": null,
    "prompt_text": null
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "Z",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 1,
        "prompt_tokens": 1635,
        "total_tokens": 1636,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "ack",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 2,
        "prompt_tokens": 1635,
        "total_tokens": 1637,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": " Blue",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 3,
        "prompt_tokens": 1635,
        "total_tokens": 1638,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": " 的",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 4,
        "prompt_tokens": 1635,
        "total_tokens": 1639,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "职业",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 5,
        "prompt_tokens": 1635,
        "total_tokens": 1640,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 6,
        "prompt_tokens": 1635,
        "total_tokens": 1641,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "律师",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 7,
        "prompt_tokens": 1635,
        "total_tokens": 1642,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": ", ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 8,
        "prompt_tokens": 1635,
        "total_tokens": 1643,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "所在",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 9,
        "prompt_tokens": 1635,
        "total_tokens": 1644,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "国家",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 10,
        "prompt_tokens": 1635,
        "total_tokens": 1645,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 11,
        "prompt_tokens": 1635,
        "total_tokens": 1646,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "澳大利亚",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 12,
        "prompt_tokens": 1635,
        "total_tokens": 1647,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": ". ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 13,
        "prompt_tokens": 1635,
        "total_tokens": 1648,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "stop_reason": null,
            "token_ids": null
        }
    ],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 14,
        "prompt_tokens": 1635,
        "total_tokens": 1649,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-bba2d8ca740ebab4",
    "choices": [],
    "created": 1787893905,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": "vllm-0.22.0-85f39604",
    "usage": {
        "completion_tokens": 14,
        "prompt_tokens": 1635,
        "total_tokens": 1649,
        "completion_tokens_details": null,
        "prompt_tokens_details": {
            "audio_tokens": null,
            "cache_write_tokens": null,
            "cached_tokens": 1600,
            "image_tokens": null,
            "text_tokens": null
        }
    }
}
---
📝 [模型回答]: Zack Blue 的职业是律师, 所在国家是澳大利亚.
⏱️ [耗时指标]: TTFT (首字延迟) = 464.10 ms | 总响应耗时 = 474.99 ms
📊 [Token Usage 详情]:
   ├─ Prompt Tokens (输入总数): 1635
   ├─ Cached Tokens (复用缓存数): 1600  <-- [关键判定依据]
   ├─ Uncached Tokens (实际Prefill): 35
   ├─ Completion Tokens (生成数): 14
   └─ 本次请求前缀缓存命中率: 97.9%
   ✅ [确凿证据]: vLLM 成功跳过了 1600 个 Token 的 Prefill 计算, 直接读取显存 KV Cache!

################################################################################
🧪 实验二: 较短前缀测试 (约 45 Tokens 系统指令)
################################################################################

----------------------------------------------------------------------
🚀 发送请求: [短 Prompt - 第 1 次请求 (Cold Start / Cache Miss)]
----------------------------------------------------------------------
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": "assistant",
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 92,
        "total_tokens": 92,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    },
    "prompt_token_ids": null,
    "prompt_text": null
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "木",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 1,
        "prompt_tokens": 92,
        "total_tokens": 93,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "星",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 2,
        "prompt_tokens": 92,
        "total_tokens": 94,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 3,
        "prompt_tokens": 92,
        "total_tokens": 95,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "太阳",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 4,
        "prompt_tokens": 92,
        "total_tokens": 96,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "系",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 5,
        "prompt_tokens": 92,
        "total_tokens": 97,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "中",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 6,
        "prompt_tokens": 92,
        "total_tokens": 98,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "体积",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 7,
        "prompt_tokens": 92,
        "total_tokens": 99,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "最大的",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 8,
        "prompt_tokens": 92,
        "total_tokens": 100,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "行星",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 9,
        "prompt_tokens": 92,
        "total_tokens": 101,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": ". ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 10,
        "prompt_tokens": 92,
        "total_tokens": 102,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "stop_reason": null,
            "token_ids": null
        }
    ],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 11,
        "prompt_tokens": 92,
        "total_tokens": 103,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-baab328b754f345f",
    "choices": [],
    "created": 1787893906,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": "vllm-0.22.0-85f39604",
    "usage": {
        "completion_tokens": 11,
        "prompt_tokens": 92,
        "total_tokens": 103,
        "completion_tokens_details": null,
        "prompt_tokens_details": {
            "audio_tokens": null,
            "cache_write_tokens": null,
            "cached_tokens": 16,
            "image_tokens": null,
            "text_tokens": null
        }
    }
}
---
📝 [模型回答]: 木星是太阳系中体积最大的行星.
⏱️ [耗时指标]: TTFT (首字延迟) = 352.06 ms | 总响应耗时 = 365.09 ms
📊 [Token Usage 详情]:
   ├─ Prompt Tokens (输入总数): 92
   ├─ Cached Tokens (复用缓存数): 16  <-- [关键判定依据]
   ├─ Uncached Tokens (实际Prefill): 76
   ├─ Completion Tokens (生成数): 11
   └─ 本次请求前缀缓存命中率: 17.4%
   ✅ [确凿证据]: vLLM 成功跳过了 16 个 Token 的 Prefill 计算, 直接读取显存 KV Cache!

----------------------------------------------------------------------
🚀 发送请求: [短 Prompt - 第 2 次请求 (Shared Prefix / Cache Hit)]
----------------------------------------------------------------------
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": "assistant",
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 92,
        "total_tokens": 92,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    },
    "prompt_token_ids": null,
    "prompt_text": null
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "光",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 1,
        "prompt_tokens": 92,
        "total_tokens": 93,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "在",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 2,
        "prompt_tokens": 92,
        "total_tokens": 94,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "真",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 3,
        "prompt_tokens": 92,
        "total_tokens": 95,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "空中",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 4,
        "prompt_tokens": 92,
        "total_tokens": 96,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "传播",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 5,
        "prompt_tokens": 92,
        "total_tokens": 97,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "的速度",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 6,
        "prompt_tokens": 92,
        "total_tokens": 98,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "大约",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 7,
        "prompt_tokens": 92,
        "total_tokens": 99,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "是",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 8,
        "prompt_tokens": 92,
        "total_tokens": 100,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "2",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 9,
        "prompt_tokens": 92,
        "total_tokens": 101,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "9",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 10,
        "prompt_tokens": 92,
        "total_tokens": 102,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "9",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 11,
        "prompt_tokens": 92,
        "total_tokens": 103,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": ",",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 12,
        "prompt_tokens": 92,
        "total_tokens": 104,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "7",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 13,
        "prompt_tokens": 92,
        "total_tokens": 105,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "9",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 14,
        "prompt_tokens": 92,
        "total_tokens": 106,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "2",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 15,
        "prompt_tokens": 92,
        "total_tokens": 107,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "公里",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 16,
        "prompt_tokens": 92,
        "total_tokens": 108,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "/",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 17,
        "prompt_tokens": 92,
        "total_tokens": 109,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "秒",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 18,
        "prompt_tokens": 92,
        "total_tokens": 110,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": ". ",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": null,
            "index": 0,
            "logprobs": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 19,
        "prompt_tokens": 92,
        "total_tokens": 111,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [
        {
            "delta": {
                "content": "",
                "function_call": null,
                "refusal": null,
                "role": null,
                "tool_calls": null
            },
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "stop_reason": null,
            "token_ids": null
        }
    ],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 20,
        "prompt_tokens": 92,
        "total_tokens": 112,
        "completion_tokens_details": null,
        "prompt_tokens_details": null
    }
}
---
chunk: {
    "id": "chatcmpl-870e449e55d4fd1d",
    "choices": [],
    "created": 1787893907,
    "model": "Qwen2.5-7B-Instruct",
    "object": "chat.completion.chunk",
    "moderation": null,
    "obfuscation": null,
    "service_tier": null,
    "system_fingerprint": "vllm-0.22.0-85f39604",
    "usage": {
        "completion_tokens": 20,
        "prompt_tokens": 92,
        "total_tokens": 112,
        "completion_tokens_details": null,
        "prompt_tokens_details": {
            "audio_tokens": null,
            "cache_write_tokens": null,
            "cached_tokens": 64,
            "image_tokens": null,
            "text_tokens": null
        }
    }
}
---
📝 [模型回答]: 光在真空中传播的速度大约是299,792公里/秒.
⏱️ [耗时指标]: TTFT (首字延迟) = 665.65 ms | 总响应耗时 = 673.86 ms
📊 [Token Usage 详情]:
   ├─ Prompt Tokens (输入总数): 92
   ├─ Cached Tokens (复用缓存数): 64  <-- [关键判定依据]
   ├─ Uncached Tokens (实际Prefill): 28
   ├─ Completion Tokens (生成数): 20
   └─ 本次请求前缀缓存命中率: 69.6%
   ✅ [确凿证据]: vLLM 成功跳过了 64 个 Token 的 Prefill 计算, 直接读取显存 KV Cache!

================================================================================
📈 实验对比汇总表
================================================================================
对比维度                   | [长 Prompt 实验组]            | [短 Prompt 实验组]
--------------------------------------------------------------------------------
Prompt 总 Token 数     | 1634                        | 92
二次请求 Cached Tokens | 1600                        | 64
前缀缓存命中比例             | 97.9%                       | 69.6%
首次 TTFT (无缓存)        | 2548.56 ms                  | 352.06 ms
二次 TTFT (命中缓存)       | 464.10 ms                   | 665.65 ms
🚀 TTFT 加速比           | 5.49 x 提升                   | 0.53 x 提升
--------------------------------------------------------------------------------
🌐 [vLLM 服务端全局 Prometheus 状态]
   ├─ 前缀缓存命中率 (prefix_cache_hit_rate): N/A
   └─ GPU KV Cache 使用率 (gpu_cache_usage) : N/A
================================================================================

💡 [高级架构师技术解析: 前缀缓存与 Prompt 长度的关系]
1. 缓存生效判定依据:
   - 通过响应流中的 `usage.prompt_tokens_details.cached_tokens` 可以 100% 确定是否复用了 KV Cache.
   - 若 `cached_tokens > 0`, 代表该数量的 Token 未参与 Prefill 矩阵乘法, 而是直接从 GPU 物理显存块(Block)复用.

2. 前缀缓存与 Prompt 长度的关系与机制约束:
   - Block 对齐限制(离散化分块):
     vLLM 以 `block_size`(默认为 16 个 Token)为基本单位进行哈希管理. 只有凑满整块的 Token 才会进入 Radix Tree.
     * 若 Prompt 长度极短(< 16 Tokens), `cached_tokens` 会始终为 0, 前缀缓存无法生效!
     * 若 Prompt 长度为 45 Tokens, 最多只能缓存 `floor(45/16)*16 = 32` 个 Tokens, 剩余不满一整块的末尾 Token 必须重新 Prefill.
   - 延迟加速效益与 Prompt 长度呈强正相关:
     * 超长 Prompt: Prefill 计算复杂度为 O(N^2), 耗时极长. 命中缓存后省去了数千个 Token 的重算, TTFT 加速极其显著(通常可达 3x ~ 10x+).
     * 极短 Prompt: Prefill 本身耗时仅需几毫秒, 此时性能瓶颈在于 API 框架调度、CUDA Kernel 启动以及网络 I/O, 因此 TTFT 加速比可能并不明显(1.0x ~ 1.5x 左右), 但底层 `cached_tokens` 依然真实生效.

"""
