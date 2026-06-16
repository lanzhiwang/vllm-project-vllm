# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
To run this example, you can start the vLLM server
without any specific flags:

```bash
vllm serve unsloth/Llama-3.2-1B-Instruct \
    --structured-outputs-config.backend outlines
```

This example demonstrates how to generate chat completions
using the OpenAI Python client library.
"""

from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
# openai_api_key = "EMPTY"
# openai_api_base = "http://localhost:8000/v1"
openai_api_key = "my_secret_token_123"
openai_api_base = "http://172.16.10.51:8090/v1"

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to find the weather for"
                        ", e.g. 'San Francisco'",
                    },
                    "state": {
                        "type": "string",
                        "description": (
                            "the two-letter abbreviation for the state that the "
                            "city is in, e.g. 'CA' which would mean 'California'"
                        ),
                    },
                    "unit": {
                        "type": "string",
                        "description": "The unit to fetch the temperature in",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["city", "state", "unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Get the weather forecast for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "The city to get the forecast for, e.g. 'New York'"
                        ),
                    },
                    "state": {
                        "type": "string",
                        "description": (
                            "The two-letter abbreviation for the state, e.g. 'NY'"
                        ),
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to get the forecast for (1-7)",
                    },
                    "unit": {
                        "type": "string",
                        "description": "The unit to fetch the temperature in",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["city", "state", "days", "unit"],
            },
        },
    },
]

messages = [
    {"role": "user", "content": "Hi! How are you doing today?"},
    {"role": "assistant", "content": "I'm doing well! How can I help you?"},
    {
        "role": "user",
        "content": "Can you tell me what the current weather is in Dallas \
            and the forecast for the next 5 days, in fahrenheit?",
    },
]


def main():
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    models = client.models.list()
    model = models.data[0].id
    print(f"main model: {model}\n")

    print(f"main messages: {messages}")
    print(f"main tools: {tools}\n")
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        tools=tools,
        tool_choice="required",
        stream=True,  # Enable streaming response
    )

    for chunk in chat_completion:
        print(f"main chunk: {chunk}")
        if chunk.choices and chunk.choices[0].delta.tool_calls:
            print(chunk.choices[0].delta.tool_calls)

    chat_completion = client.chat.completions.create(
        messages=messages, model=model, tools=tools, tool_choice="required"
    )
    print(f"main chat_completion: {chat_completion}")

    print(chat_completion.choices[0].message.tool_calls)


if __name__ == "__main__":
    main()

"""
vllm serve mistralai/Mistral-7B-Instruct-v0.3 \
            --chat-template examples/tool_chat_template_mistral.jinja \
            --enable-auto-tool-choice --tool-call-parser mistral

docker run -ti --rm \
--entrypoint /usr/bin/env \
--security-opt seccomp=unconfined \
--gpus '"device=2, 6"' \
-v /data/model:/model \
-p 0.0.0.0:8090:8000 \
--name vllm-server \
vllm/vllm-openai:v0.20.0-cu129-ubuntu2404 bash

export VLLM_LOGGING_LEVEL=DEBUG
export VLLM_DEBUG_LOG_API_SERVER_RESPONSE=TRUE
export VLLM_TRACE_FUNCTION=1

export TORCH_DISTRIBUTED_DEBUG=DETAIL
export TORCH_SHOW_CPP_STACKTRACES=1
export CUDA_LAUNCH_BLOCKING=1

export NCCL_DEBUG=TRACE
export NCCL_DEBUG_SUBSYS=INIT,COLL,ENV,ALLOC

export TRITON_DEBUG=1
export TRITON_PRINT_AUTOTUNING=1

unset VLLM_TRACE_FUNCTION
unset CUDA_LAUNCH_BLOCKING
unset NCCL_DEBUG
unset NCCL_DEBUG_SUBSYS
unset TRITON_DEBUG
unset TRITON_PRINT_AUTOTUNING
unset TORCH_DISTRIBUTED_DEBUG

vllm serve \
/model/Mistral-7B-Instruct-v0.3 \
--served-model-name Mistral-7B-Instruct-v0.3 \
--trust-remote-code \
--use-tqdm-on-load \
--host 0.0.0.0 \
--port 8000 \
--api-key my_secret_token_123 my_secret_token_456 \
--enable-log-requests \
--enable-log-outputs \
--no-disable-uvicorn-access-log \
--uvicorn-log-level debug \
--aggregate-engine-logging \
--enable-logging-iteration-details \
--log-error-stack \
--cudagraph-metrics \
--kv-cache-metrics \
--enable-mfu-metrics \
--enable-log-deltas \
--enable-prompt-tokens-details \
--enable-tokenizer-info-endpoint \
--enable-server-load-tracking \
--enable-force-include-usage \
--shutdown-timeout 30 \
--chat-template /model/tool_chat_template_mistral.jinja \
--enable-auto-tool-choice \
--tool-call-parser mistral

"""
