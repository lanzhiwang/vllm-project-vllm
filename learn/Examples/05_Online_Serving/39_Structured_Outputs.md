# Structured Outputs
结构化输出

* https://docs.vllm.ai/en/v0.20.0/examples/online_serving/structured_outputs

Source https://github.com/vllm-project/vllm/tree/main/examples/online_serving/structured_outputs.

This script demonstrates various structured output capabilities of vLLM's OpenAI-compatible server. It can run individual constraint type or all of them. It supports both streaming responses and concurrent non-streaming requests.
此脚本演示了 vLLM 的 OpenAI 兼容服务器的各种结构化输出功能. 它可以运行单个约束类型或所有约束类型. 它支持流式响应和并发的非流式请求.

To use this example, you must start an vLLM server with any model of your choice.
要使用此示例, 您必须启动一个使用您选择的任何模型的 vLLM 服务器.

```bash
vllm serve Qwen/Qwen2.5-3B-Instruct
```

To serve a reasoning model, you can use the following command:
要运行推理模型, 可以使用以下命令:

```bash
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --reasoning-parser deepseek_r1
```

If you want to run this script standalone with `uv`, you can use the following:
如果想使用 `uv` 独立运行此脚本, 可以使用以下方法:

```bash
uvx --from git+https://github.com/vllm-project/vllm#subdirectory=examples/online_serving/structured_outputs structured-outputs
```

See [feature docs](https://docs.vllm.ai/en/latest/features/structured_outputs.html) for more information.
更多信息请参阅[功能文档](https://docs.vllm.ai/en/latest/features/structured_outputs.html).

> Tip
> If vLLM is running remotely, then set `OPENAI_BASE_URL=<remote_url>` before running the script.
> 如果 vLLM 是远程运行的, 则在运行脚本之前设置 `OPENAI_BASE_URL=<remote_url>`.
>

## Usage

Run all constraints, non-streaming:
运行所有约束, 非流式处理:

```bash
uv run structured_outputs.py
```

Run all constraints, streaming:
运行所有约束, 流式传输:

```bash
uv run structured_outputs.py --stream
```

Run certain constraints, for example `structural_tag` and `regex`, streaming:
运行某些约束, 例如 `structural_tag` 和 `regex` , 流式传输:

```bash
uv run structured_outputs.py \
    --constraint structural_tag regex \
    --stream
```

Run all constraints, with reasoning models and streaming:
运行所有约束条件, 包括推理模型和流式传输:

```bash
uv run structured_outputs.py --reasoning --stream
```

## Example materials
