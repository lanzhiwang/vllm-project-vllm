import time
from typing import Dict, Any, Optional
from llmlingua import PromptCompressor
from openai import OpenAI

# ==========================================
# 1. 本地路径与基础配置
# ==========================================
VLLM_BASE_URL = "http://10.41.0.4:8000/v1"  # 本地 vLLM 推理服务
VLLM_API_KEY = "my_secret_token_123"
MODEL_NAME = "Qwen2.5-7B-Instruct"


LOCAL_COMPRESSOR_PATH = "/model/llmlingua-2-xlm-roberta-large-meetingbank"
LOCAL_MAIN_MODEL_PATH = "/model/Qwen2.5-7B-Instruct"
LOCAL_TIKTOKEN_FILE_PATH = "/path/to/tokens/cl100k_base.tiktoken"

# 初始化 vLLM 客户端
vllm_client = OpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY)


# ==========================================
# 2. 本地离线 Token 计算器初始化
# ==========================================
def init_local_tokenizer(use_tiktoken: bool = False):
    """
    初始化本地 Tokenizer
    """
    if use_tiktoken:
        # ---- 纯离线加载 tiktoken 词表文件 ----
        import tiktoken
        from tiktoken.load import load_tiktoken_bpe

        print(
            f"📦 [Tokenizer] 正在从本地文件加载 tiktoken 词表: {LOCAL_TIKTOKEN_FILE_PATH}"
        )
        mergeable_ranks = load_tiktoken_bpe(LOCAL_TIKTOKEN_FILE_PATH)

        # 构建与 cl100k_base 严格一致的本地 Encoding 对象
        special_tokens = {
            "<|endoftext|>": 100257,
            "<|fim_prefix|>": 100258,
            "<|fim_middle|>": 100259,
            "<|fim_suffix|>": 100260,
            "<|endofprompt|>": 100276,
        }
        enc = tiktoken.Encoding(
            name="cl100k_base",
            pat_str=r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+""",
            mergeable_ranks=mergeable_ranks,
            special_tokens=special_tokens,
        )
        return lambda text: len(enc.encode(text))

    else:
        # ---- 直接加载本地主模型的 Tokenizer ----
        from transformers import AutoTokenizer

        print(
            f"📦 [Tokenizer] 正在从本地模型目录加载 AutoTokenizer: {LOCAL_MAIN_MODEL_PATH}"
        )
        tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_MAIN_MODEL_PATH,
            trust_remote_code=True,
        )
        return lambda text: len(tokenizer.encode(text))


# 实例化本地 Token 计数函数 (默认使用与 vLLM 完全一致的本地模型 Tokenizer)
count_tokens_offline = init_local_tokenizer(use_tiktoken=False)
print("✅ 本地离线 Tokenizer 加载成功!\n")


# ==========================================
# 3. 本地离线加载 LLMLingua-2 压缩器
# ==========================================
print(f"📦 [Compressor] 正在从本地加载压缩模型: {LOCAL_COMPRESSOR_PATH}")
compressor = PromptCompressor(
    model_name=LOCAL_COMPRESSOR_PATH,
    use_llmlingua2=True,
    device_map="cuda",  # 若无 GPU 可切换为 "cpu"
)
print("✅ 本地压缩模型加载完成!\n")


# ==========================================
# 4. 构造长上下文 Prompt 样本
# ==========================================
long_context = """
[背景材料文档切片 1]:
根据2025年第一季度的全球宏观经济环境报告显示, 在当前全球通胀逐步降温但地缘政治摩擦加剧的复杂背景下,
人工智能基础设施产业链迎来了新一轮的结构性分化. 具体而言, 以高性能GPU、高带宽内存(HBM3e/HBM4)
以及先进异构封装为核心的硬件算力层, 依然保持着超过45%的高速年复合增长率.
与此同时, 北美与亚太地区的主要云服务提供商(CSP)持续加码资本支出(CapEx),
其中微软、谷歌、Meta与亚马逊四大巨头在2025年Q1的总资本开支历史上首次突破了650亿美元大关.

[背景材料文档切片 2]:
然而, 在极其旺盛的下游算力需求驱动下, 上游供应链的脆弱性问题正在被迅速放大.
由于台积电(TSMC)先进CoWoS封装产能在短期内的扩张速度受制于特种设备交付周期,
导致交期依然维持在18至24周的高位. 此外, 高压配电设备、大型变压器以及数据中心液冷散热模块的短缺,
已经成为制约算力集群快速交付的第二大物理瓶颈. 行业分析师明确指出, 电力接入申请(Power Interconnection)
的漫长审批周期正迫使部分超大型数据中心向电力资源更为充沛但网络基础设施较弱的次级区域迁移.

[背景材料文档切片 3]:
在企业端软件与模型应用落地层面, 企业对ROI(投资回报率)的考核正变得空前严苛.
2024年下半年以来盲目上马端到端大模型重构业务流程的项目中, 有接近35%由于推理调用成本过高、
长文本上下文响应延迟过大(TTFT超过10秒)而被迫暂停或转为采用小模型蒸馏方案.
因此, 能够显著降低模型单次推理成本的显存优化技术(如KV Cache量化、Chunked Prefill)
以及上下文压缩裁剪技术(如Semantic Prompt Compression)正在从学术探索加速走向工业界主流生产管线.
"""

instruction = "你是一位精通半导体硬件与 AI 云计算产业的资深分析师."
question = "请深入剖析当前 AI 算力供应链面临的核心瓶颈是什么? 以及这些瓶颈对企业落地 AI 项目造成了哪些实质影响?"


# ==========================================
# 5. 执行压缩与本地 Token 对比统计
# ==========================================
def compress_prompt_workflow(
    context: str, instruction: str, question: str, target_rate: float = 0.4
) -> Dict[str, Any]:
    print("=" * 70)
    print(f"🚀 开始执行本地语义提示词压缩 (目标保留率: {target_rate * 100}%)...")
    start_time = time.time()

    # 本地压缩
    compression_result = compressor.compress_prompt(
        context=[context],
        instruction=instruction,
        question=question,
        rate=target_rate,
        drop_consecutive=True,
    )
    compress_latency_ms = (time.time() - start_time) * 1000
    compressed_text = compression_result["compressed_prompt"]

    # 原始完整 Prompt 拼接
    raw_text = f"{instruction}\n\n参考资料: \n{context}\n\n问题: {question}"

    # 使用本地 Tokenizer 计算精确 Token 数量
    raw_token_count = count_tokens_offline(raw_text)
    comp_token_count = count_tokens_offline(compressed_text)
    saved_tokens = raw_token_count - comp_token_count
    reduction_pct = (saved_tokens / raw_token_count) * 100

    print(f"⏱️ 压缩耗时: {compress_latency_ms:.2f} ms")
    print(
        f"📊 [本地 Tokenizer 统计] 原始 Prompt: {raw_token_count} Tokens | 压缩后: {comp_token_count} Tokens"
    )
    print(
        f"💡 上下文空间释放: 节省 {saved_tokens} Tokens (缩减率: {reduction_pct:.2f}%)"
    )
    print("=" * 70)

    print("\n🔍 [压缩后的 Prompt 内容预览]:")
    print("-" * 50)
    print(compressed_text)
    print("-" * 50 + "\n")

    return {
        "raw_prompt": raw_text,
        "compressed_prompt": compressed_text,
        "raw_tokens": raw_token_count,
        "compressed_tokens": comp_token_count,
        "compress_latency_ms": compress_latency_ms,
    }


# ==========================================
# 6. 调用 vLLM 推理服务捕获性能指标
# ==========================================
def call_vllm_inference(prompt: str, label: str) -> Optional[Dict[str, Any]]:
    print(f"📡 正在向 vLLM 发送请求 -> {label} ...")
    start_time = time.time()

    try:
        response = vllm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        total_latency = time.time() - start_time

        output_text = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        print(
            f"✅ {label} 推理完成! 耗时: {total_latency:.2f}s | 生成 Tokens: {completion_tokens}"
        )

        return {
            "label": label,
            "latency": total_latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "output_text": output_text,
        }
    except Exception as e:
        print(f"⚠️ vLLM 调用失败: {e}")
        return None


# ==========================================
# 7. 主执行入口: A/B 对比评测看板
# ==========================================
if __name__ == "__main__":
    # 1. 运行压缩流程
    compression_data = compress_prompt_workflow(
        context=long_context,
        instruction=instruction,
        question=question,
        target_rate=0.4,
    )

    # 2. 调用对照组: 未压缩 Prompt
    raw_result = call_vllm_inference(
        prompt=compression_data["raw_prompt"], label="[对照组]原始未压缩 Prompt"
    )

    # 3. 调用实验组: 压缩后 Prompt
    comp_result = call_vllm_inference(
        prompt=compression_data["compressed_prompt"],
        label="[实验组]语义压缩后 Prompt",
    )

    # 4. 输出最终量化对比面板
    if raw_result and comp_result:
        print("\n" + "=" * 70)
        print("🏆 [vLLM 纯离线环境推理性能与上下文 A/B 对比结果]")
        print("=" * 70)
        print(
            f"{'指标维度':<22} | {'[对照组]原始 Prompt':<20} | {'[实验组]压缩后 Prompt':<20}"
        )
        print("-" * 70)
        print(
            f"{'本地统计 Prompt Tokens':<18} | {compression_data['raw_tokens']:<20} | {compression_data['compressed_tokens']:<20}"
        )
        print(
            f"{'vLLM 实际 Prompt Tokens':<17} | {raw_result['prompt_tokens']:<20} | {comp_result['prompt_tokens']:<20}"
        )
        print(
            f"{'输出 Completion Tokens':<18} | {raw_result['completion_tokens']:<20} | {comp_result['completion_tokens']:<20}"
        )
        print(
            f"{'端到端耗时 (Latency)':<18} | {raw_result['latency']:.2f} s{'':<16} | {comp_result['latency']:.2f} s"
        )

        saved_input = raw_result["prompt_tokens"] - comp_result["prompt_tokens"]
        saved_ratio = (saved_input / raw_result["prompt_tokens"]) * 100
        print("-" * 70)
        print(
            f"✨ 核心收益: 输入上下文缩减 {saved_ratio:.1f}% (节省 {saved_input} Tokens), 为长输出释放了充分预算! "
        )
        print("=" * 70)

        # 对比生成回答质量
        print("\n📄 [对照组输出内容节选]:")
        print(raw_result["output_text"][:260] + "...\n")

        print("📄 [实验组输出内容节选]:")
        print(comp_result["output_text"][:260] + "...\n")


"""
$ python3 prompt_compression_demo.py
📦 [Tokenizer] 正在从本地模型目录加载 AutoTokenizer: /model/Qwen2.5-7B-Instruct
✅ 本地离线 Tokenizer 加载成功!

📦 [Compressor] 正在从本地加载压缩模型: /model/llmlingua-2-xlm-roberta-large-meetingbank
Loading weights: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 391/391 [00:00<00:00, 751.01it/s]
✅ 本地压缩模型加载完成!

======================================================================
🚀 开始执行本地语义提示词压缩 (目标保留率: 40.0%)...
⏱️ 压缩耗时: 421.58 ms
📊 [本地 Tokenizer 统计] 原始 Prompt: 502 Tokens | 压缩后: 185 Tokens
💡 上下文空间释放: 节省 317 Tokens (缩减率: 63.15%)
======================================================================

🔍 [压缩后的 Prompt 内容预览]:
--------------------------------------------------
根据2025年第一季度的全球宏观经济环境报告显示 以高性能GPU、高带宽内存(HBM3e 以及先进异构封装为核心的硬件算力层 北美与亚太地区的主要云服务提供商)持续加码资本支出 其中微软、谷歌、Meta与亚马逊四大巨头在2025年Q1的总资本开支历史上首次突破了650亿美元大关(TSMC)先进CoWoS封装产能在短期内的扩张速度受制于特种设备交付周期 高压配电设备、大型变压器以及数据中心液冷散热模块的短缺 已经成为制约算力集群快速交付的第二大物理瓶颈(投资回报率 2024年下半年以来盲目上马端到端大模型重构业务流程的项目中 有接近35%由于推理调用成本过高、Cache量化、Chunked Prefill Prompt Compression
--------------------------------------------------

📡 正在向 vLLM 发送请求 -> [对照组]原始未压缩 Prompt ...
✅ [对照组]原始未压缩 Prompt 推理完成! 耗时: 15.48s | 生成 Tokens: 477
📡 正在向 vLLM 发送请求 -> [实验组]语义压缩后 Prompt ...
✅ [实验组]语义压缩后 Prompt 推理完成! 耗时: 8.86s | 生成 Tokens: 314

======================================================================
🏆 [vLLM 纯离线环境推理性能与上下文 A/B 对比结果]
======================================================================
指标维度                   | [对照组]原始 Prompt       | [实验组]压缩后 Prompt
----------------------------------------------------------------------
本地统计 Prompt Tokens | 502                  | 185
vLLM 实际 Prompt Tokens | 531                  | 214
输出 Completion Tokens | 477                  | 314
端到端耗时 (Latency)    | 15.48 s                 | 8.86 s
----------------------------------------------------------------------
✨ 核心收益: 输入上下文缩减 59.7% (节省 317 Tokens), 为长输出释放了充分预算!
======================================================================

📄 [对照组输出内容节选]:
当前AI算力供应链面临的核心瓶颈主要包括以下几个方面:

1. 上游硬件产能受限: 特别是高性能GPU、高带宽内存(HBM3e/HBM4)以及先进异构封装等核心硬件算力层, 其产能扩张速度受到限制. 具体来说, 台积电先进CoWoS封装产能扩张受制于特种设备交付周期, 导致交期维持在18至24周的高位.

2. 电力接入和大型基础设施短缺: 高压配电设备、大型变压器以及数据中心液冷散热模块的短缺成为制约算力集群快速交付的第二大大瓶颈. 这主要是因为电力接入申请的漫长审批周期迫使一些超大型数据中心不得不向电力资源丰...

📄 [实验组输出内容节选]:
根据您提供的信息, 2025年第一季度全球宏观经济环境下, 北美和亚太地区的云服务提供商在硬件算力层方面持续增加资本支出, 尤其是高性能GPU、HBM3e(高带宽内存)和先进异构封装技术. 这表明这些公司在提升计算能力方面投入巨大.

然而, 值得注意的是, 尽管这些技术进步有助于提高性能, 但它们也面临着一些挑战:

1. 先进CoWoS封装产能限制: 台积电(TSMC)的先进CoWoS(Chip-on-Wafer-on-Substrate)封装技术虽然能够显著提升集成度和性能, 但由于特种设备的交付周期较长, 短期内其产能...

$
"""
