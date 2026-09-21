#!/bin/bash
# ==============================================================================
# 脚本说明: vLLM 预填充与解码分离 (Disaggregated Prefill & Decode, P/D 分离) 容器启动入口脚本
# 适用基准镜像: vllm/vllm-openai:v0.22.0-cu129-ubuntu2404
# 核心职责:
#   1. 管理容器内多进程生命周期, 充当 PID 1 代理, 转发终止信号 (SIGTERM/SIGINT);
#   2. 在 GPU 0 上拉起 Prefill 实例 (KV Producer, 计算 Prompt 注意力);
#   3. 在 GPU 1 上拉起 Decode 实例 (KV Consumer, 负责自回归解码生成);
#   4. 启动异步协调代理 (Proxy Server), 负责接收外部请求并编排两阶段推理;
#   5. 提供服务保活及非侵入式健康探针.
# ==============================================================================

# -e (errexit): 只要任何一条命令返回非零退出码, 脚本立即终止退出, 防止错误累积
set -e
# -x (xtrace): 在执行每行命令前将其打印到标准输出, 便于在容器日志 (docker logs) 中排查执行流程
set -x

# ------------------------------------------------------------------------------
# 环境变量与默认配置解析
# ------------------------------------------------------------------------------
# 语法 ${VAR:-DEFAULT}: 若宿主机/Docker Compose 传入了 HF_MODEL_NAME 则优先使用, 否则回退到默认的 Llama-3.1-8B
MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

# 实例间内部通信绑定的 IP, 默认容器内回环地址 127.0.0.1
# 若在跨节点/多机部署场景下, 可通过外部环境变量指定为本机物理网络 IP
VLLM_HOST_IP=${VLLM_HOST_IP:-127.0.0.1}

echo "=== Starting vLLM Disaggregated Prefill & Decode Cluster ==="
echo "Model Name  : $MODEL_NAME"
echo "Internal IP : $VLLM_HOST_IP"

# ------------------------------------------------------------------------------
# 容器进程生命周期管理 (优雅退出钩子)
# ------------------------------------------------------------------------------
# 当执行 `docker stop` 时, Docker 引擎默认向 PID 1 发送 SIGTERM 信号, 超时后发送 SIGKILL.
# 若无信号处理钩子, 容器内的后台子进程 (&) 会被强制杀死, 导致 GPU 显存未及时释放或 NCCL 处于悬挂状态.
cleanup() {
    echo "Caught shutdown signal. Stopping all background processes..."
    # jobs -p 列出当前 Shell 管理的所有后台作业 PID
    # 发送 SIGTERM 信号通知两个 vllm serve 与 python proxy 进行优雅停机释放资源
    # 2>/dev/null || true 忽略可能已退出的进程产生的报错
    kill -TERM $(jobs -p) 2>/dev/null || true
    # wait 等待所有后台子进程完全终止退出
    wait
    echo "All processes stopped. Exiting."
    exit 0
}
# 捕获 SIGINT (Ctrl+C) 和 SIGTERM (docker stop), 执行 cleanup 函数
trap cleanup SIGINT SIGTERM

# ------------------------------------------------------------------------------
# 健康检查轮询函数
# ------------------------------------------------------------------------------
# 参数 $1: 待检测的 HTTP 端口号
wait_for_server() {
    local port=$1
    echo "Waiting for service on port ${port} to be ready..."
    # timeout 1200 限制最多等待 20 分钟 (大模型首次加载权重并初始化 KV Cache 较耗时)
    # curl -s (静默模式) -f (HTTP 错误码 4xx/5xx 时返回非零退出码)
    # 请求 /v1/models 接口, 当且仅当 vLLM 引擎初始化完毕并返回 200 OK 时, 循环终止
    timeout 1200 bash -c "
    until curl -s -f http://127.0.0.1:${port}/v1/models > /dev/null 2>&1; do
      sleep 1
    done" || {
        echo "Service on port ${port} failed to start within timeout!"
        exit 1
    }
    echo "Service on port ${port} is ready!"
}

# ------------------------------------------------------------------------------
# 1. 启动 Prefill 阶段实例 (KV Producer / 键值对生产者)
# ------------------------------------------------------------------------------
echo "Starting Prefill instance on GPU 0..."
# CUDA_VISIBLE_DEVICES=0 物理隔离, 确保该实例独占 GPU 0 (计算密集型)
CUDA_VISIBLE_DEVICES=0 vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8100 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config \
    '{
        "kv_connector": "P2pNcclConnector",  # 使用基于 NCCL 点对点 (P2P NVLink/PCIe) 的高速传输通道
        "kv_role": "kv_producer",            # 角色: 生产者 (负责 prompt 前向计算并推送 KV Cache)
        "kv_rank": 0,                        # 通信拓扑中的编号 (Prefill 设为 0)
        "kv_parallel_size": 2,               # P2P 通信组包含的节点总数 (Producer + Consumer 共 2 个)
        "kv_buffer_size": "1e9",             # 发送端暂存缓冲区大小 (1e9 字节 ≈ 1GB 显存)
        "kv_port": "14579",                  # Prefill 节点监听的 NCCL 底层套接字通信端口
        "kv_connector_extra_config": {
            "proxy_ip": "'"$VLLM_HOST_IP"'",
            "proxy_port": "30001",
            "http_ip": "'"$VLLM_HOST_IP"'",
            "http_port": "8100",
            "send_type": "PUT_ASYNC"         # 异步推送模式 (Prefill 计算完毕后非阻塞发送给 Decode 节点)
        }
    }' &
# 末尾的 & 表示置于后台运行, 主脚本继续向下执行

# ------------------------------------------------------------------------------
# 2. 启动 Decode 阶段实例 (KV Consumer / 键值对消费者)
# ------------------------------------------------------------------------------
echo "Starting Decode instance on GPU 1..."
# CUDA_VISIBLE_DEVICES=1 物理隔离, 确保该实例独占 GPU 1 (显存带宽密集型)
CUDA_VISIBLE_DEVICES=1 vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8200 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config \
    '{
        "kv_connector": "P2pNcclConnector",  # 协议必须与 Producer 严格匹配
        "kv_role": "kv_consumer",            # 角色: 消费者 (接收 Prefill 传来的 KV Cache, 执行自回归解码)
        "kv_rank": 1,                        # 通信拓扑中的编号 (Decode 设为 1)
        "kv_parallel_size": 2,               # 通信组节点总数
        "kv_buffer_size": "1e10",            # 接收端缓冲区 (1e10 字节 ≈ 10GB 显存, 需容纳多并发请求的 KV 缓存)
        "kv_port": "14580",                  # Decode 节点监听的 NCCL 底层套接字通信端口
        "kv_connector_extra_config": {
            "proxy_ip": "'"$VLLM_HOST_IP"'",
            "proxy_port": "30001",
            "http_ip": "'"$VLLM_HOST_IP"'",
            "http_port": "8200",
            "send_type": "PUT_ASYNC"
        }
    }' &

# ------------------------------------------------------------------------------
# 3. 阻塞等待 Prefill 和 Decode 两个后端实例就绪
# ------------------------------------------------------------------------------
# 必须先等底层 vLLM 实例全部就绪并完成模型加载与显存预分配, 才能启动调度代理
wait_for_server 8100
wait_for_server 8200

# ------------------------------------------------------------------------------
# 4. 启动轻量调度代理服务器 (Proxy Server)
# ------------------------------------------------------------------------------
echo "Starting Disagg Proxy Server on port 8000..."
# 代理服务器负责对外提供统一的 OpenAI 规范接口 (端口 8000)
# 调度逻辑: 将请求改写 max_tokens=1 先发给 8100 计算 KV, 随后将请求重定向发给 8200 进行流式生成
python3 /app/disagg_prefill_proxy_server.py \
    --host 0.0.0.0 \
    --port 8000 \
    --prefill-url http://127.0.0.1:8100 \
    --decode-url http://127.0.0.1:8200 \
    --kv-host 127.0.0.1 \
    --prefill-kv-port 14579 \
    --decode-kv-port 14580 &

# ------------------------------------------------------------------------------
# 5. 校验代理服务器健康状态
# ------------------------------------------------------------------------------
# 针对 POST 路由 /v1/completions 发送空请求进行连通性探测
# 状态说明:
#   - 只要 TCP 端口通畅, curl 会返回状态码或特定的退出码:
#   - $? -eq 22 (HTTP 405 Method Not Allowed / 400 Bad Request 等应用层响应, 说明 Web 服务已存活)
#   - $? -eq 52 (服务端关闭连接/空响应, 但在初始监听阶段代表 Socket 已就绪)
timeout 30 bash -c 'until curl -s http://127.0.0.1:8000/v1/completions >/dev/null 2>&1 || [ $? -eq 22 ] || [ $? -eq 52 ]; do sleep 0.5; done' || true
echo "🎉 Cluster is fully operational! Listening on 0.0.0.0:8000"

# ------------------------------------------------------------------------------
# 6. 容器前台保活与异常感知
# ------------------------------------------------------------------------------
# wait -n: 等待任意一个后台子进程退出.
# 容器中不能直接 exit 0, 否则容器会立即停止.
# 采用 wait -n 的核心优势: 若 Prefill、Decode 或 Proxy 中有任何一个服务意外崩溃 (Crash),
# wait -n 会立即解除阻塞并使脚本退出, 从而让 Docker / K8s 及时感知容器异常并触发重启策略 (restartPolicy).
wait -n
