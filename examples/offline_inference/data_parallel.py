# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Usage:
Single node:
    python examples/offline_inference/data_parallel.py \
            --model="ibm-research/PowerMoE-3b" \
            -dp=2 \
            -tp=2

Multi-node:
    Node 0 (assume the node has ip of 10.99.48.128):
            python examples/offline_inference/data_parallel.py \
                    --model="ibm-research/PowerMoE-3b" \
                    -dp=2 \
                    -tp=2 \
                    --dp-num-nodes=2 \
                    --dp-node-rank=0 \
                    --dp-master-addr=10.99.48.128 \
                    --dp-master-port=13345
    Node 1:
            python examples/offline_inference/data_parallel.py \
                    --model="ibm-research/PowerMoE-3b" \
                    -dp=2 \
                    -tp=2 \
                    --dp-num-nodes=2 \
                    --dp-node-rank=1 \
                    --dp-master-addr=10.99.48.128 \
                    --dp-master-port=13345
"""

import os
from time import sleep

from vllm import LLM, EngineArgs, SamplingParams
from vllm.platforms import current_platform
from vllm.utils.argparse_utils import FlexibleArgumentParser
from vllm.utils.network_utils import get_open_port


def create_parser():
    # 使用 vLLM 自定义的参数解析器, 它比原生的 argparse 更灵活, 支持从文件/环境变量读取等
    parser = FlexibleArgumentParser(description="Data Parallel Inference")

    # [核心点] EngineArgs.add_cli_args 会把 vLLM 引擎所有支持的参数
    # (如 --model, --tensor-parallel-size/tp 等)
    # 全部自动注册到 parser 里. 这样不需要手动去写一堆 add_argument.
    # Add all engine args
    EngineArgs.add_cli_args(parser)

    # 设置默认模型为 IBM 的 PowerMoE-3b, 并开启专家并行(EP)
    # 这只是个示例, 实际运行时可以通过命令行覆盖
    parser.set_defaults(
        model="ibm-research/PowerMoE-3b",
        enable_expert_parallel=True,
    )

    # ==========================================
    # 以下添加的是"数据并行(DP)"专用的控制参数.
    # [为什么要分离?]因为 vLLM 底层的 LLM 引擎类只认识 EngineArgs.
    # DP 的调度是在 Python 进程层面上做的, 引擎不需要也不应该知道 DP 的细节.
    # ==========================================
    # Add DP-specific args (separate from engine args to avoid conflicts)

    # 数据并行的总节点(机器)数.
    parser.add_argument(
        "--dp-num-nodes",
        type=int,
        default=1,
        help="Total number of nodes for data parallel.",
    )
    # 当前节点在整个数据并行集群中的编号(0 到 dp-num-nodes - 1).
    parser.add_argument(
        "--dp-node-rank",
        type=int,
        default=0,
        help="Rank of the current node for data parallel.",
    )
    # 主节点的 IP 地址. 用于底层的分布式通信组网(如 PyTorch RPC/NCCL).
    parser.add_argument(
        "--dp-master-addr",
        type=str,
        default="",
        help="Master node IP address for DP coordination.",
    )
    # 主节点的通信端口.
    parser.add_argument(
        "--dp-master-port",
        type=int,
        default=0,
        help="Master node port for DP coordination.",
    )
    # 超时时间(秒). 如果某个进程卡死超过这个时间, 将被主进程强制 kill, 防止 GPU 僵尸进程.
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Number of seconds before unresponsive process is killed.",
    )

    return parser


# 这是每一个 Data Parallel Worker(数据并行工作进程)的入口函数
def main(
    dp_size,  # 全局总共的 DP 数量(比如 2 台机器, 每台起 2 个 DP, 那这个值就是 4)
    local_dp_rank,  # 当前进程在[这台机器上]的 DP 编号(比如 0 或 1)
    global_dp_rank,  # 当前进程在[整个集群里]的 DP 编号(比如 0, 1, 2, 3)
    dp_master_ip,  # 分布式通信 Master IP
    dp_master_port,  # 分布式通信 Master 端口
    engine_args,  # 传递给 vLLM 底层的引擎参数字典
):
    # [极度关键]把 DP 的拓扑信息注入到环境变量中.
    # 为什么? 因为 vLLM 的底层分布式框架(特别是如果同时还开启了 TP 张量并行, 或者多节点 GPU 通信时),
    # 需要依赖这些环境变量来初始化 PyTorch Distributed(init_process_group)或者 Ray 引擎.
    # vLLM 内部的代码会去读取这些 VLLM_DP_* 变量来感知自己处于整个集群的哪个位置.
    os.environ["VLLM_DP_RANK"] = str(global_dp_rank)
    os.environ["VLLM_DP_RANK_LOCAL"] = str(local_dp_rank)
    os.environ["VLLM_DP_SIZE"] = str(dp_size)
    os.environ["VLLM_DP_MASTER_IP"] = dp_master_ip
    os.environ["VLLM_DP_MASTER_PORT"] = str(dp_master_port)

    # CUDA_VISIBLE_DEVICES for each DP rank is set automatically inside the
    # engine processes.
    # 注释说明: 每个 DP rank 的 CUDA_VISIBLE_DEVICES 是 vLLM 引擎内部根据这些 rank 自动分配的.
    # 例如机器有 8 张卡, DP = 4, TP = 2, 那么引擎会计算出 local_dp_rank = 0 占用 GPU 0, 1, local_dp_rank = 1 占用 GPU 2,3

    # 准备一份巨大的测试数据集(这里用基础 prompt 乘以 100 构造了 400 条数据)
    # Sample prompts.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ] * 100

    # ==========================================
    # 数据集切分逻辑(Data Partitioning)
    # 核心思想: 确保每个 DP Rank 处理的数据是不重叠的.
    # ==========================================
    # with DP, each rank should process different prompts.
    # usually all the DP ranks process a full dataset,
    # and each rank processes a different part of the dataset.
    floor = len(prompts) // dp_size  # 每个 rank 基础分到的数量
    remainder = len(prompts) % dp_size  # 余数, 前 remainder 个 rank 需要多处理 1 条

    # 这是一个计算当前 rank 应该从哪个索引开始取数据的辅助函数
    # Distribute prompts into even groups.
    def start(rank):
        # rank * floor: 基础偏移量
        # min(rank, remainder): 补偿由于不能整除带来的偏移
        return rank * floor + min(rank, remainder)

    # 使用切片, 将属于当前 global_dp_rank 的 prompts 截取出来
    prompts = prompts[start(global_dp_rank) : start(global_dp_rank + 1)]
    # 容错处理: 如果 DP_SIZE 比请求总数还多, 会导致部分 rank 分不到数据.
    # vLLM 引擎如果接受到空的 prompt 列表可能会报错或退出异常, 所以塞一个 Placeholder 进去保底.
    if len(prompts) == 0:
        # if any rank has no prompts to process,
        # we need to set a placeholder prompt
        prompts = ["Placeholder"]
    print(f"DP rank {global_dp_rank} needs to process {len(prompts)} prompts")

    # 配置采样参数.
    # [设计巧妙点]因为每个 DP 实例是完全独立的, 因此它们不仅处理不同的数据, 甚至可以拥有完全不同的采样策略.
    # 这里的示例展示了: 偶数 rank 生成 16 个 token, 奇数 rank 生成 20 个 token.
    # Create a sampling params object.
    # since we are doing data parallel, every rank can have different
    # sampling params. here we set different max_tokens for different
    # ranks for demonstration.
    sampling_params = SamplingParams(
        temperature=0.8, top_p=0.95, max_tokens=[16, 20][global_dp_rank % 2]
    )

    # [引擎初始化与推理]
    # 实例化 vLLM 引擎. 这里 kwargs 解包了传进来的 engine_args(如 model, tensor_parallel_size 等)
    # 当这一句执行时, 当前进程会去占用对应的 GPU 显存, 并加载模型权重.
    # Create an LLM.
    llm = LLM(**engine_args)
    # 批量执行离线推理, vLLM 内部会进行 PagedAttention 和 Continuous Batching 调度
    outputs = llm.generate(prompts, sampling_params)
    # 打印每个 DP worker 的前 5 条结果(避免 400 条全部刷屏)
    # Print the outputs.
    for i, output in enumerate(outputs):
        if i >= 5:
            # print only 5 outputs
            break
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(
            f"DP rank {global_dp_rank}, Prompt: {prompt!r}, "
            f"Generated text: {generated_text!r}"
        )

    # [重要防坑]在进程退出前 sleep 1秒.
    # 为什么? 因为 vLLM 底层包含很多异步线程(例如 C++ 端的 zmq 通信、CUDA 回调等),
    # 强行瞬间退出进程可能导致底层 C++ runtime 抛出 Segment Fault 或显存释放不干净.
    # 稍微停顿一下, 让垃圾回收机制(GC)优雅地销毁引擎对象.
    # Give engines time to pause their processing loops before exiting.
    sleep(1)


if __name__ == "__main__":
    parser = create_parser()
    # 将 parser 转换为字典方便后续操作
    args = vars(parser.parse_args())

    # ==========================================
    # 参数解耦隔离
    # ==========================================
    # vLLM 内部实际上把 DP args 映射到了 data_parallel_size 这个名字.
    # args.pop 的作用是把这些外部控制循环用的参数从字典里拿出来并删掉.
    # 因为如果不删掉, 下面直接把剩下的 kwargs 传给 LLM()时, 会触发 TypeError(找不到未知参数).
    # Extract DP-specific args (pop to remove from engine_args)
    dp_size = args.pop("data_parallel_size")
    dp_num_nodes = args.pop("dp_num_nodes")
    dp_node_rank = args.pop("dp_node_rank")
    dp_master_addr = args.pop("dp_master_addr")
    dp_master_port = args.pop("dp_master_port")
    timeout = args.pop("timeout")

    # 经过上面的 pop 操作, 剩下的字典里全是合法的 vLLM EngineArgs 了
    # Remaining args are engine args
    engine_args = args

    # 如果是单机运行, 自动指定 master ip 为本机, 并去系统里找一个未被占用的随机端口
    if dp_num_nodes == 1:
        dp_master_ip = "127.0.0.1"
        dp_master_port_val = get_open_port()
    else:
        # 如果是多机运行, 必须严格使用用户传入的 master IP 和 端口, 否则跨机器无法通信
        dp_master_ip = dp_master_addr
        dp_master_port_val = dp_master_port

    # 健全性检查: 全局 DP 总数必须能被节点数整除, 保证负载均衡
    assert dp_size % dp_num_nodes == 0, "dp_size should be divisible by dp_num_nodes"
    # 计算当前这台机器需要启动几个 DP 进程
    dp_per_node = dp_size // dp_num_nodes

    from multiprocessing import Process

    # ==========================================
    # 多进程启动模型设置(针对 AMD GPU 的特判)
    # ==========================================
    # PyTorch/CUDA 环境下, 默认的多进程启动方式(如 Linux 的 fork)会直接复制父进程的内存空间.
    # 但一旦父进程初始化了任何 GPU 上下文, fork 后子进程的 GPU 上下文就会全盘崩溃!
    # ROCm 环境对这一点极其敏感, 所以强制要求用 'spawn'(重新启动一个干净的 python 解释器环境).
    # 实际上, 在 NVIDIA CUDA 环境跑多进程推理时, 最好也显式设定为 'spawn'.
    if current_platform.is_rocm():
        from multiprocessing import set_start_method

        set_start_method("spawn", force=True)

    procs = []
    # 循环遍历属于当前节点的 global rank 范围.
    # 举例: 如果是第 1 号节点(dp_node_rank=1), 每台节点起 2 个 DP, 那么 global_dp_rank 范围就是 [2, 3], local 是 [0, 1]
    for local_dp_rank, global_dp_rank in enumerate(
        range(dp_node_rank * dp_per_node, (dp_node_rank + 1) * dp_per_node)
    ):
        # 为每一个 DP rank 独立创建一个操作系统级的进程(Process)
        # 不用多线程(Threading)的原因是:
        # 1. Python有 GIL 锁, 多线程无法跑满多核 CPU.
        # 2. PyTorch 的 CUDA Runtime 和 NCCL 强依赖多进程来实现卡间隔离和分布式通信.
        proc = Process(
            target=main,
            args=(
                dp_size,
                local_dp_rank,
                global_dp_rank,
                dp_master_ip,
                dp_master_port_val,
                engine_args,
            ),
        )
        # 启动该进程
        proc.start()
        procs.append(proc)
    exit_code = 0

    # ==========================================
    # 进程守护与回收(Process Join & Cleanup)
    # ==========================================
    for proc in procs:
        # 主进程阻塞等待子进程运行完毕. 这里的 timeout 机制至关重要.
        proc.join(timeout=timeout)
        # 如果 join 退出是因为超时, 此时 exitcode 仍为 None, 说明子进程卡死了(可能是 NCCL hang 或 GPU 硬件错误)
        if proc.exitcode is None:
            print(f"Killing process {proc.pid} that didn't stop within 5 minutes.")
            # 必须强制猎杀, 否则 GPU 显存永远无法释放, 引发显卡僵尸进程问题
            proc.kill()
            exit_code = 1
        elif proc.exitcode:
            # 如果子进程非正常退出(exitcode 不为 0), 则记录失败状态
            exit_code = proc.exitcode

    # 整个脚本以最终的退出码退出, 方便 CI/CD 系统或调度脚本(如 bash)捕获运行状态
    exit(exit_code)
