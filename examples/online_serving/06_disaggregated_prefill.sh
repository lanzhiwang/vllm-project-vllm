#!/bin/bash
# This file demonstrates the example usage of disaggregated prefilling
# We will launch 2 vllm instances (1 for prefill and 1 for decode),
# and then transfer the KV cache between them.

# set -xe 是 Bash 脚本中常用的调试和安全控制组合:
# -e (errexit): 只要任何一个命令执行失败(返回非零状态码), 脚本立即退出, 防止错误累积.
# -x (xtrace): 在执行每个命令前, 先将该命令打印到终端, 便于追踪执行路径.
set -xe

echo "🚧🚧 Warning: The usage of disaggregated prefill is experimental and subject to change 🚧🚧"
sleep 1

# 变量默认值语法 ${VAR:-DEFAULT}:
# 如果环境变量 HF_MODEL_NAME 已经存在且非空, 则使用它; 否则默认使用后面的 Llama-3.1 路径.
# meta-llama/Meta-Llama-3.1-8B-Instruct or deepseek-ai/DeepSeek-V2-Lite
MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

# trap 命令用于捕获系统信号. 这里捕获的是 SIGINT(即 Ctrl+C 终止信号).
# 当用户按下 Ctrl+C 时, Bash 会暂停当前操作, 跳转执行 cleanup 函数.
# Trap the SIGINT signal (triggered by Ctrl+C)
trap 'cleanup' INT

# 清理函数: 由于 vLLM 实例和代理服务器都在后台运行(带有 &),
# 如果直接退出脚本, 后台进程会变成孤儿进程继续占用 GPU 显存.
# Cleanup function
cleanup() {
    echo "Caught Ctrl+C, cleaning up..."
    # 强制杀死当前用户下所有的 python 进程(包含 vllm serve 和 proxy)
    # Cleanup commands
    pgrep python | xargs kill -9
    pkill -f python
    echo "Cleanup complete. Exiting."
    exit 0
}

# 检查 VLLM_HOST_IP 是否设置:
# [[ -z "..." ]] 判断字符串是否为空.
# ${VLLM_HOST_IP:-} 是一种安全的写法, 即使 VLLM_HOST_IP 未定义也不会触发 "unbound variable" 错误.
if [[ -z "${VLLM_HOST_IP:-}" ]]; then
    export VLLM_HOST_IP=127.0.0.1
    echo "Using default VLLM_HOST_IP=127.0.0.1 (override by exporting VLLM_HOST_IP before running this script)"
else
    echo "Using provided VLLM_HOST_IP=${VLLM_HOST_IP}"
fi

# 检查 Quart 库(轻量级异步 Python Web 框架)是否安装:
# python3 -c 执行单行 python 代码.
# &>/dev/null 将标准输出和标准错误均重定向到空设备(不污染终端屏幕).
# install quart first -- required for disagg prefill proxy serve
if python3 -c "import quart" &>/dev/null; then
    echo "Quart is already installed."
else
    echo "Quart is not installed. Installing..."
    python3 -m pip install quart
fi

# 等待服务端就绪的轮询函数:
# $1 表示传入的第一个参数(端口号).
# timeout 1200 限制内部命令的最长执行时间为 1200 秒(20 分钟), 超时则强制退出并返回失败.
# a function that waits vLLM server to start
wait_for_server() {
    local port=$1
    # bash -c 启动一个子 Shell 运行循环, 直到 curl 成功访问 /v1/models 并返回 0 状态码
    timeout 1200 bash -c "
    until curl -i localhost:${port}/v1/models > /dev/null; do
      sleep 1
    done" && return 0 || return 1
}

# You can also adjust --kv-ip and --kv-port for distributed inference.

# [实例 1: Prefill 阶段(KV Producer 生产者)]
# 限制此实例仅使用 GPU 0
# prefilling instance, which is the KV producer
CUDA_VISIBLE_DEVICES=0 vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8100 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config \
    '{"kv_connector":"P2pNcclConnector","kv_role":"kv_producer","kv_rank":0,"kv_parallel_size":2,"kv_buffer_size":"1e9","kv_port":"14579","kv_connector_extra_config":{"proxy_ip":"'"$VLLM_HOST_IP"'","proxy_port":"30001","http_ip":"'"$VLLM_HOST_IP"'","http_port":"8100","send_type":"PUT_ASYNC"}}' &
# 末尾的 & 表示将此进程放入后台异步运行, 以便脚本继续向下执行

# {
#     "kv_connector": "P2pNcclConnector",
#     "kv_role": "kv_producer",
#     "kv_rank": 0,
#     "kv_parallel_size": 2,
#     "kv_buffer_size": "1e9",
#     "kv_port": "14579",
#     "kv_connector_extra_config": {
#         "proxy_ip": "$VLLM_HOST_IP",
#         "proxy_port": "30001",
#         "http_ip": "$VLLM_HOST_IP",
#         "http_port": "8100",
#         "send_type": "PUT_ASYNC"
#     }
# }

# [实例 2: Decode 阶段(KV Consumer 消费者)]
# 限制此实例仅使用 GPU 1
# decoding instance, which is the KV consumer
CUDA_VISIBLE_DEVICES=1 vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8200 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config \
    '{"kv_connector":"P2pNcclConnector","kv_role":"kv_consumer","kv_rank":1,"kv_parallel_size":2,"kv_buffer_size":"1e10","kv_port":"14580","kv_connector_extra_config":{"proxy_ip":"'"$VLLM_HOST_IP"'","proxy_port":"30001","http_ip":"'"$VLLM_HOST_IP"'","http_port":"8200","send_type":"PUT_ASYNC"}}' &

# {
#     "kv_connector": "P2pNcclConnector",
#     "kv_role": "kv_consumer",
#     "kv_rank": 1,
#     "kv_parallel_size": 2,
#     "kv_buffer_size": "1e10",
#     "kv_port": "14580",
#     "kv_connector_extra_config": {
#         "proxy_ip": "$VLLM_HOST_IP",
#         "proxy_port": "30001",
#         "http_ip": "$VLLM_HOST_IP",
#         "http_port": "8200",
#         "send_type": "PUT_ASYNC"
#     }
# }

# 调用前面声明的轮询函数, 等待这两个端口的 vLLM 实例完全加载并启动完毕
# wait until prefill and decode instances are ready
wait_for_server 8100
wait_for_server 8200

# 运行 P/D 分离的协调代理.
# 为什么要运行这个 Proxy? 因为客户端发送请求时, 不能直接分别发给 Prefill 和 Decode,
# 需要一个中介将请求"拆分调度":
# - 步骤 1: Proxy 收到请求, 改写 max_tokens=1 并发往 Prefill 实例(8100), 生成初始 KV Cache.
# - 步骤 2: Prefill 实例通过内部的 P2pNcclConnector 将 KV Cache 直接传到 Decode 实例(8200).
# - 步骤 3: Proxy 再将完整的生成请求发往 Decode 实例, Decode 实例加载传输过来的 KV Cache 并完成后续的 Token 生成.
# launch a proxy server that opens the service at port 8000
# the workflow of this proxy:
# - send the request to prefill vLLM instance (port 8100), change max_tokens
#   to 1
# - after the prefill vLLM finishes prefill, send the request to decode vLLM
#   instance
# NOTE: the usage of this API is subject to change --- in the future we will
# introduce "vllm connect" to connect between prefill and decode instances
python3 ../../benchmarks/disagg_benchmarks/disagg_prefill_proxy_server.py &
sleep 1 # 稍微等待, 确保 Proxy 的 HTTP 服务正常拉起

# 发送请求时, 直接访问 Proxy 所在的 8000 端口, 而不是单独访问 8100 或 8200.
# curl -s (silent) 隐藏进度条和错误信息.
# $(...) 是命令替换, 将 curl 返回的 JSON 响应保存到变量 output1 和 output2 中.
# serve two example requests
output1=$(curl -X POST -s http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
"model": "'"$MODEL_NAME"'",
"prompt": "San Francisco is a",
"max_tokens": 10,
"temperature": 0
}')

output2=$(curl -X POST -s http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
"model": "'"$MODEL_NAME"'",
"prompt": "Santa Clara is a",
"max_tokens": 10,
"temperature": 0
}')

# 测试完毕后, 主动清理后台运行的 vllm 实例和代理, 避免端口冲突和显存残留.
# Cleanup commands
pgrep python | xargs kill -9
pkill -f python

echo ""

sleep 1

# 打印 curl 获取到的推理响应
# Print the outputs of the curl requests
echo ""
echo "Output of first request: $output1"
echo "Output of second request: $output2"

echo "🎉🎉 Successfully finished 2 test requests! 🎉🎉"
echo ""
