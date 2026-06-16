# Run Cluster

Source https://github.com/vllm-project/vllm/blob/main/examples/online_serving/run_cluster.sh.

---------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 bash 脚本用于 vllm 的相关功能
```

```
请为这个脚本添加注释, 一是说明 bash 脚本的一些语法, 二是说明为什么要这么写, 三是说明 vllm 的相关特性和参数含义

为您编写了带有详细注释的 Bash 脚本. 为了让您更清晰地理解, 注释分为三部分:

1. Bash 语法说明: 解释特定的 Bash 结构、操作符和控制流.

2. 设计意图(为什么要这么写): 说明容器化、多节点分布式运行等架构层面的设计考量.

3. vLLM 与 Ray 的特性: 阐述分布式大模型推理(如共享内存、多节点网络通讯、Ray 框架集成)的具体参数含义.

以下是添加了详细注释的脚本, 随后附带了针对这三个维度的深度解析.

### 带有深度注释的脚本

```bash
#!/bin/bash
#
# Launch a Ray cluster inside Docker for vLLM inference.
#
# ==============================================================================
# vLLM 特性背景说明:
# vLLM 支持分布式推理(Tensor Parallelism 强依赖单机多卡/多机多卡, Pipeline Parallelism 依赖多机).
# 在多机环境下, vLLM 默认使用 Ray 作为分布式执行引擎.
# 一个完整的分布式 vLLM 集群需要:
# 1. 一个 Ray Head 节点(协调器, 通常也是 vLLM 服务的主入口).
# 2. 多个 Ray Worker 节点(提供额外的 GPU 算力).
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. 参数校验与提取 (Bash 语法 & 设计意图)
# ------------------------------------------------------------------------------

# [Bash 语法]$# 表示传递给脚本的参数个数. -lt 是 "less than"(小于).
# [设计意图]脚本运行至少需要 4 个必填参数: 镜像名、Head IP、节点类型、HF 缓存路径.
if [ $# -lt 4 ]; then
    echo "Usage: $0 docker_image head_node_ip --head|--worker path_to_hf_home [additional_args...]"
    exit 1
fi

# [Bash 语法]$1, $2 等表示位置参数.
# [设计意图]将前 4 个位置参数赋予具有业务含义的变量, 提高脚本可读性.
DOCKER_IMAGE="$1"
HEAD_NODE_ADDRESS="$2"
NODE_TYPE="$3" # --head 或 --worker
PATH_TO_HF_HOME="$4"

# [Bash 语法]shift 4 用于向左移动参数位置, 丢弃前 4 个参数.
# 移动后, 原来的 $5 变成 $1, 原来的 $@(所有参数列表)中将只剩下用户传入的额外 Docker 参数.
shift 4

# [Bash 语法]ADDITIONAL_ARGS=("$@") 将剩余的所有参数保存为一个 Bash 数组.
# 使用双引号和大括号 ("$@") 能够安全地保留参数中的空格, 防止参数被错误地拆分.
ADDITIONAL_ARGS=("$@")

# [设计意图]对关键输入进行安全校验, 限制节点类型只能是指定的两种.
if [ "${NODE_TYPE}" != "--head" ] && [ "${NODE_TYPE}" != "--worker" ]; then
    echo "Error: Node type must be --head or --worker"
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. 动态解析 VLLM_HOST_IP (Bash 语法 & vLLM 特性)
# ------------------------------------------------------------------------------
# [vLLM 特性说明]
# VLLM_HOST_IP 是 vLLM 容器环境中的关键变量.
# 在 Docker 容器中, Ray 和 vLLM 需要知道物理主机的真实 IP, 以便进行多机节点间的通信.
# 如果不显式指定, Ray 可能会绑定到容器内部的虚拟网卡 IP(如 172.17.0.x), 导致跨机器无法连通.
VLLM_HOST_IP=""

# [Bash 语法]${#ADDITIONAL_ARGS[@]} 获取数组的元素个数.
# 这里使用双括号 ((i = 0; i < len; i++)) 是 Bash 标准的 C 语言风格 for 循环.
for ((i = 0; i < ${#ADDITIONAL_ARGS[@]}; i++)); do
    arg="${ADDITIONAL_ARGS[$i]}"
    case "${arg}" in
    -e)
        # [Bash 语法]获取下一个参数. :- 表示若为空则返回空字符串.
        next="${ADDITIONAL_ARGS[$((i + 1))]:-}"
        # [Bash 语法][[ ... == ... ]] 是条件表达式. * 是通配符, 判断是否以 VLLM_HOST_IP= 开头.
        if [[ "${next}" == VLLM_HOST_IP=* ]]; then
            # [Bash 语法]${next#VLLM_HOST_IP=} 表示从变量开头截显得符合模式的最短字符串(即去掉前缀, 提取 IP 值).
            VLLM_HOST_IP="${next#VLLM_HOST_IP=}"
            break
        fi
        ;;
    # 兼容 -eVLLM_HOST_IP=ip 或直接传入 VLLM_HOST_IP=ip 的写法
    -eVLLM_HOST_IP=* | VLLM_HOST_IP=*)
        # [Bash 语法]${arg#*=} 截掉等号及等号左边的所有内容, 只保留 IP.
        VLLM_HOST_IP="${arg#*=}"
        break
        ;;
    esac
done

# [设计意图]安全校验. 如果是 Head 节点, 确保传入的 VLLM_HOST_IP 与 Head IP 保持一致.
if [[ "${NODE_TYPE}" == "--head" && -n "${VLLM_HOST_IP}" ]]; then
    if [[ "${VLLM_HOST_IP}" != "${HEAD_NODE_ADDRESS}" ]]; then
        echo "Warning: VLLM_HOST_IP (${VLLM_HOST_IP}) differs from head_node_ip (${HEAD_NODE_ADDRESS})."
        echo "Using VLLM_HOST_IP as the head node address."
        HEAD_NODE_ADDRESS="${VLLM_HOST_IP}"
    fi
fi

# ------------------------------------------------------------------------------
# 3. 容器生命周期管理 (Bash 语法 & 设计意图)
# ------------------------------------------------------------------------------

# [Bash 语法]${RANDOM} 是 Bash 内置的伪随机数生成器.
# [设计意图]通过随机数后缀, 防止同一台物理机上启动多个节点时产生 Docker 容器名称冲突.
CONTAINER_NAME="node-${RANDOM}"

# [Bash 语法]定义一个名为 cleanup 的清理函数.
# [设计意图]当脚本退出(或被中断)时, 自动停止并删除 Docker 容器.
# 因为 Ray 启动时加了 --block(阻塞模式), 如果用户使用 Ctrl+C 终止脚本,
# 容器可能会残留并在后台继续占用 GPU 显存.
cleanup() {
    docker stop "${CONTAINER_NAME}"
    docker rm "${CONTAINER_NAME}"
}

# [Bash 语法]trap 命令用于捕获系统信号.
# EXIT 信号表示脚本无论是因为执行完毕、出错、还是收到 SIGINT/SIGTERM 等而退出时, 都会触发 cleanup 函数.
trap cleanup EXIT

# ------------------------------------------------------------------------------
# 4. 构建 Ray 启动命令 (Ray / vLLM 核心参数)
# ------------------------------------------------------------------------------

# [Ray 特性]--block 表示让 Ray 进程在前端阻塞运行, 保持活跃状态.
# 如果不加 --block, Ray 会在后台启动, 导致 Docker 容器检测不到前台进程而立即退出.
RAY_START_CMD="ray start --block"

if [ "${NODE_TYPE}" == "--head" ]; then
    # [Ray 特性]--head 声明该节点为全局协调器(Head 节点).
    # --port=6379 是 Ray GCS(Global Control Store)服务的核心端口, 用于元数据存储, Worker 将连接此端口.
    # --node-ip-address 显式指定 Ray 绑定主机的 IP, 防止多网卡机器绑定错误.
    RAY_START_CMD+=" --head --node-ip-address=${HEAD_NODE_ADDRESS} --port=6379"
else
    # [Ray 特性]Worker 节点启动时, 需要指明 Head 节点的 GCS 端口以加入集群.
    RAY_START_CMD+=" --address=${HEAD_NODE_ADDRESS}:6379"
    if [ -n "${VLLM_HOST_IP}" ]; then
        RAY_START_CMD+=" --node-ip-address=${VLLM_HOST_IP}"
    fi
fi

# ------------------------------------------------------------------------------
# 5. 执行 Docker 容器 (Docker / vLLM / PyTorch 参数)
# ------------------------------------------------------------------------------

# [vLLM & Docker 参数深度解析]:
# 1. --entrypoint /bin/bash: 覆盖镜像默认入口(默认可能是直接运行 vLLM), 因为我们需要先启动 Ray 服务.
# 2. --network host: 使用宿主机网络栈.
#    - 为什么不用默认 bridge 模式? 因为 Ray 节点间通信会随机使用大量的临时端口.
#    - 使用 host 网络可以避免繁琐的端口映射(-p), 并减少 Docker 桥接网卡带来的网络延迟(大模型分布式推理对网络延迟极度敏感).
# 3. --shm-size 10.24g: 增加共享内存.
#    - 为什么? vLLM 在多 GPU(Tensor Parallel)推理时, 底层的 PyTorch/NCCL 主要通过共享内存(/dev/shm)进行卡间高速通信(IPC).
#    - Docker 默认的共享内存仅 64MB, 若不调大, 在分布式初始化或多卡训练/推理时会直接触发 Bus Error (总线错误) 崩溃.
# 4. --gpus all: 将物理机的所有 GPU 挂载进容器.
# 5. -v "${PATH_TO_HF_HOME}:/root/.cache/huggingface": 挂载宿主机的 HuggingFace 模型缓存目录.
#    - 为什么? 避免每次容器重启都重新下载几十上百 GB 的大模型权重, 实现权重文件的持久化与多容器复用.
# 6. "${ADDITIONAL_ARGS[@]}": 安全展开用户传入的额外 Docker 参数(例如额外的环境变量或设备映射).
# 7. -c "${RAY_START_CMD}": 让 bash 执行构建好的 Ray 启动命令.
docker run \
    --entrypoint /bin/bash \
    --network host \
    --name "${CONTAINER_NAME}" \
    --shm-size 10.24g \
    --gpus all \
    -v "${PATH_TO_HF_HOME}:/root/.cache/huggingface" \
    "${ADDITIONAL_ARGS[@]}" \
    "${DOCKER_IMAGE}" -c "${RAY_START_CMD}"
```

---

### 技术要点深入剖析

为了方便您及您的团队更全面地理解上述脚本的设计, 以下对其核心的技术背景进行细化说明:

#### 一、Bash 语法高级特性

* 安全扩展数组 `"${ADDITIONAL_ARGS[@]}"`: 在 Bash 中, 若直接使用 `$ADDITIONAL_ARGS`, 数组中的空格可能会导致参数被错误拆分. 使用带有双引号和 `@` 符号的写法, 能保证每个元素作为独立的参数传递, 防止包含空格的复杂 Docker 选项(如 `-e "KEY=VAL WITH SPACE"`)解析失败.

* 字符串剥离操作 `${variable#pattern}`: 这是 Bash 内置的轻量、高效的字符串截取语法. 相比于调用外部命令 `echo $variable | cut -d'=' -f2`, 这种纯内存操作不涉及子进程创建, 在循环和高频调用时能显著提升脚本性能.

* `trap` 信号捕捉: 这是生产环境 Bash 脚本生命周期管理的核心. 在大模型算力集群中, GPU 属于极度昂贵的资源. 若无 `trap` 捕获异常退出, 用户按 `Ctrl + C` 中断脚本后, 后台容器依然会常驻并持续占用 GPU 显存, 导致其他用户或任务无法初始化 GPU, 甚至导致 GPU OOM 报错.

#### 二、vLLM / Ray 的核心特性与关联

* Ray 的作用机制: vLLM 的分布式架构是将一个物理节点或多个物理节点视作一个统一的计算池. vLLM 服务本身作为 Client/Driver 启动时, 会自动检测当前的 Ray 集群. 如果不提供 Ray 环境, vLLM 在遇到 `--tensor-parallel-size` 大于单机 GPU 数时, 会无法拉起.

* `VLLM_HOST_IP` 与 Ray 绑定的重要性: 在容器环境下, Ray 默认探测到的 IP 通常是 Docker 内部的虚拟网络桥接 IP. 若不通过 `--node-ip-address` 或 `VLLM_HOST_IP` 显式将其纠正为物理宿主机的真实局域网 IP, Worker 节点在尝试向 Head 节点的 `6379` 端口注册后, Head 节点将无法反向路由到 Worker, 导致集群初始化在握手阶段无限超时.

* `--shm-size` 与 NCCL 的关系: vLLM 主要通过 NCCL (NVIDIA Collective Communications Library) 进行张量并行(TP)计算. NCCL 在多卡间同步激活值(Activation)时, 若在单机多卡环境内, 会优先使用系统共享内存(Shared Memory)来进行零拷贝(Zero-copy)的数据交换. 10GB 左右的共享内存是多卡分布式推理的一个相对安全的基准线.

---------------------------------------------------------------------------------------

vllm 如何与 ray 结合起来, 在什么场景下需要使用 ray

`vLLM` 是一款高并发、低延迟的大语言模型(LLM)推理引擎, 而 `Ray` 是一个通用的分布式计算框架. 两者的结合为大模型从"单卡/单机推理"迈向"多机多卡分布式推理"以及"生产级高可用服务"提供了强大的支撑.

下面为您详细梳理 vLLM 与 Ray 的结合方式 以及 在什么场景下需要引入 Ray.

---

### 一、vLLM 与 Ray 的结合方式

vLLM 和 Ray 主要在以下三个维度进行结合:

#### 1. 分布式推理执行后端(Distributed Execution Backend)

在多卡或多机环境下, vLLM 需要在不同的 GPU 上启动 Worker 进程来分别加载模型的分片, 并进行张量并行(Tensor Parallelism, TP)或流水线并行(Pipeline Parallelism, PP).

* 实现原理: vLLM 将 Ray 作为其分布式进程的管理器. 通过设置 `--distributed-executor-backend ray`, vLLM 会通过 Ray 自动在集群的各个节点上拉起对应的 Ray Actor(即 GPU Worker), 并由 Ray 协助完成底层的 NCCL 通信组网和生命周期管理.

#### 2. Ray Serve 生产级服务框架(Model Serving & Orchestration)

如果您需要将 vLLM 封装为高可用、弹性伸缩的微服务, 可以使用 Ray 提供的 Ray Serve 模块.

* 实现原理: Ray Serve 负责流量分发、副本控制器和负载均衡. 它可以将 vLLM 引擎包装为一组 Deployment(部署副本), 根据实时请求量(QPS)在集群内动态增加或减少 vLLM 实例, 甚至支持多模型串联(如将 Embedding 模型与 vLLM 拼接成 Pipeline).

#### 3. Ray Data 大规模离线批处理(Batch Inference)

当需要对海量数据(如百万级样本)进行离线推理或特征提取时, 直接调用 vLLM 可能会遇到 CPU 内存溢出或缺乏容错机制的问题.

* 实现原理: Ray Data 提供了流式(Streaming)数据处理能力. 它将数据集切片, 利用 `map_batches` 算子分布式地分发给多个含有 vLLM 引擎的 Ray Actor 运行, 并在节点故障时提供自动重试和容错.

---

### 二、什么场景下需要使用 Ray?

在单机、单卡或简单的单机多卡场景下, vLLM 默认使用 Python 原生的多进程(Multiprocessing, `mp`)作为执行后端, 此时不需要 Ray.
但在以下场景中, 引入 Ray 会变得非常必要, 甚至不可或缺:

#### 场景 1: 模型过大, 需要多机分布式推理(Multi-Node Inference)

* 原因: 当模型尺寸极大(如 DeepSeek-V3, LLaMA-3-70B, GPT-OSS-120B 等), 单台机器的 GPU 显存(即便 8 卡 A100/H100)也无法完全容纳, 必须跨越物理节点进行分布式部署.

* 为什么用 Ray: Python 原生的 Multiprocessing 无法跨物理机通信, 而 Ray 天生支持跨节点调度. Ray 可以自动识别多台机器的 GPU 资源, 在多台机器间建立 Actor 并组网.

#### 场景 2: 生产环境下的动态弹性伸缩(Autoscaling)

* 原因: 生产环境的流量往往具有波峰和波谷. 如果一直保持最大副本数会造成极大的 GPU 资源浪费; 如果副本数太少, 遇到突发流量则会导致排队和超时.

* 为什么用 Ray: 借助 Ray Serve, 您可以配置基于并发请求数的弹性伸缩策略(如支持缩容到 0 副本以节省成本, 或者在流量激增时自动向 Kubernetes 集群申请新的 GPU 节点并启动 vLLM 副本).

#### 场景 3: 多模型级联与复杂的 AI 业务流水线(Pipeline & DAG)

* 原因: 在实际业务中, 用户请求通常不仅仅经过一个大模型. 例如在 RAG(检索增强生成)场景中, 流程为: `用户 Query -> Embedding 向量化 -> 检索召回 -> Rerank 重排 -> vLLM 文本生成`.

* 为什么用 Ray: Ray Serve 允许您将 Embedding、Rerank、vLLM 分别部署为不同的 Ray Actor 服务, 并通过 Python 调用的方式将它们连结为一个高效、低延迟的 DAG(有向无环图). Ray 会负责这些服务之间的内部高效数据传递, 避免了多次网络 I/O 损耗.

#### 场景 4: 超大规模离线批处理与容错保障(Large-scale Batch Inference)

* 原因: 当需要对 TB 级别的语料进行批量打标、翻译或生成时, 如果中途某个 GPU 进程因为 OOM 或硬件故障挂掉, 使用原生脚本可能导致整个任务中断、数据丢失, 且难以断点续传.

* 为什么用 Ray: Ray Data 配合 vLLM 可以实现流式读取、分布式消费, 不仅吞吐量大, 而且具备高容错性(Fault Tolerance). 当某个计算节点故障时, Ray 会自动拉起新的 Worker 重新处理未完成的分片.

#### 场景 5: 集群资源统一调度与共享(Shared Cluster Resource Management)

* 原因: 如果团队内有一批共享的 GPU 算力, 既要跑模型训练、数据预处理, 又要跑 vLLM 推理服务. 如果不做调度管理, 进程之间会发生严重的 GPU 抢占和冲突.

* 为什么用 Ray: Ray 作为统一的集群底座(例如结合 KubeRay 部署在 Kubernetes 上), 可以通过 Placement Groups(位置组)对 GPU 资源进行颗粒度细致的划分与隔离, 确保 vLLM 实例与其他计算任务互不干扰.

---

### 三、简易使用示例

#### 1. 启动多机 vLLM 集群(使用 Ray 作为后端)

首先在多台机器上配置并启动 Ray 集群:

```bash
# 在主节点(Head Node)启动 Ray
ray start --head --port=6379

# 在其他工作节点(Worker Node)加入集群
ray start --address=<HEAD_NODE_IP>:6379
```

随后, 在主节点直接运行 vLLM, 指定使用 Ray 并在 8 张卡(可跨多机)上运行张量并行:

```bash
vllm serve facebook/opt-13b \
    --tensor-parallel-size 8 \
    --distributed-executor-backend ray
```

#### 2. Python 脚本中使用 Ray 初始化 vLLM

```python
from vllm import LLM

# vLLM 会自动检测当前的 Ray 集群, 并在不同的 GPU(Ray Actors)上初始化模型分片
llm = LLM(
    model="facebook/opt-13b",
    tensor_parallel_size=4,
    distributed_executor_backend="ray" # 显式指定使用 ray 后端
)

outputs = llm.generate(["Hello, my name is"])
```

---------------------------------------------------------------------------------------

```bash
docker pull rayproject/ray:2.55.1-py313-cu129
docker pull rayproject/ray:2.55.1-extra-py313-cu129
```

假设你是一位精通 LLM, 以及精通 k8s 的高级开发人员, 现在我使用容器的方式运行 ray, 启动命令和报错如下:
```
docker run -ti --rm \
--entrypoint /usr/bin/env \
--gpus '"device=2, 6"' \
--name ray-server \
rayproject/ray:2.55.1-extra-py313-cu129 bash

(base) ray@3976e4562db4:~$ ray --help
OpenBLAS blas_thread_init: pthread_create failed for thread 1 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 2 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 3 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 4 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 5 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 6 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 8 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 9 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 10 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 11 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 12 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 13 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 14 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 15 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 16 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 17 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 18 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 19 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 20 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 21 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 22 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 23 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 24 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 25 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 26 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 27 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 28 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 29 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 30 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 31 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 32 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 33 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 34 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 35 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 36 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 37 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 38 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 39 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 40 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 41 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 42 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 43 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 44 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 45 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 46 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 47 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 48 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 49 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 50 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 51 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 52 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 53 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 54 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 55 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 56 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 57 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 58 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 59 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 60 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 61 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 62 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
OpenBLAS blas_thread_init: pthread_create failed for thread 63 of 64: Operation not permitted
OpenBLAS blas_thread_init: ensure that your address space and process count limits are big enough (ulimit -a)
OpenBLAS blas_thread_init: or set a smaller OPENBLAS_NUM_THREADS to fit into what you have available
OpenBLAS blas_thread_init: RLIMIT_NPROC -1 current, -1 max
Traceback (most recent call last):
  File "/home/ray/anaconda3/bin/ray", line 3, in <module>
    from ray.scripts.scripts import main
  File "/home/ray/anaconda3/lib/python3.13/site-packages/ray/scripts/scripts.py", line 2884, in <module>
    from ray.serve.scripts import cli as serve_cli_group
  File "/home/ray/anaconda3/lib/python3.13/site-packages/ray/serve/__init__.py", line 4, in <module>
    from ray.serve._private.logging_utils import configure_default_serve_logger
  File "/home/ray/anaconda3/lib/python3.13/site-packages/ray/serve/_private/logging_utils.py", line 31, in <module>
    from ray.serve._private.utils import get_component_file_name
  File "/home/ray/anaconda3/lib/python3.13/site-packages/ray/serve/_private/utils.py", line 38, in <module>
    import pandas as pd
  File "/home/ray/anaconda3/lib/python3.13/site-packages/pandas/__init__.py", line 14, in <module>
    __import__(_dependency)
    ~~~~~~~~~~^^^^^^^^^^^^^
  File "/home/ray/anaconda3/lib/python3.13/site-packages/numpy/__init__.py", line 114, in <module>
    from numpy.__config__ import show_config
  File "/home/ray/anaconda3/lib/python3.13/site-packages/numpy/__config__.py", line 4, in <module>
    from numpy._core._multiarray_umath import (
    ...<3 lines>...
    )
  File "/home/ray/anaconda3/lib/python3.13/site-packages/numpy/_core/__init__.py", line 23, in <module>
    from . import multiarray
  File "/home/ray/anaconda3/lib/python3.13/site-packages/numpy/_core/multiarray.py", line 10, in <module>
    from . import overrides
  File "/home/ray/anaconda3/lib/python3.13/site-packages/numpy/_core/overrides.py", line 7, in <module>
    from numpy._core._multiarray_umath import (
        add_docstring,  _get_implementing_args, _ArrayFunctionDispatcher)
  File "<frozen importlib._bootstrap>", line 1349, in _find_and_load
KeyboardInterrupt
(base) ray@3976e4562db4:~$
```
请问这是什么原因, 应该如何解决

这个报错是一个在现代容器化(特别是涉及深度学习、LLM)中非常经典且常见的底层系统调用兼容性问题.

### 1. 根本原因剖析

该问题的核心在于: 新版容器内的 `glibc`(自 2.34 版本起)与宿主机上较旧的 Docker Engine / `libseccomp` 安全策略不兼容.

具体链路如下:

1. NumPy 触发线程初始化: 当你在容器内运行 `ray` 或导入 `pandas`/`numpy` 时, 其底层依赖的 OpenBLAS 库会尝试初始化一个多线程线程池(通常与你的 CPU 核心数相同, 这里是 64 个).

2. `clone3` 系统调用受阻: 在 `glibc >= 2.34`(对应的 Python 3.13 基础镜像中), `pthread_create()` 在底层开始改用 `clone3` 系统调用来创建线程, 而不再是传统的 `clone`.

3. Seccomp 拦截: 宿主机上如果 Docker 版本较旧, 其默认的 Seccomp(安全计算模式) 配置文件中并不认识或允许 `clone3` 系统调用, 因此直接拦截并返回了 `EPERM` (Operation not permitted) 错误. 这就导致 OpenBLAS 无法成功创建线程, 进而抛出 `pthread_create failed: Operation not permitted`.

---

### 2. 解决方案

解决此问题有以下几种手段, 你可以根据当前的环境和权限进行选择:

#### 方案一: 在 Docker 启动命令中放开 Seccomp 限制(最快捷)

如果你无法立即升级宿主机系统, 可以通过在 `docker run` 时添加 `--security-opt seccomp=unconfined` 参数来关闭 Seccomp 的系统调用过滤:

```bash
docker run -ti --rm \
  --entrypoint /usr/bin/env \
  --gpus '"device=2, 6"' \
  --security-opt seccomp=unconfined \
  --name ray-server \
  rayproject/ray:2.55.1-extra-py313-cu129 bash
```
(注意: 这会降低一点容器的隔离安全性, 但在开发、测试或受信任的环境中是非常常用的临时解决方法.)

#### 方案二: 如果你在 Kubernetes (K8s) 中运行(精通 K8s 场景)

由于你在生产中可能会把 Ray 跑在 K8s 上(例如使用 KubeRay 部署 RayCluster), K8s Pod 也会默认继承宿主机的容器运行时 Seccomp 限制.

如果遇到此报错, 你需要在 K8s YAML 的 `securityContext` 中将 `seccompProfile` 设置为 `Unconfined`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ray-worker
spec:
  template:
    spec:
      containers:
      - name: ray-node
        image: rayproject/ray:2.55.1-extra-py313-cu129
        securityContext:
          seccompProfile:
            type: Unconfined
        # 其它 GPU、Ray 相关配置...
```

#### 方案三: 升级宿主机的 Docker 和 `libseccomp`(最优雅、最安全)

最根本的解决办法是升级宿主机的相关安全组件, 使其能够原生识别并允许 `clone3`:

1. 将宿主机的 Docker Engine 升级到 `20.10.12` 或更高版本.

2. 确保宿主机的 `libseccomp` 包处于最新状态(例如在 Ubuntu/Debian 宿主机上执行 `sudo apt-get update && sudo apt-get install --only-upgrade libseccomp2`).

#### 方案四: 通过限制 OpenBLAS 线程数绕过(临时规避)

如果只是做极其简单的测试, 并且不想改变容器权限, 可以通过注入环境变量限制 OpenBLAS 不去创建多线程:

在 `docker run` 时加入 `-e OPENBLAS_NUM_THREADS=1` 参数.

注: 由于系统调用本身被禁, 某些依赖多线程的 Python 库在后续运行时仍可能抛出类似的 `pthread_create` 报错, 因此本方法仅适用于非常轻量且无多线程需求的调试.

```bash
docker run -ti --rm \
--entrypoint /usr/bin/env \
--gpus '"device=2, 6"' \
--security-opt seccomp=unconfined \
-e OPENBLAS_NUM_THREADS=8 \
--name ray-server \
rayproject/ray:2.55.1-extra-py313-cu129 bash
(base) ray@e8cbbdd67e5f:~$
(base) ray@e8cbbdd67e5f:~$ ray --version
ray, version 2.55.1
(base) ray@e8cbbdd67e5f:~$
(base) ray@e8cbbdd67e5f:~$ ray --help
Usage: ray [OPTIONS] COMMAND [ARGS]...

Options:
  --logging-level TEXT   The logging level threshold, choices=['debug',
                         'info', 'warning', 'error', 'critical'],
                         default='info'
  --logging-format TEXT  The logging format.
                         default="%%(asctime)s\t%%(levelname)s
                         %%(filename)s:%%(lineno)s -- %%(message)s"
  --version              Show the version and exit.
  --help                 Show this message and exit.

Commands:
  attach               Create or attach to a SSH session to a Ray cluster.
  check-open-ports     Check open ports in the local Ray cluster.
  cluster-dump         Get log data from one or more nodes.
  cpp                  Show the cpp library path and generate the bazel...
  dashboard            Port-forward a Ray cluster's dashboard to the...
  debug                Show all active breakpoints and exceptions in the...
  disable-usage-stats  Disable usage stats collection.
  down                 Tear down a Ray cluster.
  enable-usage-stats   Enable usage stats collection.
  exec                 Execute a command via SSH on a Ray cluster.
  get                  Get a state of a given resource by ID.
  get-auth-token       Prints the Ray authentication token to stdout.
  get-head-ip          Return the head node IP of a Ray cluster.
  get-worker-ips       Return the list of worker IPs of a Ray cluster.
  job                  Submit, stop, delete, or list Ray jobs.
  kill-actor           Kill an actor by name.
  list                 List all states of a given resource.
  logs                 Get logs based on filename (cluster) or resource...
  memory               Print object references held in a Ray cluster.
  metrics
  microbenchmark       Run a local Ray microbenchmark on the current...
  monitor              Tails the autoscaler logs of a Ray cluster.
  rsync-down           Download specific files from a Ray cluster.
  rsync-up             Upload specific files to a Ray cluster.
  serve                CLI for managing Serve applications on a Ray cluster.
  stack                Take a stack dump of all Python workers on the...
  start                Start Ray processes manually on the local machine.
  status               Print cluster status, including autoscaling info.
  stop                 Stop Ray processes manually on the local machine.
  submit               Uploads and runs a script on the specified cluster.
  summary              Return the summarized information of a given...
  symmetric-run        Command to start Ray across all nodes and execute...
  timeline             Take a Chrome tracing timeline for a Ray cluster.
  up                   Create or update a Ray cluster.
(base) ray@e8cbbdd67e5f:~$
(base) ray@e8cbbdd67e5f:~$ ray start --help
Usage: ray start [OPTIONS]

  Start Ray processes manually on the local machine.

Options:
  --node-ip-address TEXT          the IP address of this node
  --address TEXT                  the address to use for Ray
  --port INTEGER                  the port of the head ray process. If not
                                  provided, defaults to 6379; if port is set
                                  to 0, we will allocate an available port.
  --object-manager-port INTEGER   the port to use for starting the object
                                  manager
  --node-manager-port INTEGER     the port to use for starting the node
                                  manager
  --min-worker-port INTEGER       the lowest port number that workers will
                                  bind on. If not set, random ports will be
                                  chosen.
  --max-worker-port INTEGER       the highest port number that workers will
                                  bind on. If set, '--min-worker-port' must
                                  also be set.
  --worker-port-list TEXT         a comma-separated list of open ports for
                                  workers to bind on. Overrides '--min-worker-
                                  port' and '--max-worker-port'.
  --ray-client-server-port INTEGER
                                  the port number the ray client server binds
                                  on, default to 10001, or None if ray[client]
                                  is not installed.
  --object-store-memory INTEGER   The amount of memory (in bytes) to start the
                                  object store with. By default, this is 30%
                                  of available system memory capped by the shm
                                  size and 200G but can be set higher.
  --num-cpus INTEGER              the number of CPUs on this node
  --num-gpus INTEGER              the number of GPUs on this node
  --resources TEXT                A JSON serialized dictionary mapping
                                  resource name to resource quantity.
  --head                          provide this argument for the head node
  --include-dashboard BOOLEAN     provide this argument to start the Ray
                                  dashboard GUI
  --dashboard-host TEXT           the host to bind the dashboard server to,
                                  either localhost (127.0.0.1) or 0.0.0.0
                                  (available from all interfaces). By default,
                                  this is 127.0.0.1
  --dashboard-port INTEGER        the port to bind the dashboard server to--
                                  defaults to 8265
  --dashboard-agent-listen-port INTEGER
                                  the port for dashboard agents to listen for
                                  http on.
  --dashboard-agent-grpc-port INTEGER
                                  the port for dashboard agents to listen for
                                  grpc on.
  --runtime-env-agent-port INTEGER
                                  The port for the runtime environment agents
                                  to listen for http on.
  --block                         provide this argument to block forever in
                                  this command.Process exit logs will be saved
                                  to ray_process_exit.log in the logs
                                  directory.
  --plasma-directory TEXT         object store directory for memory mapped
                                  files
  --object-spilling-directory TEXT
                                  The path to spill objects to. This path will
                                  also be used as the fallback directory when
                                  the object store is full of in-use objects
                                  and cannot spill.
  --autoscaling-config TEXT       the file that contains the autoscaling
                                  config
  --no-redirect-output            do not redirect non-worker stdout and stderr
                                  to files
  --temp-dir TEXT                 manually specify the root temporary dir of
                                  the Ray process. Can be specified per node.
  --metrics-export-port INTEGER   the port to use to expose Ray metrics
                                  through a Prometheus endpoint.
  --ray-debugger-external         Make the Ray debugger available externally
                                  to the node. This is only safe to activate
                                  if the node is behind a firewall.
  --disable-usage-stats           If True, the usage stats collection will be
                                  disabled.
  --include-log-monitor BOOLEAN   If set to True or left unset, a log monitor
                                  will start monitoring the log files of all
                                  processes on this node and push their
                                  contents to GCS. Only one log monitor should
                                  be started per physical host to avoid log
                                  duplication on the driver process.
  --enable-resource-isolation     Enable resource isolation through cgroupv2
                                  by reserving memory and cpu resources for
                                  ray system processes. To use, only cgroupv2
                                  (not cgroupv1) must be enabled with read and
                                  write permissions for the raylet. Cgroup
                                  memory and cpu controllers must also be
                                  enabled.
  --system-reserved-cpu FLOAT     The number of cpu cores to reserve for ray
                                  system processes. Cores can be fractional
                                  i.e. 1.5 means one and a half a cpu core. By
                                  default, the value will be atleast 1 core,
                                  and at maximum 3 cores. The default value is
                                  calculated using the formula min(3.0,
                                  max(1.0, 0.05 * num_cores_on_the_system))
                                  This option only works if
                                  --enable_resource_isolation is set.
  --system-reserved-memory INTEGER
                                  The amount of memory (in bytes) to reserve
                                  for ray system processes. By default, the
                                  value will be atleast 500MB, and at most
                                  10GB. The default value is  calculated using
                                  the formula min(10GB, max(500MB, 0.10 *
                                  memory_available_on_the_system)) This option
                                  only works if --enable_resource_isolation is
                                  set.
  --cgroup-path TEXT              The path for the cgroup the raylet should
                                  use to enforce resource isolation. By
                                  default, the cgroup used for resource
                                  isolation will be /sys/fs/cgroup. The
                                  process starting ray must have read/write
                                  permissions to this path.  Cgroup memory and
                                  cpu controllers be enabled for this cgroup.
                                  This option only works if
                                  enable_resource_isolation is True.
  --proxy-server-url TEXT         [Experimental] The server url to redirect
                                  dashboard backend requests to. By default,
                                  the dashboard requests will be directed to
                                  the Ray api server. If you have a custom
                                  server to serve the dashboard requests, you
                                  can set this option to override the server
                                  url. Ex: --proxy-server-
                                  url=http://historyserver:8080
  --log-style [auto|record|pretty]
                                  If 'pretty', outputs with formatting and
                                  color. If 'record', outputs record-style
                                  without formatting. 'auto' defaults to
                                  'pretty', and disables pretty logging if
                                  stdin is *not* a TTY.
  --log-color [auto|false|true]   Use color logging. Auto enables color
                                  logging if stdout is a TTY.
  -v, --verbose
  --help                          Show this message and exit.
(base) ray@e8cbbdd67e5f:~$

```

---------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm, ray 等的高级开发人员, 我使用如下命令启动了一个 ray 的集群
```bash
docker run \
    --entrypoint /bin/bash \
    --network host \
    --name node-head \
    --shm-size 10.24g \
    --gpus '"device=0, 1"' \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.51 \
    rayproject/ray:2.55.1-extra-py313-cu129 -c ray start --block --head --node-ip-address=172.16.10.51 --port=6379


docker run \
    --entrypoint /bin/bash \
    --network host \
    --name node-worker \
    --shm-size 10.24g \
    --gpus '"device=2, 3"' \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.51 \
    rayproject/ray:2.55.1-extra-py313-cu129 -c ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.51
```
第一: 请帮我检查一下上述启动命令是否需要修改, 第二: 启动 ray 集群之后, vllm 应该如何使用这个集群, vllm 相关的启动命令是怎么样的, 第三说明一下思路和原理

作为一名在分布式深度学习、Ray 以及 vLLM 领域有深厚经验的开发人员, 我为你对现有的 Ray 启动命令进行了仔细的审查. 以下将分为三部分回答你的问题:

1. 启动命令的检查与修正
2. 启动后 vLLM 的使用及启动命令
3. 整体方案的思路与核心原理说明

---

### 第一: 启动命令检查与修正

你提供的 Docker 启动命令中存在几个影响正常运行的语法问题、网络配置冲突隐患以及环境变量配置失误.

#### 1. 核心问题分析

* 问题一: `bash -c` 传参语法错误
  你的命令中使用了 `--entrypoint /bin/bash` 并在镜像名后接 `-c ray start ...`. 在 Docker 中, 如果不加双引号包裹后面的整条命令, `bash -c` 只会把紧跟的第一个单词 `ray` 视作要执行的命令, 而后面的 `start --block ...` 会被当作传递给 `bash` 的位置参数(`$0`, `$1` 等)被忽略掉. 这会导致容器启动后只运行了 `ray`(通常只输出帮助信息), 而没有真正启动 Ray 节点.

* 问题二: 关于"单机双容器"还是"跨机双容器"的配置混淆
  * 情况 A(跨两台物理机): 如果你的 Head 节点在一台机器(`172.16.10.51`), Worker 节点在另一台机器(例如 `172.16.10.52`). 那么在 Worker 容器中, `VLLM_HOST_IP` 和 `--node-ip-address` 必须修改为 Worker 节点的实际物理 IP, 而不是盲目地写 Head 的 IP(`172.16.10.51`). 否则, Ray 无法正确区分节点, 且 vLLM 进行跨节点 NCCL 通信时会因为 IP 指向错误而卡死.
  * 情况 B(在同一台物理机上用两个容器模拟): 如果两容器都在同一台 `172.16.10.51` 物理机上, 因为你使用了 `--network host`, 它们共享宿主机的网络命名空间. 此时, 当 Worker 启动时, 其内部的 `raylet` 试图绑定与 Head 相同的系统端口(如 Dashboard 的 8265 端口、Object Manager 端口、Metrics 端口等), 这会导致端口冲突并导致 Worker 启动失败.
    * 建议: 如果在单机上拥有 4 张卡, 最标准且性能最好的做法是只启动一个容器, 把 4 张 GPU 传给它, 由单个 Ray 节点管理. 不需要多此一举去拆成 Head 容器和 Worker 容器.
* 问题三: 共享内存(`--shm-size`)偏小
  多卡分布式推理(特别是 Tensor Parallel)在使用 PyTorch 和 NCCL 传输数据时, 需要频繁使用共享内存. `10.24g` 对一些中大型模型(如 70B)在多卡间通信时可能不够, 建议调整为更高值, 或者直接设为 `--ipc=host` 共享宿主机内存.
* 问题四: 镜像内置依赖问题
  `rayproject/ray:2.55.1` 镜像是没有预装 `vllm` 的. 如果你直接运行, 需要在容器启动后手动 `pip install vllm`, 或者自行构建包含 vLLM 的自定义镜像.

#### 2. 修正后的启动命令

##### 选择 1: 多台不同的物理机部署(推荐的真实分布式场景)

假设 Head 机 IP 为 `172.16.10.51`, Worker 机 IP 为 `172.16.10.52`.

* Head 节点启动命令(运行在 172.16.10.51 上):

    ```bash
    docker run -d \
        --entrypoint /bin/bash \
        --network host \
        --name node-head \
        --ipc=host \
        --gpus '"device=0,1"' \
        -v "/model:/root/.cache/huggingface" \
        -e VLLM_HOST_IP=172.16.10.51 \
        rayproject/ray:2.55.1-extra-py313-cu129 -c "ray start --block --head --node-ip-address=172.16.10.51 --port=6379"
    ```

* Worker 节点启动命令(运行在 172.16.10.52 上):

    ```bash
    docker run -d \
        --entrypoint /bin/bash \
        --network host \
        --name node-worker \
        --ipc=host \
        --gpus '"device=2,3"' \
        -v "/model:/root/.cache/huggingface" \
        -e VLLM_HOST_IP=172.16.10.52 \
        rayproject/ray:2.55.1-extra-py313-cu129 -c "ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.52"
    ```

##### 选择 2: 单台物理机部署(不推荐分两个容器, 建议单容器合并)

如果你只有一台 `172.16.10.51` 机器, 并拥有 4 张 GPU:

```bash
docker run -d \
    --entrypoint /bin/bash \
    --network host \
    --name node-single \
    --ipc=host \
    --gpus '"device=0,1,2,3"' \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.51 \
    rayproject/ray:2.55.1-extra-py313-cu129 -c "ray start --block --head --node-ip-address=172.16.10.51 --port=6379"
```

---

### 第二: vLLM 如何使用此集群及相关启动命令

当你的 Ray 集群正常启动(即 Worker 已成功连接到 Head)后, vLLM 可以在不需要重新初始化 Ray 的情况下, 直接复用这个外部集群.

#### 1. 准备工作: 在容器内安装 vLLM

因为你使用的是 `rayproject/ray` 基础镜像, 你需要在 Head 容器 中安装 vLLM:

```bash
docker exec -it node-head pip install vllm
```

(注: 分布式环境下, Worker 容器中也必须安装相同版本的 vllm, 你可以通过 `docker exec -it node-worker pip install vllm` 在 Worker 中执行相同操作).

#### 2. vLLM 启动服务命令

进入 Head 容器, 执行以下命令来启动 vLLM:

```bash
# 1. 进入 Head 容器
docker exec -it node-head /bin/bash

# 2. 设置 RAY_ADDRESS 环境变量, 让 vLLM 自动连接已有的本地 Ray 实例
export RAY_ADDRESS="http://127.0.0.1:8265"

# 3. 启动 vLLM OpenAI 兼容服务
# 假设我们要运行一个需要 4 张 GPU 的大模型(Tensor Parallel = 4)
vllm serve facebook/opt-6.7b \
    --tensor-parallel-size 4 \
    --distributed-executor-backend ray \
    --host 0.0.0.0 \
    --port 8000
```
提示: 如果你的模型权重已经在映射的路径 `/model` 中, 可以直接指定本地路径以避免重复下载: `vllm serve /root/.cache/huggingface/hub/models--...`.

---

### 第三: 思路与原理说明

这个部署方案能够成功运作并对模型进行分布式推理, 核心依赖于 Ray 与 vLLM 的协同机制. 其工作原理如下:

#### 1. Ray 节点的资源注册机制

* 在启动 Head 节点时, Ray 在主控端(GCS - Global Control Store, 运行于 6379 端口)初始化一个元数据中心.

* 当 Worker 节点使用 `ray start --address=172.16.10.51:6379` 启动时, 它在本地的 `raylet` 守护进程会自动检测该容器被分配的 GPU 资源(通过 `--gpus '"device=2,3"'` 暴露的两张显卡), 并向 Head 汇报.

* 此时, 整个 Ray 逻辑集群汇总了 Head 上的 2 张卡和 Worker 上的 2 张卡, 在逻辑上形成了一个拥有 4 块 GPU 的统一计算资源池.

#### 2. vLLM 调度与 Placement Group(放置组)

* 当你在 Head 容器中运行 `vllm serve` 并配置 `--tensor-parallel-size 4` 以及 `--distributed-executor-backend ray` 时, vLLM 不会使用 Python 原生的多进程(Multiprocessing), 而是向 Ray 集群申请资源.

* vLLM 会通过 Ray API 创建一个 Placement Group(通常采用 `STRICT_SPREAD` 或 `PACK` 策略), 申请 4 个计算资源束(Bundles), 每个 Bundle 对应 `1 GPU`.

* Ray 的调度器在集群资源池中寻址, 发现 Head 节点有 2 个空闲 GPU, Worker 节点有 2 个空闲 GPU, 正好满足 4 个 GPU 的申请, 于是将这 4 个 Bundle 分配下去, 并在这些槽位上拉起 4 个 `vllm_worker` 的 Ray Actor.

#### 3. 分布式通信(NCCL)与 `VLLM_HOST_IP` 的作用

* Tensor Parallel(张量并行)需要在每次 Transformer 层计算中进行多次多卡间的 All-Reduce 数据同步. 由于 GPU 的计算速度极快, 多卡通信效率决定了推理吞吐量.

* vLLM 的 Actor 在跨节点通信时会调用 PyTorch Distributed 使用 NCCL 引擎.

* 在初始化 NCCL 环(NCCL clique)时, 各个节点上的 GPU 需要通过 TCP 握手确立通信信道.

* `VLLM_HOST_IP` 的作用就在于明确告诉每一个 Worker Actor: "请使用这个具体的物理网卡 IP 去进行跨节点监听与连接建立". 如果这个 IP 设置错误, NCCL 可能会尝试绑定到容器内不可达的虚拟网段, 从而导致服务启动时在 `Waiting for NCCL...` 步骤无限卡死.

* 通过 `--network host` 模式, 容器直接使用了宿主机的网络协议栈, 完全绕过了 Docker 桥接网卡的虚拟化网络损耗, 这使得跨物理机 NCCL 通信的延迟和带宽能够逼近物理极限.

---------------------------------------------------------------------------------------

Q: 我现在使用多台不同的物理机进行部署, Ray Head 机 IP 为 `172.16.10.51`, 2 张显卡, Ray Worker 机 IP 为 `172.16.10.52`, 2 张显卡, vllm serve 机 IP 为 `172.16.10.53`, 没有显卡. 在这个三台物理机上都使用容器的方式进行部署, 请帮我总结部署的命令和客户端请求的方法

在这种三台物理机(A、B 用于 GPU 计算, C 用于无显卡的 API 接入层)的场景下, 采用的是典型的计算与 API 网关分离(Decoupled Architecture)架构.

在这种设计下, 无显卡的 Machine C 将作为 Ray 宿主集群的一个 CPU 节点运行, 并作为 vLLM Driver(驱动端)运行 API 服务. Machine A 和 Machine B 仅作为 GPU 算力节点提供计算.

以下为您总结三台物理机的部署命令、vLLM 的启动步骤以及客户端请求方法.

---

### 第一部分: 三台物理机部署命令

为了确保 Ray 集群能够正常握手, 所有节点的 Python 版本、Ray 版本必须保持高度一致. 因此, 即使 Machine C 没有显卡, 我们依然建议使用相同的 Docker 镜像.

#### 1. Machine A(Ray Head 节点 | IP: `172.16.10.51`)

拥有 2 张显卡. 启动命令如下:

```bash
docker run -d \
    --network host \
    --name ray-head \
    --ipc=host \
    --gpus '"device=0,1"' \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.51 \
    rayproject/ray:2.55.1-extra-py313-cu129 \
    bash -c "ray start --block --head --node-ip-address=172.16.10.51 --port=6379"
```

#### 2. Machine B(Ray GPU Worker 节点 | IP: `172.16.10.52`)

拥有 2 张显卡. 启动命令如下(注意: 这里的 `--gpus '"device=0,1"'` 指的是该机器本地的前两张卡):

```bash
docker run -d \
    --network host \
    --name ray-worker-gpu \
    --ipc=host \
    --gpus '"device=0,1"' \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.52 \
    rayproject/ray:2.55.1-extra-py313-cu129 \
    bash -c "ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.52"
```

#### 3. Machine C(Ray CPU Worker 节点 / API 网关 | IP: `172.16.10.53`)

无显卡. 作为 CPU 节点加入集群, 启动命令如下:

```bash
docker run -d \
    --network host \
    --name ray-worker-cpu \
    --ipc=host \
    -v "/model:/root/.cache/huggingface" \
    -e VLLM_HOST_IP=172.16.10.53 \
    rayproject/ray:2.55.1-extra-py313-cu129 \
    bash -c "ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.53"
```
(注: Machine C 必须挂载 `/model` 路径, 因为 vLLM 的 API 驱动端在处理请求时, 需要加载本地的分词器 tokenizer 权重进行文本编解码.)

---

### 第二部分: 启动 vLLM 服务 (在 Machine C 上执行)

所有容器成功运行并加入 Ray 集群后, 我们需要在 Machine C(无显卡机)上启动 vLLM 实例.

#### 1. 安装 vLLM 依赖

在 三台机器的容器内 均需安装 vLLM 以确保分布式 Actor 的代码一致:

```bash
# 分别在 Machine A, B, C 的容器内执行
docker exec -it <容器名> pip install vllm
```

#### 2. 在 Machine C 容器内启动服务

进入 Machine C 的容器, 配置环境变量并启动服务:

```bash
# 1. 进入 Machine C 的容器
docker exec -it ray-worker-cpu /bin/bash

# 2. 设置连接本地已加入的 Ray 实例
export RAY_ADDRESS="auto"

# 3. 启动服务(通过 --tensor-parallel-size 4 调度 A、B 上的 4 张 GPU)
vllm serve Qwen/Qwen2.5-7B-Instruct \
    --tensor-parallel-size 4 \
    --distributed-executor-backend ray \
    --host 0.0.0.0 \
    --port 8000
```

---

### 第三部分: 客户端请求方法

vLLM 启动后会在 Machine C(`172.16.10.53:8000`)上暴露与 OpenAI 兼容的 API. 你可以通过以下两种主流方式发起请求:

#### 方法 1: 使用 `curl` 命令行请求

在任意能够访问到 `172.16.10.53` 网络的服务端或个人电脑上执行:

```bash
curl http://172.16.10.53:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手. "},
            {"role": "user", "content": "请简要解释什么是大语言模型的分布式推理. "}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }'
```

#### 方法 2: 使用 Python `openai` 客户端 SDK

在你的客户端应用程序中, 安装 `openai` 包:

```bash
pip install openai
```

编写请求代码:
```python
from openai import OpenAI

# 将 base_url 指向 Machine C 的 IP
client = OpenAI(
    base_url="http://172.16.10.53:8000/v1",
    api_key="token-not-needed"  # vLLM 默认不需要 API Key, 可填任意字符
)

completion = client.chat.completions.create(
    model="Qwen/Qwen2.5-7B-Instruct",
    messages=[
        {"role": "user", "content": "请用一句话概括 Ray 的作用. "}
    ]
)

print(completion.choices[0].message.content)
```

---

### 第四部分: 核心原理解释

1. 分布式组件分工
   * API Gateway (Machine C): 不参与矩阵乘法等重度 GPU 计算. 它只负责接收 HTTP 请求、将文本转化为 Token (Tokenization)、向计算节点发起推理任务调度, 以及最后将 Token 还原为文本 (Detokenization) 并流式返回给用户.

   * GPU Workers (Machine A & B): 作为 Ray 的 GPU 计算 Actor 存在. 它们载入模型并进行高性能的张量并行计算.

2. 为什么需要将 Machine C 注册为 Ray 节点?
   * vLLM 在执行 `vllm serve` 时, 会通过本地的 Ray 驱动程序向 Ray GCS 申请 Placement Group(放置组). 由于 Machine C 已经在 Ray 拓扑中, 它可以非常方便地和 Head 节点(Machine A)进行内部元数据通信, 直接将 GPU 计算子任务分派给机器 A 和 B.

3. 数据流走向
   * 请求输入: Client $\rightarrow$ `172.16.10.53:8000` (Machine C 编解码).
   * 内部计算: Machine C $\rightarrow$ 通过 Ray 内部通信协议分发数据 $\rightarrow$ Machine A 与 Machine B (GPU 之间通过 10Gbps/100Gbps 物理网络使用 NCCL 进行高速 Tensor Parallel 运算).
   * 响应输出: Machine A & B 计算出的 Logits $\rightarrow$ 返回给 Machine C (拼装为文本) $\rightarrow$ Client.

---------------------------------------------------------------------------------------

Q: 对于上述启动命令和核心原理解释, 我有两个疑问,
第一: 可以不将 Machine C 注册为 Ray 节点吗, 在 Machine C 上只启动 vllm serve 服务, 通过环境变量找到 ray 集群, 这种思路可以吗?
第二: 为什么需要在三台机器的容器内均需安装 vLLM, 只在 Machine C 中安装 vllm 可以吗? 甚至在 Machine C 上直接使用 vllm/vllm-openai:v0.20.0-cu129-ubuntu2404 镜像, 这是可行的吗?

这两个疑问切中了 vLLM 与 Ray 分布式协同底层的核心设计痛点. 在实际的大模型生产环境部署中, 这两个问题非常经典. 以下为您进行深入解答:

---

### 第一: 可以不将 Machine C 注册为 Ray 节点吗?

结论是: 不行. 在目前的 vLLM 架构下, Machine C 必须注册为 Ray 节点.

#### 核心原理解释

即使你在 Machine C 上通过环境变量设置了 `RAY_ADDRESS=172.16.10.51:6379`, 如果不事先在 Machine C 上执行 `ray start` 将其作为节点加入集群, vLLM 的服务启动依然会报错崩溃.

1. 依赖本地节点元数据(`node_ip_address.json` 限制)
   vLLM 的引擎在初始化分布式执行器(`RayGPUExecutor`)时, 需要调用 Ray 的 Runtime Context 来获取本地节点的 IP 和拓扑状态.
   在这个过程中, vLLM 底层会去读取本地路径 `/tmp/ray/session_...` 下的一个关键配置文件 `node_ip_address.json`.
   * 如果 Machine C 不是 Ray 节点(即没有在本地运行 `ray start`), 这个本地会话目录和 JSON 文件将不存在.
   * 此时, vLLM 会抛出如下经典报错并直接退出:
     > `Can't find a node_ip_address.json file from /tmp/ray/session_xxx. Have you started Ray instance using ray start or ray.init?`

2. Ray Client 的限制
   如果你尝试让 Machine C 以"Ray 外部客户端(Ray Client)"的形式(即 `ray://172.16.10.51:10001`)连接, vLLM 底层代码由于并未对纯 Client 模式进行完整的兼容适配, 同样会因为无法定位到本地物理节点的状态而初始化失败.

因此, 为了让 Machine C 充当 Driver 并拉起 API 服务, 它必须至少作为一个 CPU-only 节点加入到 Ray 拓扑网中.

---

### 第二: 为什么三台机器都需要安装 vLLM? 直接用官方 `vllm/vllm-openai` 镜像可行吗?

#### 1. 为什么 A、B、C 节点都必须安装 vLLM?

这是由 Ray 的序列化与代码分发机制决定的.

* Ray 的 RPC 机制: Machine C 上的 `vllm serve` 启动时, 它只是一个"控制端(Driver)". 它会通过 Ray 的 API 告诉集群: "请在 GPU 节点(Machine A 和 B)上实例化几个名为 `RayWorker` 的分布式执行 Actor".

* 反序列化失败风险: 当 Machine A 和 Machine B 的本地守护进程(`raylet`)接收到这个创建 Actor 的指令后, 它们会在本地的 Python 工作进程中去还原(反序列化)并导入 `vllm.worker.ray_worker.RayWorker` 这个类.

* 致命报错: 如果 Machine A 和 B 的容器内没有安装 `vllm` 库, 它们的 Python 解释器在尝试加载这个类时, 会立即抛出 `ModuleNotFoundError: No module named 'vllm'`, 导致 Ray Actor 启动失败, 进而导致 Machine C 上的主服务崩溃.

核心准则: 在 Ray 的分布式世界中, 任何节点只要需要承载某个库定义的 Task 或 Actor, 该节点的环境中就必须安装对应的 Python 依赖包.

---

#### 2. 在 Machine C 上直接使用官方 `vllm/vllm-openai` 镜像可行吗?

可行, 但有一个极端关键的限制前提: 全集群的 Python 版本和 Ray 版本必须严格一致.

Ray 框架对分布式节点之间的版本一致性要求非常严苛. 如果节点之间的版本发生偏差, Ray 往往会在节点握手阶段直接报错, 拒绝节点加入集群.

* 版本冲突风险分析:
  * 你在 Machine A 和 B 上使用的是 `rayproject/ray:2.55.1-extra-py313-cu129`(使用 Python 3.13, Ray 2.55.1).

  * 官方的 `vllm/vllm-openai` 镜像(例如较新版本)可能内置的是 Python 3.10 或 3.12, 且内置的 Ray 版本可能为 2.40.0 等其他版本.

  * 如果你直接在 Machine C 上使用该镜像并尝试连接 Machine A 的 Head 节点, Ray 会在连接时直接抛出 `RuntimeError: Version mismatch`, 导致 Machine C 无法加入集群.

#### 生产环境的最佳实践方案

在分布式部署中, 为了避免上述繁琐的版本对齐问题, 业界通常采用以下统一镜像方案:

在 Machine A、Machine B、Machine C 上统一使用完全相同的 `vllm/vllm-openai` 官方镜像.

* 不用担心无显卡的问题: 即使 Machine C 没有显卡, 它同样可以正常运行包含了 CUDA/C++ 算子的 `vllm/vllm-openai` 镜像. 它在启动时, Ray 会自动识别出该节点的 GPU 数量为 0.

* 省去手动安装步骤: 这样可以确保三台机器内的 Python 版本、Ray 版本、vLLM 版本以及相关科学计算库版本 100% 绝对一致, 从根本上杜绝了序列化失败和版本冲突的问题.

##### 示例: 使用统一镜像拉起集群

1. Machine A (Head):

   ```bash
   docker run -d --network host --ipc=host --gpus '"device=0,1"' \
     -v "/model:/root/.cache/huggingface" \
     vllm/vllm-openai:latest \
     ray start --block --head --node-ip-address=172.16.10.51 --port=6379
   ```

2. Machine B (GPU Worker):

   ```bash
   docker run -d --network host --ipc=host --gpus '"device=0,1"' \
     -v "/model:/root/.cache/huggingface" \
     vllm/vllm-openai:latest \
     ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.52
   ```

3. Machine C (CPU Web Gateway):

   ```bash
   docker run -d --network host --ipc=host \
     -v "/model:/root/.cache/huggingface" \
     vllm/vllm-openai:latest \
     ray start --block --address=172.16.10.51:6379 --node-ip-address=172.16.10.53
   ```

4. 启动服务: 直接在 Machine C 容器内执行 `vllm serve ... --tensor-parallel-size 4` 即可.

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------
