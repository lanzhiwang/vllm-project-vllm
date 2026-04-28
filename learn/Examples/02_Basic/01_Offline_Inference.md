# Offline Inference
离线推理

* https://docs.vllm.ai/en/v0.20.0/examples/basic/offline_inference/

Source [vllm/examples/basic/offline_inference](https://github.com/vllm-project/vllm/tree/main/examples/basic/offline_inference).

The [`LLM`](https://docs.vllm.ai/en/v0.20.0/api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM "LLM") class provides the primary Python interface for doing offline inference, which is interacting with a model without using a separate model inference server.
`LLM` 类提供了用于进行离线推理的主要 Python 接口, 即在不使用单独的模型推理服务器的情况下与模型进行交互.

## Usage
用法

The first script in this example shows the most basic usage of vLLM. If you are new to Python and vLLM, you should start here.
本示例中的第一个脚本展示了 vLLM 的最基本用法. 如果您是 Python 和 vLLM 的新手, 应该从这里开始.

```bash
python examples/basic/offline_inference/basic.py
```

The rest of the scripts include an [argument parser](https://docs.python.org/3/library/argparse.html), which you can use to pass any arguments that are compatible with [`LLM`](https://docs.vllm.ai/en/latest/api/offline_inference/llm.html). Try running the script with `--help` for a list of all available arguments.
其余脚本包含一个参数解析器, 您可以使用它来传递任何与 `LLM` 兼容的参数. 尝试使用 `--help` 运行脚本以获取所有可用参数的列表.

```bash
python examples/basic/offline_inference/classify.py
```

```bash
python examples/basic/offline_inference/embed.py
```

```bash
python examples/basic/offline_inference/score.py
```

The chat and generate scripts also accept the [sampling parameters](https://docs.vllm.ai/en/latest/api/inference_params.html#sampling-parameters): `max_tokens`, `temperature`, `top_p` and `top_k`.
聊天和生成脚本也接受采样参数: `max_tokens`、`temperature`、`top_p` 和 `top_k`.

```bash
python examples/basic/offline_inference/chat.py
```

```bash
python examples/basic/offline_inference/generate.py
```

## Features
特征

In the scripts that support passing arguments, you can experiment with the following features.
在支持传递参数的脚本中, 您可以尝试以下功能.

### Default generation config
默认生成配置

The `--generation-config` argument specifies where the generation config will be loaded from when calling `LLM.get_default_sampling_params()`. If set to 'auto', the generation config will be loaded from model path. If set to a folder path, the generation config will be loaded from the specified folder path. If it is not provided, vLLM defaults will be used.
`--generation-config` 参数指定调用 `LLM.get_default_sampling_params()` 时生成配置的加载位置. 如果设置为 `'auto'`, 则生成配置将从模型路径加载. 如果设置为文件夹路径, 则生成配置将从指定的文件夹路径加载. 如果未提供此参数, 则使用 vLLM 默认值.

> If max_new_tokens is specified in generation config, then it sets a server-wide limit on the number of output tokens for all requests.
> 如果在生成配置中指定了 max_new_tokens, 那么它会为所有请求的输出 tokens 数量设置服务器范围的限制.
>

Try it yourself with the following argument:

```bash
--generation-config auto
```

### Quantization

#### GGUF

vLLM supports models that are quantized using GGUF.
vLLM 支持使用 GGUF 量化的模型.

Try one yourself using the `repo_id:quant_type` format to load directly from HuggingFace:
您可以自己尝试使用 `repo_id:quant_type` 格式直接从 HuggingFace 加载:

```bash
--model unsloth/Qwen3-0.6B-GGUF:Q4_K_M --tokenizer Qwen/Qwen3-0.6B
```

### CPU offload
CPU 卸载

The `--cpu-offload-gb` argument can be seen as a virtual way to increase the GPU memory size. For example, if you have one 24 GB GPU and set this to 10, virtually you can think of it as a 34 GB GPU. Then you can load a 13B model with BF16 weight, which requires at least 26GB GPU memory. Note that this requires fast CPU-GPU interconnect, as part of the model is loaded from CPU memory to GPU memory on the fly in each model forward pass.
`--cpu-offload-gb` 参数可以看作是一种虚拟增加 GPU 内存大小的方法. 例如, 如果您有一个 24 GB 的 GPU, 并将其设置为 10, 那么实际上您可以将其视为一个 34 GB 的 GPU. 然后, 您可以加载一个权重为 BF16 的 13B 模型, 这至少需要 26GB 的 GPU 内存. 请注意, 这需要快速的 CPU-GPU 互连, 因为在每次模型前向传播中, 模型的一部分都会动态地从 CPU 内存加载到 GPU 内存.

Try it yourself with the following arguments:

```bash
--model meta-llama/Llama-2-13b-chat-hf --cpu-offload-gb 10
```

## Example materials
示例材料

```python
# basic.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from vllm import LLM, SamplingParams

# Sample prompts.
prompts = [
    "Hello, my name is",
    "The president of the United States is",
    "The capital of France is",
    "The future of AI is",
]
# Create a sampling params object.
sampling_params = SamplingParams(temperature=0.8, top_p=0.95)


def main():
    # Create an LLM.
    llm = LLM(model="facebook/opt-125m")
    # Generate texts from the prompts.
    # The output is a list of RequestOutput objects
    # that contain the prompt, generated text, and other information.
    outputs = llm.generate(prompts, sampling_params)
    # Print the outputs.
    print("\nGenerated Outputs:\n" + "-" * 60)
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt:    {prompt!r}")
        print(f"Output:    {generated_text!r}")
        print("-" * 60)


if __name__ == "__main__":
    main()
```

```python
# chat.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from vllm import LLM, EngineArgs
from vllm.outputs import RequestOutput
from vllm.utils.argparse_utils import FlexibleArgumentParser


def create_parser():
    parser = FlexibleArgumentParser()
    # Add engine args
    EngineArgs.add_cli_args(parser)
    parser.set_defaults(model="meta-llama/Llama-3.2-1B-Instruct")
    # Add sampling params
    sampling_group = parser.add_argument_group("Sampling parameters")
    sampling_group.add_argument("--max-tokens", type=int)
    sampling_group.add_argument("--temperature", type=float)
    sampling_group.add_argument("--top-p", type=float)
    sampling_group.add_argument("--top-k", type=int)
    # Add example params
    parser.add_argument("--chat-template-path", type=str)

    return parser


def main(args: dict):
    # Pop arguments not used by LLM
    max_tokens = args.pop("max_tokens")
    temperature = args.pop("temperature")
    top_p = args.pop("top_p")
    top_k = args.pop("top_k")
    chat_template_path = args.pop("chat_template_path")

    # Create an LLM
    llm = LLM(**args)

    # Create sampling params object
    sampling_params = llm.get_default_sampling_params()
    if max_tokens is not None:
        sampling_params.max_tokens = max_tokens
    if temperature is not None:
        sampling_params.temperature = temperature
    if top_p is not None:
        sampling_params.top_p = top_p
    if top_k is not None:
        sampling_params.top_k = top_k

    def print_outputs(outputs: list[RequestOutput], prompts: list):
        assert len(outputs) == len(prompts)
        print("\nGenerated Outputs:\n" + "-" * 80)
        for i, output in enumerate(outputs):
            generated_text = output.outputs[0].text
            print(f"Prompt: {prompts[i]!r}\n")
            print(f"Generated text: {generated_text!r}")
            print("-" * 80)

    print("=" * 80)

    # In this script, we demonstrate how to pass input to the chat method:
    conversation = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hello! How can I assist you today?"},
        {
            "role": "user",
            "content": "Write an essay about the importance of higher education.",
        },
    ]
    outputs = llm.chat(conversation, sampling_params, use_tqdm=False)
    print_outputs(
        outputs,
        [
            conversation,
        ],
    )

    # You can run batch inference with llm.chat API
    conversations = [conversation for _ in range(10)]

    # We turn on tqdm progress bar to verify it's indeed running batch inference
    outputs = llm.chat(conversations, sampling_params, use_tqdm=True)
    print_outputs(outputs, conversations)

    # A chat template can be optionally supplied.
    # If not, the model will use its default chat template.
    if chat_template_path is not None:
        with open(chat_template_path) as f:
            chat_template = f.read()

        outputs = llm.chat(
            conversations,
            sampling_params,
            use_tqdm=False,
            chat_template=chat_template,
        )
        print_outputs(outputs, conversations)


if __name__ == "__main__":
    parser = create_parser()
    args: dict = vars(parser.parse_args())
    main(args)
```

```python
# classify.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from argparse import Namespace

from vllm import LLM, EngineArgs
from vllm.utils.argparse_utils import FlexibleArgumentParser


def parse_args():
    parser = FlexibleArgumentParser()
    parser = EngineArgs.add_cli_args(parser)
    # Set example specific arguments
    parser.set_defaults(
        model="jason9693/Qwen2.5-1.5B-apeach",
        runner="pooling",
        enforce_eager=True,
    )
    return parser.parse_args()


def main(args: Namespace):
    # Sample prompts.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]

    # Create an LLM.
    # You should pass runner="pooling" for classification models
    llm = LLM(**vars(args))

    # Generate logits. The output is a list of ClassificationRequestOutputs.
    outputs = llm.classify(prompts)

    # Print the outputs.
    print("\nGenerated Outputs:\n" + "-" * 60)
    for prompt, output in zip(prompts, outputs):
        probs = output.outputs.probs
        probs_trimmed = (str(probs[:16])[:-1] + ", ...]") if len(probs) > 16 else probs
        print(
            f"Prompt: {prompt!r} \n"
            f"Class Probabilities: {probs_trimmed} (size={len(probs)})"
        )
        print("-" * 60)


if __name__ == "__main__":
    args = parse_args()
    main(args)
```

```python
# embed.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from argparse import Namespace

from vllm import LLM, EngineArgs
from vllm.utils.argparse_utils import FlexibleArgumentParser
from vllm.utils.print_utils import print_embeddings


def parse_args():
    parser = FlexibleArgumentParser()
    parser = EngineArgs.add_cli_args(parser)
    # Set example specific arguments
    parser.set_defaults(
        model="intfloat/e5-small",
        runner="pooling",
        enforce_eager=True,
    )
    return parser.parse_args()


def main(args: Namespace):
    # Sample prompts.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]

    # Create an LLM.
    # You should pass runner="pooling" for embedding models
    llm = LLM(**vars(args))

    # Generate embedding. The output is a list of EmbeddingRequestOutputs.
    outputs = llm.embed(prompts)

    # Print the outputs.
    print("\nGenerated Outputs:\n" + "-" * 60)
    for prompt, output in zip(prompts, outputs):
        embeds = output.outputs.embedding
        print(f"Prompt: {prompt!r}")
        print_embeddings(embeds)
        print("-" * 60)


if __name__ == "__main__":
    args = parse_args()
    main(args)
```

```python
# generate.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from vllm import LLM, EngineArgs
from vllm.utils.argparse_utils import FlexibleArgumentParser


def create_parser():
    parser = FlexibleArgumentParser()
    # Add engine args
    EngineArgs.add_cli_args(parser)
    parser.set_defaults(model="meta-llama/Llama-3.2-1B-Instruct")
    # Add sampling params
    sampling_group = parser.add_argument_group("Sampling parameters")
    sampling_group.add_argument("--max-tokens", type=int)
    sampling_group.add_argument("--temperature", type=float)
    sampling_group.add_argument("--top-p", type=float)
    sampling_group.add_argument("--top-k", type=int)

    return parser


def main(args: dict):
    # Pop arguments not used by LLM
    max_tokens = args.pop("max_tokens")
    temperature = args.pop("temperature")
    top_p = args.pop("top_p")
    top_k = args.pop("top_k")

    # Create an LLM
    llm = LLM(**args)

    # Create a sampling params object
    sampling_params = llm.get_default_sampling_params()
    if max_tokens is not None:
        sampling_params.max_tokens = max_tokens
    if temperature is not None:
        sampling_params.temperature = temperature
    if top_p is not None:
        sampling_params.top_p = top_p
    if top_k is not None:
        sampling_params.top_k = top_k

    # Generate texts from the prompts. The output is a list of RequestOutput
    # objects that contain the prompt, generated text, and other information.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]
    outputs = llm.generate(prompts, sampling_params)
    # Print the outputs.
    print("-" * 50)
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"Prompt: {prompt!r}\nGenerated text: {generated_text!r}")
        print("-" * 50)


if __name__ == "__main__":
    parser = create_parser()
    args: dict = vars(parser.parse_args())
    main(args)
```

```python
# reward.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from argparse import Namespace

from vllm import LLM, EngineArgs
from vllm.utils.argparse_utils import FlexibleArgumentParser
from vllm.utils.print_utils import print_embeddings


def parse_args():
    parser = FlexibleArgumentParser()
    parser = EngineArgs.add_cli_args(parser)
    # Set example specific arguments
    parser.set_defaults(
        model="internlm/internlm2-1_8b-reward",
        runner="pooling",
        enforce_eager=True,
        max_model_len=1024,
        trust_remote_code=True,
    )
    return parser.parse_args()


def main(args: Namespace):
    # Sample prompts.
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
    ]

    # Create an LLM.
    # You should pass runner="pooling" for reward models
    llm = LLM(**vars(args))

    # Generate rewards. The output is a list of PoolingRequestOutput.
    outputs = llm.reward(prompts)

    # Print the outputs.
    print("\nGenerated Outputs:\n" + "-" * 60)
    for prompt, output in zip(prompts, outputs):
        rewards = output.outputs.data
        print(f"Prompt: {prompt!r}")
        print_embeddings(rewards, prefix="Reward")
        print("-" * 60)


if __name__ == "__main__":
    args = parse_args()
    main(args)
```

```python
# score.py
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from argparse import Namespace

from vllm import LLM, EngineArgs
from vllm.utils.argparse_utils import FlexibleArgumentParser


def parse_args():
    parser = FlexibleArgumentParser()
    parser = EngineArgs.add_cli_args(parser)
    # Set example specific arguments
    parser.set_defaults(
        model="BAAI/bge-reranker-v2-m3",
        runner="pooling",
        enforce_eager=True,
    )
    return parser.parse_args()


def main(args: Namespace):
    # Sample prompts.
    query = "What is the capital of France?"
    documents = [
        "The capital of Brazil is Brasilia.",
        "The capital of France is Paris.",
    ]

    # Create an LLM.
    # You should pass runner="pooling" for cross-encoder models
    llm = LLM(**vars(args))

    # Generate scores. The output is a list of ScoringRequestOutputs.
    outputs = llm.score(query, documents)

    # Print the outputs.
    print("\nGenerated Outputs:\n" + "-" * 60)
    for document, output in zip(documents, outputs):
        score = output.outputs.score
        print(f"Pair: {[query, document]!r} \nScore: {score}")
        print("-" * 60)


if __name__ == "__main__":
    args = parse_args()
    main(args)
```
