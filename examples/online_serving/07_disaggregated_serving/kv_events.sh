#!/bin/bash
# This file demonstrates the KV cache event publishing
# We will launch a vllm instances configured to publish KV cache
# events and launch a simple subscriber to log those events.

# [Bash 语法]set -xe 是一种严格/调试模式组合:
# -e (errexit): 只要任何一个命令执行失败(返回非零状态码), 脚本就会立即退出, 防止错误累积.
# -x (xtrace): 在执行每条命令前将其打印到终端, 极大地方便了自动化流水线中的排错和日志追踪.
set -xe

echo "🚧🚧 Warning: The usage of KV cache events is experimental and subject to change 🚧🚧"

# [设计意图]给用户或 CI/CD 系统 1 秒缓冲时间阅读警告信息, 避免刷屏太快无法看清.
sleep 1

# [Bash 语法]${变量:-默认值} 是一种参数默认值置换语法:
# 如果环境变量 HF_MODEL_NAME 已设置且非空, 则使用它; 否则, 默认使用后面的 Llama 3.1 模型.
MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

# [Bash 语法]trap '命令' 信号: 用于捕获系统信号.
# 这里捕获 INT (SIGINT, 通常由 Ctrl+C 触发). 一旦捕获, 立即执行指定的 'cleanup' 函数.
# [设计意图]因为 vLLM 服务和订阅者脚本都是在后台运行(带 &), 如果不做捕获清理,
# 用户中途强行终止脚本时, 后台的 GPU 进程和 Python 进程会变成孤儿进程, 继续占用显存.
# Trap the SIGINT signal (triggered by Ctrl+C)
trap 'cleanup' INT

# Cleanup function
cleanup() {
    echo "Caught Ctrl+C, cleaning up..."
    # [设计意图]强行终止所有残留的 python 进程, 释放 GPU 显存.
    # pgrep 找出所有包含 python 的 PID, xargs 将其传递给 kill -9(强制杀进程).
    # Cleanup commands
    pgrep python | xargs kill -9
    pkill -f python
    echo "Cleanup complete. Exiting."
    exit 0
}

# [Bash 语法]$(...) 用于命令替换, 执行里面的命令并将其输出作为值.
# hostname -I 获取主机所有的 IP 地址(通常包括内网、Docker 等).
# awk '{print $1}' 提取输出的第一列(通常是主网卡的主机 IP).
# export 将该变量提升为全局环境变量, 供子进程(如 vllm 内部组件)读取.
export VLLM_HOST_IP=$(hostname -I | awk '{print $1}')

# [设计意图]大语言模型加载权重并初始化 CUDA 环境可能需要数十秒至数分钟.
# 如果直接运行后续的 curl 请求, 会因为端口未监听而报错. 因此必须实现一个阻塞式的"健康检查"等待函数.
# a function that waits vLLM server to start
wait_for_server() {
    local port=$1
    # timeout 1200: 限制整个等待过程最多持续 1200 秒(20 分钟), 超时后强制退出, 防止 CI/CD 无限挂起.
    # bash -c "...": 启动一个子 shell 运行轮询逻辑.
    # until ...; do sleep 1; done: 循环执行 curl, 直到其成功响应(返回 0 状态码).
    # -s (silent) 隐藏 curl 进度条, 避免污染日志.
    timeout 1200 bash -c "
    until curl -s localhost:${port}/v1/completions > /dev/null; do
      sleep 1
    done" && return 0 || return 1
}

# [vLLM 参数解析]:
# vllm serve: 启动 OpenAI 兼容的 API 服务.
# --port 8100: 指定服务监听的端口号.
# --max-model-len 100: 限制模型最大上下文长度为 100.
#   [设计意图]在测试脚本中将其设得很小, 可以极大减少 GPU 显存的预分配(Pre-allocation)时间.
# --enforce-eager: 强制使用 PyTorch Eager 模式, 禁用 CUDA Graphs.
#   [设计意图]CUDA Graphs 可以在推理时加快速度, 但启动时需要几分钟来进行 Warmup(热身预编译).
#   在开发测试场景下, 禁用它可以让服务在几秒内迅速启动.
# --gpu-memory-utilization 0.8: 限制 vLLM 最多只占用当前 GPU 80% 的显存, 保留 20% 显存供其他任务或防 OOM.
# --trust-remote-code: 允许加载 Hugging Face 上模型自带的自定义代码(部分模型架构必须).
# --kv-events-config: [核心特性]启用 vLLM 的 KV Cache 事件发布功能.
#   - enable_kv_cache_events: 开启事件生成.
#   - publisher: "zmq": 指定通过 ZeroMQ (ZMQ) 协议异步发布这些事件.
#   - topic: "kv-events": 订阅者需要过滤的 ZMQ Topic 话题.
# &: [Bash 语法]在命令末尾加 &, 将该进程放到后台异步运行, 使脚本能够继续往下执行.
vllm serve "$MODEL_NAME" \
    --port 8100 \
    --max-model-len 100 \
    --enforce-eager \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-events-config \
    '{"enable_kv_cache_events": true, "publisher": "zmq", "topic": "kv-events"}' &

# 调用前面定义的函数, 阻塞等待 vLLM 服务在 8100 端口完全就绪
wait_for_server 8100

# [Bash 语法]获取当前执行脚本所在目录的绝对路径, 这是一种非常鲁棒的写法:
# - ${BASH_SOURCE[0]} 获取当前脚本文件的相对路径.
# - dirname 提取出该文件所在的目录.
# - cd 进入该目录, pwd 输出绝对路径, 确保脚本在任何工作目录下被调用时, 都能正确找到同目录下的其他文件.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# [设计意图]启动一个后台订阅者脚本. 它会通过 ZMQ 连接到 vLLM 的事件发布端口,
# 当 vLLM 进行推理并修改 KV Cache 时, 该脚本能捕获到 `BlockStored` 或 `BlockRemoved` 事件并记录日志.
python3 "$SCRIPT_DIR/kv_events_subscriber.py" &
sleep 1

# [设计意图与 vLLM 特性]:
# 我们发送了两个高度相似的请求, 前缀完全一致: "Explain quantum computing in simple terms a ..."
# 1. 第一个请求会强制模型对前缀进行 Pre-fill(预填充), 并在 GPU 显存中分配 KV Cache 块(Block),
#    此时会发布 `BlockStored` 事件.
# 2. 第二个请求到达时, 由于前缀相同, 如果 vLLM 启用了 Prefix Caching(前缀缓存),
#    它会直接命中并复用已有的 KV 缓存, 从而展示 KV Cache 的共享特性.
# serve two example requests
output1=$(curl -X POST -s http://localhost:8100/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
"model": "'"$MODEL_NAME"'",
"prompt": "Explain quantum computing in simple terms a 5-year-old could understand.",
"max_tokens": 80,
"temperature": 0
}')

output2=$(curl -X POST -s http://localhost:8100/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
"model": "'"$MODEL_NAME"'",
"prompt": "Explain quantum computing in simple terms a 50-year-old could understand.",
"max_tokens": 80,
"temperature": 0
}')

# [设计意图]测试完成, 主动杀掉后台的 vLLM 和 Python 进程, 防止显存泄漏.
# pkill -9: 强制杀死进程.
# -u "$USER": 仅杀死当前用户拥有的进程, 防止误杀系统中其他用户的任务.
# -f: 匹配完整的命令行参数(而不仅是进程名), 确保精准匹配到我们刚才启动的特定 Python 和 vLLM 实例.
# Cleanup commands
pkill -9 -u "$USER" -f python
pkill -9 -u "$USER" -f vllm

sleep 1

echo "Cleaned up"

# 打印两次请求的输出结果, 以便开发者验证模型是否正常生成
# Print the outputs of the curl requests
echo ""
echo "Output of first request: $output1"
echo "Output of second request: $output2"

echo "🎉🎉 Successfully finished 2 test requests! 🎉🎉"
echo ""
