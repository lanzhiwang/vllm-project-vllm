#!/bin/bash

# [BASH语法] 启用严格执行模式
# -e: 任何单条命令返回非零(失败)状态时, 脚本立即终止退出, 防止错误向后传递.
# -u: 遇到未声明或未定义的变量时直接报错, 避免由于拼写错误导致非预期行为.
# -o pipefail: 只要管道命令中任何一个子命令失败, 整个管道就返回失败状态.
set -euo pipefail

# [BASH语法] 显式声明一个索引数组 PIDS, 用于存储所有后台进程的 PID.
# [设计逻辑] 方便在脚本结束或收到退出信号时, 通过 PID 统一进行资源回收.
declare -a PIDS=()

###############################################################################
# Configuration -- override via env before running
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

# [设计逻辑] 兼容不同的异构计算硬件平台.
# Device platform and affinity env name.
# DEVICE_PLATFORM supports: cuda, xpu
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
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-12000}" # wait_for_server timeout

# 基准测试时向服务器发送的样本总数
NUM_PROMPTS="${NUM_PROMPTS:-100}" # number of prompts to send in benchmark

# Serve args (vLLM 服务参数配置)
# [vLLM特性] 显存利用率配置. 由于两阶段分工不同, 显存占用策略差异巨大:
# - Encoder(E)仅运行 Vision Transformer, 不保留文本 KV Cache 空间, 因此显存需求极低(分配 1% 即可).
# - PD 节点承载了完整的 LLM 解码, 需要大量空间来装载模型参数并管理 PagedAttention 缓存, 因此分配较大比例(70%).
# Serve args
GPU_MEMORY_UTILIZATION_E="${GPU_MEMORY_UTILIZATION_E:-0.01}"
GPU_MEMORY_UTILIZATION_PD="${GPU_MEMORY_UTILIZATION_PD:-0.7}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-128}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"

###############################################################################
# Helpers
###############################################################################
# [BASH语法] 命令替换 $(git ...), 动态计算当前 Git 仓库的根路径.
# [设计逻辑] 用于确保在后续加载本地图像文件时, 路径指向始终与仓库结构保持一致.
# Find the git repository root directory
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
# Cleanup function
cleanup() {
    echo "Stopping everything…"
    # [BASH语法] 临时取消信号捕获, 避免在清理资源期间发生重入和死循环.
    trap - INT TERM USR1 # prevent re-entrancy

    # [BASH语法] "${PIDS[@]}" 展开数组. 第一阶段先通过 kill -0 测试进程是否存在, 若存在则尝试友好关闭(SIGTERM).
    # Kill all tracked PIDs
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Killing process $pid"
            kill "$pid" 2>/dev/null
        fi
    done

    # 给进程留出 2 秒用于释放 GPU 显存和关闭句柄
    # Wait a moment for graceful shutdown
    sleep 2

    # 第二阶段: 如果 2 秒后依然有存活进程, 则升级为 kill -9(SIGKILL)物理清除.
    # Force kill any remaining processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # [BASH语法] kill -- -$$: 向当前 shell 的整个进程组(Process Group ID 等同于主进程的 PID)发送终止信号, 确保无孤儿进程.
    # Kill the entire process group as backup
    kill -- -$$ 2>/dev/null

    echo "All processes stopped."
    exit 0
}

# [BASH语法] 注册信号陷阱. 当脚本接收到 Ctrl+C (INT)、终端关闭 (TERM) 或用户自定义信号 (USR1) 时触发 cleanup.
trap cleanup INT
trap cleanup USR1
trap cleanup TERM

# [设计逻辑] 每次启动前, 必须清理旧的共享磁盘缓存, 防止由于残留的脏数据导致 PD 节点误读取.
# clear previous cache
echo "remove previous ec cache folder"
rm -rf "$EC_SHARED_STORAGE_PATH"

echo "make ec cache folder"
mkdir -p "$EC_SHARED_STORAGE_PATH"

###############################################################################
# Encoder worker
###############################################################################
# 启动图像特征编码实例
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
    >"${ENC_LOG}" 2>&1 &
# [BASH语法] & 表示在后台异步运行, 同时利用 > 结合 2>&1 将 stdout 与 stderr 合并重定向写入日志.

# [BASH语法] $! 存储最近一个后台进程的 PID, 并将其加入 PIDS 数组.
PIDS+=($!)

###############################################################################
# Prefill+Decode worker
###############################################################################
# 启动统一的 LLM 生成实例
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

# [设计逻辑] 按照调用链拓扑阻塞等待, 保障底层服务的端口可用.
# Wait for workers
wait_for_server "$ENCODE_PORT"
wait_for_server "$PREFILL_DECODE_PORT"

###############################################################################
# Proxy
###############################################################################
# 中控路由网关
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
# Benchmark
###############################################################################
# 并发性能基准测试
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
# Single request with local image
###############################################################################
# 全链路冒烟测试
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

# [设计逻辑] 完成测试后调用清理, 保障环境不发生资源或显存泄露.
# cleanup
echo "cleanup..."
cleanup
