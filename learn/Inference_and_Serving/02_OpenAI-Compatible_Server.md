# OpenAI-Compatible Server
兼容 OpenAI 的服务器

* https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/

vLLM provides an HTTP server that implements OpenAI's [Completions API](https://platform.openai.com/docs/api-reference/completions), [Chat API](https://platform.openai.com/docs/api-reference/chat), and more! This functionality lets you serve models and interact with them using an HTTP client.
vLLM 提供了一个 HTTP 服务器, 它实现了 OpenAI 的 [Completions API]()、[Chat API]() 等等! 此功能允许您使用 HTTP 客户端为模型提供服务并与它们交互.

In your terminal, you can [instal](https://docs.vllm.ai/en/v0.20.0/getting_started/installation/) vLLM, then start the server with the [`vllm serve`](https://docs.vllm.ai/en/v0.20.0/configuration/serve_args/) command. (You can also use our [Docker](https://docs.vllm.ai/en/v0.20.0/deployment/docker/) image.)
您可以在终端中安装 vLLM, 然后使用 `vllm serve` 命令启动服务器. (您也可以使用我们的 Docker 镜像.)

```bash
vllm serve NousResearch/Meta-Llama-3-8B-Instruct \
  --dtype auto \
  --api-key token-abc123
```

To call the server, in your preferred text editor, create a script that uses an HTTP client. Include any messages that you want to send to the model. Then run that script. Below is an example script using the [official OpenAI Python client](https://github.com/openai/openai-python).
要调用服务器, 请在您首选的文本编辑器中创建一个使用 HTTP 客户端的脚本. 其中包含您想要发送给模型的任何消息. 然后运行该脚本. 以下是使用官方 OpenAI Python 客户端的示例脚本.

```python
from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123",
)

completion = client.chat.completions.create(
    model="NousResearch/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "user", "content": "Hello!"},
    ],
)

print(completion.choices[0].message)
```

> Tip
> vLLM supports some parameters that are not supported by OpenAI, `top_k` for example. You can pass these parameters to vLLM using the OpenAI client in the `extra_body` parameter of your requests, i.e. `extra_body={"top_k": 50}` for `top_k`.
> vLLM 支持一些 OpenAI 不支持的参数, 例如 `top_k`. 您可以使用 OpenAI 客户端在请求的 `extra_body` 参数中将这些参数传递给 vLLM, 例如, 对于 `top_k` `extra_body={"top_k": 50}`.
>

> Important
> By default, the server applies `generation_config.json` from the Hugging Face model repository if it exists. This means the default values of certain sampling parameters can be overridden by those recommended by the model creator.
> 默认情况下, 服务器会应用 Hugging Face 模型仓库中的 `generation_config.json` 如果存在. 这意味着某些采样参数的默认值可以被模型创建者推荐的值所覆盖.
> To disable this behavior, please pass `--generation-config vllm` when launching the server.
> 要禁用此行为, 请在启动服务器时传递 `--generation-config vllm`.
>

## Supported APIs

We currently support the following OpenAI APIs:
我们目前支持以下 OpenAI API:

- [Completions API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#completions-api) (`/v1/completions`)

  - Only applicable to [text generation models](https://docs.vllm.ai/en/v0.20.0/models/generative_models/).

  - Note: `suffix` parameter is not supported.

- [Responses API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#responses-api) (`/v1/responses`)

  - Only applicable to [text generation models](https://docs.vllm.ai/en/v0.20.0/models/generative_models/).

- [Chat Completions API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#chat-api) (`/v1/chat/completions`)

  - Only applicable to [text generation models](https://docs.vllm.ai/en/v0.20.0/models/generative_models/) with a [chat template](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#chat-template).
    仅适用于带有聊天模板的文本生成模型.

  - Note: `user` parameter is ignored.

  - Note: Setting the `parallel_tool_calls` parameter to `false` ensures vLLM only returns zero or one tool call per request. Setting it to `true` (the default) allows returning more than one tool call per request. There is no guarantee more than one tool call will be returned if this is set to `true`, as that behavior is model dependent and not all models are designed to support parallel tool calls.
    注意: 将 `parallel_tool_calls` 参数设置为 `false` 可确保 vLLM 每个请求仅返回零个或一个 tool 调用. 将其设置为 `true` (默认值)则允许每个请求返回多个 tool 调用. 但如果将其设置为 `true`, 则不能保证一定会返回多个 tool 调用, 因为此行为取决于模型, 并非所有模型都支持并行 tool 调用.

- [Embeddings API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/embed/#openai-compatible-embeddings-api) (`/v1/embeddings`)

  - Only applicable to [embedding models](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/embed/).

- [Transcriptions API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#transcriptions-api) (`/v1/audio/transcriptions`)

  - Only applicable to [Automatic Speech Recognition (ASR) models](https://docs.vllm.ai/en/v0.20.0/models/supported_models/#transcription).
    仅适用于自动语音识别(ASR)模型

- [Translation API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#translations-api) (`/v1/audio/translations`)

  - Only applicable to [Automatic Speech Recognition (ASR) models](https://docs.vllm.ai/en/v0.20.0/models/supported_models/#transcription).
    仅适用于自动语音识别(ASR)模型

- [Realtime API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#realtime-api) (`/v1/realtime`)

  - Only applicable to [Automatic Speech Recognition (ASR) models](https://docs.vllm.ai/en/v0.20.0/models/supported_models/#realtime-transcription).
    仅适用于自动语音识别(ASR)模型

In addition, we have the following custom APIs:
此外, 我们还有以下自定义 API:

- [Tokenizer API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#tokenizer-api) (`/tokenize`, `/detokenize`)

  - Applicable to any model with a tokenizer.
    适用于任何带有标记器的模型.

- [pooling API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/#pooling-api) (`/pooling`)

  - Applicable to all [pooling models](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/).
    适用于所有[池化模型](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/).

- [Classification API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/classify/#classification-api) (`/classify`)

  - Only applicable to [classification models](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/classify/).
    仅适用于[分类模型](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/classify/).

- [Cohere Embed API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/embed/#cohere-embed-api) (`/v2/embed`)

  - Compatible with [Cohere's Embed API](https://docs.cohere.com/reference/embed)
    与 Cohere 的 Embed API 兼容

  - Works with any [embedding model](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/embed/#supported-models), including multimodal models.
    适用于任何[嵌入模型](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/embed/#supported-models), 包括多模态模型.

- [Score API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/scoring/#score-api) (`/score`, `/v1/score`)

  - Applicable to [score models](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/scoring/) (cross-encoder, bi-encoder, late-interaction).
    适用于评分模型(交叉编码器、双编码器、后期交互).

- [Generative Scoring API](https://docs.vllm.ai/en/v0.20.0/serving/openai_compatible_server/#generative-scoring-api) (`/generative_scoring`)

  - Applicable to [CausalLM models](https://docs.vllm.ai/en/v0.20.0/models/generative_models/) (task `"generate"`).

  - Computes next-token probabilities for specified `label_token_ids`.
    计算指定 `label_token_ids` 的下一个标记概率.

- [Rerank API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/scoring/#rerank-api) (`/rerank`, `/v1/rerank`, `/v2/rerank`)

  - Implements [Jina AI's v1 rerank API](https://jina.ai/reranker/)
    实现了 Jina AI 的 v1 重排序 API

  - Also compatible with [Cohere's v1 & v2 rerank APIs](https://docs.cohere.com/v2/reference/rerank)
    同时兼容 Cohere 的 v1 和 v2 重排序 API

  - Jina and Cohere's APIs are very similar; Jina's includes extra information in the rerank endpoint's response.
    Jina 和 Cohere 的 API 非常相似; Jina 在重新排名端点的响应中包含了额外的信息.

## Chat Template

In order for the language model to support chat protocol, vLLM requires the model to include a chat template in its tokenizer configuration. The chat template is a Jinja2 template that specifies how roles, messages, and other chat-specific tokens are encoded in the input.
为了使语言模型支持聊天协议, vLLM 要求模型在其分词器配置中包含一个聊天模板. 该聊天模板是一个 Jinja2 模板, 用于指定角色、消息和其他聊天特定标记在输入中的编码方式.

An example chat template for `NousResearch/Meta-Llama-3-8B-Instruct` can be found [here](https://llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/#prompt-template-for-meta-llama-3)

Some models do not provide a chat template even though they are instruction/chat fine-tuned. For those models, you can manually specify their chat template in the `--chat-template` parameter with the file path to the chat template, or the template in string form. Without a chat template, the server will not be able to process chat and all chat requests will error.
有些模型即使经过指令/聊天微调, 也不提供聊天模板. 对于这些模型, 您可以通过 `--chat-template` 参数手动指定聊天模板, 参数可以是聊天模板的文件路径, 也可以是字符串形式的模板内容. 如果没有聊天模板, 服务器将无法处理聊天, 所有聊天请求都​​会出错.

```bash
vllm serve <model> --chat-template ./path-to-chat-template.jinja
```

vLLM community provides a set of chat templates for popular models. You can find them under the [examples](https://github.com/vllm-project/vllm/tree/main/examples) directory.

With the inclusion of multi-modal chat APIs, the OpenAI spec now accepts chat messages in a new format which specifies both a `type` and a `text` field. An example is provided below:
随着多模式聊天 API 的加入, OpenAI 规范现在可以接受一种新格式的聊天消息, 该格式指定了 `type` 和 `text` 字段. 以下提供了一个示例:

```python
completion = client.chat.completions.create(
    model="NousResearch/Meta-Llama-3-8B-Instruct",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Classify this sentiment: vLLM is wonderful!"},
            ],
        },
    ],
)
```

Most chat templates for LLMs expect the `content` field to be a string, but there are some newer models like `meta-llama/Llama-Guard-3-1B` that expect the content to be formatted according to the OpenAI schema in the request. vLLM provides best-effort support to detect this automatically, which is logged as a string like *"Detected the chat template content format to be..."*, and internally converts incoming requests to match the detected format, which can be one of:
大多数 LLM 聊天模板都要求 `content` 字段为字符串, 但一些较新的模型(例如 `meta-llama/Llama-Guard-3-1B`)要求内容根据请求中的 OpenAI 模式进行格式化. vLLM 尽力支持自动检测, 并将其记录为类似 *"检测到聊天模板内容格式为..."的*字符串, 并在内部将传入的请求转换为与检测到的格式匹配的格式, 该格式可以是以下之一:

- `"string"`: A string.

  - Example: `"Hello world"`

- `"openai"`: A list of dictionaries, similar to OpenAI schema.

  - Example: `[{"type": "text", "text": "Hello world!"}]`

If the result is not what you expect, you can set the `--chat-template-content-format` CLI argument to override which format to use.
如果结果不符合您的预期, 您可以设置 `--chat-template-content-format` CLI 参数来覆盖要使用的格式.

## Extra Parameters

vLLM supports a set of parameters that are not part of the OpenAI API. In order to use them, you can pass them as extra parameters in the OpenAI client. Or directly merge them into the JSON payload if you are using HTTP call directly.
vLLM 支持一组不属于 OpenAI API 的参数. 为了使用它们, 你可以将它们作为 OpenAI 客户端的额外参数传递. 或者, 如果你直接使用 HTTP 调用, 也可以直接将它们合并到 JSON 负载中.

```python
completion = client.chat.completions.create(
    model="NousResearch/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "user", "content": "Classify this sentiment: vLLM is wonderful!"},
    ],
    extra_body={
        "structured_outputs": {"choice": ["positive", "negative"]},
    },
)
```

## Extra HTTP Headers

Only `X-Request-Id` HTTP request header is supported for now. It can be enabled with `--enable-request-id-headers`.
目前仅支持 `X-Request-Id` HTTP 请求头. 可以使用 `--enable-request-id-headers` 启用.

```python
completion = client.chat.completions.create(
    model="NousResearch/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "user", "content": "Classify this sentiment: vLLM is wonderful!"},
    ],
    extra_headers={
        "x-request-id": "sentiment-classification-00001",
    },
)
print(completion._request_id)

completion = client.completions.create(
    model="NousResearch/Meta-Llama-3-8B-Instruct",
    prompt="A robot may not injure a human being",
    extra_headers={
        "x-request-id": "completion-test",
    },
)
print(completion._request_id)
```

## Offline API Documentation
离线 API 文档

The FastAPI `/docs` endpoint requires an internet connection by default. To enable offline access in air-gapped environments, use the `--enable-offline-docs` flag:
FastAPI 的 `/docs` 端点默认需要网络连接. 要在物理隔离环境中启用离线访问, 请使用 `--enable-offline-docs` 标志:

```bash
vllm serve NousResearch/Meta-Llama-3-8B-Instruct --enable-offline-docs
```

## API Reference

### Completions API

Our Completions API is compatible with [OpenAI's Completions API](https://platform.openai.com/docs/api-reference/completions); you can use the [official OpenAI Python client](https://github.com/openai/openai-python) to interact with it.
我们的 Completions API 与 [OpenAI 的 Completions API](https://platform.openai.com/docs/api-reference/completions) 兼容; 您可以使用[官方 OpenAI Python 客户端](https://github.com/openai/openai-python)与其进行交互.

Code example: [examples/basic/online_serving/openai_completion_client.py](https://github.com/vllm-project/vllm/blob/main/examples/basic/online_serving/openai_completion_client.py)

#### Extra parameters

The following [sampling parameters](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters) are supported.
支持以下采样参数.

```python
    use_beam_search: bool = False
    top_k: int | None = None
    min_p: float | None = None
    repetition_penalty: float | None = None
    length_penalty: float = 1.0
    stop_token_ids: list[int] | None = []
    include_stop_str_in_output: bool = False
    ignore_eos: bool = False
    min_tokens: int = 0
    skip_special_tokens: bool = True
    spaces_between_special_tokens: bool = True
    truncate_prompt_tokens: Annotated[int, Field(ge=-1, le=_INT64_MAX)] | None = None
    allowed_token_ids: list[int] | None = None
    prompt_logprobs: int | None = None
```

The following extra parameters are supported:
支持以下额外参数:

```python
    prompt_embeds: bytes | list[bytes] | None = None
    add_special_tokens: bool = Field(
        default=True,
        description=(
            "If true (the default), special tokens (e.g. BOS) will be added to "
            "the prompt."
        ),
    )
    response_format: AnyResponseFormat | None = Field(
        default=None,
        description=(
            "Similar to chat completion, this parameter specifies the format "
            "of output. Only {'type': 'json_object'}, {'type': 'json_schema'}"
            ", {'type': 'structural_tag'}, or {'type': 'text' } is supported."
        ),
    )
    structured_outputs: StructuredOutputsParams | None = Field(
        default=None,
        description="Additional kwargs for structured outputs",
    )
    priority: int = Field(
        default=0,
        ge=_INT64_MIN,
        le=_INT64_MAX,
        description=(
            "The priority of the request (lower means earlier handling; "
            "default: 0). Any priority other than 0 will raise an error "
            "if the served model does not use priority scheduling."
        ),
    )
    request_id: str = Field(
        default_factory=random_uuid,
        description=(
            "The request_id related to this request. If the caller does "
            "not set it, a random_uuid will be generated. This id is used "
            "through out the inference process and return in response."
        ),
    )

    return_tokens_as_token_ids: bool | None = Field(
        default=None,
        description=(
            "If specified with 'logprobs', tokens are represented "
            " as strings of the form 'token_id:{token_id}' so that tokens "
            "that are not JSON-encodable can be identified."
        ),
    )
    return_token_ids: bool | None = Field(
        default=None,
        description=(
            "If specified, the result will include token IDs alongside the "
            "generated text. In streaming mode, prompt_token_ids is included "
            "only in the first chunk, and token_ids contains the delta tokens "
            "for each chunk. This is useful for debugging or when you "
            "need to map generated text back to input tokens."
        ),
    )

    cache_salt: str | None = Field(
        default=None,
        description=(
            "If specified, the prefix cache will be salted with the provided "
            "string to prevent an attacker to guess prompts in multi-user "
            "environments. The salt should be random, protected from "
            "access by 3rd parties, and long enough to be "
            "unpredictable (e.g., 43 characters base64-encoded, corresponding "
            "to 256 bit)."
        ),
    )

    kv_transfer_params: dict[str, Any] | None = Field(
        default=None,
        description="KVTransfer parameters used for disaggregated serving.",
    )

    vllm_xargs: dict[str, str | int | float] | None = Field(
        default=None,
        description=(
            "Additional request parameters with string or "
            "numeric values, used by custom extensions."
        ),
    )

    repetition_detection: RepetitionDetectionParams | None = Field(
        default=None,
        description="Parameters for detecting repetitive N-gram patterns "
        "in output tokens. If such repetition is detected, generation will "
        "be ended early. LLMs can sometimes generate repetitive, unhelpful "
        "token patterns, stopping only when they hit the maximum output length "
        "(e.g. 'abcdabcdabcd...' or '\\emoji \\emoji \\emoji ...'). This feature "
        "can detect such behavior and terminate early, saving time and tokens.",
    )
```

### Chat API

Our Chat API is compatible with [OpenAI's Chat Completions API](https://platform.openai.com/docs/api-reference/chat); you can use the [official OpenAI Python client](https://github.com/openai/openai-python) to interact with it.
我们的聊天 API 与 [OpenAI 的聊天完成 API](https://platform.openai.com/docs/api-reference/chat) 兼容; 您可以使用[官方 OpenAI Python 客户端](https://github.com/openai/openai-python)与其进行交互.

We support both [Vision](https://platform.openai.com/docs/guides/vision) - and [Audio](https://platform.openai.com/docs/guides/audio?audio-generation-quickstart-example=audio-in) - related parameters; see our [Multimodal Inputs](https://docs.vllm.ai/en/v0.20.0/features/multimodal_inputs/) guide for more information.
我们支持视觉和音频相关的参数; 请参阅我们的多模式输入指南了解更多信息.

- Note: `image_url.detail` parameter is not supported.

Code example: [examples/basic/online_serving/openai_chat_completion_client.py](https://github.com/vllm-project/vllm/blob/main/examples/basic/online_serving/openai_chat_completion_client.py)

#### Extra parameters

The following [sampling parameters](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters) are supported.

```python
    use_beam_search: bool = False
    top_k: int | None = None
    min_p: float | None = None
    repetition_penalty: float | None = None
    length_penalty: float = 1.0
    stop_token_ids: list[int] | None = []
    include_stop_str_in_output: bool = False
    ignore_eos: bool = False
    min_tokens: int = 0
    skip_special_tokens: bool = True
    spaces_between_special_tokens: bool = True
    truncate_prompt_tokens: Annotated[int, Field(ge=-1, le=_INT64_MAX)] | None = None
    prompt_logprobs: int | None = None
    allowed_token_ids: list[int] | None = None
    bad_words: list[str] = Field(default_factory=list)
```

The following extra parameters are supported:
支持以下额外参数:

```python
    echo: bool = Field(
        default=False,
        description=(
            "If true, the new message will be prepended with the last message "
            "if they belong to the same role."
        ),
    )
    add_generation_prompt: bool = Field(
        default=True,
        description=(
            "If true, the generation prompt will be added to the chat template. "
            "This is a parameter used by chat template in tokenizer config of the "
            "model."
        ),
    )
    continue_final_message: bool = Field(
        default=False,
        description=(
            "If this is set, the chat will be formatted so that the final "
            "message in the chat is open-ended, without any EOS tokens. The "
            "model will continue this message rather than starting a new one. "
            'This allows you to "prefill" part of the model\'s response for it. '
            "Cannot be used at the same time as `add_generation_prompt`."
        ),
    )
    add_special_tokens: bool = Field(
        default=False,
        description=(
            "If true, special tokens (e.g. BOS) will be added to the prompt "
            "on top of what is added by the chat template. "
            "For most models, the chat template takes care of adding the "
            "special tokens so this should be set to false (as is the "
            "default)."
        ),
    )
    documents: list[dict[str, str]] | None = Field(
        default=None,
        description=(
            "A list of dicts representing documents that will be accessible to "
            "the model if it is performing RAG (retrieval-augmented generation)."
            " If the template does not support RAG, this argument will have no "
            "effect. We recommend that each document should be a dict containing "
            '"title" and "text" keys.'
        ),
    )
    chat_template: str | None = Field(
        default=None,
        description=(
            "A Jinja template to use for this conversion. "
            "As of transformers v4.44, default chat template is no longer "
            "allowed, so you must provide a chat template if the tokenizer "
            "does not define one."
        ),
    )
    chat_template_kwargs: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Additional keyword args to pass to the template renderer. "
            "Will be accessible by the chat template."
        ),
    )
    media_io_kwargs: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Additional kwargs to pass to the media IO connectors, "
            "keyed by modality. Merged with engine-level media_io_kwargs."
        ),
    )
    mm_processor_kwargs: dict[str, Any] | None = Field(
        default=None,
        description=("Additional kwargs to pass to the HF processor."),
    )
    structured_outputs: StructuredOutputsParams | None = Field(
        default=None,
        description="Additional kwargs for structured outputs",
    )
    priority: int = Field(
        default=0,
        ge=_INT64_MIN,
        le=_INT64_MAX,
        description=(
            "The priority of the request (lower means earlier handling; "
            "default: 0). Any priority other than 0 will raise an error "
            "if the served model does not use priority scheduling."
        ),
    )
    request_id: str = Field(
        default_factory=random_uuid,
        description=(
            "The request_id related to this request. If the caller does "
            "not set it, a random_uuid will be generated. This id is used "
            "through out the inference process and return in response."
        ),
    )

    return_tokens_as_token_ids: bool | None = Field(
        default=None,
        description=(
            "If specified with 'logprobs', tokens are represented "
            " as strings of the form 'token_id:{token_id}' so that tokens "
            "that are not JSON-encodable can be identified."
        ),
    )
    return_token_ids: bool | None = Field(
        default=None,
        description=(
            "If specified, the result will include token IDs alongside the "
            "generated text. In streaming mode, prompt_token_ids is included "
            "only in the first chunk, and token_ids contains the delta tokens "
            "for each chunk. This is useful for debugging or when you "
            "need to map generated text back to input tokens."
        ),
    )

    cache_salt: str | None = Field(
        default=None,
        description=(
            "If specified, the prefix cache will be salted with the provided "
            "string to prevent an attacker to guess prompts in multi-user "
            "environments. The salt should be random, protected from "
            "access by 3rd parties, and long enough to be "
            "unpredictable (e.g., 43 characters base64-encoded, corresponding "
            "to 256 bit)."
        ),
    )

    kv_transfer_params: dict[str, Any] | None = Field(
        default=None,
        description="KVTransfer parameters used for disaggregated serving.",
    )

    vllm_xargs: dict[str, str | int | float | list[str | int | float]] | None = Field(
        default=None,
        description=(
            "Additional request parameters with (list of) string or "
            "numeric values, used by custom extensions."
        ),
    )

    repetition_detection: RepetitionDetectionParams | None = Field(
        default=None,
        description="Parameters for detecting repetitive N-gram patterns "
        "in output tokens. If such repetition is detected, generation will "
        "be ended early. LLMs can sometimes generate repetitive, unhelpful "
        "token patterns, stopping only when they hit the maximum output length "
        "(e.g. 'abcdabcdabcd...' or '\\emoji \\emoji \\emoji ...'). This feature "
        "can detect such behavior and terminate early, saving time and tokens.",
    )
```

### Responses API

Our Responses API is compatible with [OpenAI's Responses API](https://platform.openai.com/docs/api-reference/responses); you can use the [official OpenAI Python client](https://github.com/openai/openai-python) to interact with it.
我们的响应 API 与 [OpenAI 的响应 API](https://platform.openai.com/docs/api-reference/responses) 兼容; 您可以使用[官方的 OpenAI Python 客户端](https://github.com/openai/openai-python)与之交互.

Code example: [examples/online_serving/openai_responses_client_with_tools.py](https://github.com/vllm-project/vllm/blob/main/examples/online_serving/openai_responses_client_with_tools.py)

#### Extra parameters

The following extra parameters in the request object are supported:
请求对象中支持以下额外参数:

```python
    request_id: str = Field(
        default_factory=lambda: f"resp_{random_uuid()}",
        description=(
            "The request_id related to this request. If the caller does "
            "not set it, a random_uuid will be generated. This id is used "
            "through out the inference process and return in response."
        ),
    )
    media_io_kwargs: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Additional kwargs to pass to the media IO connectors, "
            "keyed by modality. Merged with engine-level media_io_kwargs."
        ),
    )
    mm_processor_kwargs: dict[str, Any] | None = Field(
        default=None,
        description=("Additional kwargs to pass to the HF processor."),
    )
    priority: int = Field(
        default=0,
        ge=_INT64_MIN,
        le=_INT64_MAX,
        description=(
            "The priority of the request (lower means earlier handling; "
            "default: 0). Any priority other than 0 will raise an error "
            "if the served model does not use priority scheduling."
        ),
    )
    cache_salt: str | None = Field(
        default=None,
        description=(
            "If specified, the prefix cache will be salted with the provided "
            "string to prevent an attacker to guess prompts in multi-user "
            "environments. The salt should be random, protected from "
            "access by 3rd parties, and long enough to be "
            "unpredictable (e.g., 43 characters base64-encoded, corresponding "
            "to 256 bit)."
        ),
    )

    enable_response_messages: bool = Field(
        default=False,
        description=(
            "Dictates whether or not to return messages as part of the "
            "response object. Currently only supported for non-background."
        ),
    )
    # similar to input_messages / output_messages in ResponsesResponse
    # we take in previous_input_messages (ie in harmony format)
    # this cannot be used in conjunction with previous_response_id
    # TODO: consider supporting non harmony messages as well
    previous_input_messages: list[OpenAIHarmonyMessage | dict] | None = None
    structured_outputs: StructuredOutputsParams | None = Field(
        default=None,
        description="Additional kwargs for structured outputs",
    )

    repetition_penalty: float | None = None
    seed: int | None = Field(None, ge=_INT64_MIN, le=_INT64_MAX)
    stop: str | list[str] | None = []
    ignore_eos: bool = False
    vllm_xargs: dict[str, str | int | float | list[str | int | float]] | None = Field(
        default=None,
        description=(
            "Additional request parameters with (list of) string or "
            "numeric values, used by custom extensions."
        ),
    )
    kv_transfer_params: dict[str, Any] | None = Field(
        default=None,
        description="KVTransfer parameters used for disaggregated serving.",
    )
```

The following extra parameters in the response object are supported:
响应对象中支持以下额外参数:

```python
    # These are populated when enable_response_messages is set to True
    # NOTE: custom serialization is needed
    # see serialize_input_messages and serialize_output_messages
    input_messages: ResponseInputOutputMessage | None = Field(
        default=None,
        description=(
            "If enable_response_messages, we can show raw token input to model."
        ),
    )
    output_messages: ResponseInputOutputMessage | None = Field(
        default=None,
        description=(
            "If enable_response_messages, we can show raw token output of model."
        ),
    )
```

### Transcriptions API

Our Transcriptions API is compatible with [OpenAI's Transcriptions API](https://platform.openai.com/docs/api-reference/audio/createTranscription); you can use the [official OpenAI Python client](https://github.com/openai/openai-python) to interact with it.
我们的转录 API 与 [OpenAI 的转录 API](https://platform.openai.com/docs/api-reference/audio/createTranscription) 兼容; 您可以使用[官方的 OpenAI Python 客户端](https://github.com/openai/openai-python)与之交互.

> Note
> To use the Transcriptions API, please install with extra audio dependencies using `pip install vllm[audio]`.
> 要使用转录 API, 请使用 `pip install vllm[audio]` 安装额外的音频依赖项.
>

Code example: [examples/online_serving/openai_transcription_client.py](https://github.com/vllm-project/vllm/blob/main/examples/online_serving/openai_transcription_client.py)

NOTE: beam search is currently supported in the transcriptions endpoint for encoder-decoder multimodal models, e.g., whisper, but highly inefficient as work for handling the encoder/decoder cache is actively ongoing. This is an active point of ongoing optimization and will be handled properly in the very near future.
注意: 目前, 编码器-解码器多模态模型(例如 Whisper)的转录端点支持束搜索, 但由于编码器/解码器缓存的处理工作仍在积极进行中, 因此效率极低. 这是一个正在积极优化的方面, 我们将在不久的将来妥善解决.

#### API Enforced Limits
API 强制限制

Set the maximum audio file size (in MB) that VLLM will accept, via the `VLLM_MAX_AUDIO_CLIP_FILESIZE_MB` environment variable. Default is 25 MB.
通过环境变量 `VLLM_MAX_AUDIO_CLIP_FILESIZE_MB` 设置 VLLM 可接受的最大音频文件大小(以 MB 为单位). 默认值为 25 MB.

#### Uploading Audio Files
上传音频文件

The Transcriptions API supports uploading audio files in various formats including FLAC, MP3, MP4, MPEG, MPGA, M4A, OGG, WAV, and WEBM.
转录 API 支持上传各种格式的音频文件, 包括 FLAC、MP3、MP4、MPEG、MPGA、M4A、OGG、WAV 和 WEBM.

**Using OpenAI Python Client:**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123",
)

# Upload audio file from disk
with open("audio.mp3", "rb") as audio_file:
    transcription = client.audio.transcriptions.create(
        model="openai/whisper-large-v3-turbo",
        file=audio_file,
        language="en",
        response_format="verbose_json",
    )

print(transcription.text)
```

**Using curl with multipart/form-data:**

```bash
curl -X POST "http://localhost:8000/v1/audio/transcriptions" \
  -H "Authorization: Bearer token-abc123" \
  -F "file=@audio.mp3" \
  -F "model=openai/whisper-large-v3-turbo" \
  -F "language=en" \
  -F "response_format=verbose_json"
```

**Supported Parameters: 支持的参数:**

- `file`: The audio file to transcribe (required)
  `file` : 要转录的音频文件(必填)

- `model`: The model to use for transcription (required)
  `model` : 用于转录的模型(必填)

- `language`: The language code (e.g., "en", "zh") (optional)
  `language` : 语言代码(例如, "en"、"zh")(可选)

- `prompt`: Optional text to guide the transcription style (optional)
  `prompt` : 用于指导转录风格的可选文本(可选)

- `response_format`: Format of the response ("json", "text") (optional)
  `response_format` : 响应格式("json"、"text")(可选)

- `temperature`: Sampling temperature between 0 and 1 (optional)
  `temperature` : 采样温度, 取值范围为 0 到 1(可选)

For the complete list of supported parameters including sampling parameters and vLLM extensions, see the [protocol definitions](https://github.com/vllm-project/vllm/blob/main/vllm/entrypoints/openai/protocol.py#L2182).
有关支持的参数(包括采样参数和 vLLM 扩展)的完整列表, 请参阅协议定义.

**Response Format:**

For `verbose_json` response format:

```json
{
    "text": "Hello, this is a transcription of the audio file.",
    "language": "en",
    "duration": 5.42,
    "segments": [
        {
            "id": 0,
            "seek": 0,
            "start": 0,
            "end": 2.5,
            "text": "Hello, this is a transcription",
            "tokens": [
                50364,
                938,
                428,
                307,
                275,
                28347
            ],
            "temperature": 0,
            "avg_logprob": -0.245,
            "compression_ratio": 1.235,
            "no_speech_prob": 0.012
        }
    ]
}
```

Currently "verbose_json" response format doesn’t support no_speech_prob.
目前"verbose_json"响应格式不支持 no_speech_prob.

#### Extra Parameters

The following [sampling parameters](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters) are supported.
支持以下[采样参数](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters).

```python
    use_beam_search: bool = False
    """Whether or not beam search should be used."""

    n: int = 1
    """The number of beams to be used in beam search."""

    length_penalty: float = 1.0
    """Length penalty to be used for beam search."""

    include_stop_str_in_output: bool = False
    """Whether to include the stop strings in output text."""

    temperature: float = Field(default=0.0)
    """The sampling temperature, between 0 and 1.

    Higher values like 0.8 will make the output more random, while lower values
    like 0.2 will make it more focused / deterministic. If set to 0, the model
    will use [log probability](https://en.wikipedia.org/wiki/Log_probability)
    to automatically increase the temperature until certain thresholds are hit.
    """

    top_p: float | None = None
    """Enables nucleus (top-p) sampling, where tokens are selected from the
    smallest possible set whose cumulative probability exceeds `p`.
    """

    top_k: int | None = None
    """Limits sampling to the `k` most probable tokens at each step."""

    min_p: float | None = None
    """Filters out tokens with a probability lower than `min_p`, ensuring a
    minimum likelihood threshold during sampling.
    """

    seed: int | None = Field(None, ge=_LONG_INFO.min, le=_LONG_INFO.max)
    """The seed to use for sampling."""

    frequency_penalty: float | None = 0.0
    """The frequency penalty to use for sampling."""

    repetition_penalty: float | None = None
    """The repetition penalty to use for sampling."""

    presence_penalty: float | None = 0.0
    """The presence penalty to use for sampling."""

    max_completion_tokens: int | None = None
    """The maximum number of tokens to generate."""
```

The following extra parameters are supported:
支持以下额外参数:

```python
    # Flattened stream option to simplify form data.
    stream_include_usage: bool | None = False
    stream_continuous_usage_stats: bool | None = False

    vllm_xargs: dict[str, str | int | float | bool] | None = Field(
        default=None,
        description=(
            "Additional request parameters with string or "
            "numeric values, used by custom extensions."
        ),
    )
```

### Translations API

Our Translation API is compatible with [OpenAI's Translations API](https://platform.openai.com/docs/api-reference/audio/createTranslation); you can use the [official OpenAI Python client](https://github.com/openai/openai-python) to interact with it. Whisper models can translate audio from one of the 55 non-English supported languages into English. Please mind that the popular `openai/whisper-large-v3-turbo` model does not support translating.
我们的翻译 API 与 [OpenAI 的翻译 API](https://platform.openai.com/docs/api-reference/audio/createTranslation) 兼容; 您可以使用[官方的 OpenAI Python 客户端](https://github.com/openai/openai-python)与之交互. Whisper 模型可以将 55 种非英语支持的语言的音频翻译成英语. 请注意, 常用的 `openai/whisper-large-v3-turbo` 模型不支持翻译功能.

> Note
> To use the Translation API, please install with extra audio dependencies using `pip install vllm[audio]`.
> 要使用翻译 API, 请使用 `pip install vllm[audio]` 安装额外的音频依赖项.
>

Code example: [examples/online_serving/openai_translation_client.py](https://github.com/vllm-project/vllm/blob/main/examples/online_serving/openai_translation_client.py)

#### Extra Parameters

The following [sampling parameters](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters) are supported.
支持以下[采样参数](https://docs.vllm.ai/en/v0.20.0/api/#inference-parameters).

```python
    use_beam_search: bool = False
    """Whether or not beam search should be used."""

    n: int = 1
    """The number of beams to be used in beam search."""

    length_penalty: float = 1.0
    """Length penalty to be used for beam search."""

    include_stop_str_in_output: bool = False
    """Whether to include the stop strings in output text."""

    seed: int | None = Field(None, ge=_LONG_INFO.min, le=_LONG_INFO.max)
    """The seed to use for sampling."""

    temperature: float = Field(default=0.0)
    """The sampling temperature, between 0 and 1.

    Higher values like 0.8 will make the output more random, while lower values
    like 0.2 will make it more focused / deterministic. If set to 0, the model
    will use [log probability](https://en.wikipedia.org/wiki/Log_probability)
    to automatically increase the temperature until certain thresholds are hit.
    """
```

The following extra parameters are supported:
支持以下额外参数:

```python
    language: str | None = None
    """The language of the input audio we translate from.

    Supplying the input language in
    [ISO-639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) format
    will improve accuracy.
    """

    to_language: str | None = None
    """The language of the input audio we translate to.

    Please note that this is not supported by all models, refer to the specific
    model documentation for more details.
    For instance, Whisper only supports `to_language=en`.
    """

    stream: bool | None = False
    """Custom field not present in the original OpenAI definition. When set,
    it will enable output to be streamed in a similar fashion as the Chat
    Completion endpoint.
    """
    # Flattened stream option to simplify form data.
    stream_include_usage: bool | None = False
    stream_continuous_usage_stats: bool | None = False

    max_completion_tokens: int | None = None
    """The maximum number of tokens to generate."""
```

### Realtime API

The Realtime API provides WebSocket-based streaming audio transcription, allowing real-time speech-to-text as audio is being recorded.
实时 API 提供基于 WebSocket 的流式音频转录, 允许在录制音频的同时进行实时语音转文本.

> Note
> To use the Realtime API, please install with extra audio dependencies using `uv pip install vllm[audio]`.
> 要使用实时 API, 请使用 `uv pip install vllm[audio]` 安装额外的音频依赖项.
>

#### Audio Format
音频格式

Audio must be sent as base64-encoded PCM16 audio at 16kHz sample rate, mono channel.
音频必须以 base64 编码的 PCM16 音频格式发送, 采样率为 16kHz, 单声道.

#### Protocol Overview
协议概述

1. Client connects to `ws://host/v1/realtime`
   客户端连接到 `ws://host/v1/realtime`

2. Server sends `session.created` event
   服务器发送 `session.created` 事件

3. Client optionally sends `session.update` with model/params
   客户端可以选择性地发送 `session.update` 其中包含模型/参数.

4. Client sends `input_audio_buffer.commit` when ready
   客户端准备就绪后会发送 `input_audio_buffer.commit`

5. Client sends `input_audio_buffer.append` events with base64 PCM16 chunks
   客户端发送带有 base64 PCM16 数据块的 `input_audio_buffer.append` 事件

6. Server sends `transcription.delta` events with incremental text
   服务器发送包含增量文本的 `transcription.delta` 事件

7. Server sends `transcription.done` with final text + usage
   服务器发送 `transcription.done`, 包含最终文本和使用情况.

8. Repeat from step 5 for next utterance
   对下一个语句重复步骤 5.

9. Optionally, client sends input_audio_buffer.commit with final=True to signal audio input is finished. Useful when streaming audio files
   客户端可以选择性地发送 `input_audio_buffer.commit` 并设置 `final=True`, 以表明音频输入已结束. 这在流式传输音频文件时非常有用.

#### Client → Server Events

| Event                       | Description                                                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------- |
| `input_audio_buffer.append` | Send base64-encoded audio chunk: `{"type": "input_audio_buffer.append", "audio": "<base64>"}`   |
| `input_audio_buffer.commit` | Trigger transcription processing or end: `{"type": "input_audio_buffer.commit", "final": bool}` |
| `session.update`            | Configure session: `{"type": "session.update", "model": "model-name"}`                          |

#### Server → Client Events


| Event                 | Description                                                                        |
| --------------------- | ---------------------------------------------------------------------------------- |
| `session.created`     | Connection established with session ID and timestamp                               |
| `transcription.delta` | Incremental transcription text: `{"type": "transcription.delta", "delta": "text"}` |
| `transcription.done`  | Final transcription with usage stats                                               |
| `error`               | Error notification with message and optional code                                  |

#### Example Clients

- [openai_realtime_client.py](https://github.com/vllm-project/vllm/tree/main/examples/online_serving/openai_realtime_client.py) - Upload and transcribe an audio file
  openai_realtime_client.py - 上传并转录音频文件

- [openai_realtime_microphone_client.py](https://github.com/vllm-project/vllm/tree/main/examples/online_serving/openai_realtime_microphone_client.py) - Gradio demo for live microphone transcription
  openai_realtime_microphone_client.py - Gradio 实时麦克风转录演示

### Tokenizer API

Our Tokenizer API is a simple wrapper over [HuggingFace-style tokenizers](https://huggingface.co/docs/transformers/en/main_classes/tokenizer). It consists of two endpoints:
我们的分词器 API 是对 HuggingFace 式分词器的简单封装. 它包含两个端点:

- `/tokenize` corresponds to calling `tokenizer.encode()`.

- `/detokenize` corresponds to calling `tokenizer.decode()`.

### Generative Scoring API

The `/generative_scoring` endpoint uses a CausalLM model (e.g., Llama, Qwen, Mistral) to compute the probability of specified token IDs appearing as the next token. Each item (document) is concatenated with the query to form a prompt, and the model predicts how likely each label token is as the next token after that prompt. This lets you score items against a query — for example, asking "Is this the capital of France?" and scoring each city by how likely the model is to answer "Yes".
`/generative_scoring` 端点使用 CausalLM 模型(例如 Llama、Qwen、Mistral)来计算指定词元 ID 作为下一个词元出现的概率. 每个条目(文档)都与查询连接起来形成一个提示, 模型预测每个标签词元作为该提示之后下一个词元的可能性. 这样, 您就可以根据查询对条目进行评分 — 例如, 询问"这是法国的首都吗?", 并根据模型回答"是"的可能性对每个城市进行评分.

This endpoint is automatically available when the server is started with a generative model (task `"generate"`). It is separate from the pooling-based [Score API](https://docs.vllm.ai/en/v0.20.0/models/pooling_models/scoring/#score-api), which uses cross-encoder, bi-encoder, or late-interaction models.
当服务器启动时使用生成模型(任务 `"generate"` ), 此端点会自动可用. 它与基于池化的评分 API 不同, 后者使用交叉编码器、双编码器或后期交互模型.

**Requirements:**

- The `label_token_ids` parameter is **required** and must contain **at least 1 token ID**.
  `label_token_ids` 参数是必需的, 并且必须至少包含 1 个 token ID.

- When 2 label tokens are provided, the score equals `P(label_token_ids[0]) / (P(label_token_ids[0]) + P(label_token_ids[1]))` (softmax over the two labels).
  当提供 2 个标签标记时, 得分等于 `P(label_token_ids[0]) / (P(label_token_ids[0]) + P(label_token_ids[1]))` (对两个标签进行 softmax 运算).

- When more labels are provided, the score is the softmax-normalized probability of the first label token across all label tokens.
  当提供更多标签时, 得分是第一个标签标记在所有标签标记中的 softmax 归一化概率.

#### Example

```bash
curl -X POST http://localhost:8000/generative_scoring \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "query": "Is this city the capital of France?",
    "items": ["Paris", "London", "Berlin"],
    "label_token_ids": [9454, 2753]
  }'
```

Here, each item is appended to the query to form prompts like `"Is this city the capital of France? Paris"`, `"... London"`, etc. The model then predicts the next token, and the score reflects the probability of "Yes" (token 9454) vs "No" (token 2753).
在这里, 每个项目都附加到查询中, 形成诸如 `"Is this city the capital of France? Paris"`、`"... London"` 等提示. 然后, 模型预测下一个标记, 得分反映了"是"(标记 9454)与"否"(标记 2753)的概率.

Response

```json
{
    "id": "generative-scoring-abc123",
    "object": "list",
    "created": 1234567890,
    "model": "Qwen/Qwen3-0.6B",
    "data": [
        {
            "index": 0,
            "object": "score",
            "score": 0.95
        },
        {
            "index": 1,
            "object": "score",
            "score": 0.12
        },
        {
            "index": 2,
            "object": "score",
            "score": 0.08
        }
    ],
    "usage": {
        "prompt_tokens": 45,
        "total_tokens": 48,
        "completion_tokens": 3
    }
}
```

#### How it works

1. **Prompt Construction**: For each item, builds `prompt = query + item` (or `item + query` if `item_first=true`)
   提示构建: 对于每个项目, 构建 `prompt = query + item` (如果 `item_first=true`, 则为 `item + query`)

2. **Forward Pass**: Runs the model on each prompt to get next-token logits
   前向传递: 对每个提示运行模型以获取下一个标记的 logits

3. **Probability Extraction**: Extracts logprobs for the specified `label_token_ids`
   概率提取: 提取指定 `label_token_ids` 的对数概率

4. **Softmax Normalization**: Applies softmax over only the label tokens (when `apply_softmax=true`)
   Softmax 归一化: 仅对标签标记应用 softmax 函数(当 `apply_softmax=true` 时).

5. **Score**: Returns the normalized probability of the first label token
   得分: 返回第一个标签标记的归一化概率.

#### Finding Token IDs

To find the token IDs for your labels, use the tokenizer:
要查找标签的标记 ID, 请使用分词器:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
yes_id = tokenizer.encode("Yes", add_special_tokens=False)[0]
no_id = tokenizer.encode("No", add_special_tokens=False)[0]
print(f"Yes: {yes_id}, No: {no_id}")
```

## Ray Serve LLM

Ray Serve LLM enables scalable, production-grade serving of the vLLM engine. It integrates tightly with vLLM and extends it with features such as auto-scaling, load balancing, and back-pressure.
Ray Serve LLM 能够以可扩展的生产级方式提供 vLLM 引擎服务. 它与 vLLM 紧密集成, 并扩展了其功能, 例如自动扩缩容、负载均衡和背压.

Key capabilities:
主要能力:

- Exposes an OpenAI-compatible HTTP API as well as a Pythonic API.
  提供与 OpenAI 兼容的 HTTP API 以及 Pythonic API.

- Scales from a single GPU to a multi-node cluster without code changes.
  无需更改代码即可从单个 GPU 扩展到多节点集群.

- Provides observability and autoscaling policies through Ray dashboards and metrics.
  通过 Ray 仪表板和指标提供可观测性和自动扩展策略.

The following example shows how to deploy a large model like DeepSeek R1 with Ray Serve LLM: [examples/online_serving/ray_serve_deepseek.py](https://github.com/vllm-project/vllm/blob/main/examples/online_serving/ray_serve_deepseek.py).
以下示例展示了如何使用 Ray Serve LLM 部署像 DeepSeek R1 这样的大型模型: examples/online_serving/ray_serve_deepseek.py

Learn more about Ray Serve LLM with the official [Ray Serve LLM documentation](https://docs.ray.io/en/latest/serve/llm/index.html).
欲了解更多关于 Ray Serve LLM 的信息, 请参阅 Ray Serve LLM 的官方文档.
