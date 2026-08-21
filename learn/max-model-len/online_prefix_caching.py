import time
import requests
from openai import OpenAI

# ==========================================
# 1. 服务端连接配置
# ==========================================
SERVER_HOST = "http://localhost:8090"
API_KEY = "my_secret_token_123"
MODEL_NAME = "Qwen2.5-7B-Instruct"

client = OpenAI(base_url=f"{SERVER_HOST}/v1", api_key=API_KEY)

# ==========================================
# 2. 构造共享的超长前缀 Prompt (模拟长文档/系统知识库)
# ==========================================
# 构造一个包含 30 个人员信息的 Markdown 大表格作为共享前缀 (约 1500+ Tokens)
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


# ==========================================
# 3. 核心请求与性能度量函数 (基于流式首字延迟 TTFT)
# ==========================================
def query_with_streaming_metrics(prompt: str, query_label: str):
    """
    通过 stream=True 模式发送请求, 精准测量:
    1. TTFT (Time To First Token): 衡量 Prefill / KV Cache 复用效率
    2. Total Generation Time: 总体响应时间
    """
    print(f"\n🚀 正在发送请求: [{query_label}] ...")

    start_time = time.perf_counter()
    first_token_time = None
    full_response = []

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=60,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content if chunk.choices else ""
        if delta:
            if first_token_time is None:
                first_token_time = (
                    time.perf_counter()
                )  # 记录接收到第一个 Token 的时间点
            full_response.append(delta)

    end_time = time.perf_counter()

    ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else 0
    total_time_ms = (end_time - start_time) * 1000
    answer_text = "".join(full_response).strip()

    print(f"📝 模型回答: {answer_text}")
    print(
        f"⏱️  [性能指标] TTFT (首字延迟): {ttft_ms:.2f} ms | 总耗时: {total_time_ms:.2f} ms"
    )

    return {
        "label": query_label,
        "ttft_ms": ttft_ms,
        "total_time_ms": total_time_ms,
        "answer": answer_text,
    }


# ==========================================
# 4. 辅助函数: 从 vLLM Prometheus 端点获取缓存指标
# ==========================================
def get_vllm_cache_metrics():
    """抓取 vLLM 的 /metrics 接口, 提取 Prefix Cache 命中统计"""
    try:
        res = requests.get(f"{SERVER_HOST}/metrics", timeout=3)
        if res.status_code == 200:
            metrics_text = res.text
            hit_rate = "N/A"
            for line in metrics_text.splitlines():
                # 兼容不同的 metric 命名
                if "prefix_cache_hit_rate" in line and not line.startswith("#"):
                    hit_rate = line.split()[-1]
                    break
            return hit_rate
    except Exception as e:
        return f"获取失败 ({e})"
    return "未找到相关指标"


# ==========================================
# 5. 主执行与对比验证流程
# ==========================================
def main():
    print("=" * 60)
    print("🎯 vLLM 在线推理服务 - Automatic Prefix Caching (APC) 验证")
    print("=" * 60)

    # -------------------------------------------------------------
    # 请求 1: 首次请求 (Cold Start - Cache Miss)
    # 此时 vLLM 显存中没有任何该前缀的 KV Block, 必须执行全量 Prefill 计算
    # -------------------------------------------------------------
    prompt_query_1 = (
        LONG_PREFIX_TABLE + "问题: 请问 John Doe 的年龄和职业是什么? 请简明回答:"
    )
    res1 = query_with_streaming_metrics(
        prompt_query_1, "Query 1: 首次调用 (Cache Miss)"
    )

    # 稍微停顿 1 秒
    time.sleep(1)

    # -------------------------------------------------------------
    # 请求 2: 相同前缀的二次请求 (Warm Start - Cache Hit)
    # 共享前面的长表格, 仅问题不同. 应当直接命中 Radix Tree 中的 KV Cache
    # -------------------------------------------------------------
    prompt_query_2 = (
        LONG_PREFIX_TABLE + "问题: 请问 Zack Blue 的职业和所在国家是什么? 请简明回答:"
    )
    res2 = query_with_streaming_metrics(
        prompt_query_2, "Query 2: 共享前缀调用 (Cache Hit)"
    )

    # -------------------------------------------------------------
    # 验证与效果汇总
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("📊 验证结果对比汇总")
    print("=" * 60)

    ttft_speedup = res1["ttft_ms"] / res2["ttft_ms"] if res2["ttft_ms"] > 0 else 0
    print(f"1️⃣ 首次请求 TTFT (无缓存预填充) : {res1['ttft_ms']:.2f} ms")
    print(f"2️⃣ 二次请求 TTFT (命中前缀缓存) : {res2['ttft_ms']:.2f} ms")
    print(f"🚀 TTFT 延迟加速比            : {ttft_speedup:.2f}x (首字生成速度提升)")

    # 抓取服务端的 Prometheus 指标
    server_metric = get_vllm_cache_metrics()
    print(f"📈 vLLM 服务端 Prefix Cache 命中率: {server_metric}")
    print("=" * 60)

    if ttft_speedup > 1.5:
        print("🎉 验证成功: Prefix Caching 已在在线服务中成功生效并复用 KV Cache!")
    else:
        print(
            "⚠️ 提示: 加速不明显, 请检查启动命令中是否包含 --enable-prefix-caching 以及 Prompt 前缀是否完全一致."
        )


if __name__ == "__main__":
    main()


"""
$ python online_prefix_caching.py
============================================================
🎯 vLLM 在线推理服务 - Automatic Prefix Caching (APC) 验证
============================================================

🚀 正在发送请求: [Query 1: 首次调用 (Cache Miss)] ...
📝 模型回答: John Doe 的年龄是 29 岁，职业是 Engineer。
⏱️  [性能指标] TTFT (首字延迟): 2122.96 ms | 总耗时: 2128.01 ms

🚀 正在发送请求: [Query 2: 共享前缀调用 (Cache Hit)] ...
📝 模型回答: Zack Blue 的职业是律师，所在国家是澳大利亚。
⏱️  [性能指标] TTFT (首字延迟): 424.57 ms | 总耗时: 428.52 ms

============================================================
📊 验证结果对比汇总
============================================================
1️⃣ 首次请求 TTFT (无缓存预填充) : 2122.96 ms
2️⃣ 二次请求 TTFT (命中前缀缓存) : 424.57 ms
🚀 TTFT 延迟加速比            : 5.00x (首字生成速度提升)
📈 vLLM 服务端 Prefix Cache 命中率: N/A
============================================================
🎉 验证成功: Prefix Caching 已在在线服务中成功生效并复用 KV Cache!
$
"""
