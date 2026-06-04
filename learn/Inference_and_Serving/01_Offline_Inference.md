# Offline Inference
离线推理

* https://docs.vllm.ai/en/v0.20.0/serving/offline_inference/

Offline inference is possible in your own code using vLLM's [`LLM`](https://docs.vllm.ai/en/v0.20.0/api/vllm/#vllm.LLM "LLM") class.
您可以在自己的代码中使用 vLLM 的 `LLM` 类进行离线推理.

For example, the following code downloads the [`facebook/opt-125m`](https://huggingface.co/facebook/opt-125m) model from HuggingFace and runs it in vLLM using the default configuration.
例如, 以下代码从 HuggingFace 下载 `facebook/opt-125m` 模型, 并使用默认配置在 vLLM 中运行它.

```python
from vllm import LLM

# Initialize the vLLM engine.
llm = LLM(model="facebook/opt-125m")
```

After initializing the [`LLM`](https://docs.vllm.ai/en/v0.20.0/api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM "LLM") instance, use the available APIs to perform model inference. The available APIs depend on the model type:
初始化 `LLM` 实例后, 使用可用的 API 执行模型推理. 可用的 API 取决于模型类型:

- [Generative models](https://docs.vllm.ai/en/v0.20.0/models/generative_models/) output logprobs which are sampled from to obtain the final output text.
  生成模型输出对数概率, 从中采样以获得最终的输出文本.

- [Pooling models](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/) output their hidden states directly.
  池化模型直接输出其隐藏状态.

> Info
> [API Reference](https://docs.vllm.ai/en/v0.20.0/api/#offline-inference)
>

## Ray Data LLM API

Ray Data LLM is an alternative offline inference API that uses vLLM as the underlying engine. This API adds several batteries-included capabilities that simplify large-scale, GPU-efficient inference:
Ray Data LLM 是一种替代的离线推理 API, 它使用 vLLM 作为底层引擎. 此 API 添加了多项内置功能, 可简化大规模、GPU 高效的推理:

- Streaming execution processes datasets that exceed aggregate cluster memory.
  流式执行处理超出聚合集群内存的数据集.

- Automatic sharding, load balancing, and autoscaling distribute work across a Ray cluster with built-in fault tolerance.
  自动分片、负载平衡和自动缩放可在具有内置容错功能的 Ray 集群中分配工作.

- Continuous batching keeps vLLM replicas saturated and maximizes GPU utilization.
  连续批处理使 vLLM 副本保持饱和并最大限度地提高 GPU 利用率.

- Transparent support for tensor and pipeline parallelism enables efficient multi-GPU inference.
  对张量和流水线并行性的透明支持实现了高效的多 GPU 推理.

- Reading and writing to most popular file formats and cloud object storage.
  读取和写入最流行的文件格式和云对象存储.

- Scaling up the workload without code changes.
  无需更改代码即可扩展工作负载.

Code

```python
import ray  # Requires ray>=2.44.1
from ray.data.llm import vLLMEngineProcessorConfig, build_llm_processor

config = vLLMEngineProcessorConfig(model_source="unsloth/Llama-3.2-1B-Instruct")
processor = build_llm_processor(
    config,
    preprocess=lambda row: {
        "messages": [
            {"role": "system", "content": "You are a bot that completes unfinished haikus."},
            {"role": "user", "content": row["item"]},
        ],
        "sampling_params": {"temperature": 0.3, "max_tokens": 250},
    },
    postprocess=lambda row: {"answer": row["generated_text"]},
)

ds = ray.data.from_items(["An old silent pond..."])
ds = processor(ds)
ds.write_parquet("local:///tmp/data/")
```

For more information about the Ray Data LLM API, see the [Ray Data LLM documentation](https://docs.ray.io/en/latest/data/working-with-llms.html).
有关 Ray Data LLM API 的更多信息, 请参阅 Ray Data LLM 文档
