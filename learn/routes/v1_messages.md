
```bash
$ curl -s http://172.16.21.3:8090/openapi.json | jq '.components.schemas.AnthropicMessagesRequest.properties | keys'
[
  "chat_template_kwargs",
  "kv_transfer_params",
  "max_tokens",
  "messages",
  "metadata",
  "model",
  "stop_sequences",
  "stream",
  "system",
  "temperature",
  "tool_choice",
  "tools",
  "top_k",
  "top_p"
]
$
```
