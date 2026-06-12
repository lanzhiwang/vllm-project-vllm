# Disaggregated Encoder
分解编码器

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/disaggregated_encoder

Source https://github.com/vllm-project/vllm/tree/main/examples/online_serving/disaggregated_encoder.

These example scripts that demonstrate the disaggregated encoder (EPD) features of vLLM.
这些示例脚本演示了 vLLM 的分解编码器 (EPD) 功能.

For a detailed explanation of the EPD features, please refer to the [Disaggregated Encoder Feature Documentation](https://github.com/vllm-project/vllm/tree/main/docs/features/disagg_encoder.md).
有关 EPD 功能的详细说明, 请参阅分解编码器功能文档.

## Files

- `disagg_epd_proxy.py` - Proxy script that demonstrates the XeYpZd setup (X encode instances, Y prefill instances, Z decode instances). Currently stable for the `1e1p1d` configuration.
  `disagg_epd_proxy.py` - 代理脚本, 演示 XeYpZd 设置(X 编码实例、Y 预填充实例、Z 解码实例). 目前对 1e1p1d 配置稳定.

- `disagg_1e1p1d_example.sh` - Sets up the `1e1p1d` configuration, runs the VisionArena benchmark, and processes a single request with a local image.
  `disagg_1e1p1d_example.sh` - 设置 1e1p1d 配置, 运行 VisionArena 基准测试, 并使用本地图像处理单个请求.

- `disagg_1e1pd_example.sh` - Sets up the `1e1pd` configuration, runs the VisionArena benchmark, and processes a single request with a local image.
  `disagg_1e1pd_example.sh` - 设置 1e1pd 配置, 运行 VisionArena 基准测试, 并使用本地图像处理单个请求.

### Custom Configuration
自定义配置

```bash
# Use specific GPUs
GPU_E=0 GPU_PD=1 GPU_P=1 GPU_D=2 bash disagg_1e1p1d_example.sh

# Use specific ports
ENDPOINT_PORT=10001 bash disagg_1e1p1d_example.sh

# Use specific model
MODEL="Qwen/Qwen2.5-VL-3B-Instruct" bash disagg_1e1p1d_example.sh

# Use specific storage path
EC_SHARED_STORAGE_PATH="/tmp/my_ec_cache" bash disagg_1e1p1d_example.sh

# Run on XPU; scripts switch from CUDA_VISIBLE_DEVICES to ZE_AFFINITY_MASK
DEVICE_PLATFORM=xpu GPU_E=0 GPU_PD=1 bash disagg_1e1pd_example.sh
```

`DEVICE_PLATFORM` defaults to `cuda`. Set `DEVICE_PLATFORM=xpu` when running these examples on Intel GPUs so the scripts use `ZE_AFFINITY_MASK` instead of `CUDA_VISIBLE_DEVICES` for device selection.
`DEVICE_PLATFORM` 默认为 `cuda`. 在 Intel GPU 上运行这些示例时, 请设置 `DEVICE_PLATFORM=xpu`, 以便脚本使用 `ZE_AFFINITY_MASK` 而不是 `CUDA_VISIBLE_DEVICES` 进行设备选择.

## Encoder Instances
编码器实例

Encoder engines should be launched with the following flags:
编码器引擎应使用以下标志启动:

- `--enforce-eager` (required) – The current EPD implementation is only compatible with encoder instances running in this mode.
  `--enforce-eager` (必需) – 当前的 EPD 实现仅与在此模式下运行的编码器实例兼容.

- `--no-enable-prefix-caching` (required) – Encoder instances do not consume KV cache; prefix caching is disabled to avoid conflicts with other features.
  `--no-enable-prefix-caching` (必需) – 编码器实例不使用 KV 缓存; 已禁用前缀缓存, 以避免与其他功能冲突.

- `--max-num-batched-tokens=<large value>` (default: 2048) – This flag controls the token scheduling budget per decoding step and is irrelevant to encoder-only instances. Set it to a very high value (effectively unlimited) to bypass scheduler limitations. The actual token budget is managed by the encoder cache manager.
  `--max-num-batched-tokens=<large value>` (默认值: 2048) – 此标志控制每个解码步骤的令牌调度预算, 与仅编码器实例无关. 将其设置为非常大的值(实际上是无限制)可以绕过调度器限制. 实际的令牌预算由编码器缓存管理器管理.

- `--mm-encoder-only` (Optional) - If possible, skips the language model during initialization to reduce device memory usage.
  `--mm-encoder-only` (可选) - 如果可能, 则在初始化期间跳过语言模型, 以减少设备内存使用量.

## Local media inputs

To support local image inputs (from your `MEDIA_PATH` directory), add the following flag to the encoder instance:
要支持本地图像输入(来自您的 `MEDIA_PATH` 目录), 请将以下标志添加到编码器实例:

```bash
--allowed-local-media-path $MEDIA_PATH
```

The vllm instances and `disagg_encoder_proxy` supports local URIs with `{"url": "file://'"$MEDIA_PATH_FILENAME"'}` as multimodal inputs. Each URI is passed unchanged from the `disagg_encoder_proxy` to the encoder instance so that the encoder can load the media locally.
vllm 实例和 `disagg_encoder_proxy` 支持以 `{"url": "file://'"$MEDIA_PATH_FILENAME"'}` 为多模态输入的本地 URI. 每个 URI 都从 `disagg_encoder_proxy` 原封不动地传递给编码器实例, 以便编码器可以在本地加载媒体.

## EC connector and KV transfer
EC 连接器和 KV 转换

The `ECExampleonnector` is used to store the encoder cache on local disk and facilitate transfer. To enable the encoder disaggregation feature, add the following configuration:
`ECExampleonnector` 用于将编码器缓存存储在本地磁盘上, 以便于传输. 要启用编码器解耦功能, 请添加以下配置:

```bash
# Add to encoder instance:
--ec-transfer-config '{
    "ec_connector": "ECExampleConnector",
    "ec_role": "ec_producer",
    "ec_connector_extra_config": {
        "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
    }
}'

# Add to prefill/prefill+decode instance:
--ec-transfer-config '{
    "ec_connector": "ECExampleConnector",
    "ec_role": "ec_consumer",
    "ec_connector_extra_config": {
        "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
    }
}'
```

`$EC_SHARED_STORAGE_PATH` is the path where the EC connector temporarily stores the cache.
`$EC_SHARED_STORAGE_PATH` 是 EC 连接器临时存储缓存的路径.

If you enable prefill instance (`--prefill-servers-urls` not disabled), you will need --kv-transfer-config to facilitate the PD disaggregation. Currently, we use the `NixlConnector` for this purpose. Refer to `tests/v1/kv_connector/nixl_integration` for more example codes on PD disaggregation with Nixl.
如果启用预填充实例(未禁用 `--prefill-servers-urls` ), 则需要使用 `--kv-transfer-config` 来简化 PD 分离. 目前, 我们使用 `NixlConnector` 来实现此目的. 有关使用 Nixl 进行 PD 分离的更多示例代码, 请参阅 `tests/v1/kv_connector/nixl_integration`.

```bash
# Add to prefill instance:
--kv-transfer-config '{
    "kv_connector": "NixlConnector",
    "kv_role": "kv_producer"
}'

# Add to decode instance:
--kv-transfer-config '{
    "kv_connector": "NixlConnector",
    "kv_role": "kv_consumer"
}'
```

## Proxy Instance Flags (`disagg_epd_proxy.py`)
代理实例标志(`disagg_epd_proxy.py`)

| Flag                     | Description                                                                                                                                                                                                                                                                                     |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--encode-servers-urls`  | Comma-separated list of encoder endpoints. Every multimodal item extracted from the request is fanned out to one of these URLs in a round-robin fashion. <br> 以逗号分隔的编码器端点列表. 从请求中提取的每个多模态项都会以轮询方式分发到这些 URL 之一.                                          |
| `--prefill-servers-urls` | Comma-separated list of prefill endpoints. Set to `disable`, `none`, or `""` to skip the dedicated prefill phase and run E+PD (encoder + combined prefill/decode). <br> 以逗号分隔的预填充端点列表. 设置为 `disable`、`none` 或 `""` 可跳过专用预填充阶段并运行 E+PD(编码器 + 组合预填充/解码). |
| `--decode-servers-urls`  | Comma-separated list of decode endpoints. Non-stream and stream paths both round-robin over this list. <br> 以逗号分隔的解码端点列表. 非流路径和流路径都会轮询此列表.                                                                                                                           |
| `--host`, `--port`       | Bind address for the proxy itself (defaults: `0.0.0.0:8000`).                                                                                                                                                                                                                                   |

Example usage: For E + PD setup:

```bash
$ python disagg_encoder_proxy.py \
      --encode-servers-urls "http://e1:8001,http://e2:8002" \
      --prefill-servers-urls "disable" \
      --decode-servers-urls "http://pd1:8003,http://pd2:8004"
```

For E + P + D setup:

```bash
$ python disagg_encoder_proxy.py \
      --encode-servers-urls "http://e1:8001,http://e2:8001" \
      --prefill-servers-urls "http://p1:8003,http://p2:8004" \
      --decode-servers-urls "http://d1:8005,http://d2:8006"
```

## Example materials

----------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 bash 脚本用于 vllm 的相关功能
```
# disagg_1e1p1d_example.sh

```
请为这个脚本添加注释, 一是说明 bash 脚本的一些语法, 二是说明为什么要这么写, 三是说明 vllm 的相关特性和参数含义

这份 Bash 脚本展示了 vLLM 中前沿的多模态解耦推理架构(EPD: Encoder-Prefill-Decode Disaggregation). 针对视觉语言模型(如脚本中的 `Qwen/Qwen2.5-VL-3B-Instruct`), 由于图像处理、文本 Prefill 以及自回归 Decode 在计算模式和资源消耗上有极大差异, 将它们在物理或逻辑上进行解耦部署, 可以有效提升系统的整体吞吐并降低延迟.

为了帮助您深入理解, 以下将从代码注释、Bash 语法与编程范式、异构解耦设计逻辑以及 vLLM 核心参数与技术内幕四个维度进行全面拆解.

---

### 一、带中文详细注释的完整脚本

以下是添加了多维度注释(涵盖 Bash、设计逻辑、vLLM 特性)的脚本代码:

```bash
#!/bin/bash
# ==============================================================================
# [BASH语法] 启用严格的 Bash 运行模式(Strict Mode)
# -e: 任何单条命令如果执行失败(返回非 0 状态码), 脚本会立即退出, 防止错误累积.
# -u: 遇到未绑定的变量(即未声明、无默认值的变量)时直接报错退出, 避免拼写错误导致异常.
# -o pipefail: 当管道命令(|)中任何一个子命令失败, 整条管道的状态便为失败(默认仅保留最后一条命令的状态).
# ==============================================================================
set -euo pipefail

# [BASH语法] 显式声明一个名为 PIDS 的索引数组(Indexed Array).
# [设计逻辑] 用于统一收集后台启动的所有子进程的 PID(包括 E/P/D Worker、Proxy 和 Benchmark), 以便在清理阶段统一回收.
declare -a PIDS=()

###############################################################################
# Configuration -- 默认参数配置. 支持在执行前通过环境变量进行覆盖
###############################################################################
# [BASH语法] ${VAR:-default}: 参数默认值展开语法. 若 $MODEL 环境变量为空或未定义, 则使用右侧默认值.
MODEL="${MODEL:-Qwen/Qwen2.5-VL-3B-Instruct}"
LOG_PATH="${LOG_PATH:-./logs}"

# [设计逻辑] 确保日志存放目录存在, 避免后续进程重定向标准输出时报错.
mkdir -p "$LOG_PATH"

# [设计逻辑] 在单机多卡或者局域网环境中, 必须显式区分各子服务的监听端口以防止端口冲突.
ENCODE_PORT="${ENCODE_PORT:-19534}"
PREFILL_PORT="${PREFILL_PORT:-19535}"
DECODE_PORT="${DECODE_PORT:-19536}"
PROXY_PORT="${PROXY_PORT:-10001}"

# [设计逻辑] 分配 GPU 绑定关系. 多卡环境下通常将 Encoder、Prefill、Decode 绑定到不同的 GPU 上.
GPU_E="${GPU_E:-2}"
GPU_P="${GPU_P:-2}"
GPU_D="${GPU_D:-3}"

# Device platform and affinity env name.
# DEVICE_PLATFORM supports: cuda, xpu
# [设计逻辑] 支持异构加速平台.
DEVICE_PLATFORM="${DEVICE_PLATFORM:-cuda}"
if [[ -z "${DEVICE_AFFINITY_ENV:-}" ]]; then
    # [BASH语法] ${DEVICE_PLATFORM,,}: Bash 4.0+ 语法, 将变量内所有字符转为小写, 实现不区分大小写的匹配.
    if [[ "${DEVICE_PLATFORM,,}" == "xpu" ]]; then
        # 针对英特尔 XPU 平台的 GPU 亲和性环境变量
        DEVICE_AFFINITY_ENV="ZE_AFFINITY_MASK"
    else
        # 针对 NVIDIA CUDA 平台的 GPU 亲和性环境变量
        DEVICE_AFFINITY_ENV="CUDA_VISIBLE_DEVICES"
    fi
fi

# [vLLM特性] EC(Encoder Cache)共享存储路径.
# Encoder 计算出的多模态视觉 Embedding 会临时写入这个共享目录, Prefill 阶段再去读取, 以避免多节点/多进程之间重复计算.
EC_SHARED_STORAGE_PATH="${EC_SHARED_STORAGE_PATH:-/tmp/ec_cache}"

# [设计逻辑] 设置等待各 Worker 服务就绪的最大超时时间(秒).
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-12000}"

# [设计逻辑] 基准测试中发送的 Prompt 样本总量.
NUM_PROMPTS="${NUM_PROMPTS:-100}"

# Serve args (vLLM 服务参数)
# [vLLM特性] 显存利用率上限设置:
# - Encoder(E)不保留文本 KV Cache, 只做单次 Vision 编码, 所需显存极小, 故设为 0.01(1%).
# - Prefill(P)和 Decode(D)负责大语言模型(LLM)部分且需存储大量 KV 缓存, 故分配 0.7(70%).
GPU_MEMORY_UTILIZATION_E="${GPU_MEMORY_UTILIZATION_E:-0.01}"
GPU_MEMORY_UTILIZATION_P="${GPU_MEMORY_UTILIZATION_P:-0.7}"
GPU_MEMORY_UTILIZATION_D="${GPU_MEMORY_UTILIZATION_D:-0.7}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"

# [vLLM特性] NIXL(NVIDIA高性能KV缓存传输库)底层基于 UCX. 这里声明允许使用所有可用的网卡与底层传输协议.
export UCX_TLS=all
export UCX_NET_DEVICES=all

###############################################################################
# Helpers (辅助工具函数)
###############################################################################
# [BASH语法] $(git rev-parse ...): 命令替换, 动态获取当前 Git 工作流的根路径.
# [设计逻辑] 用于后续限定允许加载多模态本地图片的路径范围, 提升服务的安全性.
GIT_ROOT=$(git rev-parse --show-toplevel)

START_TIME=$(date +"%Y%m%d_%H%M%S")
ENC_LOG=$LOG_PATH/encoder_${START_TIME}.log
P_LOG=$LOG_PATH/p_${START_TIME}.log
D_LOG=$LOG_PATH/d_${START_TIME}.log
PROXY_LOG=$LOG_PATH/proxy_${START_TIME}.log

# [BASH语法] 定义健康检查函数.
# [设计逻辑] 分布式启动是一个有时序依赖的流水线. 在启动代理(Proxy)之前, 必须确保后台所有的 E/P/D 服务已经就绪并开通了 HTTP 服务.
# 内部使用 timeout 机制限制等待时长, 并在 while 循环中利用 curl 定期探测核心路由.
wait_for_server() {
    local port=$1
    timeout "$TIMEOUT_SECONDS" bash -c "
        until curl -s localhost:$port/v1/chat/completions > /dev/null; do
            sleep 1
        done" && return 0 || return 1
}

# Cleanup function (清理函数)
# [设计逻辑] 当发生异常、脚本被中断(如按 Ctrl+C)或运行正常结束时, 必须妥善杀掉所有后台常驻服务, 防止 GPU 显存泄漏和孤儿进程残留.
cleanup() {
    echo "Stopping everything…"
    trap - INT TERM USR1 # [BASH语法] 解除当前注册的信号捕获, 防止在执行 cleanup 的过程中因信号再次触发 cleanup 陷入无限递归.

    # Kill all tracked PIDs
    # [BASH语法] "${PIDS[@]}" 展开数组内所有的 PID 元素.
    # [设计逻辑] 两阶段清理策略:
    # 1. 第一阶段: 对进程先使用 "kill -0" 探测是否存在, 存在则发送 SIGTERM(默认温柔终止), 允许 vLLM 优雅退出.
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing process $pid"
            kill "$pid" 2>/dev/null
        fi
    done

    # 留给进程 2 秒的优雅保存/释放资源时间
    sleep 2

    # Force kill any remaining processes
    # 2. 第二阶段: 对依然顽固存活的进程发送 SIGKILL (kill -9) 强行杀死.
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # Kill the entire process group as backup
    # [BASH语法] kill -- -$$: 向当前 shell 进程组(Process Group)的所有进程发送终止信号(负数 PID 表示整个进程组), 作为兜底.
    kill -- -$$ 2>/dev/null

    echo "All processes stopped."
    exit 0
}

# [BASH语法] 注册信号拦截处理器. 当脚本收到 Ctrl+C (INT)、手动终止信号 (TERM) 或自定义信号 (USR1) 时, 自动调度 cleanup 函数.
trap cleanup INT
trap cleanup USR1
trap cleanup TERM

# [设计逻辑] 运行前清空残留的旧 EC(视觉 Embedding 缓存)目录, 并重新初始化, 确保实验数据隔离.
echo "remove previous ec cache folder"
rm -rf "$EC_SHARED_STORAGE_PATH"

echo "make ec cache folder"
mkdir -p "$EC_SHARED_STORAGE_PATH"

###############################################################################
# Encoder worker (启动多模态解耦架构中的: 图像编码节点)
###############################################################################
# [vLLM特性] 异构 EPD 解耦 - Encoder 阶段:
# 1. env "$DEVICE_AFFINITY_ENV=$GPU_E": 只给当前运行的进程临时注入 GPU 绑定变量.
# 2. --enforce-eager: 在多模态解耦下, 输入的图像长宽多变, CUDA Graph 的动态尺寸开销过高, 通常强制使用 Eager 模式执行.
# 3. --no-enable-prefix-caching: 视觉特征提取属于单次计算且图像随机性大, 关闭 Prompt 前缀缓存以降低内存逻辑开销.
# 4. --max-num-batched-tokens 114688: 设置较大的最大批处理 Token, 确保高分辨率多模态输入能被一次性加载解析.
# 5. --ec-transfer-config: 配置 EC(Encoder Cache)传输通道:
#    - "ec_connector": "ECExampleConnector" (在生产场景常配置为共享存储连接器 ECSharedStorageConnector).
#    - "ec_role": "ec_producer": 指定本节点作为视觉嵌入特征的生产者, 负责计算并将特征保存至 EC_SHARED_STORAGE_PATH.
env "$DEVICE_AFFINITY_ENV=$GPU_E" vllm serve "$MODEL" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION_E" \
    --port "$ENCODE_PORT" \
    --enforce-eager \
    --enable-request-id-headers \
    --no-enable-prefix-caching \
    --max-num-batched-tokens 114688 \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --allowed-local-media-path "${GIT_ROOT}"/tests/v1/ec_connector/integration \
    --ec-transfer-config '{
        "ec_connector": "ECExampleConnector",
        "ec_role": "ec_producer",
        "ec_connector_extra_config": {
            "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
        }
    }' \
    >"${ENC_LOG}" 2>&1 & # [BASH语法] 后台异步执行命令(&), 并将标准输出(stdout)与标准错误(stderr, 2>&1)重定向到日志文件中.

# [BASH语法] $! 符号表示最近一个转入后台异步运行的进程的 PID. 将它加入 PIDS 数组.
PIDS+=($!)

###############################################################################
# Prefill worker (启动多模态解耦架构中的: 计算密集型 Prefill 节点)
###############################################################################
# [vLLM特性] 异构 EPD 解耦 - Prefill 阶段:
# 1. VLLM_NIXL_SIDE_CHANNEL_PORT=5559: NixlConnector 的控制面握手带外通信端口.
# 2. --ec-transfer-config 中指定 "ec_role": "ec_consumer": 作为视觉 Embedding 的消费者. 它会从共享路径读取 Encoder 预先计算好的视觉 Embedding.
# 3. --kv-transfer-config: 指定本节点同时扮演 KV(Key-Value Cache)的传输生产者.
#    - "kv_connector": "NixlConnector": 使用 NIXL 库(一种通过高速网络直接传输张量和 KV 缓存的高性能连接器).
#    - "kv_role": "kv_producer": 代表 Prefill 完成后, 它不执行 Decode 生成步骤, 而是直接将算好的 Prompt KV 缓存通过 NIXL 快速推送到下流 Decode 节点.
env "$DEVICE_AFFINITY_ENV=$GPU_P" \
    UCX_NET_DEVICES=all \
    VLLM_NIXL_SIDE_CHANNEL_PORT=5559 \
    vllm serve "$MODEL" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION_P" \
    --port "$PREFILL_PORT" \
    --enforce-eager \
    --enable-request-id-headers \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --max-model-len "$MAX_MODEL_LEN" \
    --allowed-local-media-path "${GIT_ROOT}"/tests/v1/ec_connector/integration \
    --ec-transfer-config '{
        "ec_connector": "ECExampleConnector",
        "ec_role": "ec_consumer",
        "ec_connector_extra_config": {
            "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
        }
    }' \
    --kv-transfer-config '{
        "kv_connector": "NixlConnector",
        "kv_role": "kv_producer"
    }' \
    >"${P_LOG}" 2>&1 &

PIDS+=($!)

###############################################################################
# Decode worker (启动多模态解耦架构中的: 访存密集型 Decode 节点)
###############################################################################
# [vLLM特性] 异构 EPD 解耦 - Decode 阶段:
# 1. Decode 阶段节点不再需要配置 "--ec-transfer-config", 因为它不和原始图片、ViT 模块产生直接关联.
# 2. --kv-transfer-config 中指定 "kv_role": "kv_consumer": 作为 KV 的消费者. 它通过 NixlConnector 的零拷贝和异步传输机制接收 Prefill 发送过来的 KV 缓存.
# 3. 本节点专职进行极其高效的自回归 Token-by-token 解码计算, 由于没有 Prefill 和 Vision 阶段的抢占, 能保持稳定的低延迟.
env "$DEVICE_AFFINITY_ENV=$GPU_D" \
    UCX_NET_DEVICES=all \
    VLLM_NIXL_SIDE_CHANNEL_PORT=6000 \
    vllm serve "$MODEL" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION_D" \
    --port "$DECODE_PORT" \
    --enforce-eager \
    --enable-request-id-headers \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --max-model-len "$MAX_MODEL_LEN" \
    --allowed-local-media-path "${GIT_ROOT}"/tests/v1/ec_connector/integration \
    --kv-transfer-config '{
        "kv_connector": "NixlConnector",
        "kv_role": "kv_consumer"
    }' \
    >"${D_LOG}" 2>&1 &

PIDS+=($!)

# [设计逻辑] 按照依赖顺序阻塞, 保证底层所有微服务彻底就绪, 才会继续往下执行代理.
wait_for_server "$ENCODE_PORT"
wait_for_server "$PREFILL_PORT"
wait_for_server "$DECODE_PORT"

###############################################################################
# Proxy (启动解耦架构中控网关: EPD 路由代理)
###############################################################################
# [设计逻辑]
# 用户发起的多模态大模型请求由于包含了图片和文本, 无法由单一解耦组件独立完成.
# Proxy 进程接收客户端请求后, 先将多模态图片路由给 Encoder 节点,
# 随后在接收到特征后再把整个上下文导向 Prefill 节点, 最后由 Decode 节点输出文本流, 并由 Proxy 收集汇总吐给客户端.
python disagg_epd_proxy.py \
    --host "0.0.0.0" \
    --port "$PROXY_PORT" \
    --encode-servers-urls "http://localhost:$ENCODE_PORT" \
    --prefill-servers-urls "http://localhost:$PREFILL_PORT" \
    --decode-servers-urls "http://localhost:$DECODE_PORT" \
    >"${PROXY_LOG}" 2>&1 &

PIDS+=($!)

# [设计逻辑] 保证中控 Proxy 的健康端口可用后, 再发起 Benchmark.
wait_for_server "$PROXY_PORT"
echo "All services are up!"

###############################################################################
# Benchmark (使用官方自带工具进行性能测试)
###############################################################################
# [设计逻辑] 调用 vLLM 内置测试工具对网关 Proxy 发起 100 条多模态对话的高并发流式压力测试.
echo "Running benchmark (stream)..."
vllm bench serve \
    --model "$MODEL" \
    --backend openai-chat \
    --endpoint /v1/chat/completions \
    --dataset-name hf \
    --dataset-path lmarena-ai/VisionArena-Chat \
    --seed 0 \
    --num-prompts "$NUM_PROMPTS" \
    --port "$PROXY_PORT"

PIDS+=($!)

###############################################################################
# Single request with local image (单请求验证)
###############################################################################
# [设计逻辑] 发送一个本地非流式的多模态请求.
# 测试图像(file:// 格式)必须在 --allowed-local-media-path 的授权范围内. 用于进行全链路的逻辑冒烟测试.
echo "Running single request with local image (non-stream)..."
curl http://127.0.0.1:"${PROXY_PORT}"/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
    "model": "'"${MODEL}"'",
    "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "file://'"${GIT_ROOT}"'/tests/v1/ec_connector/integration/hato.jpg"}},
        {"type": "text", "text": "What is in this image?"}
    ]}
    ]
    }'

# cleanup
# [设计逻辑] 主流程结束, 调用清理逻辑, 优雅结束并强制清除所有驻留后台的服务进程.
echo "cleanup..."
cleanup
```

---

### 二、Bash 语法与编程范式深度解析

脚本中使用了许多高级 Bash 编程技巧, 保证了分布式测试脚本在无人值守环境下的稳定性与健壮性:

1. `set -euo pipefail`(严格模式)

   * 作用: 通过这三项配置, 只要有任何未捕获错误(包括未声明变量、命令执行失败、管道子过程故障), 脚本就会立刻中断. 这在多进程联调时极为关键, 否则如果某一环节(如 Prefill)默默启动失败, 脚本继续盲目执行后面的 Proxy, 将导致极其混乱且难以定位的超时或网络连接报错.

2. 信号捕获(`trap`)与清理范式(`cleanup`)

   * 双阶段清理机制: 在 cleanup 函数中, 通过遍历收集到的 `PIDS` 数组, 先执行 `kill -0` 探活, 之后发出 `kill`(SIGTERM). 若 2 秒内子进程未自然退出, 则升级为 `kill -9`(SIGKILL)强制清除.

   * `kill -- -$$`(进程组清理): `$$` 代表当前脚本的 PID. 负号 `-$$` 代表对该 PID 对应的整个进程组发送信号. 如果脚本有未记录在 PIDS 中的派生子进程, 此举可实行强力兜底清扫.

   * `trap - INT ...`(重入防止): 在 cleanup 入口立刻解除 trap 捕获. 因为如果不解除, 在 cleanup 运行期间由于强制 kill 动作可能会再次产生终止信号, 导致脚本死循环重复执行 cleanup, 直至栈溢出或系统异常崩溃.

3. 参数默认值展开 `${VAR:-default}`

   * 该语法支持极其便利的外部干预. 例如您可以在执行本脚本前, 在外部直接输入 `GPU_E=0 GPU_P=1 GPU_D=2 ./run.sh`, 从而快速灵活地变更 GPU 分配.

---

### 三、异构分布式推理架构设计逻辑(为什么要这么写)

为什么我们要如此繁琐地将原本单机部署的 vLLM 拆分为 Encoder、Prefill、Decode 三个独立服务, 并通过一个 Proxy 进行整合?

在传统的多模态(VLM)部署中, 这三种任务是在相同的 GPU 上排队串行处理的:

1. Vision Encoding(视觉编码): 图像通过庞大的 Vision Transformer 编码, 具有强计算(Compute-bound)但非时效(Transient)的特征.

2. Prefill(首字延迟计算): 文本与图片 Embedding 拼接, 属于计算密集型(Compute-bound), 对算力吞吐要求极高.

3. Decode(自回归解码): 生成后续 Token, 属于访存密集型(Memory-bandwidth bound), 其时延极易受到突然涌入的新请求(新 Prefill)的影响.

如果统一混合运行:

* Prefill 会导致 Decode 发生严重的排队(泡泡效应), 引发极高的时间抖动.

* 视觉多模态模型的图像尺寸通常多变, 这与 LLM 的文本静态尺寸不契合, 难以在一个实例中高效调度.

通过 EPD 解耦后:

* Encoder 独占低配卡(因为内存要求极低, 不存 KV 缓存, 只做 Vision 模型计算), 将 Embedding 保存下来.

* Prefill 接收 Embedding 并仅完成密集的前向传播计算(即 Prompt 处理).

* Decode 卡上只存放纯粹的自回归生成状态, 没有长图像计算、没有大 Batch 首字计算. 它通过高速网络(NIXL / RDMA)直接在几毫秒内接收到 Prefill 发来的 KV 缓存, 保证了极其稳定、低延迟的文本生成过程.

* Proxy 逻辑 充当了"编排大脑", 将图像流、文本流、KV 传输、最终流式文本在各个组件之间进行完美拼装.

---

### 四、vLLM 核心参数技术解读

1. `--ec-transfer-config`(Encoder 缓存传输配置)

   * `ec_connector`: `ECExampleConnector` / `ECSharedStorageConnector`. 它定义了多模态模型中"视觉 Embedding"的持久化与传输实现. 这里是通过共享文件系统(如 NVMe 上的共享路径)来实现近乎零延迟的物理媒介共享.

   * `ec_role`: 生产者(`ec_producer`)和消费者(`ec_consumer`)互相配合. Encoder 算完写入, Prefill 读出.

2. `--kv-transfer-config`(KV 缓存传输配置)

   * `kv_connector`: `NixlConnector`. 这是 vLLM 中非常强大的高级网络传输模块, 专门用于解耦 Prefill 和 Decode.

   * NIXL 充分利用底层的 UCX(Unified Communication X)网络栈, 如果硬件支持, 它能在 GPU 之间进行 GPUDirect RDMA 级别的跨网卡异步传输, 将原本因长文本产生的大容量 KV Cache, 以高达数十 GB/s 的线速在不同卡的显存间直接移动, 不经过 CPU 中转, 从而使得跨卡、跨机器的 PD 解耦延迟降低到可忽略不计.

   * `VLLM_NIXL_SIDE_CHANNEL_PORT`: 为 NIXL 在跨卡交互时分配的控制面握手带外端口, 避免多 Worker 端口打架.

3. `--gpu-memory-utilization` 分配不对称

   * 这是最能体现您对 vLLM 显存分配极其纯熟的一点. Encoder 仅设置 `0.01`, 因为它是彻底的 Stateless 节点, 完全不需要预留存放历史交互 KV 块的 PagedAttention 显存池；而 P 节点和 D 节点因为要应对持续并发的 Token 缓存, 需要分配更高的 `0.7` 来尽量扩大 KV Page 的容量.

----------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 bash 脚本用于 vllm 的相关功能
```
# disagg_1e1pd_example.sh

```
请为这个脚本添加注释, 一是说明 bash 脚本的一些语法, 二是说明为什么要这么写, 三是说明 vllm 的相关特性和参数含义

这份 Bash 脚本实现了一种针对多模态视觉语言模型(VLM)的"两阶段异构解耦"部署方案(即 Encoder 与 LLM Prefill+Decode 分离). 与三阶段的 EPD(Encoder-Prefill-Decode)完全解耦不同, 此方案将文本 Prefill 与自回归 Decode 放在同一个 Worker 上运行(统称为 PD 节点), 仅将极其耗费计算资源且输入尺寸多变的视觉编码(Encoder)剥离到独立的卡上.

以下为您提供详细的代码中文注释以及背后技术细节的深度剖析.

---

### 一、带多维度中文注释的完整脚本

```bash
#!/bin/bash
# ==============================================================================
# [BASH语法] 启用严格执行模式
# -e: 任何单条命令返回非零(失败)状态时, 脚本立即终止退出, 防止错误向后传递.
# -u: 遇到未声明或未定义的变量时直接报错, 避免由于拼写错误导致非预期行为.
# -o pipefail: 只要管道命令中任何一个子命令失败, 整个管道就返回失败状态.
# ==============================================================================
set -euo pipefail

# [BASH语法] 显式声明一个索引数组 PIDS, 用于存储所有后台进程的 PID.
# [设计逻辑] 方便在脚本结束或收到退出信号时, 通过 PID 统一进行资源回收.
declare -a PIDS=()

###############################################################################
# Configuration -- 默认配置, 支持在运行前通过外部环境变量进行覆盖
###############################################################################
# [BASH语法] ${VAR:-default}: 变量默认值展开. 若 $MODEL 未定义, 则默认使用 Qwen2.5-VL 3B 实例.
MODEL="${MODEL:-Qwen/Qwen2.5-VL-3B-Instruct}"
LOG_PATH="${LOG_PATH:-./logs}"

# [设计逻辑] 自动创建日志存储目录, 避免后续在后台重定向标准输出时由于文件夹不存在而报错.
mkdir -p "$LOG_PATH"

# [设计逻辑] 定义组件端口. 由于此处是两阶段解耦, 所以只需要 Encoder 端口、PD 统一端口和 Proxy 代理端口.
ENCODE_PORT="${ENCODE_PORT:-19534}"
PREFILL_DECODE_PORT="${PREFILL_DECODE_PORT:-19535}"
PROXY_PORT="${PROXY_PORT:-10001}"

# [设计逻辑] 分配 GPU 设备. 此处仅需两张卡(或一块卡分两个实例), GPU_E 用于 Vision 编码, GPU_PD 用于 LLM 生成.
GPU_E="${GPU_E:-0}"
GPU_PD="${GPU_PD:-1}"

# Device platform and affinity env name.
# DEVICE_PLATFORM supports: cuda, xpu
# [设计逻辑] 兼容不同的异构计算硬件平台.
DEVICE_PLATFORM="${DEVICE_PLATFORM:-cuda}"
if [[ -z "${DEVICE_AFFINITY_ENV:-}" ]]; then
    # [BASH语法] ${DEVICE_PLATFORM,,}: 将变量字符串内所有大写字母转为小写.
    if [[ "${DEVICE_PLATFORM,,}" == "xpu" ]]; then
        # 针对英特尔 XPU 的 GPU 设备隔离变量
        DEVICE_AFFINITY_ENV="ZE_AFFINITY_MASK"
    else
        # 针对 NVIDIA CUDA 的 GPU 设备隔离变量
        DEVICE_AFFINITY_ENV="CUDA_VISIBLE_DEVICES"
    fi
fi

# [vLLM特性] EC(Encoder Cache)共享存储路径.
# Encoder (E) 节点计算出的图像视觉特征向量(Embedding)会序列化存放在此目录, 供 PD 节点快速读取.
EC_SHARED_STORAGE_PATH="${EC_SHARED_STORAGE_PATH:-/tmp/ec_cache}"

# [设计逻辑] 等待服务端口响应的超时阈值(秒).
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-12000}"

NUM_PROMPTS="${NUM_PROMPTS:-100}" # 基准测试时向服务器发送的样本总数

# Serve args (vLLM 服务参数配置)
# [vLLM特性] 显存利用率配置. 由于两阶段分工不同, 显存占用策略差异巨大:
# - Encoder(E)仅运行 Vision Transformer, 不保留文本 KV Cache 空间, 因此显存需求极低(分配 1% 即可).
# - PD 节点承载了完整的 LLM 解码, 需要大量空间来装载模型参数并管理 PagedAttention 缓存, 因此分配较大比例(70%).
GPU_MEMORY_UTILIZATION_E="${GPU_MEMORY_UTILIZATION_E:-0.01}"
GPU_MEMORY_UTILIZATION_PD="${GPU_MEMORY_UTILIZATION_PD:-0.7}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"

###############################################################################
# Helpers (辅助工具函数)
###############################################################################
# [BASH语法] 命令替换 $(git ...), 动态计算当前 Git 仓库的根路径.
# [设计逻辑] 用于确保在后续加载本地图像文件时, 路径指向始终与仓库结构保持一致.
GIT_ROOT=$(git rev-parse --show-toplevel)

START_TIME=$(date +"%Y%m%d_%H%M%S")
ENC_LOG=$LOG_PATH/encoder_${START_TIME}.log
PD_LOG=$LOG_PATH/pd_${START_TIME}.log
PROXY_LOG=$LOG_PATH/proxy_${START_TIME}.log

# [BASH语法] 定义检测服务器就绪状态的函数.
# [设计逻辑] 轮询指定的 HTTP 接口. 直到 curl 返回状态码 200 或达到超时, 函数才会退出, 用于保障多进程顺序链条的安全启动.
wait_for_server() {
    local port=$1
    timeout "$TIMEOUT_SECONDS" bash -c "
        until curl -s localhost:$port/v1/chat/completions > /dev/null; do
            sleep 1
        done" && return 0 || return 1
}

# Cleanup function (资源安全清理函数)
# [设计逻辑] 发生任何退出信号(中断、强制杀死或正常退出)时, 自动触发垃圾回收, 彻底杀死所有派生的后台微服务进程.
cleanup() {
    echo "Stopping everything…"
    trap - INT TERM USR1 # [BASH语法] 临时取消信号捕获, 避免在清理资源期间发生重入和死循环.

    # Kill all tracked PIDs
    # [BASH语法] "${PIDS[@]}" 展开数组. 第一阶段先通过 kill -0 测试进程是否存在, 若存在则尝试友好关闭(SIGTERM).
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing process $pid"
            kill "$pid" 2>/dev/null
        fi
    done

    # 给进程留出 2 秒用于释放 GPU 显存和关闭句柄
    sleep 2

    # Force kill any remaining processes
    # 第二阶段: 如果 2 秒后依然有存活进程, 则升级为 kill -9(SIGKILL)物理清除.
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # Kill the entire process group as backup
    # [BASH语法] kill -- -$$: 向当前 shell 的整个进程组(Process Group ID 等同于主进程的 PID)发送终止信号, 确保无孤儿进程.
    kill -- -$$ 2>/dev/null

    echo "All processes stopped."
    exit 0
}

# [BASH语法] 注册信号陷阱. 当脚本接收到 Ctrl+C (INT)、终端关闭 (TERM) 或用户自定义信号 (USR1) 时触发 cleanup.
trap cleanup INT
trap cleanup USR1
trap cleanup TERM

# clear previous cache
# [设计逻辑] 每次启动前, 必须清理旧的共享磁盘缓存, 防止由于残留的脏数据导致 PD 节点误读取.
echo "remove previous ec cache folder"
rm -rf "$EC_SHARED_STORAGE_PATH"

echo "make ec cache folder"
mkdir -p "$EC_SHARED_STORAGE_PATH"

###############################################################################
# Encoder worker (启动图像特征编码实例)
###############################################################################
# [vLLM特性] 图像 Encoder 节点:
# 1. env "$DEVICE_AFFINITY_ENV=$GPU_E": 隔离当前进程使用的 GPU(通常单卡运行).
# 2. --no-enable-prefix-caching: 多模态图像分辨率与输入具备随机性, 视觉 embedding 极少命中 Prefix Cache, 关闭可节省管理开销.
# 3. --max-num-batched-tokens 114688: 多模态大图编码时单次产生的 token 数量庞大, 必须设大此阈值.
# 4. --ec-transfer-config 中 "ec_role": "ec_producer": 标志该节点扮演视觉特征的生成者. 它执行 Qwen2.5-VL 中的 ViT 部分, 提取完特征后写入 `EC_SHARED_STORAGE_PATH` 路径.
env "$DEVICE_AFFINITY_ENV=$GPU_E" vllm serve "$MODEL" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION_E" \
    --port "$ENCODE_PORT" \
    --enforce-eager \
    --enable-request-id-headers \
    --no-enable-prefix-caching \
    --max-num-batched-tokens 114688 \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --allowed-local-media-path "${GIT_ROOT}"/tests/v1/ec_connector/integration \
    --ec-transfer-config '{
        "ec_connector": "ECExampleConnector",
        "ec_role": "ec_producer",
        "ec_connector_extra_config": {
            "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
        }
    }' \
    >"${ENC_LOG}" 2>&1 & # [BASH语法] & 表示在后台异步运行, 同时利用 > 结合 2>&1 将 stdout 与 stderr 合并重定向写入日志.

# [BASH语法] $! 存储最近一个后台进程的 PID, 并将其加入 PIDS 数组.
PIDS+=($!)

###############################################################################
# Prefill+Decode worker (启动统一的 LLM 生成实例)
###############################################################################
# [vLLM特性] 统一的 PD 节点:
# 1. 在此架构下, 该实例不拆分 Prefill 和 Decode, 因此无需配置复杂的网络库连接器(如 NixlConnector ).
# 2. --ec-transfer-config 中 "ec_role": "ec_consumer": 标志该节点扮演视觉特征的消费者. 它在开始计算首字(Prefill)时, 会自动读取由 Encoder 生成并存放在共享目录的视觉特征数据, 然后将特征直接塞入 LLM 的 context 窗口.
env "$DEVICE_AFFINITY_ENV=$GPU_PD" vllm serve "$MODEL" \
    --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION_PD" \
    --port "$PREFILL_DECODE_PORT" \
    --enforce-eager \
    --enable-request-id-headers \
    --max-num-seqs "$MAX_NUM_SEQS" \
    --max-model-len "$MAX_MODEL_LEN" \
    --allowed-local-media-path "${GIT_ROOT}"/tests/v1/ec_connector/integration \
    --ec-transfer-config '{
        "ec_connector": "ECExampleConnector",
        "ec_role": "ec_consumer",
        "ec_connector_extra_config": {
            "shared_storage_path": "'"$EC_SHARED_STORAGE_PATH"'"
        }
    }' \
    >"${PD_LOG}" 2>&1 &

PIDS+=($!)

# Wait for workers
# [设计逻辑] 按照调用链拓扑阻塞等待, 保障底层服务的端口可用.
wait_for_server "$ENCODE_PORT"
wait_for_server "$PREFILL_DECODE_PORT"

###############################################################################
# Proxy (中控路由网关)
###############################################################################
# [设计逻辑]
# 由于系统进行了两阶段解耦, 用户的 HTTP 请求需要先拆解、再聚合:
# --encode-servers-urls: 告知网关将输入图像路由给 Encoder 提取特征.
# --prefill-servers-urls "disable": 极关键的配置. 通知网关, 在整个集群中没有物理独立的纯 Prefill 实例,
#                                   因此网关不应把 prefill 和 decode 阶段分发给不同的端点.
# --decode-servers-urls: 告知网关, 当首字处理(Prefill)与随后的自回归解码(Decode)由同一个节点执行时, 直接向该端口发起文本生成任务.
python disagg_epd_proxy.py \
    --host "0.0.0.0" \
    --port "$PROXY_PORT" \
    --encode-servers-urls "http://localhost:$ENCODE_PORT" \
    --prefill-servers-urls "disable" \
    --decode-servers-urls "http://localhost:$PREFILL_DECODE_PORT" \
    >"${PROXY_LOG}" 2>&1 &

PIDS+=($!)

# 等待 Proxy 就绪
wait_for_server "$PROXY_PORT"
echo "All services are up!"

###############################################################################
# Benchmark (并发性能基准测试)
###############################################################################
# [设计逻辑] 使用内置的压力测试工具, 向代理端口并发发送 100 条包含图像的多模态对话请求.
echo "Running benchmark (stream)..."
vllm bench serve \
    --model "$MODEL" \
    --backend openai-chat \
    --endpoint /v1/chat/completions \
    --dataset-name hf \
    --dataset-path lmarena-ai/VisionArena-Chat \
    --seed 0 \
    --num-prompts "$NUM_PROMPTS" \
    --port "$PROXY_PORT"

PIDS+=($!)

###############################################################################
# Single request with local image (全链路冒烟测试)
###############################################################################
# [设计逻辑] 发送一个真实的本地单图 HTTP 多模态请求, 用于对上述两阶段架构进行功能性端到端验证.
echo "Running single request with local image (non-stream)..."
curl http://127.0.0.1:"${PROXY_PORT}"/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
    "model": "'"${MODEL}"'",
    "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "file://'"${GIT_ROOT}"'/tests/v1/ec_connector/integration/hato.jpg"}},
        {"type": "text", "text": "What is in this image?"}
    ]}
    ]
    }'

# cleanup
# [设计逻辑] 完成测试后调用清理, 保障环境不发生资源或显存泄露.
echo "cleanup..."
cleanup
```

---

### 二、核心 Bash 语法解析

1. `set -euo pipefail` 策略:

   在编写多进程、分布式 AI 部署脚本时, 这是通用的生产级实践. 没有此设置, 如果某一个节点(例如 GPU 1 上的 PD 节点)因为显存爆满而未能成功启动, 脚本仍会盲目执行 Proxy 代理, 最终导致漫长的超时等待, 增加排查难度.

2. `PIDS+=($!)` 数组追踪机制:

   在后台启动一个异步进程(带 `&`)时, Bash 变量 `$!` 会捕捉到该子进程的 PID. 通过 `declare -a` 声明的数组, 我们将每一个组件(Encoder、PD、Proxy、Benchmark)的生命周期都记录在案.

3. `kill -- -$$` 强制清理:

   这是多进程 Shell 脚本中的高级防残留手段. 如果后台启动的进程本身又派生了子进程(例如 Python 下的多进程进程池), 单纯 `kill <pid>` 可能会使子进程沦为孤儿. 通过发送给 `-$$`(当前进程组), 可以确保主进程派生的所有关联子孙进程一次性被清理.

---

### 三、架构设计逻辑解析: 为什么不进行"完全解耦"?

与完整的三阶段解耦(Encoder, Prefill, Decode 相互物理独立)相比, 这份脚本实现的 两阶段解耦(Encoder 与 PD 统合) 架构设计有其独特的工程价值:

#### 1. 降低网络带宽要求与复杂性

在三阶段完全解耦下, 计算完 Prefill 的节点必须通过高性能通道(如 NixlConnector、RDMA、UCX 网卡)将大规模的 KV Cache(数十 GB/s 级别)传输给 Decode 节点. 如果硬件条件没有配备昂贵的高速 Infiniband 或 RoCE 网络, KV Cache 传输的开销可能会抵消解耦带来的性能收益.

而在两阶段架构下, Prefill 和 Decode 发生在一张卡或一个实例上(`GPU_PD`), 不产生任何 KV 传输, 只存在少量的视觉 Embedding 共享.

#### 2. 多模态瓶颈主要在 Encoder (ViT)

对于 Qwen2.5-VL 这样的大型视觉语言模型, 单张大图在 ViT 层(编码阶段)的前向传播会产生极大的瞬时计算瓶颈, 并阻碍 LLM 本身自回归生成的流式响应. 通过将 Encoder 完全挪出, LLM 节点(PD 节点)可以获得以下优势:

* 更平滑的延迟响应: 不再需要在同一个 GPU 上交替调度耗时的 3D 视觉注意力计算与轻量的自回归 Token 生成.

* 显存分配的高内聚性: Encoder 的显存需求与图像分辨率正相关且极具抖动；而 PD 的显存由 LLM 层数及 KV 空间决定. 将两者完全拆开后, 可避免由于大图输入导致 PD 节点发生 OOM(显存溢出).

---

### 四、vLLM 特性与参数深度释义

1. `--ec-transfer-config` (Encoder Cache 传输)

   * `ec_connector`: 脚本中使用了 `ECExampleConnector`(或生产环境中的 `ECSharedStorageConnector`), 它是利用磁盘/内存映射(Shared Memory)等本地共享媒介对 Embedding 向量进行高速中转.

   * `ec_role`:

      * `ec_producer` (Encoder 节点): ViT 提取特征后把结果落盘.

      * `ec_consumer` (PD 节点): LLM 接受到文本请求时, 根据 Request ID 直接从共享目录提取特征载入 LLM 关联的第一个 Token 位置.

2. `--prefill-servers-urls "disable"`

   * 这是 `disagg_epd_proxy.py` 脚本的关键参数. 它通知路由网关: "系统中没有只做 Prefill 运算的实例". 当网关面对需要生成新 Token 的多模态请求时, 它会先将图片解析交给 `encode-servers`；收到视觉向量标志后, 将剩余的 Prefill 计算与 Decode 文本流生成任务完整托付给同一台 `decode-servers`(即 PD 节点).

3. 不对称的显存利用率 (`--gpu-memory-utilization`)

   * `GPU_MEMORY_UTILIZATION_E=0.01` (1%): Encoder 仅仅执行 Vision 计算, 不需要预分配 PagedAttention 显存池(该池是给 LLM 存 KV 缓存用的), 1% 的显存已经足够其静态计算. 这使得该卡的大量剩余显存可以分配给其他任务, 或者甚至在低配、廉价的显卡上运行.

   * `GPU_MEMORY_UTILIZATION_PD=0.7` (70%): 运行完整的 LLM 解码, 需要大量显存保存模型的自回归状态, 因此必须预留大部分资源.

----------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 python 脚本用于运行 vllm EPD 分离的协调代理
```
# disagg_epd_proxy.py

```
请为这个脚本添加注释, 一是说明为什么要这么写, 二是说明其中一些深层次的原理

这个代理服务器(Proxy)是 vLLM 在执行多模态解耦推理(EPD: Encoder-Prefill-Decode Disaggregation)时的中控大脑. 它并不直接处理复杂的张量(Tensor)或 KV 缓存(KV Cache), 而是通过轻量级的控制流(Control Plane), 编排并协调物理隔离的 Encoder 节点、Prefill 节点和 Decode 节点.

以下为您提供添加了详尽技术内幕注释的完整 Python 脚本, 并在脚本后面对其中蕴含的深层次原理进行了全面、客观的技术剖析.

---

### 一、核心代理脚本(带深层原理与设计目的注释)

```python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
disagg_encoder_proxy.py

[设计目的]
该代理服务是多模态 EPD 解耦的核心路由器. 用户只需要像往常一样向该 Proxy
发送 OpenAI 兼容的 API 请求, Proxy 内部会将复杂的 Vision 提取、LLM 文本首字预计算(Prefill)
以及流式自回归生成(Decode)拆分到不同的物理实例运行, 从而将不兼容的计算模式完美隔离开.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import uuid
from collections.abc import AsyncIterator

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

###############################################################################
# FastAPI app & global state
###############################################################################

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s"
)
logger = logging.getLogger("proxy")

app = FastAPI()
# [设计目的] 建立物理隔离的服务连接池.
# 分别维护连接到 Encoder、Prefill、Decode 物理集群的长连接会话, 防止高并发下频繁建立 TCP 连接带来的时延.
encode_session: aiohttp.ClientSession | None = None
prefill_session: aiohttp.ClientSession | None = None
decode_session: aiohttp.ClientSession | None = None

###############################################################################
# Utils
###############################################################################

# 多模态媒体类型定义
MM_TYPES = {"image_url", "audio_url", "input_audio"}


def extract_mm_items(request_data: dict) -> list[dict]:
    """
    [设计目的]
    快速扫描并剥离出整个请求消息历史(messages)中的所有多模态对象(图片、音频等).
    """
    items: list[dict] = []
    for msg in request_data.get("messages", []):
        content = msg.get("content")
        if not isinstance(content, list):
            continue

        for item in content:
            if item.get("type") in MM_TYPES:
                items.append(item)
    return items


async def fanout_encoder_primer(
    orig_request: dict,
    e_urls: list[str],
    req_id: str,
) -> None:
    """
    [设计目的]
    并行触发多模态特征提取. 如果有 N 张图, Proxy 会将 N 张图拆分并并行派发给物理 Encoder 集群.

    [深层原理 - 为什么要把文本全部移除, 且 max_tokens 设为 1?]
    1. 文本剥离: Encoder 节点物理上只装载并执行多模态大模型的视觉部分(例如 ViT). 它不需要、也无法执行 LLM 文本计算.
    2. max_tokens=1: 强制 vLLM 在执行完多模态图像特征提取并写入 EC 共享缓存(Encoder Cache)后立即退出.
    3. 避免无效算力浪费: 如果不设 max_tokens=1 或不剥离文本, Encoder 节点会尝试对整段 Prompt 执行多模态自回归文本生成, 这与解耦设计完全相悖.
    """
    logger.info("[%s] Processing multimodal items...", req_id)

    mm_items = extract_mm_items(orig_request)
    if not mm_items:
        logger.info("[%s] No multimodal items, skipping encoder", req_id)
        return  # 没有多模态图像/音频, 直接跳过视觉提取节点

    logger.info("[%s] got %d multimodal items...", req_id, len(mm_items))

    tasks = []

    # [设计目的] 轮询(Round-Robin)分发负载.
    # 当单次请求包含多张大图(例如相册多轮对话)时, 将图片均匀打散到 Encoder 物理集群的多台实例上并行处理, 实现计算级负载均衡.
    url_cycle = (e_urls[i % len(e_urls)] for i in range(len(mm_items)))

    for idx, (item, target_url) in enumerate(zip(mm_items, url_cycle)):
        # [设计逻辑] 生成可追踪的子请求 ID. 在分布式系统中, 这能极大地方便开发人员通过日志检索某张图在哪个节点上出错.
        child_req_id = f"{req_id}:{idx}:{uuid.uuid4().hex[:6]}"
        headers = {"x-request-id": child_req_id}

        # 构造一个纯净的视觉处理请求, 只包含单张图, 不含任何 LLM 文本 prompt
        encoder_req = {
            "model": orig_request.get("model"),
            "messages": [
                {"role": "user", "content": [item]},
            ],
            "max_tokens": 1,
            "stream": False,
        }
        tasks.append(
            encode_session.post(
                f"{target_url}/v1/chat/completions",
                json=encoder_req,
                headers=headers,
            )
        )

    # [深层原理] 异步并发执行.
    # 多媒体数据的传输和 ViT 的前向传播需要耗费数十毫秒甚至数百毫秒. 使用 asyncio.gather 并发处理,
    # 可保证处理多图请求的时间瓶颈仅取决于单张图的最慢处理时间(O(1) 延迟开销), 而不是串行堆叠.
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 快速失败响应机制(Fail-fast)
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(
                "[%s] Encoder request #%d raised exception: %s",
                req_id, idx, r, exc_info=r,
            )
            raise HTTPException(
                status_code=502, detail=f"Encoder request failed: {str(r)}"
            )
        if r.status != 200:
            try:
                detail = await r.text()
            except Exception:
                detail = "<unable to read body>"
            logger.error(
                "[%s] Encoder request #%d returned status %s: %s",
                req_id, idx, r.status, detail,
            )
            raise HTTPException(
                status_code=r.status,
                detail=f"Encoder request failed: {detail}",
            )

    logger.info(
        "[%s] All %d encoder requests completed successfully", req_id, len(mm_items)
    )


async def maybe_prefill(
    req_data: dict,
    p_url: str,
    req_id: str,
) -> dict:
    """
    [设计目的]
    决定是执行 E->P->D(三阶段解耦)还是 E->PD(两阶段解耦).
    如果用户显式关闭了物理 Prefill 节点(p_url 为空), 则不进行任何干预, 直接原样下发给后续 PD 节点.
    """
    if p_url:
        logger.info("[%s] Processing through prefill: %s", req_id, p_url)

        # 驱动物理 Prefill 阶段进行文本首字计算
        prefill_response = await process_prefill_stage(req_data, p_url, req_id)

        # [深层原理 - 桥接控制信号]
        # Prefill 节点在物理显存中计算完本次 Prompt 的 KV Cache 后, 不会执行 Decode,
        # 而是将物理显存的虚拟指针、存储块(Block)地址映射以及网络直连协议等元数据, 打包封装在 `kv_transfer_params` 中返回给 Proxy.
        prefill_response_json = await prefill_response.json()
        kv_transfer_params = prefill_response_json.get("kv_transfer_params", {})

        if kv_transfer_params:
            # 将该传输参数动态注入请求体中, 以通知下流的 Decode 节点执行高速 RDMA 直接读取
            req_data["kv_transfer_params"] = kv_transfer_params

        return req_data
    else:
        return req_data


async def process_prefill_stage(
    req_data: dict,
    p_url: str,
    req_id: str,
) -> dict:
    """
    [深层原理 - 驱动离线 Prefill 计算并准备跨节点传输]
    1. 复制原请求: 保留模型设置和文本 prompt, 因为 Prefill 节点需要读取文本以及从 EC 存储中读取多模态图像 Embedding.
    2. 注入特定参数:
       - `do_remote_decode = True` & `do_remote_prefill = False`: 告知 Prefill 节点, “你只需要计算首字 KV 缓存并准备异步网络推送, 后续生成不要由你执行”.
    3. max_tokens=1: 同样强制 Prefill 节点在首字预热完毕并生成网络传输句柄后, 立即释放当前请求执行上下文.
    """
    logger.info("[%s] Sending prefill request to: %s", req_id, p_url)

    prefill_request = req_data.copy()
    prefill_request["kv_transfer_params"] = {
        "do_remote_decode": True,
        "do_remote_prefill": False,
        "remote_engine_id": None,
        "remote_block_ids": None,
        "remote_host": None,
        "remote_port": None,
    }
    prefill_request["stream"] = False
    prefill_request["max_tokens"] = 1
    if "max_completion_tokens" in prefill_request:
        prefill_request["max_completion_tokens"] = 1
    if "stream_options" in prefill_request:
        del prefill_request["stream_options"]

    headers = {"x-request-id": req_id}
    try:
        prefill_response = await prefill_session.post(
            f"{p_url}/v1/chat/completions", json=prefill_request, headers=headers
        )
        prefill_response.raise_for_status()

        if prefill_response.status != 200:
            error_text = await prefill_response.text()
            logger.error(
                "[%s] Prefill request failed with status %d: %s",
                req_id, prefill_response.status, error_text,
            )
            raise HTTPException(
                status_code=prefill_response.status,
                detail={"error": "Prefill request failed", "message": error_text},
            )
        logger.info("[%s] Prefill request completed successfully", req_id)

        return prefill_response

    except Exception as e:
        logger.error("Prefill processing failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "Prefill processing error", "message": str(e)},
        ) from e


###############################################################################
# Middleware for request/response logging (全局请求生命周期追踪中间件)
###############################################################################


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    [设计目的]
    全局 Trace 中间件. 在异步高并发代理中, 成百上千个请求的日志会完全交织在一起.
    引入唯一的 x-request-id 头能将整条分布式链路(Proxy -> E -> P -> D)的所有事件聚合排查.
    """
    req_id = request.headers.get("x-request-id", str(uuid.uuid4()))

    logger.info(
        ">>> [%s] %s %s from %s",
        req_id, request.method, request.url.path,
        request.client.host if request.client else "unknown",
    )

    try:
        response = await call_next(request)
        logger.info(
            "<<< [%s] %s %s completed with status %d",
            req_id, request.method, request.url.path, response.status_code,
        )
        return response
    except Exception as e:
        logger.exception(
            "!!! [%s] %s %s failed with error: %s",
            req_id, request.method, request.url.path, str(e),
        )
        raise


###############################################################################
# FastAPI lifecycle (高并发网络吞吐性能优化)
###############################################################################


@app.on_event("startup")
async def on_startup() -> None:
    """
    [深层原理 - 异步 HTTP 吞吐极限优化配置]
    1. limit=0: 禁用 aiohttp 内部的连接数上限限制. 在高并发微服务网关中, 如果限制连接池大小, 会导致大量并发请求在
       TCP 握手队列上排队(Head-of-Line Blocking), 从而极大地增加首字延迟(TTFT).
    2. force_close=False: 强制启用 HTTP Keep-Alive 连接复用, 杜绝每一次请求都重新发起 TCP 三次握手和 TLS 协商.
    """
    global encode_session, prefill_session, decode_session
    timeout = aiohttp.ClientTimeout(total=100_000)
    connector = aiohttp.TCPConnector(limit=0, force_close=False)
    encode_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    if app.state.p_urls:
        prefill_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    decode_session = aiohttp.ClientSession(timeout=timeout, connector=connector)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """优雅地关闭连接池, 防止断开网络插槽(Socket)导致底层通信异常. """
    global encode_session, prefill_session, decode_session
    if encode_session:
        await encode_session.close()
    if prefill_session:
        await prefill_session.close()
    if decode_session:
        await decode_session.close()


###############################################################################
# Core forwarding (核心请求级协调转发引擎)
###############################################################################


async def forward_non_stream(
    req_data: dict, req_id: str, e_urls: list[str], p_url: str, d_url: str
) -> dict:
    """
    [设计目的] 协调非流式请求
    """
    try:
        # Step 1: 先提取原始请求中的所有视觉多媒体, 多播发给物理 Encoder 集群, 生成视觉 embedding 写入 EC
        await fanout_encoder_primer(req_data, e_urls, req_id)

        # Step 2: 驱动 Prefill 节点读取视觉特征, 并在物理卡上预热 prompt 并导出 KV Cache 元数据
        req_data = await maybe_prefill(req_data, p_url, req_id)

        # Step 3: 向 Decode 节点发送最终的文本生成任务
        # 如果存在 Step 2, 此时 req_data 内已经封装了物理 KV 缓存跨节点读取的技术句柄.
        # Decode 节点在收到该请求后, 直接通过 Nixl 网卡通道零拷贝(Zero-copy)拉取 KV Cache 并执行自回归推理.
        logger.info("[%s] Forwarding to decode: %s", req_id, d_url)
        headers = {"x-request-id": req_id}

        async with decode_session.post(
            f"{d_url}/v1/chat/completions", json=req_data, headers=headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[%s] Error in forward_non_stream: %s", req_id, str(e))
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}") from e


async def forward_stream(
    req_data: dict, req_id: str, e_urls: list[str], p_url: str, d_url: str
) -> AsyncIterator[str]:
    """
    [设计目的] 协调高并发流式(Stream)请求.

    [深层原理 - 异步流式背压机制]
    虽然解耦了 Encoder 和 Prefill, 但流式请求(Token-by-token 输出)由 Decode 节点掌控.
    使用 AsyncIterator 包装 resp.content.iter_chunked 可以在不堵塞 Python 主线程的前提下,
    保持与 Decode 实例的高速流式数据块(chunks)中转, 直接将生成结果推回用户端.
    """
    try:
        await fanout_encoder_primer(req_data, e_urls, req_id)
        req_data = await maybe_prefill(req_data, p_url, req_id)

        logger.info("[%s] Starting streaming from decode: %s", req_id, d_url)
        headers = {"x-request-id": req_id}

        async with decode_session.post(
            f"{d_url}/v1/chat/completions",
            json=req_data,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for chunk in resp.content.iter_chunked(1024):
                if chunk:
                    # 使用 utf-8 容错解码(ignore), 防止流式响应发生断句字节截断时抛出致命异常
                    yield chunk.decode("utf-8", errors="ignore")

        logger.info("[%s] Streaming completed", req_id)

    except HTTPException:
        logger.exception("[%s] HTTPException in forward_stream", req_id)
        raise
    except Exception as e:
        logger.exception("[%s] Error in forward_stream: %s", req_id, str(e))
        raise HTTPException(
            status_code=500, detail=f"Proxy streaming error: {str(e)}"
        ) from e


###############################################################################
# Public routes
###############################################################################


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    [设计目的]
    OpenAI 兼容的标准微服务总网关. 外部客户端无法感知后端极其复杂的解耦实现, 在此抹平异构细节.
    """
    try:
        req_data = await request.json()
        req_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        e_urls = app.state.e_urls  # 全量获取 Encoder 节点的端口, 用作 fan-out 多路并行派发

        # [设计目的]
        # 对 Prefill 和 Decode 集群进行随机负载均衡(random.choice),
        # 极大地简化了微服务负载均衡器的部署, 实现了请求级的流量横向平铺.
        p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
        d_url = random.choice(app.state.d_urls)

        is_streaming = req_data.get("stream", False)

        if is_streaming:
            return StreamingResponse(
                forward_stream(req_data, req_id, e_urls, p_url, d_url),
                media_type="text/event-stream",
            )
        result = await forward_non_stream(req_data, req_id, e_urls, p_url, d_url)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in chat_completions endpoint: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Request processing error: {str(e)}"
        ) from e


@app.get("/v1/models")
async def list_models():
    """代理路由: 获取当前运行的模型. 直接向下游实例转发请求以实现接口一致. """
    async with decode_session.get(f"{app.state.d_urls[0]}/v1/models") as resp:
        resp.raise_for_status()
        return await resp.json()


@app.get("/health")
async def health_check():
    """
    [设计目的] 分布式集群联合健康状态监控.
    如果后端三个物理集群中有一个处于异常不可用状态, 则立刻对外界返回 503 (Service Unavailable),
    以触发诸如 Kubernetes 等容器管理平台的自动故障迁移(Failover).
    """
    async def healthy(urls):
        if not urls:
            return "empty"
        for u in urls:
            try:
                async with encode_session.get(f"{u}/health") as resp:
                    resp.raise_for_status()
            except Exception:
                return "unhealthy"
        return "healthy"

    # 并发查询各物理组件集群的健康状况
    e_status, p_status, d_status = await asyncio.gather(
        healthy(app.state.e_urls), healthy(app.state.p_urls), healthy(app.state.d_urls)
    )

    overall_healthy = all(
        status != "unhealthy" for status in (e_status, p_status, d_status)
    )

    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        {
            "proxy": "healthy",
            "encode_cluster": e_status,
            "prefill_cluster": p_status,
            "decode_cluster": d_status,
        },
        status_code=status_code,
    )


###############################################################################
# Simple profiler fan-out (性能遥测数据采集)
###############################################################################


async def _post_if_available(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
    headers: dict,
) -> dict | None:
    """
    [设计目的]
    一个支持容错的遥测命令发送管道. 在未启用 profiling 的测试节点上直接静默忽略 404, 防止阻塞主体.
    """
    try:
        resp = await session.post(url, json=payload, headers=headers)
        if resp.status == 404:
            logger.warning("Profiling endpoint missing on %s", url)
            return None
        resp.raise_for_status()
        return await resp.json(content_type=None)
    except aiohttp.ClientResponseError as exc:
        if exc.status == 404:
            logger.warning("Profiling endpoint missing on %s", url)
            return None
        raise
    except Exception:
        raise


async def _profile_cmd(cmd: str, payload: dict, e_url: str, p_url: str, d_url: str):
    """
    [深层原理] 多节点分布式性能追踪同步.
    多模态解耦架构极其复杂, 由于跨多节点传输, 传统的单机 PyTorch Profiler 只能看到单一环节, 无法看到端到端.
    此方法能够协调所有的物理实例, 在接收到 start 命令后同步对底层计算、通信(Nixl RDMA)进行 Trace 记录.
    """
    headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"}

    encode_task = _post_if_available(
        encode_session, f"{e_url}/{cmd}_profile", payload, headers
    )
    prefill_task = (
        _post_if_available(prefill_session, f"{p_url}/{cmd}_profile", payload, headers)
        if p_url is not None
        else asyncio.sleep(0)
    )
    decode_task = _post_if_available(
        decode_session, f"{d_url}/{cmd}_profile", payload, headers
    )

    encode_res, prefill_res, decode_res = await asyncio.gather(
        encode_task, prefill_task, decode_task
    )

    if encode_res is prefill_res is decode_res is None:
        raise HTTPException(
            status_code=503,
            detail="Profiling endpoints are disabled on all clusters",
        )

    return {
        "encode": encode_res,
        "prefill": prefill_res,
        "decode": decode_res,
    }


@app.post("/start_profile")
async def start_profile(request: Request):
    body = await request.json()
    e_url = random.choice(app.state.e_urls)
    p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
    d_url = random.choice(app.state.d_urls)
    return await _profile_cmd("start", body, e_url, p_url, d_url)


@app.post("/stop_profile")
async def stop_profile(request: Request):
    body = await request.json()
    e_url = random.choice(app.state.e_urls)
    p_url = random.choice(app.state.p_urls) if app.state.p_urls else None
    d_url = random.choice(app.state.d_urls)
    return await _profile_cmd("stop", body, e_url, p_url, d_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--encode-servers-urls",
        required=True,
        help='Comma-separated encode URLs ("http://e1:8001,http://e2:8001")',
    )
    parser.add_argument(
        "--prefill-servers-urls",
        required=True,
        help=(
            'Comma-separated prefill URLs ("http://p1:8003,http://p2:8004") ',
            'to enable E->P->D, set "disable" or "none" to enable E->PD',
        ),
    )
    parser.add_argument(
        "--decode-servers-urls",
        required=True,
        help='Comma-separated decode URLs ("http://d1:8005,http://d2:8006")',
    )

    args = parser.parse_args()
    app.state.e_urls = [
        u.strip() for u in args.encode_servers_urls.split(",") if u.strip()
    ]
    app.state.d_urls = [
        u.strip() for u in args.decode_servers_urls.split(",") if u.strip()
    ]

    # [设计原理] 处理两阶段解耦和三阶段解耦的自适应路由.
    if args.prefill-servers-urls.lower() in ("disable", "none", ""):
        app.state.p_urls = []
        logger.info(
            "Disaggregated prefill phase explicitly disabled by user. Running E + PD..."
        )
    else:
        app.state.p_urls = [
            u.strip() for u in args.prefill-servers-urls.split(",") if u.strip()
        ]
        logger.info("Disaggregated prefill phase is enabled. Running E + P + D...")

    logger.info("Proxy listening on %s:%s", args.host, args.port)
    logger.info("Encode servers: %s", app.state.e_urls)
    logger.info("Prefill instances %s", app.state.p_urls)
    logger.info("Decode servers: %s", app.state.d_urls)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        loop="uvloop", # [设计原理] 采用高性能 uvloop 替换 Python 原生的 asyncio 事件循环, 提升高并发网络 I/O 的处理上限.
        access_log=True,
    )
```

---

### 二、脚本设计中蕴含的深层次技术原理

为了在生产环境部署高吞吐、低延迟的多模态分布式大模型推理, 该代理采用了如下三项核心深层原理:

#### 1. 控制面与数据面彻底分离 (Control & Data Plane Separation)

* 面临的瓶颈: 跨物理节点传输多模态大模型的 KV Cache(在文本长度极长时, 其大小可达数百兆字节乃至数吉字节), 如果通过 Proxy 中转, 会导致 Proxy 进程的网络带宽被彻底挤满.

* 脚本的解决方案:

  * 控制面(Control Plane): 由 Proxy 负责. Proxy 发送极其轻量级的 HTTP 消息(仅几十至几百个字节)来协调各节点.

  * 数据面(Data Plane): 在底层, Prefill 节点完成预计算后, 向 Proxy 返回 `kv_transfer_params`(其中仅包含虚拟存储块 ID、远端 Engine ID、存储节点 IP 端口等轻量配置标记).

  * 零拷贝跨卡传输: 下游的 Decode 节点接收到含有这些 params 的请求后, 并不通过 HTTP 接口拉取数据, 而是由 vLLM C++ 运行时通过高效的 GPUDirect RDMA(基于 NixlConnector 与 UCX) 绕过 CPU 内存, 从 Prefill 的 GPU 显存异步、零拷贝地直接复制到 Decode 的 GPU 显存.

#### 2. 多模态图像计算解耦 (Vision Feature Offloading)

* 面临的瓶颈: 多模态图像在执行视觉特征提取(如 ViT 或 SigLIP 模型)时, 其张量的输入维度(Image Shape)会根据用户图像的真实分辨率(Dynamic Shape)发生剧烈变动. 如果在同一个 LLM 实例中混合处理, 将导致 CUDA Graph 频繁编译或由于尺寸不一致而失效, 从而带来严重的延迟开销.

* 脚本的解决方案:

  * Proxy 每次截获包含多模态的请求时, 先调用 `extract_mm_items`.

  * 它构造了一个极其特异的子请求, 删除了所有 Prompt 文本, 只保留单张图, 并且设置了 `max_tokens=1`(强制前向计算只跑完 Encoder 和首个前向输出就退出).

  * 这种设计在不影响 LLM 语义的前提下, 干净地实现了 Vision Token 化提取. 提取的 Embedding 会通过 EC (Encoder Cache) 写入物理共享路径.

  * 到了 Prefill 阶段, LLM 只需根据 Request ID 像加载普通文本 embedding 一样直接映射加载该缓存, 物理上避免了 LLM 运行卡被频繁抖动的视觉计算占用.

#### 3. 并发扇出与横向负载拓展能力 (Fan-out Concurrent Extensibility)

* 面临的瓶颈: 随着在多轮对话中发送多张大图, 单机处理视觉编码会遇到极大的时间瓶颈.

* 脚本的解决方案:

  * Proxy 在 `fanout_encoder_primer` 模块中, 利用 `asyncio.gather` 同时向物理集群发起 N 个异步并发请求.

  * 每个请求由 `url_cycle` 实现 Round-Robin 循环轮询. 也就是说, 如果用户一次发送了 4 张图, 这 4 张图会同时分布在物理上不同的 4 块 Encoder GPU 卡上并发处理.

  * 在底层高并发场景下, 通过横向堆叠低配的 Encoder 显卡(ViT 模型的显存需求极小), 即可应对成百上千路的图片并发提取.

#### 4. aiohttp 连接池的无限制配置 (`limit=0`)

* 面临的瓶颈: 在高并发场景下, 微服务代理由于内部连接池容量受限, 会导致后续请求即使在本地也会面临长达数毫秒甚至数秒的 `TCP Connection Acquisition Timeout`(排队获取空闲 HTTP 物理连接).

* 脚本的解决方案:

  * 初始化时调用 `aiohttp.TCPConnector(limit=0, force_close=False)`.

  * `limit=0` 解锁了 TCP 物理套接字连接的总池数限制.

  * `force_close=False` 会维持标准的 HTTP Keep-Alive 连接. 这意味着在整个系统的生命周期内, Proxy 到 E、P、D 组件之间的连接只会在启动时进行三次握手, 后续所有的分布式编排请求都是直接通过这些已经开通的热连接(Hot connections)并行发送, 消除了物理握手引入的毫秒级 TTFT(首字延迟)延迟.

----------------------------------------------------


----------------------------------------------------
