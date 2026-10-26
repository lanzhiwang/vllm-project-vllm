# 清程极智 | v1/responses | "stream": true
```bash
$ curl https://aiping.cn/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer QC-2d4760be29bff6dc7f21d2a272fa9333-5cf3066364cb75987cfcce74fa52adf5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "instructions": "You are a helpful assistant.",
    "input": "Hello!",
    "stream": true
  }'
event: response.created
data: {
    "type": "response.created",
    "sequence_number": 0,
    "response": {
        "id": "resp-a4mpv4p43x",
        "object": "response",
        "created_at": 1790160817,
        "status": "in_progress",
        "model": "deepseek-v4-flash",
        "store": true,
        "expire_at": 1790420017
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160817
}

event: response.in_progress
data: {
    "type": "response.in_progress",
    "sequence_number": 1,
    "response": {
        "id": "resp-a4mpv4p43x",
        "object": "response",
        "created_at": 1790160817,
        "status": "in_progress",
        "model": "deepseek-v4-flash",
        "store": true,
        "expire_at": 1790420017
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160817
}

event: response.output_item.added
data: {
    "type": "response.output_item.added",
    "sequence_number": 2,
    "output_index": 0,
    "item": {
        "id": "rsn-gp6rm89c8j",
        "type": "reasoning",
        "status": "in_progress"
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.content_part.added
data: {
    "type": "response.content_part.added",
    "sequence_number": 3,
    "item_id": "rsn-gp6rm89c8j",
    "output_index": 0,
    "content_index": 0,
    "part": {
        "type": "reasoning_text",
        "text": ""
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.reasoning_text.delta
data: {
    "type": "response.reasoning_text.delta",
    "sequence_number": 4,
    "item_id": "rsn-gp6rm89c8j",
    "output_index": 0,
    "content_index": 0,
    "delta": "The",
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 5, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " user just", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 6, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " said \"Hello!\"", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 7, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " I need to", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 8, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " respond in", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 9, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " a friendly and", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 10, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " helpful manner. Since", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 11, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " this is a general", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 12, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " greeting, I'll respond", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 13, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " warmly and offer", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 14, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " assistance. I", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 15, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": " should keep it simple and open", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.delta
data: {"type": "response.reasoning_text.delta", "sequence_number": 16, "item_id": "rsn-gp6rm89c8j", "output_index": 0, "content_index": 0, "delta": "-ended.", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.reasoning_text.done
data: {
    "type": "response.reasoning_text.done",
    "sequence_number": 17,
    "item_id": "rsn-gp6rm89c8j",
    "output_index": 0,
    "content_index": 0,
    "text": "The user just said \"Hello!\" I need to respond in a friendly and helpful manner. Since this is a general greeting, I'll respond warmly and offer assistance. I should keep it simple and open-ended.",
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.content_part.done
data: {
    "type": "response.content_part.done",
    "sequence_number": 18,
    "item_id": "rsn-gp6rm89c8j",
    "output_index": 0,
    "content_index": 0,
    "part": {
        "type": "reasoning_text",
        "text": "The user just said \"Hello!\" I need to respond in a friendly and helpful manner. Since this is a general greeting, I'll respond warmly and offer assistance. I should keep it simple and open-ended."
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.output_item.done
data: {
    "type": "response.output_item.done",
    "sequence_number": 19,
    "output_index": 0,
    "item": {
        "id": "rsn-gp6rm89c8j",
        "type": "reasoning",
        "status": "completed",
        "content": [
            {
                "type": "reasoning_text",
                "text": "The user just said \"Hello!\" I need to respond in a friendly and helpful manner. Since this is a general greeting, I'll respond warmly and offer assistance. I should keep it simple and open-ended."
            }
        ]
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.output_item.added
data: {
    "type": "response.output_item.added",
    "sequence_number": 20,
    "output_index": 1,
    "item": {
        "id": "msg-cn5cda0g44",
        "type": "message",
        "status": "in_progress",
        "role": "assistant"
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.content_part.added
data: {
    "type": "response.content_part.added",
    "sequence_number": 21,
    "item_id": "msg-cn5cda0g44",
    "output_index": 1,
    "content_index": 0,
    "part": {
        "type": "output_text",
        "text": ""
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.output_text.delta
data: {
    "type": "response.output_text.delta",
    "sequence_number": 22,
    "item_id": "msg-cn5cda0g44",
    "output_index": 1,
    "content_index": 0,
    "delta": "Hello! How can I help",
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.output_text.delta
data: {"type": "response.output_text.delta", "sequence_number": 23, "item_id": "msg-cn5cda0g44", "output_index": 1, "content_index": 0, "delta": " you today?", "provider": "-", "model": "DeepSeek-V4-Flash", "is_fallback": false, "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661", "created": 1790160818}

event: response.output_text.done
data: {
    "type": "response.output_text.done",
    "sequence_number": 24,
    "item_id": "msg-cn5cda0g44",
    "output_index": 1,
    "content_index": 0,
    "text": "Hello! How can I help you today?",
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.content_part.done
data: {
    "type": "response.content_part.done",
    "sequence_number": 25,
    "item_id": "msg-cn5cda0g44",
    "output_index": 1,
    "content_index": 0,
    "part": {
        "type": "output_text",
        "text": "Hello! How can I help you today?"
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.output_item.done
data: {
    "type": "response.output_item.done",
    "sequence_number": 26,
    "output_index": 1,
    "item": {
        "id": "msg-cn5cda0g44",
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [
            {
                "type": "output_text",
                "text": "Hello! How can I help you today?"
            }
        ]
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

event: response.completed
data: {
    "type": "response.completed",
    "sequence_number": 27,
    "response": {
        "id": "resp-a4mpv4p43x",
        "object": "response",
        "created_at": 1790160817,
        "status": "completed",
        "model": "deepseek-v4-flash",
        "output": [
            {
                "id": "rsn-gp6rm89c8j",
                "type": "reasoning",
                "status": "completed",
                "content": [
                    {
                        "type": "reasoning_text",
                        "text": "The user just said \"Hello!\" I need to respond in a friendly and helpful manner. Since this is a general greeting, I'll respond warmly and offer assistance. I should keep it simple and open-ended."
                    }
                ]
            },
            {
                "id": "msg-cn5cda0g44",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Hello! How can I help you today?"
                    }
                ]
            }
        ],
        "usage": {
            "input_tokens": 91,
            "output_tokens": 53,
            "output_tokens_details": {
                "reasoning_tokens": 0
            },
            "total_tokens": 144
        },
        "store": true,
        "expire_at": 1790420017
    },
    "provider": "-",
    "model": "DeepSeek-V4-Flash",
    "is_fallback": false,
    "aiping_id": "0871d4d9-4d4e-40ed-ba17-a515c1408661",
    "created": 1790160818
}

$
```

总结规律:
```bash
# response.created
event: response.created

# response.in_progress
event: response.in_progress

# reasoning_text
event: response.output_item.added

event: response.content_part.added

event: response.reasoning_text.delta
event: response.reasoning_text.delta
event: response.reasoning_text.done

event: response.content_part.done

event: response.output_item.done

# output_text
event: response.output_item.added

event: response.content_part.added

event: response.output_text.delta
event: response.output_text.delta
event: response.output_text.done

event: response.content_part.done

event: response.output_item.done

# response.completed
event: response.completed
```


# 清程极智 | v1/responses | "stream": false
```bash
$ curl https://aiping.cn/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer QC-2d4760be29bff6dc7f21d2a272fa9333-5cf3066364cb75987cfcce74fa52adf5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "instructions": "You are a helpful assistant.",
    "input": "Hello!",
    "stream": false
  }'
{
    "id": "resp-77y9wezhr2",
    "object": "response",
    "created_at": 1790160886,
    "status": "completed",
    "model": "DeepSeek-V4-Flash",
    "output": [
        {
            "id": "rsn-163t1jwwc9",
            "type": "reasoning",
            "status": "completed",
            "content": [
                {
                    "type": "reasoning_text",
                    "text": "We need answer hello. Need maybe respond friendly."
                }
            ]
        },
        {
            "id": "msg-9te86ix57v",
            "type": "message",
            "status": "completed",
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": "Hello! How can I help you today?"
                }
            ]
        }
    ],
    "usage": {
        "input_tokens": 91,
        "output_tokens": 21,
        "output_tokens_details": {
            "reasoning_tokens": 0
        },
        "total_tokens": 112
    },
    "store": true,
    "expire_at": 1790420086,
    "provider": "-",
    "is_fallback": false,
    "aiping_id": "a23a0ef7-e3cc-4893-ab1c-3a38207ec9c1",
    "created": 1790160887
}
$
```

# 清程极智 | /v1/chat/completions | "stream": true
```bash
$ curl https://aiping.cn/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer QC-2d4760be29bff6dc7f21d2a272fa9333-5cf3066364cb75987cfcce74fa52adf5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "stream": true
  }'
data: {
    "id": "as-qv39mhhnab",
    "object": "chat.completion.chunk",
    "created": 1790160937,
    "model": "DeepSeek-V4-Flash",
    "choices": [
        {
            "index": 0,
            "delta": {
                "content": null,
                "role": "assistant",
                "reasoning_content": "H"
            },
            "flag": 0
        }
    ],
    "provider": "-",
    "is_fallback": false,
    "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"
}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "mm, the user just"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " greeted me with a simple"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " \"Hello!\""}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " This"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " is a very common"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " opening."}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " The"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " user likely"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " wants to"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " initiate a conversation or test"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " my responsiveness"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": ". There"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "'s no complex request"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " or hidden"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " question"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " here.\n\nMy"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " response should be warm"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " and friendly to"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " set"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " a positive"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " tone. I'll start"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " with a matching"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " greeting and introduce"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " myself as \""}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "Deep"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "Seek\""}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " to establish my"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " identity. Since the"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " greeting"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " is open"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "-ended, I should immediately"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " follow"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " up by offering"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " assistance to encourage"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " the"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " user to share their"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " actual need. I"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "'ll list"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " a"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " few common areas"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " where"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " I can help—general"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " questions, writing"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": ", coding, brainstorming"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "—to make it easy"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " for them to specify"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "."}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " Asking \""}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "what"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " can I"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " do for"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " you today?\" directly"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " invites"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " them"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " to state"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": " their purpose"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": null, "reasoning_content": "."}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {
    "id": "as-qv39mhhnab",
    "object": "chat.completion.chunk",
    "created": 1790160937,
    "model": "DeepSeek-V4-Flash",
    "choices": [
        {
            "index": 0,
            "delta": {
                "content": "Hello"
            },
            "flag": 0
        }
    ],
    "provider": "-",
    "is_fallback": false,
    "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"
}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": "! How"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " can I assist"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " you today? If"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " you have any questions,"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " need help with"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " a"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " task"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": ", or just"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " want to chat, feel"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " free to let"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {"id": "as-qv39mhhnab", "object": "chat.completion.chunk", "created": 1790160937, "model": "DeepSeek-V4-Flash", "choices": [{"index": 0, "delta": {"content": " me know! 😊"}, "flag": 0}], "provider": "-", "is_fallback": false, "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"}

data: {
    "id": "as-qv39mhhnab",
    "object": "chat.completion.chunk",
    "created": 1790160937,
    "model": "DeepSeek-V4-Flash",
    "choices": [
        {
            "index": 0,
            "delta": {
                "content": ""
            },
            "finish_reason": "stop",
            "flag": 0
        }
    ],
    "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 189,
        "total_tokens": 201,
        "completion_tokens_details": {
            "reasoning_tokens": 151
        }
    },
    "provider": "-",
    "is_fallback": false,
    "aiping_id": "2d6df445-946a-4de7-bc9f-f3aa306a83eb"
}

data: [DONE]

$
```

# 清程极智 | /v1/chat/completions | "stream": false
```bash
$ curl https://aiping.cn/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer QC-2d4760be29bff6dc7f21d2a272fa9333-5cf3066364cb75987cfcce74fa52adf5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "stream": false
  }'
{
    "id": "as-y7c9p6tk20",
    "object": "chat.completion",
    "created": 1790161012,
    "model": "DeepSeek-V4-Flash",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello there! I'm glad to be your helpful assistant today. How can I assist you? Feel free to ask me anything—whether it's answering questions, brainstorming ideas, writing content, solving problems, or just having a chat. I'm all ears!",
                "reasoning_content": "1.  **Analyze the User's Input**:\n    *   User says: \"You are a helpful assistant.\" (This is a system prompt injection/instruction, but it's also what I *am*, so I acknowledge it).\n    *   User says: \"Hello!\" (Standard greeting).\n\n2.  **Determine the appropriate response**:\n    *   Acknowledge the greeting.\n    *   Acknowledge the \"helpful assistant\" part (confirming my role).\n    *   Offer assistance to keep the conversation moving.\n\n3.  **Draft the response**:\n    *   \"Hello! Yes, I am a helpful assistant. How can I assist you today?\"\n    *   *Refinement*: Make it warm, welcoming, and open-ended. \"Hello there! I'm glad to be your helpful assistant today. What can I do for you? Feel free to ask me anything.\""
            },
            "finish_reason": "stop",
            "flag": 0
        }
    ],
    "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 242,
        "total_tokens": 254,
        "completion_tokens_details": {
            "reasoning_tokens": 188
        }
    },
    "provider": "-",
    "is_fallback": false,
    "aiping_id": "16f6635b-db99-41b9-84f9-c6016a99012d"
}
$
```

# 首都在线 | v1/responses | "stream": true
```bash
$ curl https://api.gpugeek.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer b0eafnpr1ayzlux1000dkynvug6rhkd4c00ev3g5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "instructions": "You are a helpful assistant.",
    "input": "Hello!",
    "stream": true
  }'
event: response.created
data: {
    "response": {
        "caching": {
            "type": "disabled"
        },
        "created_at": 1790161072,
        "expire_at": 1790420271,
        "id": "cds_e6816797-3735-4062-a3fc-cfc21d77b90a",
        "instructions": "You are a helpful assistant.",
        "max_output_tokens": 32768,
        "model": "DeepSeek-V4-Flash",
        "object": "response",
        "output": [

        ],
        "service_tier": "auto",
        "status": "in_progress",
        "store": true,
        "thinking": {
            "type": "enabled"
        }
    },
    "sequence_number": 0,
    "type": "response.created"
}

event: response.in_progress
data: {
    "response": {
        "caching": {
            "type": "disabled"
        },
        "created_at": 1790161072,
        "expire_at": 1790420271,
        "id": "cds_e6816797-3735-4062-a3fc-cfc21d77b90a",
        "instructions": "You are a helpful assistant.",
        "max_output_tokens": 32768,
        "model": "DeepSeek-V4-Flash",
        "object": "response",
        "output": [

        ],
        "service_tier": "auto",
        "status": "in_progress",
        "store": true,
        "thinking": {
            "type": "enabled"
        }
    },
    "sequence_number": 1,
    "type": "response.in_progress"
}

event: response.output_item.added
data: {
    "item": {
        "id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
        "status": "in_progress",
        "summary": [

        ],
        "type": "reasoning"
    },
    "output_index": 0,
    "sequence_number": 2,
    "type": "response.output_item.added"
}

event: response.reasoning_summary_part.added
data: {
    "item_id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
    "output_index": 0,
    "part": {
        "type": "summary_text"
    },
    "sequence_number": 3,
    "summary_index": 0,
    "type": "response.reasoning_summary_part.added"
}

event: response.reasoning_summary_text.delta
data: {
    "delta": "The",
    "item_id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
    "output_index": 0,
    "sequence_number": 4,
    "summary_index": 0,
    "type": "response.reasoning_summary_text.delta"
}

event: response.reasoning_summary_text.delta
data: {"delta":" user","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":5,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" just","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":6,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" said","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":7,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" hello","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":8,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":".","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":9,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" I","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":10,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" should","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":11,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" respond","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":12,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" with","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":13,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" a","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":14,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" friendly","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":15,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" greeting","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":16,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":".","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":17,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" Keep","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":18,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" it","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":19,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" simple","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":20,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" and","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":21,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":" open","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":22,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":"-ended","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":23,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.delta
data: {"delta":".","item_id":"rs_02179016107282200000000000000000000ffffac191d0cc02b1f","output_index":0,"sequence_number":24,"summary_index":0,"type":"response.reasoning_summary_text.delta"}

event: response.reasoning_summary_text.done
data: {
    "item_id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
    "output_index": 0,
    "sequence_number": 25,
    "summary_index": 0,
    "text": "The user just said hello. I should respond with a friendly greeting. Keep it simple and open-ended.",
    "type": "response.reasoning_summary_text.done"
}

event: response.reasoning_summary_part.done
data: {
    "item_id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
    "output_index": 0,
    "part": {
        "text": "The user just said hello. I should respond with a friendly greeting. Keep it simple and open-ended.",
        "type": "summary_text"
    },
    "sequence_number": 26,
    "summary_index": 0,
    "type": "response.reasoning_summary_part.done"
}

event: response.output_item.done
data: {
    "item": {
        "id": "rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
        "status": "completed",
        "summary": [
            {
                "text": "The user just said hello. I should respond with a friendly greeting. Keep it simple and open-ended.",
                "type": "summary_text"
            }
        ],
        "type": "reasoning"
    },
    "output_index": 0,
    "sequence_number": 27,
    "type": "response.output_item.done"
}

event: response.output_item.added
data: {"item":{"content":[],"id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","role":"assistant","status":"in_progress","type":"message"},"output_index":1,"sequence_number":28,"type":"response.output_item.added"}

event: response.content_part.added
data: {"content_index":0,"item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"part":{"text":"","type":"output_text"},"sequence_number":29,"type":"response.content_part.added"}

event: response.output_text.delta
data: {"content_index":0,"delta":"Hello","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":30,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":"!","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":31,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" How","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":32,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" can","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":33,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" I","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":34,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" help","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":35,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" you","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":36,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":" today","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":37,"type":"response.output_text.delta"}

event: response.output_text.delta
data: {"content_index":0,"delta":"?","item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":38,"type":"response.output_text.delta"}

event: response.output_text.done
data: {"content_index":0,"item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"sequence_number":39,"text":"Hello! How can I help you today?","type":"response.output_text.done"}

event: response.content_part.done
data: {"content_index":0,"item_id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","output_index":1,"part":{"text":"Hello! How can I help you today?","type":"output_text"},"sequence_number":40,"type":"response.content_part.done"}

event: response.output_item.done
data: {"item":{"content":[{"text":"Hello! How can I help you today?","type":"output_text"}],"id":"msg_02179016107301300000000000000000000ffffac191d0cc8af37","role":"assistant","status":"completed","type":"message"},"output_index":1,"sequence_number":41,"type":"response.output_item.done"}

event: response.completed
data: {
    "response": {
        "caching": {
            "type": "disabled"
        },
        "created_at": 1790161072,
        "expire_at": 1790420271,
        "id": "cds_e6816797-3735-4062-a3fc-cfc21d77b90a",
        "instructions": "You are a helpful assistant.",
        "max_output_tokens": 32768,
        "metrics": {
            "input_token_count": 91,
            "output_token_count": 31,
            "predict_time": 1.933146624
        },
        "model": "DeepSeek-V4-Flash",
        "object": "response",
        "output": [
            {
                "id": "Vendor3-rs_02179016107282200000000000000000000ffffac191d0cc02b1f",
                "status": "completed",
                "summary": [
                    {
                        "text": "The user just said hello. I should respond with a friendly greeting. Keep it simple and open-ended.",
                        "type": "summary_text"
                    }
                ],
                "type": "reasoning"
            },
            {
                "content": [
                    {
                        "text": "Hello! How can I help you today?",
                        "type": "output_text"
                    }
                ],
                "id": "Vendor3-msg_02179016107301300000000000000000000ffffac191d0cc8af37",
                "role": "assistant",
                "status": "completed",
                "type": "message"
            }
        ],
        "service_tier": "default",
        "status": "completed",
        "store": true,
        "thinking": {
            "type": "enabled"
        },
        "usage": {
            "input_tokens": 91,
            "input_tokens_details": {
                "cached_tokens": 0
            },
            "output_tokens": 31,
            "output_tokens_details": {
                "reasoning_tokens": 21
            },
            "total_tokens": 122
        }
    },
    "sequence_number": 42,
    "type": "response.completed"
}

$
```

总结规律:
```bash
# response.created
event: response.created

# response.in_progress
event: response.in_progress

# reasoning_summary_text
event: response.output_item.added

event: response.reasoning_summary_part.added

event: response.reasoning_summary_text.delta
event: response.reasoning_summary_text.delta
event: response.reasoning_summary_text.done

event: response.reasoning_summary_part.done

event: response.output_item.done

# output_text
event: response.output_item.added

event: response.content_part.added

event: response.output_text.delta
event: response.output_text.delta
event: response.output_text.done

event: response.content_part.done

event: response.output_item.done

# response.completed
event: response.completed

```

# 首都在线 | v1/responses | "stream": false
```bash
$ curl https://api.gpugeek.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer b0eafnpr1ayzlux1000dkynvug6rhkd4c00ev3g5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "instructions": "You are a helpful assistant.",
    "input": "Hello!",
    "stream": false
  }'
{"id":"cds_ed701ad2-998b-4453-a85e-e886a4310140","object":"response","created_at":1790161135,"status":"completed","background":false,"content_filters":null,"error":null,"incomplete_details":null,"instructions":"You are a helpful assistant.","max_output_tokens":32768,"max_tool_calls":null,"model":"DeepSeek-V4-Flash","output":[{"id":"rs_02179016113567300000000000000000000ffffac152bfda80d8f","type":"reasoning","status":"completed","summary":[{"text":"The user greeted me with \"Hello!\" in Chinese (你好). Actually, they wrote \"Hello!\" in English. The assistant responded with a friendly greeting and an offer to help. This is a simple opening exchange. I should provide a warm, helpful response. Since the user just said hello, I'll greet them back and ask what they'd like help with. No complex reasoning needed here—just a friendly, natural reply.","type":"summary_text"}]},{"id":"msg_02179016113644800000000000000000000ffffac152bfd9798cd","type":"message","status":"completed","role":"assistant","content":[{"type":"output_text","text":"Hello! How can I help you today?"}]}],"parallel_tool_calls":false,"previous_response_id":null,"prompt_cache_key":null,"prompt_cache_retention":null,"safety_identifier":null,"service_tier":"default","store":true,"temperature":0,"tool_choice":null,"tools":null,"top_logprobs":0,"top_p":0,"truncation":"","usage":{"input_tokens":91,"input_tokens_details":{"cached_tokens":0,"cache_write_tokens":0},"output_tokens":96,"output_tokens_details":{"reasoning_tokens":86},"total_tokens":187},"user":null,"metadata":null,"metrics":{"input_token_count":91,"output_token_count":96,"predict_time":2.469058268}}
$
```

# 首都在线 | /v1/chat/completions | "stream": true
```bash
$ curl https://api.gpugeek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer b0eafnpr1ayzlux1000dkynvug6rhkd4c00ev3g5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "stream": true
  }'
data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"The"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" user"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" just"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" said"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" \""}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"Hello"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"!\""}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" and"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" the"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" assistant"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" greeted"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" back"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" with"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" \""}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"Hello"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"!"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" How"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" can"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" I"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" assist"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" you"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" today"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"?\""}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" This"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" is"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" a"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" standard"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" continuation"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"."}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" Need"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" to"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" just"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" respond"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" naturally"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" as"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" the"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" assistant"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"."}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" No"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" special"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":" formatting"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"","reasoning_content":"."}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"Hello"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"!"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" How"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" can"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" I"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" assist"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" you"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":" today"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":null,"index":0,"delta":{"role":"assistant","content":"?"}}],"usage":null,"metrics":null}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":"stop","index":0,"delta":{"role":"assistant","content":""}}],"usage":{"prompt_tokens":91,"completion_tokens":52,"total_tokens":143,"prompt_tokens_details":{"cache_creation":{}},"completion_tokens_details":{"reasoning_tokens":42}},"metrics":{"input_token_count":91,"output_token_count":52,"predict_time":2.530437353}}

data: {"id":"cds_78884d70-bbe3-4399-a6e5-aee60cbe2949","object":"chat.completion.chunk","created":1790161185,"model":"DeepSeek-V4-Flash","choices":[],"usage":{"prompt_tokens":91,"completion_tokens":52,"total_tokens":143,"prompt_tokens_details":{"cache_creation":{}},"completion_tokens_details":{"reasoning_tokens":42}},"metrics":{"input_token_count":91,"output_token_count":52,"predict_time":2.530533701}}

data: [DONE]

$
```

# 首都在线 | /v1/chat/completions | "stream": false
```bash
$ curl https://api.gpugeek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer b0eafnpr1ayzlux1000dkynvug6rhkd4c00ev3g5" \
  -d '{
    "model": "DeepSeek-V4-Flash",
    "messages": [
      {
        "role": "developer",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "stream": false
  }'
{"id":"cds_307faa5f-91be-4623-b667-199c99ba936f","object":"chat.completion","created":1790161240,"model":"DeepSeek-V4-Flash","choices":[{"finish_reason":"stop","index":0,"message":{"role":"assistant","content":"Hello! How can I help you today?","reasoning_content":"We need answer. Need infer? User says Hello! Need respond friendly."}}],"usage":{"prompt_tokens":91,"completion_tokens":25,"total_tokens":116,"prompt_tokens_details":{"cache_creation":{}},"completion_tokens_details":{"reasoning_tokens":15}},"metrics":{"input_token_count":91,"output_token_count":25,"predict_time":2.5599110510000003}}
$
```
