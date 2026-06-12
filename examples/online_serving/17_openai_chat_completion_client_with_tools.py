# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Set up this example by starting a vLLM OpenAI-compatible server with tool call
options enabled. For example:

IMPORTANT: for mistral, you must use one of the provided mistral tool call
templates, or your own - the model default doesn't work for tool calls with vLLM
See the vLLM docs on OpenAI server & tool calling for more details.

vllm serve mistralai/Mistral-7B-Instruct-v0.3 \
            --chat-template examples/tool_chat_template_mistral.jinja \
            --enable-auto-tool-choice --tool-call-parser mistral

OR
vllm serve NousResearch/Hermes-2-Pro-Llama-3-8B \
            --chat-template examples/tool_chat_template_hermes.jinja \
            --enable-auto-tool-choice --tool-call-parser hermes
"""

import json
from typing import Any

from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
# openai_api_key = "EMPTY"
# openai_api_base = "http://localhost:8000/v1"
openai_api_key = "my_secret_token_123"
openai_api_base = "http://172.16.10.51:8090/v1"

properties = {
    "city": {
        "type": "string",
        "description": "The city to find the weather for, e.g. 'San Francisco'",
    },
    "state": {
        "type": "string",
        "description": "the two-letter abbreviation for the state that the city is"
        " in, e.g. 'CA' which would mean 'California'",
    },
    "unit": {
        "type": "string",
        "description": "The unit to fetch the temperature in",
        "enum": ["celsius", "fahrenheit"],
    },
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": ["city", "state", "unit"],
            },
        },
    }
]

messages = [
    {"role": "user", "content": "Hi! How are you doing today?"},
    {"role": "assistant", "content": "I'm doing well! How can I help you?"},
    {
        "role": "user",
        "content": (
            "Can you tell me what the temperate will be in Dallas, in fahrenheit?"
        ),
    },
]


def get_current_weather(city: str, state: str, unit: "str"):
    return (
        "The weather in Dallas, Texas is 85 degrees fahrenheit. It is "
        "partly cloudly, with highs in the 90's."
    )


def handle_tool_calls_stream(
    client: OpenAI,
    messages: list[dict[str, str]],
    model: str,
    tools: list[dict[str, Any]],
) -> list[Any]:
    tool_calls_stream = client.chat.completions.create(
        messages=messages, model=model, tools=tools, stream=True
    )
    chunks = []
    print("chunks: ")
    for chunk in tool_calls_stream:
        print(f"handle_tool_calls_stream chunk: {chunk}")
        chunks.append(chunk)
        if chunk.choices[0].delta.tool_calls:
            print(chunk.choices[0].delta.tool_calls[0])
        else:
            print(chunk.choices[0].delta)
    return chunks


def handle_tool_calls_arguments(chunks: list[Any]) -> list[str]:
    arguments = []
    tool_call_idx = -1
    print("arguments: ")
    for chunk in chunks:
        if chunk.choices[0].delta.tool_calls:
            tool_call = chunk.choices[0].delta.tool_calls[0]
            if tool_call.index != tool_call_idx:
                if tool_call_idx >= 0:
                    print(f"streamed tool call arguments: {arguments[tool_call_idx]}")
                tool_call_idx = chunk.choices[0].delta.tool_calls[0].index
                arguments.append("")
            if tool_call.id:
                print(f"streamed tool call id: {tool_call.id} ")

            if tool_call.function:
                if tool_call.function.name:
                    print(f"streamed tool call name: {tool_call.function.name}")

                if tool_call.function.arguments:
                    arguments[tool_call_idx] += tool_call.function.arguments

    return arguments


def main():
    # Initialize OpenAI client
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=openai_api_key,
        base_url=openai_api_base,
    )

    # Get available models and select one
    models = client.models.list()
    model = models.data[0].id
    print(f"main model: {model}")

    print(f"main messages: {messages}")
    print(f"main tools: {tools}\n")
    chat_completion = client.chat.completions.create(
        messages=messages, model=model, tools=tools
    )

    print("-" * 70)
    print("Chat completion results:")
    print(chat_completion)
    print("-" * 70)

    # Stream tool calls
    chunks = handle_tool_calls_stream(client, messages, model, tools)
    print("-" * 70)

    # Handle arguments from streamed tool calls
    arguments = handle_tool_calls_arguments(chunks)
    print(f"main arguments: {arguments}")

    if len(arguments):
        print(f"streamed tool call arguments: {arguments[-1]}\n")

    print("-" * 70)

    # Add tool call results to the conversation
    messages.append(
        {
            "role": "assistant",
            "tool_calls": chat_completion.choices[0].message.tool_calls,
            "reasoning": chat_completion.choices[0].message.reasoning,
        }
    )

    # Now, simulate a tool call
    available_tools = {"get_current_weather": get_current_weather}

    completion_tool_calls = chat_completion.choices[0].message.tool_calls
    for call in completion_tool_calls:
        print(f"main call: {call}")
        tool_to_call = available_tools[call.function.name]
        args = json.loads(call.function.arguments)
        result = tool_to_call(**args)
        print("tool_to_call result: ", result)
        messages.append(
            {
                "role": "tool",
                "content": result,
                "tool_call_id": call.id,
                "name": call.function.name,
            }
        )

    print(f"main messages: {messages}")
    print(f"main tools: {tools}\n")
    chat_completion_2 = client.chat.completions.create(
        messages=messages, model=model, tools=tools, stream=False
    )
    print("Chat completion2 results:")
    print(chat_completion_2)
    print("-" * 70)


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
-v /root/huzhi/model:/model \
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
