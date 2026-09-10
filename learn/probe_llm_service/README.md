
--------------------------------------------------------------------------------------------------

```bash

select * from token_audit_logs WHERE uuid in ('35ff460c-2142-48cd-810b-5ab46958eaf2', '4a2ba43a-7d3d-419d-8bd1-d90e40cc713f');

select * from token_audit_logs where original_auth = 'kn49enthcjzklckavdwhhleo' and authorization = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o';

SELECT
    `id`,
    `uuid`,
    `request_id`,
    `llm_model_final`,
    `status_code`,
    `input_token`,
    `output_token`,
    `cached_token`,
    `total_token`,
    `cost_total`,
    `created_at`
FROM `token_audit_logs`
WHERE `original_auth` = 'kn49enthcjzklckavdwhhleo'
  AND `authorization` = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
  AND `created_at` >= '2026-08-26 17:00:00.000'
  AND `created_at` <  '2026-08-26 18:00:00.000'
ORDER BY `created_at` DESC;



SELECT
    DATE_FORMAT(`created_at`, '%Y-%m-%d %H:00:00') AS `stat_hour`,
    COUNT(1)               AS `request_count`,      -- 当前小时请求次数
    SUM(`input_token`)     AS `total_input_token`,  -- 输入Token总数
    SUM(`output_token`)    AS `total_output_token`, -- 输出Token总数
    SUM(`cached_token`)    AS `total_cached_token`, -- 命中缓存Token总数
    SUM(`total_token`)     AS `sum_total_tokens`    -- 整体Token总数
FROM `token_audit_logs`
WHERE `original_auth` = 'kn49enthcjzklckavdwhhleo'
  AND `authorization` = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
  AND `created_at` >= '2026-08-26 17:00:00.000'
  AND `created_at` <  '2026-08-26 18:00:00.000'
GROUP BY `stat_hour`
ORDER BY `stat_hour` ASC;


WITH RECURSIVE `hours_generator` AS (
    -- 1. 生成当天 00:00:00 到 23:00:00 的 24 个时间点
    SELECT
        '2026-08-26 00:00:00' AS `stat_hour_str`,
        0 AS `h`
    UNION ALL
    SELECT
        DATE_FORMAT(DATE_ADD('2026-08-26 00:00:00', INTERVAL `h` + 1 HOUR), '%Y-%m-%d %H:00:00'),
        `h` + 1
    FROM `hours_generator`
    WHERE `h` < 23
),
`daily_logs` AS (
    -- 2. 统计当天有日志的小时数据
    SELECT
        DATE_FORMAT(`created_at`, '%Y-%m-%d %H:00:00') AS `stat_hour_str`,
        COUNT(1)            AS `request_count`,
        SUM(`input_token`)  AS `total_input_token`,
        SUM(`output_token`) AS `total_output_token`,
        SUM(`cached_token`) AS `total_cached_token`,
        SUM(`total_token`)  AS `sum_total_tokens`
    FROM `token_audit_logs`
    WHERE `original_auth` = 'kn49enthcjzklckavdwhhleo'
      AND `authorization` = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
      AND `created_at` >= '2026-08-26 00:00:00.000'
      AND `created_at` <  '2026-08-27 00:00:00.000'
    GROUP BY `stat_hour_str`
)
-- 3. LEFT JOIN 补齐没有调用记录的小时, 用 0 填充
SELECT
    h.`stat_hour_str` AS `stat_hour`,
    COALESCE(l.`request_count`, 0)      AS `request_count`,
    COALESCE(l.`total_input_token`, 0)  AS `total_input_token`,
    COALESCE(l.`total_output_token`, 0) AS `total_output_token`,
    COALESCE(l.`total_cached_token`, 0) AS `total_cached_token`,
    COALESCE(l.`sum_total_tokens`, 0)   AS `sum_total_tokens`
FROM `hours_generator` h
LEFT JOIN `daily_logs` l ON h.`stat_hour_str` = l.`stat_hour_str`
ORDER BY h.`stat_hour_str` ASC;



curl --request POST \
  --url https://api.gpugeek.com/v1/chat/completions \
  --header 'Authorization: Bearer d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Vendor3/DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "user",
        "content": "你好, 请介绍一下自己"
      }
    ]
  }'

curl --request POST \
  --url https://api.gpugeek.com/v1/chat/completions \
  --header 'Authorization: Bearer d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Vendor3/DeepSeek-V4-Flash",
    "messages": [
        {
            "role": "user",
            "content": "你好, 请用200字介绍量子计算的基本原理"
        }
    ],
    "stream": true
}'

```

Q: 假设你是一位精通 LLM 模型推理服务的高级研究人员, 我现在有一个模型推理服务, 我可以使用客户端正常请求它, 如下所示:
```bash
$ curl --request POST \
  --url https://api.gpugeek.com/v1/chat/completions \
  --header 'Authorization: Bearer d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o' \
  --header 'Content-Type: application/json' \
  --data '{
    "model": "Vendor3/DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "user",
        "content": "你好, 请介绍一下自己"
      }
    ]
  }'
{"id":"cds_682a106f-883e-4821-8bdf-f3f232d50251","object":"chat.completion","created":1787537545,"model":"Vendor3/DeepSeek-V4-Flash","choices":[{"finish_reason":"stop","index":0,"message":{"role":"assistant","content":"你好呀! 很高兴认识你! 😊\n\n我是DeepSeek, 由深度求索公司创造的AI助手. 简单来说, 我是个热心肠的"智能小助手", 随时准备帮你解决各种问题! \n\n关于我的一些特点: \n\n✨ 知识丰富: 我的知识截止到2025年5月, 涵盖各个领域, 从科技、文化到生活常识, 都能聊上几句. \n\n📚 超长记忆: 我有1M的上下文处理能力, 可以一次性处理像《三体》三部曲那么厚的书籍(大概相当于几百万字), 所以长篇文档、复杂对话都难不倒我. \n\n🌐 联网搜索: 如果你需要最新信息, 可以在Web或App端手动开启联网搜索功能, 我就能帮你查找实时资料啦! \n\n📎 文件处理: 我支持上传图片、PDF、Word、Excel、PPT、TXT等文件, 可以从中读取文字信息帮你分析处理. \n\n🗣️ 语音输入: 在App端, 你还可以用语音跟我交流, 更加方便快捷. \n\n💰 完全免费: 最重要的是, 我目前完全免费! 没有任何收费计划, 放心使用. \n\n我会用热情、细腻的方式回答你的问题, 用你使用的语言和你交流. 无论你是想聊天、学习、工作还是娱乐, 我都乐意陪伴! \n\n那么, 今天有什么我可以帮你的吗? 😊","reasoning_content":"好的, 用户让我介绍一下自己. 这是一个非常常见的开场问题, 用户可能是第一次接触我, 想了解我的基本情况和能力范围. 我需要给出一个清晰、全面且友好的自我介绍, 让用户知道我是谁、能做什么、有什么特点, 以及如何使用我. \n\n想到了可以从几个关键方面来组织回复: 我的身份和创造者、核心能力(特别是文本处理和长上下文)、文件支持、联网搜索功能、免费性质、以及知识截止日期. 最后可以加上一个友好的结束语, 表达乐于帮助的态度. 这样结构比较完整, 信息量也足够, 能帮助用户快速建立认知. \n\n就用一个热情的开头, 然后分点说明, 但回复时不用序号, 用自然的段落过渡. 语气要亲切、自信, 让用户感到可靠和愿意交流. "}}],"usage":{"prompt_tokens":9,"completion_tokens":443,"total_tokens":452,"prompt_tokens_details":{"cache_creation":{}}},"metrics":{"input_token_count":9,"output_token_count":443,"predict_time":5.165837146}}
```
这是正常的请求情况, 我现在想全面了解一下这个模型服务的各种异常或者错误情况, 比如对于这个模型, 首次token的响应时间, 整体请求的超时时间设置多少合适, 以及其他一些异常是的返回情况, 请帮忙写一个python脚本, 多次请求这个模型服务, 并打印详细信息说明上述各种情况

在 LLM 推理服务(Inference Serving)的工程实践中, 评估一个 API 服务的质量不仅要看它的吞吐与延迟, 更要全面摸清它的边界条件、容错能力、限流策略和异常返回规范.

从你提供的 `curl` 响应中可以看到几个关键特征:
1. 模型类型: `Vendor3/DeepSeek-V4-Flash` 带有 `reasoning_content`(包含推理思维链).
2. 生成性能: `predict_time: 5.16s` 生成了 `443 completion_tokens`, Decode 吞吐约为 85.7 tokens/s.
3. 元数据丰富度: 网关返回了自定义的 `metrics` 字段(包含输入输出 token 统计及纯推理耗时), 这非常适合我们做客户端与服务端耗时的对比分析.

---

### 一、核心指标与超时配置的工程建议

在编写脚本前, 我们先建立一套推理服务的超时基准配置模型:

1. TTFT (Time To First Token / 首 Token 响应时间):
   * 构成: `网络握手耗时` + `网关路由与排队耗时` + `Prefill (Prompt 处理) 耗时`.
   * 特性: 受输入上下文长度(Prompt Length)和是否有 Prompt Caching 影响极大. 对于短 Prompt, TTFT 通常在 300ms ~ 1.5s; 若服务正在排队或输入数十万字, TTFT 可能飙升到 10s 以上.

2. TPOT (Time Per Output Token / 单 Token 耗时):
   * 构成: Decode 阶段显存带宽密集型计算.
   * 特性: 单并发下通常非常稳定(例如 80~120 tokens/s, 即 8~12ms/token).

3. 超时时间(Timeout)黄金配置法则:
   * 连接超时 (`Connect Timeout`): 建议设为 `3s ~ 5s`(TCP 握手和 TLS 协商).
   * 流式 TTFT 超时 (`Read Timeout for First Chunk`): 建议设为 `15s ~ 30s`(应对突发流量排队和 Prefill 计算).
   * 流式 Token 间隔超时 (`Idle/Chunk Timeout`): 流式传输中, 如果连续 `5s` 没有任何新 chunk 到达, 判定为后端 worker 崩溃或网络假死, 主动断开重试.
   * 非流式全量请求超时 (`Non-Streaming Total Timeout`):
     $$\text{Timeout} = \text{Max\_TTFT} + \left( \frac{\text{Max\_Output\_Tokens}}{\text{Min\_Decode\_Speed}} \right) \times 1.5$$

     例: 最大输出 4096 tokens, 保守速度 50 tokens/s, 则全量超时建议设为: $30s + (4096 / 50) \times 1.5 \approx 150s$.

---

### 二、全面探测与基准测试脚本

下面是一个为你量身打造的 Python 探测脚本. 它分为三大部分:

1. 性能与延迟探测(流式 TTFT、TPOT、非流式耗时)
2. 异常与边缘场景注入测试(鉴权、模型名、超长参数、畸形字段、并发限流等)
3. 综合分析与超时配置建议报告

#### 依赖准备
```bash
pip install requests
```

#### 测试脚本 `probe_llm_service.py`

```python
```

---

### 三、深度分析: 各类异常的排查手册与应对策略

运行上述脚本后, 你可能会观察到不同类型的状态码. 下表梳理了 LLM 推理服务中最常见的异常、成因及客户端最佳处理方案:

| HTTP 状态码                                   | 典型原因(服务端角度)                                                                                            | 客户端最佳实践 / 重试策略                                                                                          |
| :-------------------------------------------- | :-------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------- |
| `400 / 422 Bad Request`                       | 1. JSON 格式错误 <br> 2. Prompt 超过上下文上限 (Context Window Exceeded) <br> 3. 参数越界(如 `temperature < 0`) | 不可重试. 需在客户端拦截并修复参数; 对于超长上下文, 需在客户端做 Token 截断或摘要压缩.                             |
| `401 / 403 Unauthorized`                      | 1. API Key 过期/错误 <br> 2. 权限不足(该 Key 无权访问此 Vendor 模型)                                            | 不可重试. 告警并通知管理员更新鉴权凭证.                                                                            |
| `404 Not Found`                               | 1. 模型名称打错 <br> 2. 该模型尚未在集群中挂载或部署                                                            | 不可重试. 核对模型字符串(如是否区分大小写、前缀 `Vendor3/` 是否正确).                                              |
| `429 Too Many Requests`                       | 1. 达到 RPM (Requests Per Minute) 上限 <br> 2. 达到 TPM (Tokens Per Minute) 上限 <br> 3. 网关并发请求队列满     | 必须指数退避重试 (Exponential Backoff). <br> 优先读取响应头中的 `Retry-After`, 并在重试间隔中加入随机抖动(Jitter). |
| `500 Internal Server Error`                   | 1. 推理引擎后端崩溃(如 vLLM/SGLang Worker OOM) <br> 2. NCCL 通信挂起                                            | 有限重试(最多 1~2 次). 若持续发生, 需服务端查看 GPU 显存与 dmesg 日志.                                             |
| `502 / 503 Bad Gateway / Service Unavailable` | 1. 推理实例正在扩缩容/冷启动加载模型权重 <br> 2. 网关到推理节点的连接断开                                       | 等待后重试(建议间隔 3~5s), 适合配合断路器(Circuit Breaker)模式.                                                    |
| `504 Gateway Timeout`                         | 1. Prefill 阶段超长导致排队超时 <br> 2. 输出 token 过多超过反向代理(如 Nginx)的 `proxy_read_timeout`            | 检查非流式是否输出过长, 强烈建议改为 `stream: true` 流式传输.                                                      |

---

### 四、生产环境 Python 客户端封装范例(含超时与重试)

在生产环境中调用该模型时, 建议采用如下封装方式, 既支持合理的超时, 又具备防御性重试机制:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_resilient_llm_client():
    session = requests.Session()

    # 定义重试策略: 仅针对 429 和 5xx 临时错误进行退避重试
    retries = Retry(
        total=3,
        backoff_factor=1.5,  # 重试等待时间: 1.5s, 3s, 6s...
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=50)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# 使用推荐超时组合
def call_deepseek_flash(session, messages, stream=True):
    url = "https://api.gpugeek.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "Vendor3/DeepSeek-V4-Flash",
        "messages": messages,
        "stream": stream
    }

    # timeout 传元组: (connect_timeout, read_timeout)
    # connect_timeout = 3.5s, read_timeout = 25s (针对首 token 和每个 chunk)
    return session.post(url, headers=headers, json=payload, stream=stream, timeout=(3.5, 25.0))
```

--------------------------------------------------------------------------------------------------

Q: 我想验证模型推理服务是否开启了前缀缓存, 请输出完整的验证脚本

在 LLM 推理架构中, 前缀缓存(Prefix Caching / Prompt Caching / RadixAttention) 是一项关键的性能优化技术. 它通过在显存中保留公共前缀(如系统提示词、长背景文档、Few-shot 示例)的 KV Cache, 避免对相同前缀进行重复的 Prefill(计算瓶颈)阶段计算.

从你之前的响应中可以看到 `"prompt_tokens_details": {"cache_creation": {}}`, 这表明后端网关/引擎具备缓存元数据结构.

---

### 一、验证前缀缓存的原理

要 100% 确定推理服务是否开启并命中了前缀缓存, 通常从以下两个维度交叉验证:

1. 元数据字段(Hard Metric):
   * 检查 `usage.prompt_tokens_details` 是否返回了 `cached_tokens` 或 `cache_read_input_tokens`.

2. TTFT 与推理耗时断崖式下降(Soft/Performance Metric):
   * 构造一段长前缀(建议 2000 ~ 3000 tokens, 因为很多引擎如 vLLM/SGLang/DeepSeek 设有 64 或 1024 tokens 的缓存门槛).
   * 将 `max_tokens` 固定为一个极小值(如 `10`), 剥离 Decode(输出生成)耗时的干扰, 让总耗时完全由 Prefill 决定.
   * 第 1 次请求(Cold Miss): 全量计算 KV Cache 并写入缓存, TTFT 和 `predict_time` 较高.
   * 第 2 次请求(Warm Hit): 携带完全相同的长前缀 + 微小的不同提问. 如果开启了前缀缓存, 由于无需重算前缀, TTFT 和 `predict_time` 会暴跌 60% ~ 90%.
   * 对照组请求(Control Miss): 携带完全不同的等长前缀, 耗时应恢复到高位.

---

### 二、完整验证脚本

以下是一个可以直接运行的 Python 验证脚本(`verify_prefix_caching.py`):

```python
```

---

### 三、结果解读指南

运行该脚本后, 观察报告输出:

1. 理想情况(前缀缓存生效):
   * Step 1 (Cold): TTFT 约为 `800ms ~ 2000ms`.
   * Step 2 & 3 (Warm): TTFT 降至 `80ms ~ 250ms`(仅剩网络 RTT + 小于 10 个 token 的 prefill).
   * Step 4 (Control): TTFT 重新升至 `800ms ~ 2000ms`.
   * 若响应头/Body 中的 `prompt_tokens_details` 返回了非空的 `cached_tokens: 2000+`, 则可直接作为显式证据.

2. 多节点负载均衡(Round-Robin)特殊情况:
   * 如果 Step 2 依然很慢, 但 Step 3 变快了, 说明集群有 2 个 Worker 节点, 第 2 次请求被路由到了第 2 台冷节点上. 针对这种情况, 可以在网关配置基于客户端 IP / Session 的一致性哈希路由以充分发挥缓存价值.

--------------------------------------------------------------------------------------------------

Q: 我想验证模型推理服务出现异常, 客户端因为长时间没有接收到数据导致 timeout

在 LLM 流式(Streaming)推理服务中, "长时间未接收到数据导致客户端超时(Read Timeout / Idle Timeout)" 是最致命的隐患之一. 如果客户端没有设置合理的超时或看门狗机制, 线程会被永久阻塞, 导致连接池耗尽、网关 Worker 线程饿死.

通常有两类典型的"断流/未响应"场景:
1. TTFT 首 Token 等待超时: 请求已发送, 但服务端由于排队过长、Prefill 显存死锁或 Worker 卡死, 迟迟不吐出第一个 Token.
2. 中途断流/挂起超时(Mid-stream Stall): 模型吐了几个 Token 后, GPU Worker 发生 NCCL 通信挂死、OOM 崩溃或网络静默丢包, 流式连接保持开放但没有任何新数据到达.

---

### 一、验证脚本: 真实环境探测 + 本地故障注入(Mock)

为了让你既能在真实云端服务上触发超时保护, 又能在不破坏线上服务的前提下 100% 稳定复现各类"服务端卡死/中途断流"的极端场景, 下面的脚本内置了一个轻量级本地故障注入服务器进行端到端验证.

#### 依赖准备
```bash
pip install requests
```

#### 完整脚本 `test_timeout_scenarios.py`

```python
```

---

### 二、核心机制深度解析

运行上述脚本后, 你需要掌握以下几个底层关键点:

#### 1. `requests` 的 `timeout=(connect, read)` 在流式中具体是如何工作的?

* `connect_timeout` (连接超时): 仅在 TCP 握手 + TLS 握手阶段生效.
* `read_timeout` (读取超时): 在 `stream=True` 模式下, 它不是整个 HTTP 请求的总耗时上限, 而是套接字(Socket)上任意两次数据包到达之间的最大空闲时间(Idle Time / Inactivity Timeout).
  * 如果模型 Prefill 花了 5 秒, 但你的 `read_timeout` 是 3 秒 $\rightarrow$ 立即抛出 `ReadTimeout`.
  * 如果模型在流式输出中, 两个 Token 之间因为 Worker 显存交换卡顿了 4 秒, 而你的 `read_timeout` 是 3 秒 $\rightarrow$ 同样立即抛出 `ReadTimeout`.

#### 2. 如果发生超时, 服务端的 GPU 会怎样?

* 当 Python 客户端捕获 `ReadTimeout` 退出时, 操作系统会向服务端发送 `TCP FIN / RST` 包关闭连接.
* 现代推理引擎(如 vLLM / SGLang)的表现: 如果开启了客户端断开检测(`disconnect detection`), 引擎检测到 Client 断开后, 会立刻中止该请求后续的 Decode 计算并释放 KV Cache.
* 较简陋的推理后端: 可能意识不到客户端已断开, 会继续把整个生成跑完, 白白浪费 GPU 算力. 因此客户端配置超时既是在保护自己, 也是在向网关发送"取消计算"的信号.

--------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM 模型推理服务的高级研究人员, 我现在有一个模型推理服务, 我可以使用客户端正常请求它, 如下所示:
```bash
$ curl -sv http://172.16.10.55:24182/v1/chat/completions \
-X POST \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer kn49enthcjzklckavdwhhleo' \
-d '{
    "model": "DEEPSEEK",
    "stream": false,
    "messages": [
        {
            "role": "user",
            "content": "什么是redis?"
        }
    ]
}'
$

```
请帮我写一个 python 脚本, 在脚本中对这个推理服务发送多次请求, 具体要求如下:
1、每次的请求的 prompt 不同
2、流式请求和非流式请求大致 8:2 的比例
3、尽可能详细的打印返回的各种信息
4、尽可能细致的区分并处理各种异常情况
请输出完整的脚本, 添加尽可能详细的日志

这份针对大模型推理服务(LLM Inference Serving)的自动化请求与压测/评测脚本, 严格遵循了生产级大模型基准测试(Benchmarking)的标准.

脚本具备以下特性:

1. 多维度 Prompt 库: 包含逻辑推理、代码生成、数学计算、常识问答等, 每次请求自动随机挑选.
2. 8:2 流式/非流式动态路由: 按照 80% 流式(Streaming SSE)与 20% 非流式(Non-Streaming)动态调度.
3. 高精度的性能与网关指标提取:
   - TTFT(Time To First Token, 首字延迟)
   - Total Latency / E2E 耗时
   - TPS(Tokens Per Second, 生成吞吐速率)
   - 网关 & Mesh 指标: 提取如 `x-envoy-upstream-service-time`、`x-cds-request-id`、`trace-id`、`req-cost-time` 等.
   - 多通道内容打印: 细致区分打印思考链过程(`reasoning_content`) 和 最终输出(`content`).
4. 精细化的异常分流与容错: 覆盖网络超时(Connect/Read Timeout)、连接重置、HTTP 4xx(鉴权失败、限流 429、模型不存在)、HTTP 5xx(后端 OOM/崩溃 500、网关 502/504)、SSE 协议截断与 JSON 解析异常.

---

### 完整 Python 脚本 (`llm_benchmark_client.py`)

```python
```

---

### 代码设计与实现亮点说明

1. 8:2 动态分流:
   使用 `random.random() < STREAM_RATIO` 实现流式与非流式的比例控制, 符合大模型测试场景中对混合流量的测试要求.

2. DeepSeek-R1 / 豆包思考链原生支持:
   从你给出的 `curl` 响应可以看出模型包含思考过程(`reasoning_content`). 脚本在非流式与流式中分别对 `reasoning_content` 和最终回复 `content` 进行了独立捕获、聚合与日志打印.

3. 网关性能指标全面捕获:
   自动从响应 Header 中提取了在生产 Mesh(如 Envoy/Istio)环境中常见的追踪头:
   - `x-envoy-upstream-service-time`: Envoy 代理到后端实际 Pod 的网络+推理总时间.
   - `trace-id` / `x-cds-request-id`: 分布式追踪 ID, 发生异常时可直接拿着这个 ID 去查后端日志.
   - `TTFT`(首字延迟计算)与 `TPS`(Tokens/s 吞吐计算).

4. 全方位的异常分流(Error Categorization):
   - 连接阶段异常: 区分是建立连接超时(`ConnectTimeout`)还是连不上被拒(`ConnectionRefused`).
   - 推理阶段异常: 区分是生成超时(`ReadTimeout`)还是流在中间被掐断(`ChunkedEncodingError`).
   - 业务错误码: 400(参数/模型名)、401(Auth Token)、429(QPS 超限)、500(后端显存 OOM/崩溃)、502/504(Gateway Timeout).

--------------------------------------------------------------------------------------------------


代码如下所示,
```python
```
不要使用 log 输出日志, 直接使用 print 输出日志信息, 保证日志信息顺序的准确


--------------------------------------------------------------------------------------------------

Q: 运行脚本之后, 输出的日志如下:
```
```
从日志中可以看到有两个问题, 一是为什么会出现乱码, 是不是代码中设置的编码有关, 二是似乎并没有按照严格的代码执行顺序输出日志

这是一个在 Python 处理 LLM 流式(SSE)传输中非常典型且隐蔽的底层编码陷阱.

你观察到的两个现象(中文乱码 以及 看似日志乱序/频繁报畸形帧), 本质上是由同一个根本原因引起的连环反应.

---

### 一、两个问题的根本原因深度剖析

#### 1. 为什么会出现乱码(`ç"¨æˆ·` -> `用户`)?

* 根因: `requests.iter_lines(decode_unicode=True)` 内部依赖 `response.encoding`. 如果推理网关返回的 `Content-Type` 是 `text/event-stream` 或 `application/json` 且未显式带上 `charset=utf-8`, `requests` 会按照 HTTP RFC 规范默认采用 `ISO-8859-1`(Latin-1) 解码.

* 现象映射:
  * 中文"用户"的 UTF-8 字节是: `\xe7\x94\xa8 \xe6\x88\xb7`
  * 按 `ISO-8859-1` 解码就变成了: `\xe7`(ç) `\x94`(") `\xa8`(¨) `\xe6`(æ) `\x88`(ˆ) `\xb7`(·) $\rightarrow$ `ç"¨æˆ·`.

---

#### 2. 为什么看似"日志乱序"并伴随"畸形帧警告"?

看你日志中的这段核心异常:
```text
[DEBUG] [1] SSE 数据流: data: {"id":..., "reasoning_content":"å†
[WARN]  [1] 忽略畸形 SSE 帧: data: {"id":..., "reasoning_content":"å†
[DEBUG] [1] SSE 数据流: å­˜"}}],"usage":null,"metrics":null}
```
* 根因(Unicode `NEL` 换行符截断陷阱):
  * 模型当时正在输出中文"内存", 其中"内"的 UTF-8 字节是 `\xe5\x86\x85`, "存"是 `\xe5\xad\x98`.
  * 当以 `ISO-8859-1` 提前解码为字符串后, 第三个字节 `\x85` 变成了 Unicode 字符 `\u0085`.
  * 在 Python 3 的字符串切分规则中, `\u0085` 代表 `NEL`(Next Line, 下一行控制符)！
  * 这导致 `iter_lines(decode_unicode=True)` 误以为遇到了换行符, 强行把一条完整的 JSON 在"内"字中间腰斩为两截！
* 连锁反应:
  1. 前半截 `... "reasoning_content":"å†` 被切出来, 由于 JSON 括号未闭合, `json.loads` 报错, 触发了 `[WARN] 忽略畸形 SSE 帧`.
  2. 后半截 `å­˜"}}],"usage":...` 紧接着被当做下一行读出, 由于它不带 `data:` 前缀, 被当做普通数据打印.
  3. 这并不是代码没有按顺序执行, 而是完整的单行数据被错误地劈成了两半, 从而产生了日志穿插和乱序的错觉.

---

### 二、彻底解决方案

1. 字节级流式读取(Byte-level Stream): 禁用 `decode_unicode=True`, 让底层仅按照标准的换行符字节 `\n` (`0x0A`) 进行断行, 避免中文字节中的 `0x85` 被误当换行符.
2. 显式 UTF-8 解码: 在拿到完整的整行字节后, 再执行 `line_bytes.decode('utf-8')`.
3. 增加 ANSI 颜色开关: 针对某些不兼容 ANSI 颜色的日志终端, 增加 `ENABLE_COLOR` 开关, 避免输出原始的 `[36m` 等字符.

---

### 三、修复后的完整 Python 脚本

```python

```



--------------------------------------------------------------------------------------------------


WITH RECURSIVE `hours_generator` AS (
    -- 1. 生成当天 00:00:00 到 23:00:00 的 24 个时间点
    SELECT
        '2026-08-26 00:00:00' AS `stat_hour_str`,
        0 AS `h`
    UNION ALL
    SELECT
        DATE_FORMAT(DATE_ADD('2026-08-26 00:00:00', INTERVAL `h` + 1 HOUR), '%Y-%m-%d %H:00:00'),
        `h` + 1
    FROM `hours_generator`
    WHERE `h` < 23
),
`daily_logs` AS (
    -- 2. 统计当天有日志的小时数据
    SELECT
        DATE_FORMAT(`created_at`, '%Y-%m-%d %H:00:00') AS `stat_hour_str`,
        COUNT(1)            AS `request_count`,
        SUM(`input_token`)  AS `total_input_token`,
        SUM(`output_token`) AS `total_output_token`,
        SUM(`cached_token`) AS `total_cached_token`,
        SUM(`total_token`)  AS `sum_total_tokens`
    FROM `token_audit_logs`
    WHERE `original_auth` = 'kn49enthcjzklckavdwhhleo'
      AND `authorization` = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
      AND `created_at` >= '2026-08-26 00:00:00.000'
      AND `created_at` <  '2026-08-27 00:00:00.000'
    GROUP BY `stat_hour_str`
)
-- 3. LEFT JOIN 补齐没有调用记录的小时, 用 0 填充
SELECT
    h.`stat_hour_str` AS `stat_hour`,
    COALESCE(l.`request_count`, 0)      AS `request_count`,
    COALESCE(l.`total_input_token`, 0)  AS `total_input_token`,
    COALESCE(l.`total_output_token`, 0) AS `total_output_token`,
    COALESCE(l.`total_cached_token`, 0) AS `total_cached_token`,
    COALESCE(l.`sum_total_tokens`, 0)   AS `sum_total_tokens`
FROM `hours_generator` h
LEFT JOIN `daily_logs` l ON h.`stat_hour_str` = l.`stat_hour_str`
ORDER BY h.`stat_hour_str` ASC;

这条 SQL 语句采用了 "分治思想", 巧妙地解决了时序数据统计中经典的"时间断点(某些小时无数据)补零"问题.

整条语句由 3 个核心部分组成:

1. `hours_generator`: 生成当天 24 个整点时间梯子的"虚拟日历表";
2. `daily_logs`: 从物理表中统计当天有日志的小时数据;
3. 主查询(`LEFT JOIN` + `COALESCE`): 以日历表为主表进行左连接, 无数据的小时自动填充为 `0`.

---

### 第一部分: `hours_generator`(递归生成 24 小时时间轴)

```sql
WITH RECURSIVE `hours_generator` AS (
    -- 1. 锚点查询(初始状态): 生成当天的 0 点, 计数器 h = 0
    SELECT
        '2026-08-26 00:00:00' AS `stat_hour_str`,
        0 AS `h`
    UNION ALL
    -- 2. 递归查询(循环迭代): 在上一行的基础上每次 +1 小时, h 计数器 +1
    SELECT
        DATE_FORMAT(DATE_ADD('2026-08-26 00:00:00', INTERVAL `h` + 1 HOUR), '%Y-%m-%d %H:00:00'),
        `h` + 1
    FROM `hours_generator`
    WHERE `h` < 23 -- 3. 循环终止条件: h 达到 23 时停止(共生成 0~23 点, 共 24 行)
)
```

#### 工作原理(类似编程语言中的 `for` 循环):

* 初始值(Anchor): 放入第一行 `2026-08-26 00:00:00`, `h = 0`.
* 迭代(Recursive):
  * 第 2 次循环: 取 `h=0`, 加 1 小时得到 `01:00:00`, 此时 `h=1`.
  * 第 3 次循环: 取 `h=1`, 加 2 小时得到 `02:00:00`, 此时 `h=2`.
  * ... 直到 `h=22` 生成 `23:00:00`(`h` 变为 23).
* 终止条件: `WHERE h < 23` 使得下一次判断不成立, 循环结束.

> 生成结果(内存临时表): 严格包含 24 行(从 `2026-08-26 00:00:00` 到 `2026-08-26 23:00:00`).

---

### 第二部分: `daily_logs`(业务数据预聚合)

```sql
`daily_logs` AS (
    SELECT
        DATE_FORMAT(`created_at`, '%Y-%m-%d %H:00:00') AS `stat_hour_str`,
        COUNT(1)            AS `request_count`,
        SUM(`input_token`)  AS `total_input_token`,
        SUM(`output_token`) AS `total_output_token`,
        SUM(`cached_token`) AS `total_cached_token`,
        SUM(`total_token`)  AS `sum_total_tokens`
    FROM `token_audit_logs`
    WHERE `original_auth` = 'kn49enthcjzklckavdwhhleo'
      AND `authorization` = 'd0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
      AND `created_at` >= '2026-08-26 00:00:00.000'
      AND `created_at` <  '2026-08-27 00:00:00.000'
    GROUP BY `stat_hour_str`
)
```

#### 关键细节解析:

1. `DATE_FORMAT(created_at, '%Y-%m-%d %H:00:00')`:
   * 将带有毫秒的时间(如 `2026-08-26 14:25:36.123`)统一截断为整点字符串 `2026-08-26 14:00:00`, 作为分组依据.
2. `WHERE` 的左闭右开区间 `[00:00:00, 次日00:00:00)`:
   * 严格包含当天所有的毫秒(`00:00:00.000` 到 `23:59:59.999`), 避免漏查.
3. `GROUP BY stat_hour_str`:
   * 对同一小时内的日志进行累加(`SUM`)和计数(`COUNT`).

> 输出特征: 如果全天只有 10 点、14 点有调用, 那么这个临时表只有 2 行数据.

---

### 第三部分: 主查询(`LEFT JOIN` 关联与 `COALESCE` 补零)

```sql
SELECT
    h.`stat_hour_str` AS `stat_hour`,
    COALESCE(l.`request_count`, 0)      AS `request_count`,
    COALESCE(l.`total_input_token`, 0)  AS `total_input_token`,
    COALESCE(l.`total_output_token`, 0) AS `total_output_token`,
    COALESCE(l.`total_cached_token`, 0) AS `total_cached_token`,
    COALESCE(l.`sum_total_tokens`, 0)   AS `sum_total_tokens`
FROM `hours_generator` h
LEFT JOIN `daily_logs` l ON h.`stat_hour_str` = l.`stat_hour_str`
ORDER BY h.`stat_hour_str` ASC;
```

#### 关键技术点:
1. 以 `hours_generator`(h)作为左表进行 `LEFT JOIN`:
   * `LEFT JOIN` 会无条件保留左表的全部 24 行.
   * 当右表 `daily_logs`(l)在某个小时没有数据时, 右表对应的字段值全部为 `NULL`.
2. `COALESCE(val, 0)` 函数:
   * 作用: 返回参数列表中第一个非 `NULL` 的值.
   * 如果 `l.total_input_token` 有值(例如 `5000`), 则返回 `5000`;
   * 如果为 `NULL`(代表该小时无日志), 则返回默认值 `0`.
3. `ORDER BY h.stat_hour_str ASC`:
   * 确保最终输出按时间顺序(从 00 点到 23 点)严格排序.

---

### 数据流动示意图

```text
[hours_generator (固定24行)]             [daily_logs (仅有日志的小时)]
00:00:00 ---------------- LEFT JOIN ---> (无数据) ---------> COALESCE 补 0
...
10:00:00 ---------------- LEFT JOIN ---> 10:00:00 (5000 Token) -> 输出 5000
...
23:00:00 ---------------- LEFT JOIN ---> (无数据) ---------> COALESCE 补 0

===============================================================
最终输出: 严格 24 行连续的、无 NULL 的整洁时序数据(前端图表可直接渲染)
```




--------------------------------------------------------------------------------------------------


```bash
export GPUGEEK_API_KEY='d0d9e85m1ayzlux1000dkuffvwpkrrl2e01iyf3o'
CACHE_PREFIX_TEXT=$(printf '这是用于验证上下文缓存的固定前缀. 缓存命中要求后续请求从第一个 token 开始保持完全一致. 以下内容不会在不同请求之间发生任何变化.  %.0s' {1..50})
jq -n --arg prefix "$CACHE_PREFIX_TEXT" '{
  model: "Vendor3/DeepSeek-V4-Flash",
  user_id: "cache-demo-20260827-small",
  messages: [
    {role: "system", content: $prefix},
    {role: "user", content: "请仅回答: 收到"}
  ],
  temperature: 0,
  max_tokens: 2
}' |
curl --silent --show-error \
  --request POST \
  --url 'https://api.gpugeek.com/v1/chat/completions' \
  --header "Authorization: Bearer ${GPUGEEK_API_KEY}" \
  --header 'Content-Type: application/json' \
  --data-binary @- |
jq '{id, usage, metrics}'
{
  "id": "cds_a84273d6-c94e-4453-a3a5-2f8ad37e81b9",
  "usage": {
    "prompt_tokens": 1709,
    "completion_tokens": 3,
    "total_tokens": 1712,
    "prompt_tokens_details": {
      "cache_creation": {},
      "cached_tokens": 1024
    }
  },
  "metrics": {
    "input_token_count": 1709,
    "output_token_count": 3,
    "predict_time": 0.994132913
  }
}











export GPUGEEK_API_KEY='kn49enthcjzklckavdwhhleo'
CACHE_PREFIX_TEXT=$(printf '这是用于验证上下文缓存的固定前缀. 缓存命中要求后续请求从第一个 token 开始保持完全一致. 以下内容不会在不同请求之间发生任何变化.  %.0s' {1..50})
jq -n --arg prefix "$CACHE_PREFIX_TEXT" '{
  model: "capital",
  user_id: "cache-demo-20260827-small",
  messages: [
    {role: "system", content: $prefix},
    {role: "user", content: "请仅回答: 收到"}
  ],
  temperature: 0,
  max_tokens: 2
}' |
curl --silent --show-error \
  --request POST \
  --url 'http://172.16.10.55:24182/v1/chat/completions' \
  --header "Authorization: Bearer ${GPUGEEK_API_KEY}" \
  --header 'Content-Type: application/json' \
  --data-binary @- |
jq '{id, usage, metrics}'


$ curl -sv http://172.16.10.55:24182/v1/chat/completions \
-X POST \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer kn49enthcjzklckavdwhhleo' \
-d '{
    "model": "capital",
    "messages": [
        {
            "role": "user",
            "content": "什么是redis?"
        }
    ]
}'


```


--------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM 和 vllm 推理框架的高级研究人员, 现在我使用 vllm 部署了模型推理服务, 正常情况下, 客户端和服务端都可以正常工作, 我现在想探究一下服务端都有哪些常见的错误或者异常, 请问如果使用 vllm 部署推理服务, 常见的错误和异常都有哪些? 他们的影响都是什么?

作为长期从事大语言模型(LLM)系统架构与底层推理优化的研究人员, 在生产环境中运行基于 vLLM 的高并发推理服务时, 尽管在基准测试和常规流量下表现平稳, 但在真实负载、长上下文、多节点/多卡分布式以及复杂网络环境下, 服务端会暴露出一系列特有的系统级、框架级和算法级异常.

以下从显存与缓存系统、分布式通信与多进程、底层 Kernel 与数值计算、异步引擎与并发调度、结构化输出与请求校验五个核心维度, 系统梳理 vLLM 服务端最常见的错误、异常及其对系统的具体影响.

---

### 一、显存与 KV Cache 调度异常

vLLM 依赖其核心的 PagedAttention 与显存预分配机制, 这使得它的显存错误形态与原生 PyTorch 存在显著差异.

#### 1. 初始化显存溢出(Init-time CUDA OOM)

* 典型报错: `torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate ...`
* 根因:
  * vLLM 在启动阶段会先加载模型权重, 然后根据 `gpu_memory_utilization`(默认 0.90)计算剩余显存并将其全部分配为 KV Cache Block, 最后还会预热(Profile)并捕获 CUDA Graph.
  * 若模型权重本身已占满大部分显存, 或显卡上有其他残留进程, 亦或是 CUDA Graph 捕获时的临时张量超出预留的 `(1 - gpu_memory_utilization)` 空间, 会导致启动即崩溃.
* 影响: 服务无法启动. 在 Kubernetes 集群中表现为 Pod 陷入 `CrashLoopBackOff`.

#### 2. KV Cache 耗尽与请求抢占(KV Cache Preemption / Block Thrashing)

* 典型现象/日志: `Engine preempted request ... due to lack of available KV blocks.`(非 Crash, 但属于严重的系统性能降级异常)
* 根因:
  * 并发请求量激增或大量请求进入超长生成阶段, 导致预分配的物理显存块(KV Blocks)被耗尽.
  * BlockManager 无法为新 Token 分配槽位, 触发调度器的抢占机制: vLLM 会选择某些已在生成的低优先级序列将其 KV Cache 换出(Swap to CPU) 或直接丢弃重计算(Recompute).
* 影响:
  * 延时断崖式恶化: P99 甚至 P95 的 TPOT(Time Per Output Token)急剧上升, 由于重算(Recomputation), TTFT 也会出现二次激增.
  * 有效吞吐量(Goodput)雪崩: GPU 算力被大量浪费在重复计算 Prefill 上, 服务可能陷入"抖动震荡(Thrashing)".

#### 3. 动态多模态/变长 Prefill 导致的运行时运行时 OOM

* 典型报错: `RuntimeError: CUDA out of memory` during execution of forward pass.
* 根因: 开启 Chunked Prefill 时切片尺寸(`max_num_batched_tokens`)设置过大; 或部署多模态模型(如 Qwen-VL、LLaVA)时, 动态分辨率的高清图片经 ViT 提取出的视觉 Token 数量不可控, 瞬时突增的中间激活值(Activation Memory)击穿了预留空间.
* 影响: 服务主进程或 Worker 异常退出, 直接导致当批次的所有请求失败.

---

### 二、分布式通信与多卡协作异常(TP / PP)

在部署 70B+ 模型时通常需开启张量并行(Tensor Parallelism, TP), 跨卡乃至跨节点通信是系统的脆弱点.

#### 1. NCCL 通信看门狗超时(NCCL Watchdog Timeout)

* 典型报错:
  * `RuntimeError: NCCL error in: .../torch/csrc/distributed/c10d/ProcessGroupNCCL.cpp, unhandled system error / watchdog timeout`
* 根因:
  * 单 Rank 卡死/掉队(Straggler): 多卡并行时, 必须所有卡执行同步集合通信(All-Reduce). 若其中一张卡遇到硬件降频、驱动死锁或长任务(如长上下文 Prefill 耗时过久且通信心跳被阻断), 其他卡会持续阻塞在 All-Reduce, 最终触发 NCCL 的默认看门狗超时(通常为几十分钟, 生产通常配得较短).
  * 物理网络波动/NVLink 链路故障.
* 影响: 全服务死锁或崩溃. 由于 TP 各 Rank 是强绑定的, 任意一张卡 NCCL 崩溃会导致整个 Ray Actor 或多进程集群瓦解, 所有进行中的流式连接瞬间断开.

#### 2. Ray / IPC 多进程非正常退出(Worker Disconnected)

* 典型报错: `ray.exceptions.RayActorError: The actor died unexpectedly...` 或 `RuntimeError: Engine background task failed`
* 根因:
  * TP Worker 进程因为系统 OOM Killer(RAM 耗尽而非显存)、CUDA 驱动崩溃、Segmentation Fault 异常终止.
  * vLLM 的 `AsyncLLMEngine` 在主进程监测到 Worker 管道断开.
* 影响: 服务不可用. 服务端口虽可能响应 HTTP 请求, 但任何调用都会抛出 `500 Internal Server Error`, 必须彻底重启服务实例.

---

### 三、底层 Kernel 与数值计算异常

#### 1. CUDA 非法内存访问(CUDA Illegal Memory Access)

* 典型报错: `RuntimeError: CUDA error: an illegal memory access was encountered`
* 根因:
  * FlashAttention、PagedAttention 或定制算子(如 FP8 GEMM、AWQ/GPTQ 反量化 Kernel、Triton 算子)存在 Edge Case 越界 Bug.
  * 算子编译版本与当前显卡架构(Compute Capability)或驱动/CUDA Toolkit 不匹配(例如在 Hopper/Ada 架构上运行未经适配合并的旧版 Triton 算子).
* 影响: 硬件上下文污染, 服务不可逆崩溃. 一旦出现该错误, 当前 CUDA Context 会彻底失效, 导致同显卡内后续所有 CUDA 操作均无法执行, 必须强杀并重启整个 Python 进程.

#### 2. 数值不稳定导致 Logits 出现 NaN/Inf 与采样死循环

* 典型报错: `RuntimeError: probability tensor contains either inf, nan or element < 0`
* 根因:
  * 在半精度(FP16)下, 超深层或大批次推理导致中间激活值数值溢出;
  * 模型由于输入畸变输出异常的极值, Softmax 之后全为 0 或产生 NaN;
  * 未正确触发 EOS(结束符)且客户端未传 `max_tokens`, 模型陷入无意义重复生成或死循环.
* 影响:
  * 触发异常的单个请求立即中断(500 错误);
  * 如果是死循环生成, 会长期霸占 KV Cache 和调度 Slot, 逐步拖垮整个集群的吞吐.

---

### 四、异步引擎与服务调度异常(Serving Layer)

vLLM 对外提供 OpenAI 兼容的 HTTP API, 结合了 FastAPI/Uvicorn、AsyncIO 驱动的 `AsyncLLMEngine`.

#### 1. 客户端提前断连(Client Disconnect & Broken Pipe)

* 典型日志: `asyncio.CancelledError`、`ClientDisconnected`
* 根因:
  * 客户端设置了较短的 HTTP 超时时间, 在 Prefill 排队时间过长时放弃等待并切断了 TCP 连接;
  * 客户端流式读取时主动点击"停止生成".
* 影响:
  * 在旧版 vLLM 中, 这可能导致后台仍在为已死请求白白执行解码(幽灵计算, Ghost Computation);
  * 在高并发场景下, 海量并发连接断开可能引起 `AsyncIO` 协程泄露, 甚至因异常未捕获导致引擎抛出全局未能处理的错误.

#### 2. 事件循环阻塞与 CPU 瓶颈(Event Loop Starvation)

* 典型现象: GPU 利用率时高时低, HTTP 请求排队时间(Queue Time)极长, 即使 GPU 显存和算力均有富余.
* 根因:
  * 分词(Tokenization)与反分词(Detokenization)瓶颈: AsyncLLMEngine 的主进程需要执行 Python 层的 Tokenizer 编解码, 当大并发流式输出时, 极高频的 detokenize 操作消耗大量 CPU 时间, 造成单线程事件循环阻塞;
  * 数据后处理、Logits 过滤(如复杂的 top_k/top_p CPU 实现)霸占 GIL.
* 影响:
  * 系统吞吐无法线性放大, 请求在 Web 框架排队层超时;
  * 误触发健康检查探针(如 K8s Liveness/Readiness Probe 报 503/Timeout), 导致服务容器被集群误判并被反复重启.

---

### 五、协议、约束与结构化输出异常

#### 1. 上下文长度溢出(Context Length Exceeded)

* 典型报错: `BadRequestError: This model's maximum context length is X tokens. However, you requested Y tokens...`
* 根因: 客户端发送的 Prompt Token 数 + `max_tokens` > 模型的 `max_model_len`(vLLM 启动参数).
* 影响: 轻度影响, 立即返回 400 Bad Request. 虽不会拖垮服务, 但若上游无重试或截断逻辑, 会产生坏死请求流.

#### 2. 引导解码/结构化输出引擎崩溃(Guided Decoding / JSON Schema 故障)

* 典型报错: `ValueError: ... Outlines / XGrammar / Guidance failed to parse grammar` 或生成阶段被强制屏蔽所有 Token.
* 根因:
  * 客户端传入了极度复杂的 JSON Schema 或非常宽泛/相互矛盾的 Regex;
  * 结构化生成状态机(FSM/Grammar)在构建阶段消耗过多 CPU/RAM, 或者构建出的 Mask 导致词表里所有 Token 的概率都被置为 `-inf`(无路可走).
* 影响:
  * 导致对应请求报错中断;
  * 某些极度复杂的 Schema 构建过程甚至会长时间阻塞主进程的 Event Loop, 导致整个服务器数秒内无法响应其他任何正常请求.

---

### 总结与防御对照表

| 异常分类   | 典型场景/报错                     | 对系统的核心影响               | 工业级关键应对措施                                                     |
| :--------- | :-------------------------------- | :----------------------------- | :--------------------------------------------------------------------- |
| 显存异常   | Init CUDA OOM / Dynamic OOM       | 服务无法启动 / 进程被 Kill     | 调小 `gpu_memory_utilization` (如 0.85); 调优 `max_num_batched_tokens` |
| 调度异常   | KV Cache Preemption (抢占/重算)   | 延迟 P99 飙高、吞吐降级、震荡  | 开启 Prefill-Decode 解耦; 合理限制 `max_num_seqs`                      |
| 通信异常   | NCCL Watchdog Timeout             | 多卡死锁、整个服务瘫痪         | 设置合理的 `NCCL_TIMEOUT`; 检查物理 NVLink; 排查长短请求不均           |
| 底层异常   | CUDA Illegal Memory Access        | 硬件 Context 损毁, 需冷重启    | 统一 CUDA/Driver 与 Triton 版本; 关闭实验性 Kernel 融合                |
| 服务层异常 | Event Loop 阻塞 / Detokenize 拥堵 | GPU 饥饿、K8s 探针超时误杀容器 | 开启多进程 Detokenization 分流; 增加 Uvicorn 调度缓冲                  |
| 结构化异常 | Guided Decoding FSM 解析失败      | CPU 飙高、请求被拒或长时间卡死 | 对客户端 JSON Schema 深度进行预校验, 避免极端嵌套                      |

--------------------------------------------------------------------------------------------------

Q: 作为 vllm 部署的推理服务的客户端, 是否有办法感知到上面的这些异常, 如何提高客户端请求代码的健壮性和鲁棒性?

作为客户端, 要应对由 vLLM 服务端复杂机制(KV Cache 抢占、算子越界、NCCL 死锁、异步队列拥堵)引发的异常, 首先需要建立多维度的感知能力, 随后通过确定性前置防御与弹性容错机制来保障生产级的高可用.

---

### 第一部分: 客户端如何精准"感知"服务端的各类异常?

客户端不能仅靠"请求成功/失败"做二元判断, 需要从 `HTTP 状态/错误体`、`网络传输层`、`流式协议(SSE)` 以及 `延迟指标(TTFT/TPOT)` 四个维度进行细分感知:

| 服务端底层异常            | 客户端感知到的现象 / 报错                                                            | 感知层级与判定特征                                                 |
| :------------------------ | :----------------------------------------------------------------------------------- | :----------------------------------------------------------------- |
| 上下文溢出 / 参数校验失败 | HTTP `400 Bad Request` <br> `{"error": {"type": "invalid_request_error", ...}}`      | 应用协议层: 错误明确且确定, 不可盲目重试.                          |
| 队列拥堵 / 服务过载       | HTTP `429 Too Many Requests` 或 `503 Service Unavailable`                            | 应用协议层: 提示服务端已饱和, 需退避.                              |
| KV Cache 抢占 / 调度重算  | 链接正常, 但 TTFT(首字延迟) 或单 Token 间隔(TPOT)突增数倍至数十倍                    | 指标感知: 未报错但性能严重降级, 需要 SLA 监控告警.                 |
| NCCL 死锁 / Worker 卡死   | 静默挂起(TCP 保持连接但不再吐出任何 Token)直至客户端超时                             | 流式传输层: Inter-Token Latency(流闲置超时)告警.                   |
| 运行时 OOM / Kernel 崩溃  | 流式传输中途截断: `httpx.RemoteProtocolError` / `ConnectionResetByPeer` / HTTP `500` | 网络与流协议层: 流意外中断, 且未收到带有 `finish_reason` 的结束包. |
| 进程完全宕机 / 容器重启   | HTTP `502 Bad Gateway` / `ConnectRefusedError`                                       | 网络传输层: 网关已失去后端 Pod, 或端口未开放.                      |

---

### 第二部分: 提升客户端健壮性与鲁棒性的核心策略

#### 1. 多层级细粒度超时控制(避免挂起)

LLM 生成具有"长等待、持续吐字"的特点, 绝对不能使用一个全局固定的 Read Timeout. 必须拆分为三段超时:

* Connect Timeout(如 3~5s): 判断节点网络可达性.
* TTFT / First-Token Timeout(如 15~30s): 涵盖 Prompt 分词、排队调度与 Prefill 耗时. 超过此时间, 说明服务端处于重度过载或队列死锁中.
* Inter-Token Timeout / Chunk Timeout(如 5~10s): 每接收到一个流式 Chunk, 就重置计时器. 这是感知 NCCL 死锁、Worker 崩溃断连最有效的手段.

#### 2. 分类智能重试与退避机制(Exponential Backoff & Jitter)

盲目重试会导致服务端发生雪崩, 必须严格分类:

* 绝对不重试(Non-retryable):
  * `400 Bad Request`(上下文超长、JSON Schema 错误等参数问题).
  * `422 Unprocessable Entity`.

* 带抖动的指数退避重试(Retry with Jitter):
  * `429 Too Many Requests`、`503 Service Unavailable`: 采用指数退避(`base * 2^attempt + uniform(-jitter, jitter)`), 避免形成重试风暴(Thundering Herd).

* 快速换节点重试(Failover Retry):
  * `502 Bad Gateway`、`ConnectionRefused`、`Chunk Timeout`: 意味着当前节点可能 CUDA 崩溃或 NCCL 死锁, 若有多实例/服务网关, 应立即换节点重试.

#### 3. 客户端前置防御(Shift-Left Defense)

将部分校验前移到客户端, 减轻服务端压力:

* 本地 Token 预计算: 在发送请求前, 利用本地 Tokenizer(如 HuggingFace Fast Tokenizer)计算 Prompt 长度, 断言 `len(prompt_tokens) + max_tokens <= max_model_len`. 超长时提前截断或抛出客户端异常, 避免无效的网络传输与 400 失败.
* Schema 语法预校验: 在发起 Guided Decoding 前, 本地用 `jsonschema` 库验证 Schema 的合法性, 避免导致服务端 FSM 编译异常.

#### 4. 完整的流式生命周期与完整性校验(Integrity Checking)

* 服务端在遭遇 OOM 或强制 Kill 时, TCP 连接可能直接中断.
* 客户端必须验证 SSE 流的完整性: 只有收到包含明确 `finish_reason`(如 `"stop"`、`"length"`、`"tool_calls"`)的数据帧, 才视为一次合法且完整的输出. 如果流在没有 `finish_reason` 的情况下结束, 即便 HTTP 状态码此前是 200, 也要判定为服务端运行时崩溃, 触发重试或补救.

#### 5. 主动取消以保护服务端(Graceful Cancellation)

* 当终端用户取消请求(如点击前端"停止", 或上游业务超时触发), 客户端应当显式调用 HTTP Client 的 `aclose()` 关闭连接.
* vLLM 的 `AsyncLLMEngine` 会监听断连事件. 客户端优雅断开能让服务端迅速中断前向推理, 及时释放对应的 KV Cache 块, 防止"幽灵计算"继续拖垮服务器.

---

### 第三部分: 生产级 Python 鲁棒客户端实现范例

以下代码结合了分段超时、流式闲置检测(Watchdog)、前置 Token 校验、细分类指数退避及完整性校验:

```python
import asyncio
import json
import logging
import random
import time
from typing import AsyncGenerator, Dict, Any, Optional
import httpx
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RobustLLMClient")

class RobustLLMClient:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        tokenizer_path: str,
        max_model_len: int = 8192,
        connect_timeout: float = 5.0,
        ttft_timeout: float = 30.0,
        chunk_timeout: float = 8.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.max_model_len = max_model_len
        self.connect_timeout = connect_timeout
        self.ttft_timeout = ttft_timeout
        self.chunk_timeout = chunk_timeout
        self.max_retries = max_retries

        # 本地初始化 fast tokenizer 进行前置防御
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, use_fast=True)

        # 针对长连接建立连接池
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=connect_timeout, read=None, write=10.0, pool=10.0),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)
        )

    def _pre_validate_input(self, prompt: str, max_tokens: int) -> int:
        """前置防御: 验证 Prompt Token 长度"""
        prompt_token_ids = self.tokenizer.encode(prompt)
        prompt_len = len(prompt_token_ids)
        if prompt_len + max_tokens > self.max_model_len:
            raise ValueError(
                f"ClientValidationError: Context exceeded. Prompt ({prompt_len}) + "
                f"MaxTokens ({max_tokens}) > Limit ({self.max_model_len})"
            )
        return prompt_len

    async def generate_stream(
        self, prompt: str, max_tokens: int = 512, sampling_params
    ) -> AsyncGenerator[str, None]:
        """带熔断、分段超时与自愈能力的鲁棒流式生成器"""
        self._pre_validate_input(prompt, max_tokens)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "stream": True,
            sampling_params,
        }

        url = f"{self.base_url}/v1/completions"

        for attempt in range(1, self.max_retries + 1):
            try:
                async for token in self._execute_request(url, payload):
                    yield token
                return  # 正常完成, 退出重试循环

            except (httpx.HTTPStatusError) as e:
                status_code = e.response.status_code
                if status_code == 400:
                    logger.error(f"Client Parameter Error: {e.response.text}. Non-retryable.")
                    raise
                elif status_code in (429, 503):
                    await self._sleep_with_backoff(attempt, is_rate_limit=True)
                else:
                    logger.warning(f"Server error {status_code} on attempt {attempt}/{self.max_retries}")
                    await self._sleep_with_backoff(attempt, is_rate_limit=False)

            except (TimeoutError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                # 涵盖: TTFT 超时、Chunk 超时、服务端 Crash、连接中途 Reset
                logger.warning(f"Transport/Timeout failure: {str(e)} on attempt {attempt}/{self.max_retries}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"Service degraded. Max retries reached: {str(e)}")
                await self._sleep_with_backoff(attempt, is_rate_limit=False)

    async def _execute_request(self, url: str, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """单次请求执行: 实施严格的分段超时与 finish_reason 校验"""
        req = self.client.build_request("POST", url, json=payload)
        response = await self.client.send(req, stream=True)

        if response.status_code != 200:
            await response.aread()
            response.raise_for_status()

        received_first_token = False
        is_generation_finished = False
        stream_iter = response.aiter_lines()

        try:
            while True:
                # 动态设置当前阶段的超时阈值
                current_timeout = self.chunk_timeout if received_first_token else self.ttft_timeout
                try:
                    line = await asyncio.wait_for(stream_iter.__anext__(), timeout=current_timeout)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    if not received_first_token:
                        raise TimeoutError(f"TTFT Timeout ({self.ttft_timeout}s): Server queue hung or prefill stuck.")
                    else:
                        raise TimeoutError(f"Chunk Timeout ({self.chunk_timeout}s): NCCL deadlock or worker died mid-stream.")

                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break

                chunk = json.loads(data_str)
                choice = chunk["choices"][0]
                text_delta = choice.get("text", "")
                finish_reason = choice.get("finish_reason")

                if text_delta:
                    received_first_token = True
                    yield text_delta

                if finish_reason is not None:
                    is_generation_finished = True

            # 完整性校验: 流断开但无结束标记, 判定为底层 Kernel 或 OOM 崩溃
            if not is_generation_finished:
                raise httpx.RemoteProtocolError("Stream abruptly closed without a valid finish_reason.")

        finally:
            # 保证客户端退出或异常中断时, 主动发信号断连, 释放服务端 KV blocks
            await response.aclose()

    async def _sleep_with_backoff(self, attempt: int, is_rate_limit: bool):
        base = 2.0 if is_rate_limit else 0.5
        delay = (base * (2  (attempt - 1))) + random.uniform(0.1, 0.5)
        logger.info(f"Backing off for {delay:.2f}s before retry...")
        await asyncio.sleep(delay)

    async def close(self):
        await self.client.aclose()
```

### 架构级建议

1. 客户端断路器(Circuit Breaker): 如果下游应用集群规模庞大, 单在客户端做退避仍可能带来冲击. 建议集成断路器(如 `pybreaker`), 当连续出现 5 次以上超时或 500 错误时, 熔断所有请求 30 秒, 直接降级(例如返回预设兜底答案或切流至备份模型).
2. 连接池心跳维护: vLLM 对静默长连接敏感, 客户端在配置连接池时应启用合理的 TCP Keepalive, 探测失效套接字, 防止把失效连接复用给后续请求.

--------------------------------------------------------------------------------------------------

Q: 在上述服务端和客户端的各种异常中, 我需要测试环境中主动触发各种异常, 验证异常产生后的各种处理办法是否有效, 请问我应该如何主动的触发各种异常

在测试环境中对 LLM 推理服务进行故障注入(Fault Injection / Chaos Testing), 是验证客户端容错、重试熔断、降级逻辑以及服务端自愈能力的关键步骤.

以下按照异常类型, 提供一套在测试环境中可复现、操作明确、贴近真实事故的主动触发方案、观测指标及验证目标.

---

### 一、显存与 KV Cache 异常注入

#### 1. 触发: 启动时显存溢出(Init CUDA OOM)

* 触发手段:
  * 方法 A(抢占显存法): 在启动 vLLM 之前, 先运行一段 Python 脚本吃掉大部分显存, 然后再启动 vLLM:
    ```python
    # pre_occupy.py: 占用例如 80% 的显存
    import torch, time
    x = torch.empty((80, 1024, 1024, 1024 // 4), device='cuda', dtype=torch.float32) # 约占用 80GB
    time.sleep(3600)
    ```
  * 方法 B(参数压榨法): 启动 vLLM 时将 `--gpu-memory-utilization` 设置为 `0.99`, 并配合极大模型或极大的 `--max-model-len 32768`.
* 服务端现象: 启动阶段抛出 `torch.cuda.OutOfMemoryError`, 容器或进程直接退出(Exit Code 1).
* 客户端验证目标: 客户端发起请求应立即捕获 `httpx.ConnectError`(拒绝连接)或网关层的 `502 Bad Gateway`, 验证客户端的健康检查与告警机制.

#### 2. 触发: KV Cache 耗尽与请求抢占(Preemption / Thrashing)

* 触发手段:
  * 限制 vLLM 的 KV Cache 显存配额: 启动时加入参数 `--gpu-memory-utilization 0.25`(或更低, 甚至指定 `--num-gpu-blocks-override 64`, 极大限制物理 Block 总数).
  * 并发打入长输出请求: 用并发脚本同时发起 10 个请求, 参数设为 `max_tokens=2048`.
* 服务端现象: 日志出现 `Engine preempted request ... due to lack of available KV blocks`, 指标 `vllm:num_preemptions_total` 快速上涨.
* 客户端验证目标:
  * 客户端流式生成的 TTFT 和 TPOT(单 Token 耗时)产生明显毛刺.
  * 验证客户端分段超时计时器是否被正常重置, 或者是否能识别出延迟退化并向监控系统上报 SLA 异常.

---

### 二、分布式与通信异常注入(TP / Ray / NCCL)

#### 1. 触发: Worker 进程暴毙(Process Crash)

* 触发手段:
  * 以张量并行启动服务(如 `--tensor-parallel-size 2`).
  * 在发起推理的途中, 直接在宿主机上找到其中一个 Worker 进程并强杀:
    ```bash
    # 查找 vLLM 相关子进程
    ps aux | grep vllm
    # 强制杀死某一个特定的 Worker PID
    kill -9 <Worker_PID>
    ```
* 服务端现象: Ray 抛出 `RayActorError` 或主进程日志抛出 `RuntimeError: Engine background task failed`.
* 客户端验证目标:
  * 正在进行的流式传输应立即抛出 `httpx.RemoteProtocolError` 或连接中断.
  * 验证客户端是否感知到"流非正常结束(未收到 `finish_reason`)", 并将其标记为传输异常进行切流重试(Failover).

#### 2. 触发: NCCL 死锁与流式静默挂起(Watchdog Timeout)

* 触发手段:
  * 启动前大幅缩短超时时间(默认 30 分钟过长, 测试不便):
    ```bash
    export NCCL_TIMEOUT=15  # 设为 15 秒
    python -m vllm.entrypoints.openai.api_server ... --tensor-parallel-size 2
    ```
  * 客户端发起一个请求, 在生成过程中, 暂停(挂起)其中一个 Rank 进程:
    ```bash
    kill -STOP <Worker_PID>   # 挂起该进程, 卡死集合通信
    ```
* 服务端现象: 另一个 Worker 和主进程由于等不到通信信号, 进入阻塞状态；15 秒后触发看门狗崩溃 `NCCL watchdog thread: detected timeout`.
* 客户端验证目标:
  * 重点验证客户端的 Inter-Token / Chunk Timeout(流闲置超时).
  * 在 15 秒服务端崩溃前, 客户端自身的 Chunk Timeout(如设为 5s)应先于服务端报错主动断开, 证明客户端具备防死锁挂起能力.

---

### 三、调度并发与队列压力注入

#### 1. 触发: 队列打满与超载拒收(429 / 503)

* 触发手段:
  * 启动时人为压缩并发槽位: `--max-num-seqs 2 --max-num-batched-tokens 512`.
  * 客户端使用并发工具瞬间发送 50 个复杂请求(例如使用 `asyncio.gather`).
* 服务端现象: 请求排队队列溢出, 服务端开始拒绝连接或向反向代理抛出高延迟响应.
* 客户端验证目标:
  * 客户端捕获到 `429 Too Many Requests` 或 `503 Service Unavailable`.
  * 验证客户端是否执行了带随机抖动的指数退避(Exponential Backoff with Jitter), 而不是暴力无脑重试加剧雪崩.

#### 2. 触发: 客户端异常主动断连(Client Broken Pipe / Ghost Inference)

* 触发手段:
  * 客户端发起流式生成请求(`max_tokens=2048`), 设置在收到第 5 个 Token 时, 主动切断连接:
    ```python
    # 模拟用户点击了前端界面的"停止生成"按钮
    async for chunk in client.generate_stream(prompt):
        count += 1
        if count == 5:
            await response.aclose()  # 主动抛出取消/关闭 socket
            break
    ```
* 服务端现象:
  * 服务端 Uvicorn / AsyncLLMEngine 应抛出 `ClientDisconnected` 或捕获到 `asyncio.CancelledError`.
  * 日志提示 `Request ... was cancelled by client`.
* 服务端验证目标: 检查 GPU 显存, 确认该请求的 KV Cache Block 是否被 BlockManager 立即释放, 证明服务端没有陷入"幽灵计算".

---

### 四、协议、参数与结构化生成异常注入

#### 1. 触发: 上下文超长(Context Length Exceeded / 400 错误)

* 触发手段:
  * 构造一个极长的 Prompt(超出模型的 `max_model_len`), 或者 `prompt_tokens + max_tokens > max_model_len`.
    ```python
    # 故意发送一个超出长度的 Payload
    payload = {
        "model": "qwen",
        "prompt": "hello " * 40000,
        "max_tokens": 100
    }
    ```
* 服务端现象: 立即返回 HTTP `400 Bad Request`, 包含错误体 `invalid_request_error`.
* 客户端验证目标:
  * 若客户端有前置 Tokenizer 检查, 此请求应该在本地直接拦截并报错, 根本不会发出网络请求.
  * 若直接发出, 验证客户端是否识别为 400 并不执行重试(Non-retryable), 防止无意义占用带宽.

#### 2. 触发: 结构化引导解码崩溃(Guided Decoding / Schema FSM 失败)

* 触发手段:
  * 传入语法错误的 Regex, 或逻辑相互矛盾的 JSON Schema:
    ```python
    # 传入非法的正则表达式语法(例如括号不闭合)
    payload = {
        "model": "qwen",
        "prompt": "Generate json",
        "guided_regex": "(?P<invalid_syntax"
    }
    ```
  * 传入一个让词表全被屏蔽的严格约束(例如要求输出大写字母, 但限定只用数字回复).
* 服务端现象: Outlines / XGrammar 引擎解析失败, 服务端返回 `400` 或生成阶段由于没有合法 Token 报错终止.
* 客户端验证目标: 验证客户端对特殊生成参数校验异常的捕获与降级处理(如通知调用方 Prompt/Schema 错误).

---

### 五、底层网络异常注入(模拟传输层黑天鹅)

如果你的服务端部署在容器(Docker / K8s)或远程节点, 推荐使用 Linux 自带的 `tc` (Traffic Control) 或轻量代理 Toxiproxy 注入传输层故障:

#### 1. 制造高丢包与断流(丢弃部分 Chunk)

在服务端执行命令:
```bash
# 增加 2 秒的网络延迟, 并设置 20% 的随机丢包
sudo tc qdisc add dev eth0 root netem delay 2000ms loss 20%
```
* 客户端验证目标: 验证客户端对于"偶尔卡顿"与"连接中断"的边界判定.

#### 2. 清理网络混沌配置

测试完成后, 务必还原网络环境:
```bash
sudo tc qdisc del dev eth0 root
```

---

### 自动化测试用例实施建议矩阵

| 序号  | 测试用例名称       | 核心注入动作                            | 客户端预期表现                                |
| :---- | :----------------- | :-------------------------------------- | :-------------------------------------------- |
| TC-01 | 参数溢出防御测试   | 发送 100k Token 的 Prompt               | 本地前置拦截 / 捕获 400 立即终止, 无重试      |
| TC-02 | Worker 崩溃测试    | 生成中对 TP Rank1 执行 `kill -9`        | 感知流中途断开, 触发切流至备用节点            |
| TC-03 | 算力挂起死锁测试   | 生成中执行 `kill -STOP`                 | Chunk Timeout (5s) 先于系统超时触发, 主动断连 |
| TC-04 | 突发流量拥塞测试   | 瞬时并发 100+ 请求(单机只能承载 10)     | 捕获 429, 执行带抖动的指数退避重试            |
| TC-05 | 客户端主动取消测试 | 客户端收到第 5 个 Token 发起 `aclose()` | 服务端显存迅速回落, 无残留推理计算            |

--------------------------------------------------------------------------------------------------

Q: 有成熟的在测试环境中对 LLM 推理服务进行故障注入的框架或者工具吗?

在当前的工程实践中, 由于大语言模型推理服务横跨了"HTTP/SSE 流式应用层"、"显存与 KV Cache 调度层"以及"GPU 算子与 NCCL 通信层", 目前业界并没有一个单一的、开箱即用的"LLM 专属一键式混沌工程工具".

工业界(如字节、阿里、NVIDIA、Red Hat 等)在测试 vLLM、Triton 等推理服务时, 普遍采用的是分层组合的成熟开源工具链. 以下是经过生产检验的成熟框架和工具选型推荐:

---

### 一、传输层与流式协议故障注入(首选: Toxiproxy)

在测试 SSE(Server-Sent Events)断流、Inter-Token 卡顿、TTFT 超时时, 常规的网络工具很难精确控制"数据块(Token)级别"的传输.

#### 推荐工具: Shopify Toxiproxy

* 定位: 专门用于在测试环境中模拟网络异常的 TCP 代理工具, 支持通过 REST API 动态热插拔故障(Toxics).
* 为什么适合 LLM 流式推理:
  * 模拟 Token 吐字停顿 / 卡死: 使用 `latency` 或 `jitter` toxic, 动态给 TCP 数据流增加延迟, 验证客户端的 Chunk Timeout.
  * 模拟中间断流(Broken Stream): 使用 `slicer` toxic 将 TCP 数据包切碎并在中途使用 `reset_peer` 或 `timeout` 强行阻断连接, 验证客户端能否发现"未收到 `finish_reason` 却断连"的异常.
  * 模拟慢客户端(Slow Client): 使用 `bandwidth` 限制客户端下行速率, 测试服务端发送队列打满后的背压(Backpressure)机制.
* 使用方式示例(Python 集成测试):
  ```python
  from toxiproxy import Toxiproxy

  proxy = Toxiproxy().get_proxy("vllm_service")
  # 动态注入: 在传输到一半时切断连接
  proxy.add_toxic(type="reset_peer", name="sudden_disconnect", stream="downstream", toxicity=1.0)
  ```

---

### 二、容器与分布式集群混沌测试(推荐: Chaos Mesh / ChaosBlade)

当模型以张量并行(TP>1)部署在 Kubernetes 或物理机多卡环境时, 用于模拟 Worker 崩溃、容器漂移、CPU 争抢.

#### 1. Chaos Mesh(CNCF 毕业级云原生混沌平台)

如果 vLLM 部署在 Kubernetes 上, Chaos Mesh 是最成熟的选择:
* 核心能力匹配:
  * `PodChaos` / `ContainerChaos`: 定时或随机 `Kill` 掉某个 Worker Pod, 测试 API 网关是否能实现秒级摘流(Pod Eviction)与切换.
  * `NetworkChaos`(网络分区): 阻断张量并行 Pod 之间的通信端口(如 PyTorch DDP / NCCL 默认的通信端口, 或阻断两台机器间的 RDMA/RoCE 网卡), 验证分布式推理是否会触发 `NCCL_TIMEOUT` 优雅退出.
  * `StressChaos`: 注入 CPU 争抢和宿主机物理内存压迫, 测试 Python 运行时的 Tokenizer 性能退化.

#### 2. ChaosBlade(阿里开源的轻量级故障注入工具)

如果 vLLM 部署在裸金属物理机(Bare Metal)或单机多卡环境中:
* 核心优势: 无需庞大的 K8s 控制面, 一条命令行即可精准操控进程.
* 典型测试动作:
  ```bash
  # 1. 模拟 NCCL 卡死: 给某个 TP worker 发送 SIGSTOP 挂起进程
  blade create process stop --process vllm --process-cmd-keyword "worker"

  # 2. 模拟 Worker 突发死亡: 直接 SIGKILL
  blade create process kill --process-cmd-keyword "ray::"
  ```

---

### 三、GPU 硬件、驱动与通信层故障模拟

传统混沌工具默认只能控制 CPU 和网卡, 针对 GPU 和 NCCL 的成熟工具如下:

#### 1. NVIDIA DCGM Diagnostic & System Management (`nvidia-smi`)

NVIDIA 官方提供的成熟运维与诊断套件:
* 模拟计算变慢(Straggler / 掉队卡异常):
  使用 `nvidia-smi` 锁定其中一张 GPU 的显卡核心频率, 人为制造"多卡性能不均":
  ```bash
  # 将 GPU 1 的频率锁在最低档(如 300MHz), 测试跨卡 All-Reduce 的长尾延迟
  sudo nvidia-smi -i 1 -lgc 300,300
  ```
* 硬件级掉卡模拟:
  使用 DCGM 的故障注入模式或在系统级使能 PCIe 重置(`nvidia-smi --gpu-reset`), 测试服务在显卡硬件掉线时的处理策略.

#### 2. LLMFI (Large Language Model Fault Injector)

* 定位: 学术界与前沿开源社区专门针对 LLM 推理运行时(Runtime) 开发的故障注入框架.
* 核心能力:
  * 支持在推理的 Prefill 阶段 或 Decode 阶段, 动态向 PyTorch 的激活值(Activation)、权重(Weights)甚至 KV Cache 张量中注入位翻转(Bit-flip)或扰动.
  * 适用场景: 测试模型出现数值异常(NaN / Inf)或者 Logits 畸变时, 服务框架与采样器的自愈或防御行为.

---

### 四、应用层载荷与"KV Cache 风暴"测试

针对"排队打满(429)"、"KV Cache 耗尽抢占(Preemption)", 工具主要是定制化的高性能压测框架:

#### 1. vLLM 官方基准套件扩展(`vllm.benchmarks.benchmark_serving`)

vLLM 源码内置的压测工具本身就是优秀的异常构造器:
* 通过传入极端参数构造 KV Cache 显存风暴:
  ```bash
  # 瞬间以高并发打入极长 Prompt, 直接击穿预分配的 KV 内存池
  python3 -m vllm.entrypoints.openai.api_server ... &

  python3 -m vllm.benchmarks.benchmark_serving \
      --dataset-name random \
      --random-input-len 8000 \
      --random-output-len 2048 \
      --request-rate 50
  ```
* 通过该套件能极其稳定地复现调度器的换入/换出(Swap)、重算(Recompute)与请求丢弃.

#### 2. Locust / k6(搭配 SSE 扩展)

* 普通的压测工具只看 HTTP 状态码, 无法感知生成一半断开.
* 使用 `locust-plugins` 或编写自定义的 Python `httpx` / Node.js 脚本:
  * 编写"恶意客户端"逻辑: 并发 500 个请求, 但每个请求只要收到 3 个 Token 就调用 `close()`, 专门压测 vLLM 处理 `asyncio.CancelledError` 的垃圾回收与显存释放稳定性.

---

### 建议的企业级实施拓扑(落地参考)

如果你要在 CI/CD 或预发环境落地一套自动化测试方案, 最具性价比的架构组合为:

```text
[ 自动化测试套件 (Pytest + Locust) ]
               |
               v (HTTP / SSE)
   [ Toxiproxy (网络层注入: 丢包/延时/切断) ]
               |
               v
   [ vLLM 推理实例集群 (部署于 K8s / 物理机) ]
               ^
               | (底层注入: PodKill / Process Hang / 锁频)
[ Chaos Mesh / ChaosBlade / nvidia-smi 脚本 ]
```

1. 协议层与网络层 交给 Toxiproxy: 覆盖"吐字卡死、中途断流、慢客户端"；
2. 进程与硬件层 交给 ChaosBlade / Chaos Mesh: 覆盖"TP Worker 暴毙、NCCL 挂起、GPU 掉队"；
3. 调度与算法层 交给 Locust / vLLM Benchmark: 覆盖"长文本压榨、KV Cache 抢占溢出、429 拥塞".

--------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM 和 vllm 推理框架的高级研究人员, 现在我使用 vllm 部署了模型推理服务, 详细过程如下:
```bash
docker run -ti --rm \
--entrypoint /usr/bin/env \
--security-opt seccomp=unconfined \
--gpus '"device=0"' \
-v /data/model:/model \
-p 0.0.0.0:8090:8000 \
--name vllm-server \
vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 bash

export VLLM_LOGGING_LEVEL=DEBUG
export VLLM_DEBUG_LOG_API_SERVER_RESPONSE=TRUE
export TORCH_SHOW_CPP_STACKTRACES=1

vllm serve \
/model/Qwen2.5-7B-Instruct \
--served-model-name Qwen2.5-7B-Instruct \
--trust-remote-code \
--use-tqdm-on-load \
--host 0.0.0.0 \
--port 8000 \
--api-key my_secret_token_123 my_secret_token_456 \
--enable-log-requests \
--enable-log-outputs \
--no-disable-uvicorn-access-log \
--uvicorn-log-level debug \
--aggregate-engine-logging \
--enable-logging-iteration-details \
--log-error-stack \
--cudagraph-metrics \
--kv-cache-metrics \
--enable-mfu-metrics \
--enable-log-deltas \
--enable-prompt-tokens-details \
--enable-tokenizer-info-endpoint \
--enable-server-load-tracking \
--enable-force-include-usage \
--shutdown-timeout 30 \
--gpu-memory-utilization 0.95 \
--max-model-len 8192 \
--enable-prefix-caching

```
现在我想主动触发服务端的错误, 让客户端连接到这个服务时, 客户端会收到 http 状态码大于等于 500 的异常, 请问我应该如何操作, 客户端应该怎么写, 服务端有没有需要修改的地方? 请列出详细的操作步骤.

在 vLLM 和 FastAPI 架构中, 客户端故意触发 HTTP 状态码 $\ge 500$(如 500 Internal Server Error 或 503 Service Unavailable) 的关键在于: 绕过 FastAPI 和 Pydantic 的入参校验(否则会返回 400/422), 将非法或引发底层异常的负载送入推理引擎(AsyncEngine/Model Runner), 或者使后台引擎崩溃.

针对你的部署配置(已开启 `DEBUG` 日志、`TORCH_SHOW_CPP_STACKTRACES=1`、映射端口为宿主机 `8090`、模型为纯文本 `Qwen2.5-7B-Instruct`), 以下为你提供三种不同层级的操作方案(从无需改动服务端到混沌工程以及精确 Mock 注入).

---

### 方案一: 纯客户端请求触发(服务端无需任何修改, 推荐)

该方案利用 vLLM 内部模块的未捕获异常机制, 通过构造特定请求, 绕过外层校验并在服务端引发 HTTP 500.

#### 触发方式 1: 向纯文本模型注入多模态结构(最稳定)

* 原理: `Qwen2.5-7B-Instruct` 是纯文本模型, 未初始化 Vision 相关 Processor. 当客户端按照 OpenAI 标准协议传递包含 `image_url` 的混合消息时, Pydantic 校验能顺利通过, 但在进入 Prompt 组装与特征提取阶段时, 后台 `asyncio.TaskGroup` 或处理器会抛出未处理的异常, 直接向上抛出 `HTTP 500 Internal Server Error`.
* 客户端代码 (Python):

```python
import requests

url = "http://localhost:8090/v1/chat/completions"
headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen2.5-7B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "描述这张图片"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,invalid_base64_payload=="
                    }
                }
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")  # 预期输出 >= 500 (通常为 500)
print(f"Response: {response.text}")
```

* 对应 cURL:

```bash
curl -i -X POST http://localhost:8090/v1/chat/completions \
-H "Authorization: Bearer my_secret_token_123" \
-H "Content-Type: application/json" \
-d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "hi"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,abc"
                    }
                }
            ]
        }
    ]
}'

```

---

#### 触发方式 2: 使用不支持的正则断言触发结构化解码异常

* 原理: vLLM 支持 `guided_regex`(结构化引导解码), 使用 `outlines` 或 `xgrammar` 编译正则有限状态机. 如果传入一个合法字符串、但在正则引擎中不被支持的高级语法(如回顾后发断言 `(?<=...)` 或 `(?<!...)`), FSM 编译器会抛出 `NotImplementedError` 或 `Unsupported` 异常, 该异常在构建 LogitsProcessor 时直接导致请求以 500 失败.
* 客户端代码 (Python):

```python
import requests

url = "http://localhost:8090/v1/chat/completions"
headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "1+1="}],
    # 传入 FSM 正则编译器不支持的前后查找断言
    "guided_regex": "(?<=test)[0-9]+"
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
```

---

#### 触发方式 3: 极端并发/超大采样触发显存 OOM

* 原理: 你的启动参数配置了 `--gpu-memory-utilization 0.95`, 意味着 GPU 95% 的显存被静态分配给权重和 KV-Cache, 给 PyTorch 运行时算子动态分配预留的 Workspace 显存不足 5%. 通过单次请求要求极大的生成分支(例如 `n=64`), 会导致显存耗尽抛出 `torch.cuda.OutOfMemoryError`, 直接产生 500 异常.
* 客户端代码 (Python):

```python
import requests

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "写一篇 5000 字的小说" * 10}],
    "max_tokens": 4096,
    "n": 64  # 一次性生成 64 条分支序列, 极易爆掉剩余显存
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
```

---

### 方案二: 混沌工程与进程故障注入(服务端无需改代码, 100% 触发 500)

在生产高可用测试中, 最标准的做法是模拟"前端网关仍存活, 但后台推理引擎已崩溃(AsyncEngineDeadError)".

#### 操作步骤:

1. 服务端保持正常运行(如你当前的容器状态).
2. 在宿主机另开一个终端, 向容器内的推理核心子进程发送 `SIGKILL` 信号:

```bash
# 杀死后台 EngineCore 或 Worker 进程, 但保留 Uvicorn 主服务
docker exec -it vllm-server pkill -9 -f "EngineCore"
```
(注: 如果当前 vLLM 版本采用 Ray 或 Multiprocessing Worker, 可执行 `docker exec -it vllm-server pkill -9 -f "vllm.worker"`)

3. 客户端立即发起标准请求:

```python
import requests

url = "http://localhost:8090/v1/chat/completions"
headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "hello"}]
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Body: {response.text}")

```

4. 现象:

- 客户端将立刻收到:
```json
HTTP/1.1 500 Internal Server Error
{"error": {"message": "EngineCore is dead or has errored already.", "type": "internal_error", "code": 500}}
```
- 服务端终端会因你配置了 `TORCH_SHOW_CPP_STACKTRACES=1` 和 `DEBUG` 打印完整的进程退出堆栈.

---

### 方案三: 服务端代码拦截/中间件注入(确定性、可编程控制)

如果你希望在 CI/CD 自动化集成测试中稳定复现 500/503, 而不希望真正搞挂 GPU 驱动或破坏服务上下文, 可以在服务端注入一个自定义中间件(Middleware).

#### 服务端修改步骤:

由于你使用 `bash` 交互式进入了容器, 可在启动 `vllm serve` 前, 对 FastAPI 入口进行轻量级 Patch.

1. 找到 API Server 代码路径:

在容器内执行:

```bash
python3 -c "import vllm.entrypoints.openai.api_server as m; print(m.__file__)"
# 路径通常位于: /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/openai/api_server.py

$ python3 -c "import vllm.entrypoints.openai.api_server as m; print(m.__file__)"
/usr/local/lib/python3.12/dist-packages/vllm/entrypoints/openai/api_server.py
$

```

2. 编辑该文件:

在创建 `app = FastAPI(...)` 之后, 添加如下中间件(支持通过 Header 触发 500 或 503):

```python
from starlette.responses import JSONResponse

@app.middleware("http")
async def mock_fault_injection_middleware(request, call_next):
    # 如果客户端携带了特定的混沌测试 Header, 直接返回 500
    if request.headers.get("X-Chaos-Fault") == "500":
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "Injected 500 Internal Server Error", "type": "chaos_test"}}
        )
    elif request.headers.get("X-Chaos-Fault") == "503":
        return JSONResponse(
            status_code=503,
            content={"error": {"message": "Service Temporarily Unavailable", "type": "chaos_test"}}
        )
    return await call_next(request)

```

3. 启动 vllm serve(使用你原有的启动参数).

4. 客户端请求:

客户端只需在 Header 中附带该标记即可自主控制触发:

```bash
curl -i -X POST http://localhost:8090/v1/chat/completions \
-H "Authorization: Bearer my_secret_token_123" \
-H "Content-Type: application/json" \
-H "X-Chaos-Fault: 500" \
-d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": "hi"
        }
    ]
}'

```

---

### 总结与选型建议

| 方案                      | 服务端是否需修改   | 稳定性/可控性            | 影响范围                               | 适用场景                                |
| :------------------------ | :----------------- | :----------------------- | :------------------------------------- | :-------------------------------------- |
| 方案一(多模态/正则注入)   | 完全不需要         | 极高(利用内部未捕获逻辑) | 仅影响当前请求                         | 黑盒测试、客户端单测重试机制            |
| 方案二(杀掉 Engine 进程)  | 仅需执行杀进程命令 | 100% 稳定出 500          | 影响该容器后续所有请求, 需重启容器恢复 | 容灾演练、熔断降级(Circuit Breaker)测试 |
| 方案三(注入 Fault 中间件) | 需要修改一行文件   | 100% 精准可控            | 按 Header 隔离, 不影响其他正常流量     | CI/CD 自动化流水线、长期性能压测验证    |

如果你手头服务正在跑, 首选「方案一的方式 1」或「方案二」, 无需改动任何代码与容器配置, 几秒钟内即可在客户端捕获标准的 HTTP 500 异常.

--------------------------------------------------------------------------------------------------

Q: 使用方案三: 服务端代码拦截/中间件注入, 原始的 api_server.py 文件如下:

```python
# /usr/local/lib/python3.12/dist-packages/vllm/entrypoints/openai/api_server.py
```
请输出完整的使用方案3修改之后的文件

以下是针对你的源码进行修改后的完整 `api_server.py` 文件.

### 修改说明

1. 导入模块: 在文件头部导入了 `Request` 与 `JSONResponse`.
2. 故障注入中间件: 在 `build_app` 函数中注入了 `@app.middleware("http")` 混沌故障拦截器 `chaos_fault_injection_middleware`.
3. 触发逻辑:
   * 支持通过 HTTP Header `X-Chaos-Fault: <code|action>` 或 URL Query 参数 `?chaos_fault=<code|action>` 触发.
   * 支持指定任意状态码(如 `500`、`502`、`503`、`504`), 直接返回符合 OpenAI 规范的 JSON 错误响应.
   * 支持传 `raise` 或 `crash`, 会在服务端主动抛出一个未捕获的 `RuntimeError`, 以此触发服务端的异常栈捕获机制.
   * 不带该 Header/参数的正常请求完全不受影响, 可安心用于测试和生产对比.

---

### 完整代码 (`api_server.py`)

```python
```

---

### 部署与客户端测试说明

#### 1. 替换容器内的文件

因为你在容器中是 `bash` 交互模式, 可以先查看文件绝对路径并进行覆盖:

```bash
# 在容器内查看文件路径
FILE_PATH=$(python3 -c "import vllm.entrypoints.openai.api_server as m; print(m.__file__)")
echo $FILE_PATH

# 直接覆盖写入上述内容
cat << 'EOF' > $FILE_PATH
<粘贴上面的完整代码>
EOF
```
然后正常执行你原有的 `vllm serve ...` 命令启动服务.

#### 2. 客户端调用方式

##### (1) cURL 测试

```bash
# 测试返回 HTTP 500
curl -i -X POST http://localhost:8090/v1/chat/completions \
  -H "Authorization: Bearer my_secret_token_123" \
  -H "Content-Type: application/json" \
  -H "X-Chaos-Fault: 500" \
  -d '{"model": "Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "hello"}]}'

# 测试返回 HTTP 503 (模拟服务不可用)
curl -i -X POST http://localhost:8090/v1/chat/completions \
  -H "Authorization: Bearer my_secret_token_123" \
  -H "Content-Type: application/json" \
  -H "X-Chaos-Fault: 503" \
  -d '{"model": "Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "hello"}]}'

# 测试抛出未捕获异常 (观察服务端终端栈回溯)
curl -i -X POST http://localhost:8090/v1/chat/completions \
  -H "Authorization: Bearer my_secret_token_123" \
  -H "Content-Type: application/json" \
  -H "X-Chaos-Fault: raise" \
  -d '{"model": "Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "hello"}]}'
```

##### (2) Python 客户端测试

```python
import requests

url = "http://localhost:8090/v1/chat/completions"

# 1. 触发 500 异常
headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json",
    "X-Chaos-Fault": "500",  # 设置为你想要返回的状态码 >= 500
}

payload = {
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "hello"}],
}

res = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {res.status_code}")  # 500
print(f"Response Body: {res.text}")

# 2. 正常请求对比 (去掉 Header 正常输出模型推理)
normal_headers = {
    "Authorization": "Bearer my_secret_token_123",
    "Content-Type": "application/json",
}
res_normal = requests.post(url, headers=normal_headers, json=payload)
print(f"Normal Request Status: {res_normal.status_code}")  # 200
```

--------------------------------------------------------------------------------------------------

Q: 使用 --middleware 参数实现

完全可以使用 `--middleware` 参数来实现, 而且这是 vLLM 官方推荐的、最优雅的无侵入式解耦方案.

### 为什么可以无缝替换?

查看你所贴出的 `vllm/entrypoints/openai/api_server.py` 源码中的解析逻辑:

```python
for middleware in args.middleware:
    module_path, object_name = middleware.rsplit(".", 1)
    imported = getattr(importlib.import_module(module_path), object_name)
    if inspect.isclass(imported):
        app.add_middleware(imported)
    elif inspect.iscoroutinefunction(imported):
        app.middleware("http")(imported)
    else:
        raise ValueError(...)
```

从源码可以看到:
1. `--middleware` 参数接收一个形如 `<module_path>.<object_name>` 的字符串, 并通过 `importlib.import_module` 动态导入.
2. 如果传入的是一个协程函数（`inspect.iscoroutinefunction`, 即 `async def`）, vLLM 会直接执行 `app.middleware("http")(imported)`. 这与你在源码中写的 `@app.middleware("http")` 底层行为完全等价.
3. 如果传入的是一个类, vLLM 会通过 `app.add_middleware(imported)` 加载.

---

### 详细操作步骤

#### 第一步: 将中间件代码抽取为独立的 Python 模块

在宿主机上（例如 `/data/middlewares/chaos_middleware.py`）创建一个独立的文件, 将中间件逻辑剥离出来:

```bash
mkdir -p /data/middlewares
cat << 'EOF' > /data/middlewares/chaos_middleware.py
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("vllm.entrypoints.openai.api_server")

async def chaos_fault_injection_middleware(request: Request, call_next):
    """
    Chaos Fault Injection Middleware:
    主动拦截请求并根据 X-Chaos-Fault 响应指定的 >=500 状态码或抛出异常
    """
    fault = request.headers.get("X-Chaos-Fault") or request.query_params.get("chaos_fault")
    if fault:
        logger.warning("Active chaos fault injection triggered with marker: %s", fault)

        # 1. 指定 HTTP >= 500 状态码 (例如 500, 502, 503, 504)
        if fault.isdigit() and int(fault) >= 500:
            status_code = int(fault)
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "message": f"Injected Fault: Service returned HTTP {status_code} intentionally.",
                        "type": "chaos_fault_injection",
                        "param": None,
                        "code": status_code,
                    }
                },
            )
        # 2. 模拟抛出未捕获服务端严重异常, 验证异常处理机制
        elif fault.lower() in ("exception", "crash", "raise"):
            raise RuntimeError(
                "Injected Fault: Simulated unhandled server exception for chaos test."
            )

    return await call_next(request)
EOF
```

---

#### 第二步: 调整 Docker 容器挂载与 Python 路径

通过挂载将宿主机的 `/data/middlewares` 映射到容器内部（例如 `/workspace/middlewares`）, 并通过设置环境变量 `PYTHONPATH` 确保 Python 能够找到该模块.

在启动 Docker 容器时挂载并导出环境:

```bash
docker run -ti --rm \
  --entrypoint /usr/bin/env \
  --security-opt seccomp=unconfined \
  --gpus '"device=0"' \
  -v /data/model:/model \
  -v /data/middlewares:/workspace/middlewares \
  -p 0.0.0.0:8090:8000 \
  --name vllm-server \
  vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 bash
```

进入容器后, 在终端执行:

```bash
# 将模块所在的父目录加入 PYTHONPATH, 确保能够直接 import middlewares.xxx
export PYTHONPATH="/workspace:${PYTHONPATH}"

export VLLM_LOGGING_LEVEL=DEBUG
export VLLM_DEBUG_LOG_API_SERVER_RESPONSE=TRUE
export TORCH_SHOW_CPP_STACKTRACES=1
```

---

#### 第三步: 启动 `vllm serve` 并传入 `--middleware` 参数

在原有命令中追加 `--middleware middlewares.chaos_middleware.chaos_fault_injection_middleware` 即可:

```bash
vllm serve \
  /model/Qwen2.5-7B-Instruct \
  --served-model-name Qwen2.5-7B-Instruct \
  --trust-remote-code \
  --use-tqdm-on-load \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key my_secret_token_123 my_secret_token_456 \
  --enable-log-requests \
  --enable-log-outputs \
  --no-disable-uvicorn-access-log \
  --uvicorn-log-level debug \
  --aggregate-engine-logging \
  --enable-logging-iteration-details \
  --log-error-stack \
  --cudagraph-metrics \
  --kv-cache-metrics \
  --enable-mfu-metrics \
  --enable-log-deltas \
  --enable-prompt-tokens-details \
  --enable-tokenizer-info-endpoint \
  --enable-server-load-tracking \
  --enable-force-include-usage \
  --shutdown-timeout 30 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 8192 \
  --enable-prefix-caching \
  --middleware middlewares.chaos_middleware.chaos_fault_injection_middleware
```

(注: 如果你使用的是类形式的中间件, 这里传入 `middlewares.chaos_middleware.ChaosFaultInjectionMiddleware` 同样有效)

---

#### 第四步: 验证中间件生效

服务启动完毕后, 在宿主机或测试机上验证:

##### 1. 正常请求验证
```bash
curl -i -X POST http://127.0.0.1:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my_secret_token_123" \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "ping"}]
  }'
```
> 应正常返回 `HTTP/1.1 200 OK`.

##### 2. 模拟 503 Service Unavailable 拦截
```bash
curl -i -X POST http://127.0.0.1:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my_secret_token_123" \
  -H "X-Chaos-Fault: 503" \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "ping"}]
  }'
```
> 应立即返回 `HTTP/1.1 503 Service Unavailable` 及注入的 JSON 错误信息, 请求不会下发给 vLLM 引擎.

##### 3. 模拟抛出未捕获异常
```bash
curl -i -X POST "http://127.0.0.1:8090/v1/chat/completions?chaos_fault=crash" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer my_secret_token_123" \
  -d '{
    "model": "Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "ping"}]
  }'
```
> 应触发未捕获异常并交由 FastAPI 底层全局 exception handler 捕获（返回 500）.

---

### 架构细节与注意事项 (Best Practices)

1. 中间件执行顺序（洋葱模型）:
   * FastAPI / Starlette 的中间件是后注册的包裹在最外层.
   * 在 `build_app` 中, `AuthenticationMiddleware` 先注册, `args.middleware` 后注册.
   * 结果: 传入的 `--middleware` 会在 API Key 鉴权之前最先触达请求. 这意味着即使请求未携带 Bearer Token, 只要触发了 `X-Chaos-Fault`, 该中间件就会提前拦截报错. 这非常符合混沌工程（Chaos Testing）的预期.
2. 多中间件级联:
   * CLI 参数 `--middleware` 的 action 是 `append`, 支持多次指定. 例如:
     ```bash
     --middleware middlewares.trace.TraceMiddleware \
     --middleware middlewares.chaos_middleware.chaos_fault_injection_middleware
     ```
3. 基于类的标准实现（可选替代方案）:
   如果你希望代码更具规范性, 也可以使用 Starlette 的 `BaseHTTPMiddleware` 类:
   ```python
   from starlette.middleware.base import BaseHTTPMiddleware
   from fastapi import Request
   from fastapi.responses import JSONResponse

   class ChaosFaultInjectionMiddleware(BaseHTTPMiddleware):
       async def dispatch(self, request: Request, call_next):
           # 逻辑与函数完全一致
           ...
           return await call_next(request)
   ```
   vLLM 的 `inspect.isclass` 分支会自动调用 `app.add_middleware(imported)` 进行加载. 两种方式在当前场景下功能完全一致.

--------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------------------------
