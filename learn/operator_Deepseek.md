* https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-V3_2.html

```bash
docker run -ti --rm \
--entrypoint /usr/bin/env \
--security-opt seccomp=unconfined \
--gpus '"device=0, 1, 2, 5"' \
-v /root/huzhi/model:/model \
-p 0.0.0.0:8090:8000 \
--name vllm-server \
vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 bash

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
/model/DeepSeek-V3.2 \
--served-model-name DeepSeek-V3.2 \
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
--tensor-parallel-size 4 \
--tokenizer-mode deepseek_v32 \
--tool-call-parser deepseek_v32 \
--enable-auto-tool-choice \
--reasoning-parser deepseek_v3

curl -X GET http://127.0.0.1:8090/version -H "Authorization: Bearer my_secret_token_123"
curl -X GET http://127.0.0.1:8090/v1/models -H "Authorization: Bearer my_secret_token_123" -H "Content-Type: application/json"

curl -X POST http://127.0.0.1:8090/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my_secret_token_123" \
    -d '{
    "model": "DeepSeek-V3.2",
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


curl -X POST http://127.0.0.1:8090/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my_secret_token_123" \
    -d '{
    "model": "DeepSeek-V3.2",
    "messages": [
        {
            "role": "user",
            "content": "帮我查一下东京现在的天气怎么样?"
        }
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "获取指定城市的实时天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "城市或地区名称, 例如 东京, 北京"
                        }
                    },
                    "required": [
                        "location"
                    ]
                }
            }
        }
    ]
}'

curl -X POST http://127.0.0.1:8090/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my_secret_token_123" \
    -d '{
    "model": "DeepSeek-V3.2",
    "messages": [
        {
            "role": "user",
            "content": "9.11 和 9.8 哪个数字更大? "
        }
    ]
}'

```
