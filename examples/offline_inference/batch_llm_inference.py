# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
This example shows how to use Ray Data for data parallel batch inference.

Ray Data is a data processing framework that can process very large datasets
with first-class support for vLLM.

Ray Data provides functionality for:
* Reading and writing to most popular file formats and cloud object storage.
* Streaming execution, so you can run inference on datasets that far exceed
  the aggregate RAM of the cluster.
* Scale up the workload without code changes.
* Automatic sharding, load-balancing, and autoscaling across a Ray cluster,
  with built-in fault-tolerance and retry semantics.
* Continuous batching that keeps vLLM replicas saturated and maximizes GPU
  utilization.
* Compatible with tensor/pipeline parallel inference.

Learn more about Ray Data's LLM integration:
https://docs.ray.io/en/latest/data/working-with-llms.html

本示例演示了如何利用 Ray Data 进行数据并行批量推理.

Ray Data 是一个数据处理框架, 能够处理超大规模的数据集, 并为 vLLM 提供了"头等公民"级别的支持.

Ray Data 提供了以下功能:
* 支持读写大多数主流的文件格式及云对象存储.
* 支持流式执行, 使您能够在数据集规模远超集群总内存容量的情况下执行推理任务.
* 无需修改代码即可实现工作负载的横向扩展.
* 在 Ray 集群内实现自动分片、负载均衡及自动扩缩容, 并内置了容错机制与重试语义.
* 支持"连续批处理"(Continuous Batching), 确保 vLLM 副本始终处于饱和运行状态, 从而最大化 GPU 的利用率.
* 兼容张量并行(Tensor Parallel)与流水线并行(Pipeline Parallel)推理模式.

了解更多关于 Ray Data 与大型语言模型(LLM)集成的详情:
https://docs.ray.io/en/latest/data/working-with-llms.html
"""

import ray
from packaging.version import Version
from ray.data.llm import build_llm_processor, vLLMEngineProcessorConfig

assert Version(ray.__version__) >= Version(
    "2.44.1"
), "Ray version must be at least 2.44.1"

# Uncomment to reduce clutter in stdout
# ray.init(log_to_driver=False)
# ray.data.DataContext.get_current().enable_progress_bars = False

# Read one text file from S3. Ray Data supports reading multiple files
# from cloud storage (such as JSONL, Parquet, CSV, binary format).
ds = ray.data.read_text("s3://anonymous@air-example-data/prompts.txt")
print(ds.schema())

size = ds.count()
print(f"Size of dataset: {size} prompts")

# Configure vLLM engine.
config = vLLMEngineProcessorConfig(
    model_source="unsloth/Llama-3.1-8B-Instruct",
    engine_kwargs={
        "enable_chunked_prefill": True,
        "max_num_batched_tokens": 4096,
        "max_model_len": 16384,
    },
    concurrency=1,  # set the number of parallel vLLM replicas
    batch_size=64,
)

# Create a Processor object, which will be used to
# do batch inference on the dataset
vllm_processor = build_llm_processor(
    config,
    preprocess=lambda row: dict(
        messages=[
            {"role": "system", "content": "You are a bot that responds with haikus."},
            {"role": "user", "content": row["text"]},
        ],
        sampling_params=dict(
            temperature=0.3,
            max_tokens=250,
        ),
    ),
    postprocess=lambda row: dict(
        answer=row["generated_text"],
        **row,  # This will return all the original columns in the dataset.
    ),
)

ds = vllm_processor(ds)

# Peek first 10 results.
# NOTE: This is for local testing and debugging. For production use case,
# one should write full result out as shown below.
outputs = ds.take(limit=10)

for output in outputs:
    prompt = output["prompt"]
    generated_text = output["generated_text"]
    print(f"Prompt: {prompt!r}")
    print(f"Generated text: {generated_text!r}")

# Write inference output data out as Parquet files to S3.
# Multiple files would be written to the output destination,
# and each task would write one or more files separately.
#
# ds.write_parquet("s3://<your-output-bucket>")
