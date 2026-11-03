#!/bin/bash
# ==============================================================================
# 脚本名称: entrypoint.sh
# 适用场景: 基于 vLLM 的预填充与解码分离 (Disaggregated Prefill & Decode, P/D 分离)
# 部署形态: 单机多卡 (单容器通过 CUDA_VISIBLE_DEVICES 分配 GPU 0 和 GPU 1)
#
# ------------------------------------------------------------------------------
# [核心架构与设计原理]
# 1. 为什么要做 P/D 分离?
#    - Prefill 阶段: 计算密集型 (Compute-bound), 一次性对长 Prompt 并行计算 Attention,
#      计算单元 (Tensor Core) 满载, 容易阻碍自回归 Token 的生成.
#    - Decode 阶段: 显存带宽受限型 (Memory-bandwidth bound), 逐 Token 串行生成,
#      算力利用率低但极度依赖显存读写速度与低延迟调度.
#    - 将两者解耦到不同的物理 GPU 甚至不同的节点, 可以彻底消除混合推理带来的"推理气泡"
#      (Inference Bubbles), 显著降低首字延迟 (TTFT) 并大幅提升解码吞吐 (ITL).
#
# 2. KV Cache 是如何点对点流转的?
#    - 底层采用 vLLM 的 P2pNcclConnector 组件.
#    - 控制面: disagg_prefill_proxy_server (端口 8000) 统一纳管流量, 通过在 HTTP
#      Header (X-Request-Id) 中编码两端的物理传输网络套接字 (IP:Port).
#    - 数据面: Prefill 实例算完 Prompt 后, 通过 ZMQ 元数据通道通知 Decode 端, 并直接
#      利用 NCCL 点对点 (NVLink / PCIe P2P) 将 KV Cache 注入 Decode 端的显存接收缓冲区.
# ==============================================================================

# -e (errexit): 脚本中任何命令如果以非零状态码退出, 整个脚本立即终止, 防止雪崩与错误累积.
set -e
# -x (xtrace): 执行命令前把该行展开后的完整参数打印到标准输出, 生产环境容器排错必备.
set -x

# ==============================================================================
# 第一部分: 网络拓扑动态感知 (踩坑点 1: IP 错位引发的握手死锁)
# ==============================================================================
# [避坑复盘]
# 在 vLLM 底层的 P2pNcclEngine 源码中, ZMQ 套接字默认使用 get_ip() 绑定容器物理网卡 IP (如 10.41.0.2).
# 如果脚本中写死 127.0.0.1, 会导致 Proxy 注入的 Request-ID 地址 (127.0.0.1) 与实例实际监听地址
# (10.41.0.2) 发生冲突, NCCL 在握手交换 Bootstrap 凭证阶段会永久挂起超时.
# 因此, 必须动态获取容器 eth0 主网卡的物理 IP, 保证上下游通讯元数据 100% 对齐.
CONTAINER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$CONTAINER_IP" ]; then
    CONTAINER_IP="127.0.0.1"
fi
echo "===> [P/D Topology] Detected Container Physical IP: ${CONTAINER_IP} <==="

# ==============================================================================
# 第二部分: 核心环境变量调优 (踩坑点 2, 3: ID 随机化 与 分布式底层库冲突)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. [核心致命配置]禁用 vLLM V1 引擎 Request-ID 随机化
# ------------------------------------------------------------------------------
# 原理: vLLM V1 引擎为了保证分布式场景下全局 Request ID 不冲突, 默认会在外部传入的 ID
# 后面强制追加 8 位随机 UUID (例如: xxx-ac08ead8).
# 严重后果: Prefill 节点将 KV 发送到带 A 后缀的 Tensor Key, 而 Decode 节点在等待带 B 后缀的 Key.
# 两端 Key 无法对齐, Decode 节点等不到数据超时退出, 导致服务端彻底卡死.
# 必须显式开启该变量, 强制 vLLM 完全信任外部 Proxy 传入的统一 Request ID.
export VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=1

# 日志输出级别: 设为 INFO 保证生产环境干净稳定且保留核心调度节点日志
export VLLM_LOGGING_LEVEL=INFO

# ------------------------------------------------------------------------------
# 2. NCCL (GPU 间通信通道) 性能与调试配置
# ------------------------------------------------------------------------------
# 打印 NCCL 初始化与 P2P 链路选择详情, 卡死时能在日志中直观看到卡在哪个环
export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,P2P,ENV

# 单机多卡 (单机双卡) 场景优化:
export NCCL_IB_DISABLE=1            # 单机单容器无需 InfiniBand, 直接禁用以防止扫描 HCA 卡超时
export NCCL_P2P_DISABLE=0           # 强制允许使用 NVLink 或 PCIe P2P 直连
export NCCL_SHM_DISABLE=0           # 强制开启宿主机/容器间共享内存 (IPC)
export CUDA_DEVICE_ORDER=PCI_BUS_ID # 确保物理卡序号与 CUDA_VISIBLE_DEVICES 严格按 PCIe 总线对齐

# 指定 NCCL 交换控制信息的套接字网卡:
# 精准指定为容器主网卡 eth0. 避免其在 Docker 复杂桥接网络下误连到不通的虚拟网口.
export NCCL_SOCKET_IFNAME=eth0
export NCCL_NET_GDR_LEVEL=0 # 禁用跨网卡 GPUDirect RDMA, 避免单机虚拟化网卡误用

# ------------------------------------------------------------------------------
# 3. [踩坑警示]关于 PyTorch Gloo 的网卡绑定
# ------------------------------------------------------------------------------
# 警告: 绝对不要设置 `export GLOO_SOCKET_IFNAME=eth0,eth,lo`!
# 原理: NCCL 支持逗号分隔的网卡前缀, 但 PyTorch 底层的 C++ Gloo 库 (用于 CPU 辅助协调)
# 仅接受单一的合法网卡名称. 若包含逗号, Gloo 会尝试把 "eth" 当作网卡名去找, 导致报:
# `RuntimeError: ifa != nullptr. Unable to find address for: eth` 并导致整个 Engine 崩溃退出.
# 最佳实践: 不设置该变量, 让 PyTorch Gloo 依据默认路由自动绑定到 eth0.

# ==============================================================================
# 第三部分: 模型与运行时基础配置
# ==============================================================================
# 优先读取外部环境变量 (如 Docker Compose 或 k8s 传入的 HF_MODEL_NAME), 默认回退到标准权重
MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

# ------------------------------------------------------------------------------
# 优雅停机钩子 (Graceful Shutdown)
# ------------------------------------------------------------------------------
# 原理: 当执行 `docker stop` 时, Docker 默认向 PID 1 发送 SIGTERM.
# 若主脚本没有 trap 信号, 后台后台的子进程 (vllm 进程池和 proxy) 会被直接强制杀死 (SIGKILL),
# 这极易导致 GPU 驱动显存未释放、NCCL 通信段残留或端口挂起.
cleanup() {
    echo "Caught shutdown signal. Stopping all background processes gracefully..."
    # 向当前 Shell 管理的所有子作业发送 SIGTERM 优雅退出
    kill -TERM $(jobs -p) 2>/dev/null || true
    wait
    echo "All processes stopped cleanly. Exiting."
    exit 0
}
trap cleanup SIGINT SIGTERM

# ------------------------------------------------------------------------------
# 阻塞式健康探针轮询函数
# ------------------------------------------------------------------------------
# 原理: 大模型加载数十 GB 权重并进行 torch.compile、CUDA 图捕获需要 1~3 分钟,
# 代理服务器必须等待两个后端实例在 HTTP 协议层完全就绪 (/v1/models 返回 200 OK) 后才能启动.
wait_for_server() {
    local port=$1
    echo "Waiting for vLLM service on port ${port} to be ready..."
    # 最长轮询 1200 秒 (20 分钟)
    timeout 1200 bash -c "
    until curl -s -f http://127.0.0.1:${port}/v1/models > /dev/null 2>&1; do
      sleep 1
    done" || {
        echo "ERROR: Service on port ${port} failed to start within timeout!"
        exit 1
    }
    echo "SUCCESS: Service on port ${port} is ready!"
}

# ==============================================================================
# 第四部分: 启动 Prefill 阶段实例 (KV Producer / 生产者)
# ==============================================================================
echo "Starting Prefill instance on GPU 0..."

# CUDA_VISIBLE_DEVICES=0: 物理隔离, 独占 GPU 0 (计算密集型)
# --gpu-memory-utilization 0.88: 预留 12% 显存给 P2P 缓冲区及 PyTorch 内部碎片
# --kv-transfer-config:
#   - kv_connector: 使用高吞吐的点对点 NCCL 通道 (P2pNcclConnector)
#   - kv_role: kv_producer (只负责 Prompt 前向计算, 计算完将 KV 推给 Consumer)
#   - kv_rank: 0 (生产者在 P2P 通信组中的编号)
#   - kv_parallel_size: 2 (组内节点总数: 1 Producer + 1 Consumer)
#   - kv_ip: 传入探测出的真实 IP, 底层 ZMQ 通信将监听在该 IP 上
#   - kv_port: 14579, Prefill 端暴露的 NCCL/ZMQ 通信 Bootstrap 端口
#   - kv_buffer_size: 发送端临时显存缓冲区大小 (2e9 字节 ≈ 2GB 显存)
#   - kv_connector_extra_config:
#       * send_type: "PUT_ASYNC" (Prefill 端前向计算完异步推流至 Consumer, 非阻塞)
#       * nccl_num_channels: 8 (开启 8 个通信通道最大化压榨 NVLink/PCIe 带宽)
CUDA_VISIBLE_DEVICES=0 vllm serve "$MODEL_NAME" \
    --trust-remote-code \
    --use-tqdm-on-load \
    --host 0.0.0.0 \
    --port 8100 \
    --gpu-memory-utilization 0.88 \
    --max-model-len 2048 \
    --max-num-batched-tokens 8192 \
    --enable-log-requests \
    --kv-transfer-config \
    '{
        "kv_connector": "P2pNcclConnector",
        "kv_role": "kv_producer",
        "kv_rank": 0,
        "kv_parallel_size": 2,
        "kv_ip": "'"$CONTAINER_IP"'",
        "kv_port": 14579,
        "kv_buffer_size": "2e9",
        "kv_connector_extra_config": {
            "send_type": "PUT_ASYNC",
            "nccl_num_channels": "8"
        }
    }' &

# ==============================================================================
# 第五部分: 启动 Decode 阶段实例 (KV Consumer / 消费者)
# ==============================================================================
echo "Starting Decode instance on GPU 1..."

# CUDA_VISIBLE_DEVICES=1: 物理隔离, 独占 GPU 1 (显存带宽受限型)
# kv_role: kv_consumer (接收 Prefill 节点发送过来的 KV Cache 并存储于本地 Buffer, 直接用于后续解码)
# kv_rank: 1 (消费者在通信拓扑中的编号)
# kv_buffer_size: 接收端显存缓冲区 (4e9 字节 ≈ 4GB 显存, 需容纳多个并发批次的 KV 缓存)
# kv_port: 14580, Decode 端暴露的 NCCL/ZMQ 监听端口
CUDA_VISIBLE_DEVICES=1 vllm serve "$MODEL_NAME" \
    --trust-remote-code \
    --use-tqdm-on-load \
    --host 0.0.0.0 \
    --port 8200 \
    --gpu-memory-utilization 0.88 \
    --max-model-len 2048 \
    --max-num-batched-tokens 8192 \
    --enable-log-requests \
    --kv-transfer-config \
    '{
        "kv_connector": "P2pNcclConnector",
        "kv_role": "kv_consumer",
        "kv_rank": 1,
        "kv_parallel_size": 2,
        "kv_ip": "'"$CONTAINER_IP"'",
        "kv_port": 14580,
        "kv_buffer_size": "4e9",
        "kv_connector_extra_config": {
            "send_type": "PUT_ASYNC",
            "nccl_num_channels": "8"
        }
    }' &

# ==============================================================================
# 第六部分: 阻塞等待两端底层实例全部就绪
# ==============================================================================
wait_for_server 8100
wait_for_server 8200

# ==============================================================================
# 第七部分: 启动轻量协调调度代理 (Disaggregated Proxy Server)
# ==============================================================================
echo "Starting Disagg Proxy Server on port 8000..."
# 代理职责:
# 1. 暴露标准 OpenAI 规范接口 (/v1/chat/completions) 于 8000 端口;
# 2. 接收客户端请求, 改写 max_tokens=1 且 stream=False 触发 Prefill (GPU 0) 生成 KV;
# 3. 将携带相同 Request-ID 的请求转发给 Decode (GPU 1) 进行低延迟自回归生成;
# 4. --kv-host 传入 CONTAINER_IP, 确保 Request-ID 内编码的通讯端点与两实例真实监听地址完全一致.
python3 /app/disagg_prefill_proxy_server.py \
    --host 0.0.0.0 \
    --port 8000 \
    --prefill-url http://127.0.0.1:8100 \
    --decode-url http://127.0.0.1:8200 \
    --kv-host "$CONTAINER_IP" \
    --prefill-kv-port 14579 \
    --decode-kv-port 14580 &

# 校验 Proxy 服务存活状态 (探测 8000 端口)
timeout 30 bash -c 'until curl -s http://127.0.0.1:8000/v1/models >/dev/null 2>&1 || [ $? -eq 22 ] || [ $? -eq 52 ]; do sleep 0.5; done' || true
echo "🎉 Cluster is fully operational! Listening on 0.0.0.0:8000"

# ==============================================================================
# 第八部分: 容器前台保活与故障感知 (Fail-fast 机制)
# ==============================================================================
# 核心原理:
# 在容器环境中, PID 1 脚本不能直接退出.
# 使用 `wait -n` 等待"任意一个"后台子进程退出.
# 优势: 若 Prefill (8100)、Decode (8200) 或 Proxy (8000) 任何一个进程发生 OOM 或崩溃异常退出,
# `wait -n` 会立刻解除阻塞, 随后触发 cleanup 杀死其他僵尸进程并退出整个容器,
# 从而让外部编排系统 (如 Kubernetes / Docker Swarm) 能够立刻感知到容器失败并执行自动重启策略.
wait -n

### 原理与实践要点备忘卡

# | 关键问题 | 根因与机制 | 生产配置/防御措施 |
# | :--- | :--- | :--- |
# | Request ID 随机化 | vLLM V1 引擎在内部为请求拼接 8 位随机 UUID, 导致 Prefill 与 Decode 的底层显存 Tensor Key 无法对齐. | 必须设置 `export VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=1`. |
# | IP 地址漂移死锁 | P2pNcclEngine 默认调用 `get_ip()` 绑定容器内真实网卡 IP, 若 Proxy 传入 `127.0.0.1` 则握手端口不通. | 使用 `hostname -I \| awk '{print $1}'` 动态获取并统一注入到 `--kv-host` 和 JSON 的 `kv_ip` 中. |
# | Gloo 初始化崩溃 | PyTorch Gloo 遇到逗号分隔的接口名(如 `eth0,eth,lo`)会把不存在的 `eth` 当作网卡名. | 严禁为 Gloo 配置逗号列表, 生产环境直接取消设置 `GLOO_SOCKET_IFNAME` 让系统走默认路由. |
# | Prefill 响应悬挂 | 客户端若发起 `stream=true`, Prefill 实例如果也开启流式会导致连接等待 EOS 挂起. | Proxy 改写请求时必须强制追加 `prefill_request["stream"] = False`. |
# | 显存 OOM 隐患 | 大模型(如 31B)占用显存极高, 若 `kv_buffer_size` 过大, 加上 CUDA Graph 容易触顶 OOM. | 设置 `--gpu-memory-utilization 0.88`, 将生产者与消费者 Buffer 严格限制在 `2e9` (2GB) 与 `4e9` (4GB). |
