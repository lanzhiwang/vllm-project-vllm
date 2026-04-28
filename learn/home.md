# Welcome to vLLM

* https://docs.vllm.ai/en/v0.20.0/

vLLM is a fast and easy-to-use library for LLM inference and serving.
vLLM 是一个快速且易于使用的 LLM 推理和服务库.

Originally developed in the [Sky Computing Lab](https://sky.cs.berkeley.edu/) at UC Berkeley, vLLM has grown into one of the most active open-source AI projects built and maintained by a diverse community of many dozens of academic institutions and companies from over 2000 contributors.
vLLM 最初由加州大学伯克利分校的天空计算实验室开发, 如今已发展成为最活跃的开源人工智能项目之一, 由来自数十个学术机构和公司的 2000 多名贡献者组成的多元化社区构建和维护.

Where to get started with vLLM depends on the type of user. If you are looking to:
vLLM 的入门方式取决于用户类型. 如果您希望:

- Run open-source models on vLLM, we recommend starting with the [Quickstart Guide](https://docs.vllm.ai/en/v0.20.0/getting_started/quickstart/)
  在 vLLM 上运行开源模型, 我们建议从快速入门指南开始

- Build applications with vLLM, we recommend starting with the [User Guide](https://docs.vllm.ai/en/v0.20.0/usage/)
  使用 vLLM 构建应用程序, 我们建议从用户指南开始

- Build vLLM, we recommend starting with [Developer Guide](https://docs.vllm.ai/en/v0.20.0/contributing/)
  构建 vLLM, 我们建议从开发者指南开始

For information about the development of vLLM, see:
有关 vLLM 开发的信息, 请参阅:

- [Roadmap](https://roadmap.vllm.ai/)
- [Releases](https://github.com/vllm-project/vllm/releases)

vLLM is fast with:
vLLM 速度很快, 因为:

- State-of-the-art serving throughput
  一流的服务吞吐量

- Efficient management of attention key and value memory with [PagedAttention](https://blog.vllm.ai/2023/06/20/vllm.html)
  使用 PagedAttention 高效管理注意键和值内存

- Continuous batching of incoming requests, chunked prefill, prefix caching
  连续批量处理传入请求、分块预填充、前缀缓存

- Fast and flexible model execution with piecewise and full CUDA/HIP graphs
  使用分段和完整 CUDA/HIP 图快速灵活地执行模型

- Quantization: FP8, MXFP8/MXFP4, NVFP4, INT8, INT4, GPTQ/AWQ, GGUF, compressed-tensors, ModelOpt, TorchAO, and [more](https://docs.vllm.ai/en/latest/features/quantization/index.html)
  量化方式: FP8、MXFP8/MXFP4、NVFP4、INT8、INT4、GPTQ/AWQ、GGUF、压缩张量、ModelOpt、TorchAO 等

- Optimized attention kernels including FlashAttention, FlashInfer, TRTLLM-GEN, FlashMLA, and Triton
  优化的注意力内核包括 FlashAttention、FlashInfer、TRTLLM-GEN、FlashMLA 和 Triton

- Optimized GEMM/MoE kernels for various precisions using CUTLASS, TRTLLM-GEN, CuTeDSL
  使用 CUTLASS、TRTLLM-GEN 和 CuTeDSL 针对不同精度优化了 GEMM/MoE 内核

- Speculative decoding including n-gram, suffix, EAGLE, DFlash
  推测性解码, 包括 n-gram、后缀、EAGLE、DFlash

- Automatic kernel generation and graph-level transformations using torch.compile
  使用 torch.compile 自动生成内核并进行图级转换

- Disaggregated prefill, decode, and encode
  分解式预填充、解码和编码

vLLM is flexible and easy to use with:
vLLM 灵活且易于使用:

- Seamless integration with popular Hugging Face models
  与流行的 Hugging Face 模型无缝集成

- High-throughput serving with various decoding algorithms, including `parallel sampling`, `beam search`, and more
  采用多种解码算法(包括并行采样、波束搜索等)实现高吞吐量服务

- Tensor, pipeline, data, expert, and context parallelism for distributed inference
  用于分布式推理的张量、管道、数据、专家和上下文并行性

- Streaming outputs
  流式输出

- Generation of structured outputs using xgrammar or guidance
  使用 xgrammar 或指南生成结构化输出

- Tool calling and reasoning parsers
  工具调用和推理解析器

- OpenAI-compatible API server, plus Anthropic Messages API and gRPC support
  兼容 OpenAI 的 API 服务器, 以及 Anthropic Messages API 和 gRPC 支持

- Efficient multi-LoRA support for dense and MoE layers
  高效的多层 RA 支持, 适用于致密层和 MoE 层

- Support for NVIDIA GPUs, AMD GPUs, and x86/ARM/PowerPC CPUs. Additionally, diverse hardware plugins such as Google TPUs, Intel Gaudi, IBM Spyre, Huawei Ascend, Rebellions NPU, Apple Silicon, MetaX GPU, and more.
  支持 NVIDIA GPU、AMD GPU 和 x86/ARM/PowerPC CPU. 此外, 还支持多种硬件插件, 例如 Google TPU、Intel Gaudi、IBM Spyre、华为 Ascend、Rebellions NPU、Apple Silicon、MetaX GPU 等.

vLLM seamlessly supports 200+ model architectures on HuggingFace, including:
vLLM 无缝支持 HuggingFace 上的 200 多种模型架构, 包括:

- Decoder-only LLMs(e.g., Llama, Qwen, Gemma)
  仅解码器 LLM(例如, Llama、Qwen、Gemma)

- Mixture-of-Expert LLMs(e.g., Mixtral, DeepSeek-V3, Qwen-MoE, GPT-OSS)
  混合专家学习逻辑模型(例如 Mixtral、DeepSeek-V3、Qwen-MoE、GPT-OSS)

- Hybrid attention and state-space models(e.g., Mamba, Qwen3.5)
  混合注意力与状态空间模型(例如, Mamba、Qwen3.5)

- Multi-modal models(e.g., LLaVA, Qwen-VL, Pixtral)
  多模态模型(例如, LLaVA、Qwen-VL、Pixtral)

- Embedding and retrieval models(e.g., E5-Mistral, GTE, ColBERT)
  嵌入和检索模型(例如, E5-Mistral、GTE、ColBERT)

- Reward and classification models(e.g., Qwen-Math)
  奖励和分类模型(例如, Qwen-Math)

Find the full list of supported models [here](https://docs.vllm.ai/en/v0.20.0/models/supported_models/).
点击此处查看所有支持的型号列表.

For more information, check out the following:
欲了解更多信息, 请查看以下内容:

- [vLLM announcing blog post](https://blog.vllm.ai/2023/06/20/vllm.html)(intro to PagedAttention)

- [vLLM paper](https://arxiv.org/abs/2309.06180)(SOSP 2023)

- [How continuous batching enables 23x throughput in LLM inference while reducing p50 latency](https://www.anyscale.com/blog/continuous-batching-llm-inference) by Cade Daniel et al.

- [vLLM Meetups](https://docs.vllm.ai/en/v0.20.0/community/meetups/)
