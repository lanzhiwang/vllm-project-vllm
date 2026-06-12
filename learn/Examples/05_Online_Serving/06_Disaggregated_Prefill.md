# Disaggregated Prefill
分散预填充物

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/disaggregated_prefill/

Source https://github.com/vllm-project/vllm/blob/main/examples/online_serving/disaggregated_prefill.sh.

-------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 bash 脚本用于 vllm 的相关功能
```

```
请为这个脚本添加注释, 一是说明 bash 脚本的一些语法, 二是说明为什么要这么写, 三是说明 vllm 的相关特性和参数含义

这份 Bash 脚本展示了 vLLM 的一个高级特性: 预填充与解码分离(Disaggregated Prefill & Decode, 简称 P/D 分离).

在传统的 LLM 推理中, Prefill(吞吐量导向, 计算密集型)和 Decode(延迟导向, 访存密集型)运行在相同的 GPU 实例上, 两者会互相抢占资源, 导致首字延迟(TTFT)和双字间隔时间(ITL)难以同时优化. P/D 分离通过将这两个阶段分配到不同的 GPU 实例上运行, 并通过高速网络(如 NCCL)传输中间生成的 KV Cache, 从而实现更高效的算力匹配.

下面是为您精心添加了详细注释的脚本, 以及针对 Bash 语法、设计原因和 vLLM 参数特性的深度剖析.

---

### 一、完整带注释的 Bash 脚本

```bash
#!/bin/bash
# -----------------------------------------------------------------------------
# 1. 脚本头部与基础配置
# -----------------------------------------------------------------------------

# set -xe 是 Bash 脚本中常用的调试和安全控制组合:
# -e (errexit): 只要任何一个命令执行失败(返回非零状态码), 脚本立即退出, 防止错误累积.
# -x (xtrace): 在执行每个命令前, 先将该命令打印到终端, 便于追踪执行路径.
set -xe

echo "🚧🚧 Warning: The usage of disaggregated prefill is experimental and subject to change 🚧🚧"
sleep 1

# 变量默认值语法 ${VAR:-DEFAULT}:
# 如果环境变量 HF_MODEL_NAME 已经存在且非空, 则使用它; 否则默认使用后面的 Llama-3.1 路径.
MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

# -----------------------------------------------------------------------------
# 2. 信号捕获与清理机制(容错设计)
# -----------------------------------------------------------------------------

# trap 命令用于捕获系统信号. 这里捕获的是 SIGINT(即 Ctrl+C 终止信号).
# 当用户按下 Ctrl+C 时, Bash 会暂停当前操作, 跳转执行 cleanup 函数.
trap 'cleanup' INT

# 清理函数: 由于 vLLM 实例和代理服务器都在后台运行(带有 &),
# 如果直接退出脚本, 后台进程会变成孤儿进程继续占用 GPU 显存.
cleanup() {
    echo "Caught Ctrl+C, cleaning up..."
    # 强制杀死当前用户下所有的 python 进程(包含 vllm serve 和 proxy)
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

# -----------------------------------------------------------------------------
# 3. 依赖检查与辅助函数
# -----------------------------------------------------------------------------

# 检查 Quart 库(轻量级异步 Python Web 框架)是否安装:
# python3 -c 执行单行 python 代码.
# &>/dev/null 将标准输出和标准错误均重定向到空设备(不污染终端屏幕).
if python3 -c "import quart" &>/dev/null; then
    echo "Quart is already installed."
else
    echo "Quart is not installed. Installing..."
    python3 -m pip install quart
fi

# 等待服务端就绪的轮询函数:
# $1 表示传入的第一个参数(端口号).
# timeout 1200 限制内部命令的最长执行时间为 1200 秒(20 分钟), 超时则强制退出并返回失败.
wait_for_server() {
    local port=$1
    # bash -c 启动一个子 Shell 运行循环, 直到 curl 成功访问 /v1/models 并返回 0 状态码
    timeout 1200 bash -c "
    until curl -i localhost:${port}/v1/models > /dev/null; do
      sleep 1
    done" && return 0 || return 1
}

# -----------------------------------------------------------------------------
# 4. 启动 vLLM 实例(P/D 分离核心配置)
# -----------------------------------------------------------------------------

# [实例 1: Prefill 阶段(KV Producer 生产者)]
# 限制此实例仅使用 GPU 0
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
wait_for_server 8100
wait_for_server 8200

# -----------------------------------------------------------------------------
# 5. 启动代理路由服务器 (Disagg Proxy)
# -----------------------------------------------------------------------------

# 运行 P/D 分离的协调代理.
# 为什么要运行这个 Proxy? 因为客户端发送请求时, 不能直接分别发给 Prefill 和 Decode,
# 需要一个中介将请求"拆分调度":
# - 步骤 1: Proxy 收到请求, 改写 max_tokens=1 并发往 Prefill 实例(8100), 生成初始 KV Cache.
# - 步骤 2: Prefill 实例通过内部的 P2pNcclConnector 将 KV Cache 直接传到 Decode 实例(8200).
# - 步骤 3: Proxy 再将完整的生成请求发往 Decode 实例, Decode 实例加载传输过来的 KV Cache 并完成后续的 Token 生成.
python3 ../../benchmarks/disagg_benchmarks/disagg_prefill_proxy_server.py &
sleep 1 # 稍微等待, 确保 Proxy 的 HTTP 服务正常拉起

# -----------------------------------------------------------------------------
# 6. 发送测试请求并获取结果
# -----------------------------------------------------------------------------

# 发送请求时, 直接访问 Proxy 所在的 8000 端口, 而不是单独访问 8100 或 8200.
# curl -s (silent) 隐藏进度条和错误信息.
# $(...) 是命令替换, 将 curl 返回的 JSON 响应保存到变量 output1 和 output2 中.
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

# -----------------------------------------------------------------------------
# 7. 清理与结果打印
# -----------------------------------------------------------------------------

# 测试完毕后, 主动清理后台运行的 vllm 实例和代理, 避免端口冲突和显存残留.
pgrep python | xargs kill -9
pkill -f python

echo ""
sleep 1

# 打印 curl 获取到的推理响应
echo "Output of first request: $output1"
echo "Output of second request: $output2"

echo "🎉🎉 Successfully finished 2 test requests! 🎉🎉"
echo ""
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

-------------------------------------------------------------------------------

Q: 假设你是一位精通 LLM, 以及精通 vllm 各种特性的高级开发人员, 现在有如下 python 脚本用于运行 vllm P/D 分离的协调代理
```

```
请为这个脚本添加注释, 一是说明为什么要这么写, 二是说明其中一些深层次的原理

这个 Python 脚本是 vLLM 预填充与解码分离(P/D 分离)架构中的 Control Plane(控制面代理).

在 P/D 分离架构中, 数据流(KV Cache 的传输)是通过 GPU 之间的 NCCL 直连通道高速传输的(Data Plane, 数据面); 而控制流(决定哪个请求何时做 Prefill、何时做 Decode, 并为其分配、绑定通道)则是由这个 Python 代理服务器来进行协调的.

---

### 一、完整带注释的 Python 脚本

这里对脚本中核心设计、异步处理、网络流控制以及 vLLM 特有机制进行了详细的中文注释:

```python
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import argparse
import asyncio
import logging
import os
import time
import uuid
from urllib.parse import urlparse

import aiohttp
# Quart 是一个支持 asyncio 的异步 Python Web 框架, 其 API 与 Flask 完全一致.
# 在 LLM 推理场景中, 由于需要进行高并发的长连接(SSE 流式输出)处理,
# 使用同步的 Flask 会阻塞线程池, 而 Quart 能够利用非阻塞 I/O 实现高并发.
from quart import Quart, Response, make_response, request

# 配置日志系统, 用于监控 P/D 两个阶段的延迟和状态
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="vLLM P/D disaggregation proxy server")

    # 超时设置: 默认 6 小时. 由于 LLM 生成长文本或排队可能耗时较长, 需要调高 HTTP 超时限制.
    parser.add_argument(
        "--timeout",
        type=float,
        default=6 * 60 * 60,
        help="Timeout for backend service requests in seconds (default: 21600)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Proxy 自身对外暴露的 API 服务端口(客户端统一请求此端口)",
    )
    # 分离的两个 vLLM 服务端地址
    parser.add_argument(
        "--prefill-url",
        type=str,
        default="http://localhost:8100",
        help="Prefill 阶段的 vLLM 实例地址",
    )
    parser.add_argument(
        "--decode-url",
        type=str,
        default="http://localhost:8200",
        help="Decode 阶段的 vLLM 实例地址",
    )
    # 用于传输 KV Cache 数据的物理网络地址和端口.
    # 这里的端口(14579 和 14580)是 vLLM 底层传输 Connector(如 P2pNcclConnector)建立通信的物理套接字.
    parser.add_argument(
        "--kv-host",
        type=str,
        default="localhost",
        help="用于 KV Cache 传输的主机名或 IP",
    )
    parser.add_argument(
        "--prefill-kv-port",
        type=int,
        default=14579,
        help="Prefill 实例的 KV 传输服务端口",
    )
    parser.add_argument(
        "--decode-kv-port",
        type=int,
        default=14580,
        help="Decode 实例的 KV 传输服务端口",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # 初始化 aiohttp 的全局超时配置
    AIOHTTP_TIMEOUT = aiohttp.ClientTimeout(total=args.timeout)
    PREFILL_SERVICE_URL = args.prefill_url
    DECODE_SERVICE_URL = args.decode_url
    PORT = args.port

    # 组装 Prefill 和 Decode 实例的数据通信网络端点(Socket 级别)
    PREFILL_KV_ADDR = f"{args.kv_host}:{args.prefill_kv_port}"
    DECODE_KV_ADDR = f"{args.kv_host}:{args.decode_kv_port}"

    logger.info(
        "Proxy resolved KV addresses -> prefill: %s, decode: %s",
        PREFILL_KV_ADDR,
        DECODE_KV_ADDR,
    )

    app = Quart(__name__)

    # 将配置存入 Quart 的 app.config 中, 避免使用全局变量, 利于多线程/协程安全访问.
    app.config.update(
        {
            "AIOHTTP_TIMEOUT": AIOHTTP_TIMEOUT,
            "PREFILL_SERVICE_URL": PREFILL_SERVICE_URL,
            "DECODE_SERVICE_URL": DECODE_SERVICE_URL,
            "PREFILL_KV_ADDR": PREFILL_KV_ADDR,
            "DECODE_KV_ADDR": DECODE_KV_ADDR,
        }
    )

    def _normalize_base_url(url: str) -> str:
        """去除 URL 结尾的斜杠, 防止拼接路径时出现双斜杠(//)导致 HTTP 404 错误"""
        return url.rstrip("/")

    def _get_host_port(url: str) -> str:
        """提取 'IP:Port'. 这将被注入到 HTTP 协议头的 X-KV-Target 中,
        提示 Prefill 节点该将 KV 传输到哪个目的地址."""
        parsed = urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port
        if port is None:
            port = 80 if parsed.scheme == "http" else 443
        return f"{host}:{port}"

    PREFILL_BASE = _normalize_base_url(PREFILL_SERVICE_URL)
    DECODE_BASE = _normalize_base_url(DECODE_SERVICE_URL)
    KV_TARGET = _get_host_port(DECODE_SERVICE_URL)

    def _build_headers(request_id: str) -> dict[str, str]:
        """构建发送给后端 vLLM 的 HTTP 请求头.
        - X-Request-Id: 极重要, 不仅是追踪号, 还暗含了 P2P 节点的寻址元数据.
        - X-KV-Target: 告知 Prefill 节点 KV Cache 最终输出的目的 HTTP 地址.
        """
        headers: dict[str, str] = {"X-Request-Id": request_id, "X-KV-Target": KV_TARGET}
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def _run_prefill(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
    ):
        """[Prefill 阶段控制]
        向 Prefill 实例发起请求, 令其对 Prompt 计算 Attention, 并触发底层网络将 KV 发送出去.
        """
        url = f"{PREFILL_BASE}{request_path}"
        start_ts = time.perf_counter()
        logger.info("[prefill] start request_id=%s url=%s", request_id, url)
        try:
            # 采用异步 aiohttp.ClientSession 避免网络 I/O 阻塞主循环进程
            async with (
                aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session,
                session.post(url=url, json=payload, headers=headers) as resp,
            ):
                if resp.status != 200:
                    error_text = await resp.text()
                    raise RuntimeError(
                        f"Prefill backend error {resp.status}: {error_text}"
                    )
                # 使用 await resp.read() 读完全部响应体, 确保连接完全释放, 并且 Prefill 节点的计算和 KV 发送动作已彻底完成
                await resp.read()
                logger.info(
                    "[prefill] done request_id=%s status=%s elapsed=%.2fs",
                    request_id,
                    resp.status,
                    time.perf_counter() - start_ts,
                )
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Prefill service timeout at {url}") from exc
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Prefill service unavailable at {url}") from exc

    async def _stream_decode(
        request_path: str,
        payload: dict,
        headers: dict[str, str],
        request_id: str,
    ):
        """[Decode 阶段控制]
        从已经接收到 KV Cache 的 Decode 节点获取流式生成的 Token.
        该函数是一个异步生成器(async generator).
        """
        url = f"{DECODE_BASE}{request_path}"
        logger.info("[decode] start request_id=%s url=%s", request_id, url)
        try:
            # 同样采用 aiohttp 异步请求, 以便实时流式地读取 Decode 节点返回的数据块
            async with (
                aiohttp.ClientSession(timeout=AIOHTTP_TIMEOUT) as session,
                session.post(url=url, json=payload, headers=headers) as resp,
            ):
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(
                        "Decode backend error %s - %s", resp.status, error_text
                    )
                    err_msg = (
                        '{"error": "Decode backend error ' + str(resp.status) + '"}'
                    )
                    yield err_msg.encode()
                    return
                logger.info(
                    "[decode] streaming response request_id=%s status=%s",
                    request_id,
                    resp.status,
                )
                # 核心非阻塞流式: 迭代以 1024 字节为单位的数据块, 实时将其 yield 回给 Quart 框架
                async for chunk_bytes in resp.content.iter_chunked(1024):
                    yield chunk_bytes
                logger.info("[decode] finished streaming request_id=%s", request_id)
        except asyncio.TimeoutError:
            logger.error("Decode service timeout at %s", url)
            yield b'{"error": "Decode service timeout"}'
        except aiohttp.ClientError as exc:
            logger.error("Decode service error at %s: %s", url, exc)
            yield b'{"error": "Decode service unavailable"}'

    async def process_request():
        """[请求编排主干逻辑]
        将客户端单次请求分步送往 Prefill 节点和 Decode 节点.
        """
        try:
            # 异步解析客户端传过来的 JSON 请求负载
            original_request_data = await request.get_json()

            # -------------------------------------------------------------
            # 步骤 1: 构造 Prefill 请求(截断为 1 Token 生成)
            # -------------------------------------------------------------
            prefill_request = original_request_data.copy()
            # 强制设置只生成 1 个 Token(或配置 max_completion_tokens)
            # 目的: 让 Prefill 节点仅计算 Prompt 的注意力键值, 产生 KV Cache 并触发 P2P 传输,
            # 之后立即结束该请求, 防止 Prefill 节点做后续的自回归解码.
            prefill_request["max_tokens"] = 1
            if "max_completion_tokens" in prefill_request:
                prefill_request["max_completion_tokens"] = 1

            # -------------------------------------------------------------
            # 步骤 2: 构造特定的 Request ID (编排设计的精髓)
            # -------------------------------------------------------------
            # 我们将 Prefill 节点和 Decode 节点的物理 KV 传输套接字编码进 Request ID 中.
            # vLLM 的底层通信网络组件(如 P2pNcclConnector)会解析此 Request ID.
            # 从而, 在没有全局路由表的情况下, Prefill 的 GPU 能够直接动态得知: 该将此请求对应的
            # KV Cache 发送到哪一个 Decode 节点的 IP 端口(DECODE_KV_ADDR).
            request_id = (
                f"___prefill_addr_{PREFILL_KV_ADDR}___decode_addr_"
                f"{DECODE_KV_ADDR}_{uuid.uuid4().hex}"
            )

            headers = _build_headers(request_id)

            # -------------------------------------------------------------
            # 步骤 3: 串行执行控制面转发
            # -------------------------------------------------------------
            # 1. 触发 Prefill
            await _run_prefill(request.path, prefill_request, headers, request_id)

            # 2. 触发 Decode(传入未经修改的原始请求, 如原 max_tokens=256)
            # Decode 节点收到该 request_id 时, 会先通过内部底层连接拦截并加载 Prefill 发过来的 KV 缓存,
            # 然后直接进行自回归计算, 吐出剩下的 Token.
            generator = _stream_decode(
                request.path, original_request_data, headers, request_id
            )

            # 使用 Quart 包装异步生成器为流式 HTTP 响应
            response = await make_response(generator)
            # 必须禁用 Quart 的响应超时设置, 否则长时间的 LLM 推理生成连接会由于没有新的 HTTP 请求而被中间切断.
            response.timeout = None
            return response

        except Exception:
            logger.exception("Error processing request")
            return Response(
                response=b'{"error": "Internal server error"}',
                status=500,
                content_type="application/json",
            )

    @app.route("/v1/completions", methods=["POST"])
    async def handle_request():
        """对外部客户端暴露的统一 OpenAI 标准接口路由"""
        try:
            return await process_request()
        except asyncio.CancelledError:
            # 必须捕获协程取消异常. 当客户端(浏览器/SDK)中途断开连接时,
            # asyncio 会向该协程发出 CancelledError, 我们需要记录并进行优雅的资源回收.
            logger.warning("Request cancelled")
            return Response(
                response=b'{"error": "Request cancelled"}',
                status=503,
                content_type="application/json",
            )

    # 启动 Quart 服务器, 开始监听来自客户端的流量
    app.run(port=PORT)


if __name__ == "__main__":
    main()
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

-------------------------------------------------------------------------------


-------------------------------------------------------------------------------


-------------------------------------------------------------------------------


-------------------------------------------------------------------------------


-------------------------------------------------------------------------------

