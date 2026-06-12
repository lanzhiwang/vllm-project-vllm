```bash

docker run -ti --rm \
--entrypoint /usr/bin/env \
--security-opt seccomp=unconfined \
--gpus '"device=0, 2, 5, 6"' \
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

export VLLM_SERVER_DEV_MODE=1

unset VLLM_TRACE_FUNCTION
unset CUDA_LAUNCH_BLOCKING
unset NCCL_DEBUG
unset NCCL_DEBUG_SUBSYS
unset TRITON_DEBUG
unset TRITON_PRINT_AUTOTUNING
unset TORCH_DISTRIBUTED_DEBUG

vllm serve \
/model/opt-125m \
--served-model-name opt-125m \
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
--tensor-parallel-size 1 \
--data-parallel-size 4 \
--enforce-eager

```
