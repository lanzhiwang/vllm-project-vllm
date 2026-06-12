"""
curl -X POST http://127.0.0.1:8090/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my_secret_token_123" \
    -d '{
    "model": "Qwen3.6-27B",
    "stream": true,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "Who won the world series in 2020?"
        }
    ]
}'

为了将您提供的 `curl` 请求(指向 vLLM 的 OpenAI 兼容 `/v1/chat/completions` 接口)集成到您的 Python 模板中, 我们需要对原始模板进行以下适配:

1. 接口路径与请求体格式: 原模板针对的是 `/generate` 接口(自定义 JSON 结构), 我们需要将其修改为 `/v1/chat/completions` 的格式, 包括增加 `messages` 列表及 `model` 参数.

2. 鉴权机制: 在 Headers 中增加 `"Authorization": "Bearer my_secret_token_123"`.

3. 流式数据解析: `/v1/chat/completions` 在启用 `stream=True` 时采用的是 Server-Sent Events (SSE) 标准格式(以 `data: ` 开头并以 `[DONE]` 结束), 因此解析时需要过滤前缀并提取 `choices[0].delta.content`.

4. 非流式数据解析: 非流式模式下, 响应内容在 `choices[0].message.content` 中.
"""

import argparse
import json
from argparse import Namespace
from collections.abc import Iterable

import requests


def clear_line(n: int = 1) -> None:
    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR, flush=True)


def post_http_request(
    messages: list[dict],
    api_url: str,
    model: str,
    token: str,
    stream: bool = False,
) -> requests.Response:
    headers = {
        "User-Agent": "Test Client",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    pload = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "stream": stream,
    }
    print(f"post_http_request api_url: {api_url}\n", flush=True)
    print(f"post_http_request headers: {headers}\n", flush=True)
    print(f"post_http_request pload: {pload}\n", flush=True)
    print(f"post_http_request stream: {stream}\n", flush=True)
    response = requests.post(api_url, headers=headers, json=pload, stream=stream)
    return response


def get_streaming_response(response: requests.Response) -> Iterable[list[str]]:
    accumulated_choices: list[str] = []

    for chunk in response.iter_lines(
        chunk_size=8192, decode_unicode=False, delimiter=b"\n"
    ):
        if chunk:
            chunk_str = chunk.decode("utf-8").strip()
            # print(f"get_streaming_response chunk_str: {chunk_str}", flush=True)
            # chunk_str: data: {"id":"chatcmpl-96b8e8f4841b3f77","object":"chat.completion.chunk","created":1781172369,"model":"Qwen3.6-27B","choices":[{"index":0,"delta":{"content":" anything"},"logprobs":null,"finish_reason":null,"token_ids":null}],"usage":{"prompt_tokens":25,"total_tokens":946,"completion_tokens":921}}

            # chunk_str: data: [DONE]

            # SSE 格式数据行以 "data: " 开头
            if chunk_str.startswith("data: "):
                data_body = chunk_str[6:].strip()
                # print(f"get_streaming_response data_body: {data_body}", flush=True)
                # data_body: {"id":"chatcmpl-96b8e8f4841b3f77","object":"chat.completion.chunk","created":1781172369,"model":"Qwen3.6-27B","choices":[{"index":0,"delta":{"content":" anything"},"logprobs":null,"finish_reason":null,"token_ids":null}],"usage":{"prompt_tokens":25,"total_tokens":946,"completion_tokens":921}}

                # data_body: [DONE]

                # 流结束标志
                if data_body == "[DONE]":
                    break

                try:
                    data = json.loads(data_body)
                    # print(f"get_streaming_response data: {data}\n", flush=True)
                    # data: {
                    #     'id': 'chatcmpl-96b8e8f4841b3f77',
                    #     'object': 'chat.completion.chunk',
                    #     'created': 1781172369,
                    #     'model': 'Qwen3.6-27B',
                    #     'choices': [
                    #         {
                    #             'index': 0,
                    #             'delta': {'content': ' anything'},
                    #             'logprobs': None,
                    #             'finish_reason': None,
                    #             'token_ids': None
                    #         }
                    #     ],
                    #     'usage': {'prompt_tokens': 25, 'total_tokens': 946, 'completion_tokens': 921}
                    # }

                    choices = data.get("choices", [])
                    for choice in choices:
                        idx = choice.get("index", 0)
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")

                        if content:
                            while len(accumulated_choices) <= idx:
                                accumulated_choices.append("")
                            accumulated_choices[idx] += content

                    if accumulated_choices:
                        yield accumulated_choices
                except json.JSONDecodeError:
                    continue


def get_response(response: requests.Response) -> list[str]:
    data = json.loads(response.content)
    print(f"get_response data: {data}\n", flush=True)
    # {
    #     'id': 'chatcmpl-b99158fce2b2806a',
    #     'object': 'chat.completion',
    #     'created': 1781171562,
    #     'model': 'Qwen3.6-27B',
    #     'choices': [
    #         {
    #             'index': 0,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'Here\'s a thinking process:\n\n1.  **Identify the core question**: The user is asking "Who won the world series in 2020?"\n2.  **Identify key entities/concepts**: World Series (Major League Baseball championship), year 2020.\n3.  **Retrieve knowledge**: I need to recall or verify who won the 2020 World Series.\n   - The 2020 World Series was played between the Los Angeles Dodgers and the Tampa Bay Rays.\n   - The Dodgers won the series 4-2.\n   - This was the Dodgers\' first World Series title since 1988.\n4.  **Verify accuracy**: \n   - Year: 2020\n   - Winner: Los Angeles Dodgers\n   - Opponent: Tampa Bay Rays\n   - Series result: 4-2\n   - This is a well-known, factual sports result. No controversy or ambiguity.\n5.  **Formulate response**: State clearly that the Los Angeles Dodgers won the 2020 World Series, optionally adding brief context (defeated Tampa Bay Rays 4-2) for completeness.\n6.  **Check tone/style**: Keep it direct and accurate. Match user\'s simple question with a concise answer.\n   - "The Los Angeles Dodgers won the 2020 World Series, defeating the Tampa Bay Rays 4 games to 2."\n7.  **Final output generation**: Matches the formulated response.✅\n</think>\n\nThe **Los Angeles Dodgers** won the 2020 World Series, defeating the Tampa Bay Rays 4 games to 2.',
    #                 'refusal': None,
    #                 'annotations': None,
    #                 'audio': None,
    #                 'function_call': None,
    #                 'tool_calls': [],
    #                 'reasoning': None
    #             },
    #             'logprobs': None,
    #             'finish_reason': 'stop',
    #             'stop_reason': None,
    #             'token_ids': None
    #         }
    #     ],
    #     'service_tier': None,
    #     'system_fingerprint': None,
    #     'usage': {
    #         'prompt_tokens': 33,
    #         'total_tokens': 384,
    #         'completion_tokens': 351,
    #         'prompt_tokens_details': None
    #     },
    #     'prompt_logprobs': None,
    #     'prompt_token_ids': None,
    #     'kv_transfer_params': None
    # }

    choices = data.get("choices", [])
    outputs = []
    for choice in choices:
        message = choice.get("message", {})
        content = message.get("content", "")
        outputs.append(content)
    return outputs


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--model", type=str, default="Qwen3.6-27B")
    parser.add_argument("--token", type=str, default="my_secret_token_123")
    parser.add_argument(
        "--prompt", type=str, default="Who won the world series in 2020?"
    )
    parser.add_argument("--stream", action="store_true")
    return parser.parse_args()


def main(args: Namespace):
    print(f"main args: {args}\n", flush=True)

    prompt = args.prompt
    model = args.model
    token = args.token
    stream = args.stream

    api_url = f"http://{args.host}:{args.port}/v1/chat/completions"

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    print(f"Prompt: {prompt!r}\n", flush=True)
    response = post_http_request(messages, api_url, model, token, stream)

    # 基础异常响应处理
    if response.status_code != 200:
        print(f"HTTP Error {response.status_code}: {response.text}")
        return

    if stream:
        num_printed_lines = 0
        for h in get_streaming_response(response):
            clear_line(num_printed_lines)
            num_printed_lines = 0
            for i, line in enumerate(h):
                num_printed_lines += 1
                print(f"Choice {i}: {line}", flush=True)
    else:
        output = get_response(response)
        for i, line in enumerate(output):
            print(f"Choice {i}: {line}", flush=True)


if __name__ == "__main__":
    args = parse_args()
    main(args)

"""
关键改动说明:
1. `post_http_request`:
   - 将原先接收单个 `prompt: str` 改为了接收 `messages: list[dict]`.
   - 增加 `model` 和 `token` 参数, 并在 Headers 里带入 `Authorization`.

2. `get_streaming_response`:
   - 适配 OpenAI 规格的 SSE (Server-Sent Events) 输出.
   - 过滤 `data:` 字符串, 并在收到 `[DONE]` 标识时中断迭代.
   - 通过 `accumulated_choices` 存储各个索引的输出片段, 从而契合原代码的终端刷新(`clear_line`)机制.

python 01_API_Client.py --host=172.16.10.51 --port=8090
python 01_API_Client.py --host=172.16.10.51 --port=8090 --stream --prompt="San Francisco is a"


"""
