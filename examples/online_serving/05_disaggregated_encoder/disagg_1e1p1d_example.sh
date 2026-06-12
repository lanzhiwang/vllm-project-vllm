#!/bin/bash

# [BASH语法] 启用严格的 Bash 运行模式(Strict Mode)
# -e: 任何单条命令如果执行失败(返回非 0 状态码), 脚本会立即退出, 防止错误累积.
# -u: 遇到未绑定的变量(即未声明、无默认值的变量)时直接报错退出, 避免拼写错误导致异常.
# -o pipefail: 当管道命令(|)中任何一个子命令失败, 整条管道的状态便为失败(默认仅保留最后一条命令的状态).
set -euo pipefail

# [BASH语法] 显式声明一个名为 PIDS 的索引数组(Indexed Array).
# [设计逻辑] 用于统一收集后台启动的所有子进程的 PID(包括 E/P/D Worker、Proxy 和 Benchmark), 以便在清理阶段统一回收.
declare -a PIDS=()

###############################################################################
# Configuration -- override via env before running
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

# [设计逻辑] 支持异构加速平台.
# Device platform and affinity env name.
# DEVICE_PLATFORM supports: cuda, xpu
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
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-12000}" # wait_for_server timeout

# [设计逻辑] 基准测试中发送的 Prompt 样本总量.
NUM_PROMPTS="${NUM_PROMPTS:-100}" # number of prompts to send in benchmark

# Serve args (vLLM 服务参数)
# [vLLM特性] 显存利用率上限设置:
# - Encoder(E)不保留文本 KV Cache, 只做单次 Vision 编码, 所需显存极小, 故设为 0.01(1%).
# - Prefill(P)和 Decode(D)负责大语言模型(LLM)部分且需存储大量 KV 缓存, 故分配 0.7(70%).
# Serve args
GPU_MEMORY_UTILIZATION_E="${GPU_MEMORY_UTILIZATION_E:-0.01}"
GPU_MEMORY_UTILIZATION_P="${GPU_MEMORY_UTILIZATION_P:-0.7}"
GPU_MEMORY_UTILIZATION_D="${GPU_MEMORY_UTILIZATION_D:-0.7}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"

# [vLLM特性] NIXL(NVIDIA高性能KV缓存传输库)底层基于 UCX. 这里声明允许使用所有可用的网卡与底层传输协议.
export UCX_TLS=all
export UCX_NET_DEVICES=all

###############################################################################
# Helpers
###############################################################################
# Find the git repository root directory
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
# Cleanup function
cleanup() {
    echo "Stopping everything…"

    # [BASH语法] 解除当前注册的信号捕获, 防止在执行 cleanup 的过程中因信号再次触发 cleanup 陷入无限递归.
    trap - INT TERM USR1 # prevent re-entrancy

    # [BASH语法] "${PIDS[@]}" 展开数组内所有的 PID 元素.
    # [设计逻辑] 两阶段清理策略:
    # 1. 第一阶段: 对进程先使用 "kill -0" 探测是否存在, 存在则发送 SIGTERM(默认温柔终止), 允许 vLLM 优雅退出.
    # Kill all tracked PIDs
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing process $pid"
            kill "$pid" 2>/dev/null
        fi
    done

    # 留给进程 2 秒的优雅保存/释放资源时间
    # Wait a moment for graceful shutdown
    sleep 2

    # 2. 第二阶段: 对依然顽固存活的进程发送 SIGKILL (kill -9) 强行杀死.
    # Force kill any remaining processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # [BASH语法] kill -- -$$: 向当前 shell 进程组(Process Group)的所有进程发送终止信号(负数 PID 表示整个进程组), 作为兜底.
    # Kill the entire process group as backup
    kill -- -$$ 2>/dev/null

    echo "All processes stopped."
    exit 0
}

# [BASH语法] 注册信号拦截处理器. 当脚本收到 Ctrl+C (INT)、手动终止信号 (TERM) 或自定义信号 (USR1) 时, 自动调度 cleanup 函数.
trap cleanup INT
trap cleanup USR1
trap cleanup TERM

# [设计逻辑] 运行前清空残留的旧 EC(视觉 Embedding 缓存)目录, 并重新初始化, 确保实验数据隔离.
# clear previous cache
echo "remove previous ec cache folder"
rm -rf "$EC_SHARED_STORAGE_PATH"

echo "make ec cache folder"
mkdir -p "$EC_SHARED_STORAGE_PATH"

###############################################################################
# Encoder worker
###############################################################################
# 启动多模态解耦架构中的: 图像编码节点
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
    >"${ENC_LOG}" 2>&1 &
# [BASH语法] 后台异步执行命令(&), 并将标准输出(stdout)与标准错误(stderr, 2>&1)重定向到日志文件中.

# [BASH语法] $! 符号表示最近一个转入后台异步运行的进程的 PID. 将它加入 PIDS 数组.
PIDS+=($!)

###############################################################################
# Prefill worker
###############################################################################
# (启动多模态解耦架构中的: 计算密集型 Prefill 节点)
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
# Decode worker
###############################################################################
# 启动多模态解耦架构中的: 访存密集型 Decode 节点
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
# Wait for workers
wait_for_server "$ENCODE_PORT"
wait_for_server "$PREFILL_PORT"
wait_for_server "$DECODE_PORT"

###############################################################################
# Proxy
###############################################################################
# 启动解耦架构中控网关: EPD 路由代理
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
# Benchmark
###############################################################################
# 使用官方自带工具进行性能测试
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
# Single request with local image
###############################################################################
# 单请求验证
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

# [设计逻辑] 主流程结束, 调用清理逻辑, 优雅结束并强制清除所有驻留后台的服务进程.
# cleanup
echo "cleanup..."
cleanup
