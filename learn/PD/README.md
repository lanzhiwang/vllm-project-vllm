# Disaggregated Prefill
分散预填充物

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/disaggregated_prefill/

> 注意是 vllm v0.20.0 版本
>

Source https://github.com/vllm-project/vllm/blob/main/examples/online_serving/disaggregated_prefill.sh.

------------------------------------------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 bash 脚本用于 vllm 的相关功能
```bash
# disaggregated_prefill.sh
```
请为这个脚本添加注释, 一是说明 bash 脚本的一些语法, 二是说明为什么要这么写, 三是说明 vllm 的相关特性和参数含义

这份 Bash 脚本展示了 vLLM 的一个高级特性: 预填充与解码分离(Disaggregated Prefill & Decode, 简称 `P/D 分离`).

在传统的 LLM 推理中, Prefill(吞吐量导向, 计算密集型)和 Decode(延迟导向, 访存密集型)运行在相同的 GPU 实例上, 两者会互相抢占资源, 导致首字延迟(TTFT)和双字间隔时间(ITL)难以同时优化. P/D 分离通过将这两个阶段分配到不同的 GPU 实例上运行, 并通过高速网络(如 NCCL)传输中间生成的 KV Cache, 从而实现更高效的算力匹配.

下面是为您精心添加了详细注释的脚本, 以及针对 Bash 语法、设计原因和 vLLM 参数特性的深度剖析.

---

### 一、完整带注释的 Bash 脚本

```bash
```

---

### 二、核心部分深度解析

#### 1. 为什么代码要这样设计? (设计意图说明)

* 资源物理隔离 (`CUDA_VISIBLE_DEVICES`)

  Prefill 任务和 Decode 任务分别绑定在不同的 GPU(GPU 0 和 GPU 1). 在真实生产环境中, Prefill 阶段通常可以使用算力更高的卡(如 H100), 而 Decode 可以使用性价比更高的卡, 或者通过更小规模的 Tensor Parallel 部署.

* 后台异步执行与端口轮询 (`wait_for_server`)

  大模型启动时, 加载权重、初始化 CUDA 上下文和分配 KV Cache 显存需要耗费数十秒甚至数分钟. 如果直接依次同步运行, 脚本会被阻塞. 使用 `&` 放入后台, 并配合 `curl /v1/models` 轮询检查, 可以确保服务彻底准备就绪后再运行 Proxy.

* 安全清理机制 (`trap` 与 `kill`)

  在多实例分布式部署中, 如果中途出错或者用户强行中断, 留在后台的 vLLM 进程通常会继续霸占 GPU 显存. 使用 `trap 'cleanup' INT` 能够捕获用户的 Ctrl+C 行为, 强行释放显卡资源.

#### 2. vLLM 特性与参数详解 (`--kv-transfer-config`)

这是 P/D 分离的核心参数, 它接受一个 JSON 字符串, 用以配置分布式 KV Cache 的传输网络:

* `"kv_connector": "P2pNcclConnector"`

  指定 KV Cache 的传输连接器. `P2pNcclConnector` 使用 PyTorch 分布式底层的 NCCL(Nvidia Collective Communications Library)库, 通过 GPU 之间的高速通道(如 NVLink 或 PCIe)直接进行 Peer-to-Peer 传输. 这种方式几乎不经过 CPU 主存, 传输效率极高.

* `"kv_role": "kv_producer"` 与 `"kv_consumer"`

  定义节点的角色:

    * `kv_producer`: 生产者(运行于 Prefill 实例), 负责计算 Prompt 的 Attention, 生成 KV Cache 并将其"推送"出去.

    * `kv_consumer`: 消费者(运行于 Decode 实例), 自己不进行长 Prompt 的 Prefill 动作, 而是"接收"生产者传过来的 KV Cache, 并在此基础上进行自回归解码(生成 Token).

* `"kv_rank"` 和 `"kv_parallel_size"`

  构建传输的分布式拓扑关系. 这里 `kv_parallel_size` 设为 `2`(表示一共有两个实例参与 P/D 传输结构). Prefill 的 rank 为 `0`, Decode 的 rank 为 `1`.

* `"kv_buffer_size"`

  设置用于暂存 KV 数据的缓冲区大小(单位: 字节). Prefill 实例设为 `1e9`(约 1GB), Decode 实例设为 `1e10`(约 10GB). 合理的缓冲区能够平滑网络传输的峰值波动.

* `"kv_port"`

  各个节点在建立 NCCL 连接时, 用于通信握手和初始化的内部端口.

* `kv_connector_extra_config` 的子项:

  * `"proxy_ip"` / `"proxy_port"`: 注册 P/D 连接器的控制端代理地址与端口(此处为 `30001`).

  * `"http_ip"` / `"http_port"`: 当前实例暴露的对外 HTTP API 服务地址, 用于 Proxy 转发请求.

  * `"send_type": "PUT_ASYNC"`: 异步发送模式. Prefill 实例计算完后, 会将 KV Cache 放入传输队列, 无需阻塞等待 Decode 实例完全接收完, 即可开始处理下一个 Prefill 请求. 这极大地提高了 Prefill 阶段的吞吐率.

#### 3. 请求代理流量走向

1. 客户端向本地端口 `8000`(由 `disagg_prefill_proxy_server.py` 监听)发送 `max_tokens: 10` 的请求.

2. Proxy 截获请求, 将请求参数改写为 `max_tokens: 1`, 发送给 `8100`(Prefill 实例).

3. `8100` 实例在 GPU 0 上完成 Prompt 预填充, 通过 NCCL 直接将数据投递给 `8200`(Decode 实例), 并响应给 Proxy.

4. Proxy 收到响应后, 再将未完成的生成请求(或继续生成请求)转发给 `8200`(Decode 实例).

5. `8200` 实例从本地接收缓冲区提取对应的 KV Cache, 在 GPU 1 上完成后续 10 个 Token 的自回归解码生成, 最终把结果返回给客户端.

------------------------------------------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 python 脚本用于运行 vllm P/D 分离的协调代理
```python
```
请为这个脚本添加注释, 一是说明为什么要这么写, 二是说明其中一些深层次的原理

这个 Python 脚本是 vLLM 预填充与解码分离(P/D 分离)架构中的 Control Plane(控制面代理).

在 P/D 分离架构中, 数据流(KV Cache 的传输)是通过 GPU 之间的 NCCL 直连通道高速传输的(Data Plane, 数据面); 而控制流(决定哪个请求何时做 Prefill、何时做 Decode, 并为其分配、绑定通道)则是由这个 Python 代理服务器来进行协调的.

---

### 一、完整带注释的 Python 脚本

这里对脚本中核心设计、异步处理、网络流控制以及 vLLM 特有机制进行了详细的中文注释:

```python
# disagg_prefill_proxy_server.py
```

---

### 二、深层原理剖析

作为高级开发人员, 要深刻理解该代理的设计, 需要下钻到 vLLM 调度器和 GPU 算力分配的底层逻辑:

#### 原理 1: 元数据隐式路由机制(Request-ID 命名黑客技术)

在代码中, `request_id` 的生成格式如下:

```python
request_id = f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_{DECODE_KV_ADDR}_{uuid.uuid4().hex}"
```

* 为什么要通过 HTTP 请求头来传网络地址?

  在超大规模的集群或动态扩缩容(K8s)环境下, Prefill 实例和 Decode 实例可能存在多对多关系. 如果使用静态配置文件配置对方的通信端口, 系统将无法弹性伸缩.

* 深层原理:

  vLLM 底层的 `P2pNcclConnector` 在接收到 HTTP 请求头 `X-Request-Id` 后, 会使用正则表达式或字符串匹配提取 `___prefill_addr_` 和 `___decode_addr_` 的内容.

    * Prefill 节点拿到这个字符串, 就知道自己的 KV 传输线程要把计算好的 Tensor 投递给谁(即 `DECODE_KV_ADDR` 的套接字连接).

    * Decode 节点拿到同一个 ID 后, 知道自己需要去监听并接收来自 `PREFILL_KV_ADDR` 的数据.

    这实现了按需动态建链(On-demand P2P Connection), 使代理层完全解耦了底层网络发现.

#### 原理 2: 两阶段截断调度模型(为什么是 `max_tokens=1`?)

在 `process_request` 中, 代码将发给 Prefill 节点的请求的 `max_tokens` 强行改写成了 `1`.

* 深层原理:

  在 Transformer 模型中, 推理分为两步:

    1. Prefill(预填充): 对所有 Prompt 输入进行 Self-Attention. 此阶段所有 Token 是并行计算的(矩阵乘法, Compute-bound), 并在 GPU 显存中产生一个完整的 $\text{Keys}$ 和 $\text{Values}$ 矩阵(即 KV Cache).

    2. Decode(解码): 拿着上一步计算好的 KV Cache, 自回归地一次产生一个 Token(Memory-bound).

      * 如果设置 `max_tokens=0`: 很多推理引擎在遇到 `max_tokens=0` 时, 会认为是非法参数或者直接退化成空请求, 从而拒绝计算 Prompt.

      * 设为 `max_tokens=1`: 能够强迫 vLLM 的后端执行完整的 Prefill 阶段(对输入 Prompt 做 Forward 计算), 并强制生成第一个 Token. 一旦生成了这一步, 当前上下文所对应的所有 Attention 键值(KV Cache)就已在 GPU 显存内实例化完成. 此时底层 `Connector` 就可以安全地把它们整体搬运到网络上.

#### 原理 3: 零拷贝数据通道(为什么代理不传输 KV Cache 本身?)

在设计分布式系统时, 最忌讳"大对象过网关".

* 一个 4096 长度的 Prompt 在 Meta-Llama-3-8B 上产生的 KV Cache 大约有上百兆大小. 如果 KV Cache 先从 Prefill 节点发送回这个 Python 代理服务器, 再由代理转发给 Decode 节点, Python 的垃圾回收(GC)、多进程/多线程切换和用户态与内核态的多次 `memcpy` 会瞬间拖垮整个集群的吞吐.

* 深层原理:

  这个 Python 脚本在这里仅扮演信号塔(Control Plane).

    1. 代理只负责发送简短的 JSON 控制命令.

    2. Prefill 节点启动了 vLLM 自研的 `P2pNcclConnector`, 该连接器在内部通过 PyTorch 的通信后端拉起了一个本地 NCCL 组(Communicator).

    3. 数据(KV Cache Tensor)会通过 GPU 底层的高速互联总线(如 NVLink、RoCEv2 网络、PCIe Gen4/5)在两个 GPU 的显存之间进行直连物理拷贝, 完全绕过 Python 代理.

#### 原理 4: 异步协程与流式响应(Quart + aiohttp)

* 为什么要采用异步 `async` / `await`?

  如果是传统的同步服务(如使用 Flask 或 Python requests), 一个请求被处理时, 当前的操作系统线程会被 `requests.post()` 挂起, 直到后端推理完(可能需要几十秒). 对于 1000 个并发请求, 你需要维护 1000 个物理线程, 这会导致内存耗尽、频繁的上下文切换以及高昂的延迟.

* 深层原理:

  Quart 运行于由 `asyncio` 驱动的单线程事件循环(Event Loop)中.

    1. 当执行到 `await _run_prefill` 时, 当前协程将控制权主动交回事件循环, 转去处理其他客户端的传入请求.

    2. 当网络的网卡上有数据返回(例如 aiohttp 收到 Prefill 完成的 TCP 信号)时, 事件循环再唤醒对应的协程继续执行 `_stream_decode`.

    3. 通过 `async for chunk_bytes in resp.content.iter_chunked` 机制, 网络接收缓冲区一收到来自 Decode 节点产生的若干字节数据, 就能立即通过 HTTP Trunked Response(分块传输编码)推送回用户的客户端. 整个代理层既保证了低首字延迟(TTFT), 也避免了任何线程阻塞.

------------------------------------------------------------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, vllm 源码中提供了一个预填充与解码分离(Disaggregated Prefill & Decode, 简称 `P/D 分离`)的示例, 代码如下:
```bash
# disaggregated_prefill.sh
```

```python
# disagg_prefill_proxy_server.py
```
现在我想在容器中部署和运行这个示例, 我想使用的基础镜像是 `vllm/vllm-openai:v0.22.0-cu129-ubuntu2404`, 请根据上述示例代码, 将这个示例改写成在容器中运行, 请列出详细的操作步骤和完整的代码

将预填充与解码分离(Disaggregated Prefill & Decode, 简称 P/D 分离)迁移到容器中运行, 是工业界提升大模型吞吐与降低首次生成延迟(TTFT)的核心实践.

在将你提供的脚本容器化时, 从底层架构的角度需要重点解决以下 4 个关键问题:

1. GPU 拓扑与隔离: Prefill(计算密集型)和 Decode(显存带宽密集型)需要分别挂载不同的物理卡(例如 GPU 0 和 GPU 1).

2. NCCL P2P 跨进程通信与共享内存(IPC): 底层传输使用的是 `P2pNcclConnector`, 数据在两个实例间通过 NVLink/PCIe 直连拷贝, 容器必须配置足够的共享内存(`--shm-size`)或直接使用宿主机 IPC(`--ipc=host`), 否则 NCCL 初始化会直接崩溃或死锁.

3. 网络监听绑定(踩坑点): 原 Python 脚本中 `app.run(port=PORT)` 默认只监听 `127.0.0.1`. 若放入容器且未配置 host 网络, 外部宿主机将无法通过端口映射访问服务, 必须将其绑定到 `0.0.0.0`.

4. 依赖补充: 官方镜像 `vllm/vllm-openai:v0.22.0-cu129-ubuntu2404` 默认未预装 `quart`, 需要在镜像构建层或启动时安装.

---

针对你的需求, 本文提供两种最主流的容器化落地方案:

- 方案一(推荐首选): 单容器一体化运行(All-in-One 模式). 最适合单机双卡快速验证、压测与原汁原味复现原 Bash 行为, 部署成本最低.
- 方案二(生产演进): Docker Compose 微服务解耦模式. 将 Prefill、Decode、Proxy 拆分为 3 个独立容器, 还原真实的分布式微服务编排.

---

### 方案一: 单容器一体化部署(All-in-One 模式)

#### 1. 目录结构

创建一个独立的工作目录:

```bash
disagg_docker/
├── Dockerfile
├── entrypoint.sh
└── disagg_prefill_proxy_server.py
```

#### 2. 代码实现

##### (1) 改造后的代理服务器代码: `disagg_prefill_proxy_server.py`

在原代码基础上补充 `--host` 参数, 并将默认绑定地址改为 `0.0.0.0`, 确保容器端口可以被宿主机映射访问:

```python
# disagg_prefill_proxy_server.py
```

##### (2) 容器启动主入口脚本: `entrypoint.sh`

负责拉起 Prefill、Decode 与 Proxy, 并正确传递 `SIGTERM` / `SIGINT` 信号实现进程组回收, 保证容器常驻运行:

```bash
# entrypoint.sh
```

##### (3) 构建镜像 Dockerfile

使用你指定的基准镜像 `vllm/vllm-openai:v0.22.0-cu129-ubuntu2404`:

```dockerfile
```

#### 3. 详细操作步骤

##### 第一步: 构建 Docker 镜像

```bash
docker build -t vllm-disagg-demo:v0.22.0 .
```

##### 第二步: 启动容器

> ⚠️ 关键参数说明:
> - `--gpus '"device=0,1"'`: 必须分配至少两张 GPU 卡.
> - `--ipc=host`: 必须开启. 确保 NCCL 能够使用宿主机的共享内存进行点对点显存数据交换.
> - `-v ~/.cache/huggingface:/root/.cache/huggingface`: 挂载宿主机模型缓存, 避免每次启动容器重新下载大模型权重.
>

```bash
docker run -d \
  --name vllm-disagg \
  --runtime nvidia \
  --gpus '"device=0,1"' \
  --ipc=host \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e HF_TOKEN="your_hf_token_if_needed" \
  -e HF_MODEL_NAME="meta-llama/Meta-Llama-3.1-8B-Instruct" \
  vllm-disagg-demo:v0.22.0
```

##### 第三步: 查看启动日志

```bash
docker logs -f vllm-disagg
```

当日志输出 `🎉 Cluster is fully operational! Listening on 0.0.0.0:8000` 时, 表明 P 节点、D 节点与 Proxy 均已拉起就绪.

---

### 方案二: Docker Compose 微服务解耦部署(生产标准模式)

在生产环境中, Prefill 实例与 Decode 实例通常部署在不同的容器中. 两个容器跨进程使用 `P2pNcclConnector` 时, 网络必须互通, 且需要共享 IPC.

#### 1. 准备 Proxy 专用轻量镜像或共用基镜像

我们在宿主机准备好 `disagg_prefill_proxy_server.py`, 直接复用 `docker-compose.yml` 编排.

#### 2. `docker-compose.yml` 配置
使用 `network_mode: "host"` 和 `ipc: "host"`, 这是单机多容器跑 NCCL 吞吐最高、最不容易踩坑的组合:

```yaml
version: "3.8"

services:
  prefill-node:
    image: vllm/vllm-openai:v0.22.0-cu129-ubuntu2404
    container_name: vllm-prefill
    ipc: host
    network_mode: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0']
              capabilities: [gpu]
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - HF_TOKEN=${HF_TOKEN}
    command: >
      serve meta-llama/Meta-Llama-3.1-8B-Instruct
      --host 0.0.0.0
      --port 8100
      --max-model-len 100
      --gpu-memory-utilization 0.8
      --trust-remote-code
      --kv-transfer-config '{"kv_connector":"P2pNcclConnector","kv_role":"kv_producer","kv_rank":0,"kv_parallel_size":2,"kv_buffer_size":"1e9","kv_port":"14579","kv_connector_extra_config":{"proxy_ip":"127.0.0.1","proxy_port":"30001","http_ip":"127.0.0.1","http_port":"8100","send_type":"PUT_ASYNC"}}'
    restart: unless-stopped

  decode-node:
    image: vllm/vllm-openai:v0.22.0-cu129-ubuntu2404
    container_name: vllm-decode
    ipc: host
    network_mode: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['1']
              capabilities: [gpu]
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - HF_TOKEN=${HF_TOKEN}
    command: >
      serve meta-llama/Meta-Llama-3.1-8B-Instruct
      --host 0.0.0.0
      --port 8200
      --max-model-len 100
      --gpu-memory-utilization 0.8
      --trust-remote-code
      --kv-transfer-config '{"kv_connector":"P2pNcclConnector","kv_role":"kv_consumer","kv_rank":1,"kv_parallel_size":2,"kv_buffer_size":"1e10","kv_port":"14580","kv_connector_extra_config":{"proxy_ip":"127.0.0.1","proxy_port":"30001","http_ip":"127.0.0.1","http_port":"8200","send_type":"PUT_ASYNC"}}'
    restart: unless-stopped

  proxy-server:
    image: python:3.11-slim
    container_name: vllm-disagg-proxy
    network_mode: host
    volumes:
      - ./disagg_prefill_proxy_server.py:/app/disagg_prefill_proxy_server.py
    working_dir: /app
    command: >
      bash -c "pip install --no-cache-dir quart aiohttp &&
               python3 disagg_prefill_proxy_server.py
               --host 0.0.0.0
               --port 8000
               --prefill-url http://127.0.0.1:8100
               --decode-url http://127.0.0.1:8200
               --kv-host 127.0.0.1
               --prefill-kv-port 14579
               --decode-kv-port 14580"
    depends_on:
      - prefill-node
      - decode-node
    restart: unless-stopped
```

#### 3. 运行 Docker Compose
```bash
docker compose up -d
docker compose logs -f proxy-server
```

---

### 三、验证与测试

当容器成功启动并监听 8000 端口后, 在宿主机或任意能够访问该机器的客户端上执行请求:

#### 1. 基础请求测试
```bash
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "prompt": "San Francisco is a",
    "max_tokens": 16,
    "temperature": 0
  }'
```

#### 2. 流式传输(SSE Stream)验证
P/D 分离最大的价值之一在于维持流式生成的平滑低延迟(降低 ITL), 验证流式输出:
```bash
curl -N -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "prompt": "The future of AI is",
    "max_tokens": 30,
    "stream": true
  }'
```

---

### 四、高级调优与生产避坑要点

1. NVLink 与 PCIe P2P 权限:
   `P2pNcclConnector` 在传输 KV Cache 时依赖 CUDA IPC. 在多容器下, 如果容器间无法通过 NVLink 直接 P2P(例如使用云厂商无 NVLink 的实例), NCCL 会降级走网络 Socket, 需确保设置环境变量 `NCCL_NET_GDR_LEVEL=0` 或放开防火墙避免握手悬挂.
2. 调试 NCCL 日志:
   如果服务卡在首次推理阶段, 通常是 KV Cache 握手超时. 可以在 Prefill 和 Decode 容器的环境变量中增加:
   ```bash
   -e NCCL_DEBUG=INFO -e NCCL_DEBUG_SUBSYS=INIT,COLL,P2P
   ```
   查看是否有 `P2P direct access engine enabled` 类似成功打通的提示.
3. KV 缓冲区容量设置 (`kv_buffer_size`):
   示例中 Prefill 设为 `1e9`(约 1GB 显存), Decode 设为 `1e10`(约 10GB 显存). 生产中如果推理并发量很高, 必须根据 `max_model_len` × 并发请求数合理调高该缓冲区, 否则会出现生产者的丢包或阻塞.





------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------
