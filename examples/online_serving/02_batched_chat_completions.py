# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""Examples of batched chat completions via the vLLM OpenAI-compatible API.

The /v1/chat/completions/batch endpoint accepts ``messages`` as a list of
conversations.  Each conversation is processed independently and the response
contains one choice per conversation, indexed 0, 1, ..., N-1.

Start a server first, e.g.:
    vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 8000

Current limitations compared to /v1/chat/completions:
    - Streaming is not supported.
    - Tool use is not supported.
    - Beam search is not supported.
"""

import json
import os

import httpx

BASE_URL = os.environ.get("VLLM_BASE_URL", "http://localhost:8000")
MODEL = os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
TOKEN = os.environ.get("VLLM_TOKEN", "my_secret_token_123")
BATCH_URL = f"{BASE_URL}/v1/chat/completions/batch"

headers = {
    "User-Agent": "Test Client",
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def post_batch(payload: dict) -> dict:
    response = httpx.post(BATCH_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("=== Example 1a: single conversation (standard endpoint) ===")

    response = httpx.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": "What is the capital of Japan?"}],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    print(f"Example 1a data: {data}")
    # {
    #     'id': 'chatcmpl-b92ab5ec373fde5b',
    #     'object': 'chat.completion',
    #     'created': 1781174265,
    #     'model': 'Qwen3.6-27B',
    #     'choices': [
    #         {
    #             'index': 0,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'Here\'s a thinking process:\n\n1.  **Identify the User\'s Question**: The user is asking "What is the capital of Japan?"\n2.  **Retrieve Knowledge**: I know that Japan\'s capital is Tokyo. This is a well-established, widely recognized fact.\n3.  **Verify Accuracy**: Double-check: Is Tokyo officially recognized as the capital? Yes. While Japan\'s constitution doesn\'t explicitly name a capital, Tokyo has been the de facto capital since 1868 (Meiji Restoration), and it\'s universally recognized as such.\n4.  **Formulate Response**: Keep it concise and direct. "The capital of Japan is Tokyo."\n5.  **Final Output Generation**: Output the response.✅\n</think>\n\nThe capital of Japan is **Tokyo**.',
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
    #         'prompt_tokens': 17,
    #         'total_tokens': 182,
    #         'completion_tokens': 165,
    #         'prompt_tokens_details': None
    #     },
    #     'prompt_logprobs': None,
    #     'prompt_token_ids': None,
    #     'kv_transfer_params': None
    # }

    for choice in data["choices"]:
        print(f"  [{choice['index']}] {choice['message']['content']}")

    print("\n=== Example 1b: batched plain text (2 conversations) ===")
    data = post_batch(
        {
            "model": MODEL,
            "messages": [
                [{"role": "user", "content": "What is the capital of France?"}],
                [{"role": "user", "content": "What is the capital of Japan?"}],
            ],
        }
    )
    print(f"Example 1b data: {data}")
    # {
    #     'id': 'chatcmpl-92a8b7fb84e55490',
    #     'object': 'chat.completion',
    #     'created': 1781174840,
    #     'model': 'Qwen3.6-27B',
    #     'choices': [
    #         {
    #             'index': 0,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'Here\'s a thinking process:\n\n1.  **Analyze User Input:**\n   - Question: "What is the capital of France?"\n   - This is a straightforward factual question.\n\n2.  **Identify Key Information Needed:**\n   - Country: France\n   - Required: Capital city\n\n3.  **Retrieve Knowledge:**\n   - From general knowledge: The capital of France is Paris.\n\n4.  **Verify Accuracy:**\n   - Cross-check with reliable sources (internal knowledge base): Paris is indeed the capital and most populous city of France.\n   - No ambiguity or recent changes.\n\n5.  **Formulate Response:**\n   - Keep it concise and direct.\n   - "The capital of France is Paris."\n\n6.  **Final Output Generation:**\n   - Output matches the formulated response.✅\n</think>\n\nThe capital of France is Paris.',
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
    #         },
    #         {
    #             'index': 1,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'Here\'s a thinking process:\n\n1.  **Identify the User\'s Question**: The user is asking "What is the capital of Japan?"\n2.  **Retrieve Knowledge**: I know that Japan is a country in East Asia. Its capital city is widely known to be Tokyo.\n3.  **Verify Accuracy**: Double-check factual knowledge. Yes, Tokyo is the capital of Japan. It\'s also the most populous city and the seat of the Emperor and the national government.\n4.  **Formulate Response**: Keep it clear, direct, and accurate. "The capital of Japan is Tokyo."\n5.  **Final Output Generation**: Output the response.✅\n</think>\n\nThe capital of Japan is **Tokyo**.',
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
    #         'prompt_tokens': 34,
    #         'total_tokens': 372,
    #         'completion_tokens': 338,
    #         'prompt_tokens_details': None
    #     },
    #     'prompt_logprobs': None,
    #     'prompt_token_ids': None,
    #     'kv_transfer_params': None
    # }

    for choice in data["choices"]:
        print(f"  [{choice['index']}] {choice['message']['content']}")

    print("\n=== Example 2: batch with regex constraint (yes|no) ===")
    data = post_batch(
        {
            "model": MODEL,
            "messages": [
                [{"role": "user", "content": "Is the sky blue? Answer yes or no."}],
                [{"role": "user", "content": "Is fire cold? Answer yes or no."}],
            ],
            "structured_outputs": {"regex": "(yes|no)"},
        }
    )
    print(f"Example 2 data: {data}")
    # {
    #     'id': 'chatcmpl-b4e84c5b3f85bf25',
    #     'object': 'chat.completion',
    #     'created': 1781174850,
    #     'model': 'Qwen3.6-27B',
    #     'choices': [
    #         {
    #             'index': 0,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'yes',
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
    #         },
    #         {
    #             'index': 1,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': 'no',
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
    #         'prompt_tokens': 39,
    #         'total_tokens': 44,
    #         'completion_tokens': 5,
    #         'prompt_tokens_details': None
    #     },
    #     'prompt_logprobs': None,
    #     'prompt_token_ids': None,
    #     'kv_transfer_params': None
    # }
    for choice in data["choices"]:
        print(f"  [{choice['index']}] {choice['message']['content']}")

    print("\n=== Example 3: batch with json_schema ===")
    person_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the person"},
            "age": {"type": "integer", "description": "Age in years"},
        },
        "required": ["name", "age"],
    }
    data = post_batch(
        {
            "model": MODEL,
            "messages": [
                [
                    {
                        "role": "user",
                        "content": "Describe the person: name Alice, age 30.",
                    }
                ],
                [{"role": "user", "content": "Describe the person: name Bob, age 25."}],
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "person",
                    "strict": True,
                    "schema": person_schema,
                },
            },
        }
    )
    print(f"Example 3 data: {data}")
    # {
    #     'id': 'chatcmpl-9a0ab1b8d3acb7f7',
    #     'object': 'chat.completion',
    #     'created': 1781174850,
    #     'model': 'Qwen3.6-27B',
    #     'choices': [
    #         {
    #             'index': 0,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': '{\n  "name": "Alice",\n  "age": 30\n}',
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
    #         },
    #         {
    #             'index': 1,
    #             'message': {
    #                 'role': 'assistant',
    #                 'content': '{\n  "name": "Bob",\n  "age": 25\n}',
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
    #         'prompt_tokens': 44,
    #         'total_tokens': 84,
    #         'completion_tokens': 40,
    #         'prompt_tokens_details': None
    #     },
    #     'prompt_logprobs': None,
    #     'prompt_token_ids': None,
    #     'kv_transfer_params': None
    # }
    for choice in data["choices"]:
        person = json.loads(choice["message"]["content"])
        print(f"  [{choice['index']}] {person}")

    print("\n=== Example 4: batch book summaries ===")
    book_schema = {
        "type": "object",
        "properties": {
            "author": {
                "type": "string",
                "description": "Full name of the author",
            },
            "num_pages": {
                "type": "integer",
                "description": "Number of pages in the book",
            },
            "short_summary": {
                "type": "string",
                "description": "A one-sentence summary of the book",
            },
            "long_summary": {
                "type": "string",
                "description": (
                    "A detailed two to three sentence summary covering "
                    "the main themes and plot"
                ),
            },
        },
        "required": ["author", "num_pages", "short_summary", "long_summary"],
    }
    system_msg = {
        "role": "system",
        "content": (
            "You are a literary analyst. Extract structured information "
            "from book descriptions."
        ),
    }
    data = post_batch(
        {
            "model": MODEL,
            "messages": [
                [
                    system_msg,
                    {
                        "role": "user",
                        "content": (
                            "Extract information from this book: '1984' by George"
                            " Orwell, published in 1949, 328 pages. A dystopian"
                            " novel set in a totalitarian society ruled by Big"
                            " Brother, following Winston Smith as he secretly"
                            " rebels against the oppressive Party that surveils"
                            " and controls every aspect of life."
                        ),
                    },
                ],
                [
                    system_msg,
                    {
                        "role": "user",
                        "content": (
                            "Extract information from this book: 'The Hitchhiker's"
                            " Guide to the Galaxy' by Douglas Adams, published in"
                            " 1979, 193 pages. A comedic science fiction novel"
                            " following Arthur Dent, an ordinary Englishman who is"
                            " whisked off Earth moments before it is demolished to"
                            " make way for a hyperspace bypass, and his subsequent"
                            " absurd adventures across the universe."
                        ),
                    },
                ],
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "book_summary",
                    "strict": True,
                    "schema": book_schema,
                },
            },
        }
    )
    print(f"Example 4 data: {data}")
    # {
    #     "id": "chatcmpl-80b9c1154e225d97",
    #     "object": "chat.completion",
    #     "created": 1781174851,
    #     "model": "Qwen3.6-27B",
    #     "choices": [
    #         {
    #             "index": 0,
    #             "message": {
    #                 "role": "assistant",
    #                 "content": '{\n  "author": "George Orwell",\n  "num_pages": 328,\n  "short_summary": "A dystopian novel set in a totalitarian society ruled by Big Brother, following Winston Smith as he secretly rebels against the oppressive Party that surveils and controls every aspect of life.",\n  "long_summary": "1984 is a dystopian novel by George Orwell, published in 1949. The story is set in a totalitarian society ruled by an omnipresent figure known as Big Brother. The protagonist, Winston Smith, works for the Ministry of Truth, where he falsifies historical records to align with the Party\'s ever-changing narrative. Despite the Party\'s intense surveillance and control over every aspect of life, Winston secretly rebels against the oppressive regime. He engages in a forbidden affair with Julia, a fellow Party member, and seeks out the rumored resistance group led by O\'Brien. However, his rebellion is ultimately crushed by the Thought Police, leading to his capture, torture, and psychological reconditioning. The novel explores themes of totalitarianism, surveillance, propaganda, and the loss of individual freedom, serving as a powerful critique of authoritarian regimes and a warning about the potential dangers of unchecked government power."\n}',
    #                 "refusal": None,
    #                 "annotations": None,
    #                 "audio": None,
    #                 "function_call": None,
    #                 "tool_calls": [],
    #                 "reasoning": None,
    #             },
    #             "logprobs": None,
    #             "finish_reason": "stop",
    #             "stop_reason": None,
    #             "token_ids": None,
    #         },
    #         {
    #             "index": 1,
    #             "message": {
    #                 "role": "assistant",
    #                 "content": '{\n  "author": "Douglas Adams",\n  "num_pages": 193,\n  "short_summary": "A comedic science fiction novel following Arthur Dent, an ordinary Englishman who is whisked off Earth moments before it is demolished to make way for a hyperspace bypass, and his subsequent absurd adventures across the universe."\n  ,"long_summary": "A comedic science fiction novel following Arthur Dent, an ordinary Englishman who is whisked off Earth moments before it is demolished to make way for a hyperspace bypass, and his subsequent absurd adventures across the universe."\n}',
    #                 "refusal": None,
    #                 "annotations": None,
    #                 "audio": None,
    #                 "function_call": None,
    #                 "tool_calls": [],
    #                 "reasoning": None,
    #             },
    #             "logprobs": None,
    #             "finish_reason": "stop",
    #             "stop_reason": None,
    #             "token_ids": None,
    #         },
    #     ],
    #     "service_tier": None,
    #     "system_fingerprint": None,
    #     "usage": {
    #         "prompt_tokens": 198,
    #         "total_tokens": 576,
    #         "completion_tokens": 378,
    #         "prompt_tokens_details": None,
    #     },
    #     "prompt_logprobs": None,
    #     "prompt_token_ids": None,
    #     "kv_transfer_params": None,
    # }
    for choice in data["choices"]:
        book = json.loads(choice["message"]["content"])
        print(f"  [{choice['index']}] {book}")


if __name__ == "__main__":
    print(f"BASE_URL: {BASE_URL}", flush=True)
    print(f"MODEL: {MODEL}", flush=True)
    print(f"BATCH_URL: {BATCH_URL}\n", flush=True)

    main()

"""
export VLLM_BASE_URL=http://172.16.10.51:8090 && \
export VLLM_MODEL=Qwen3.6-27B && \
python 02_Batched_Chat_Completions.py

"""
