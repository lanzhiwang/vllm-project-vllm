#!/bin/bash
set -e

MODEL_NAME=${HF_MODEL_NAME:-meta-llama/Meta-Llama-3.1-8B-Instruct}

echo "=========================================================="
echo " Starting 3-Container vLLM Disaggregated Serving Cluster"
echo " Model : $MODEL_NAME"
echo "=========================================================="

# 1. 确保旧容器已清理
./stop.sh 2>/dev/null || true

# 2. 构建 Proxy 镜像
if ! docker image inspect disagg-proxy:v1 >/dev/null 2>&1; then
    echo "Building disagg-proxy:v1..."
    docker build -f Dockerfile.proxy -t disagg-proxy:v1 .
fi

# 3. 启动 Prefill 容器
echo "🚀 [1/3] Launching Prefill container on GPU 0..."
docker run -d \
    --name vllm-prefill-node \
    --gpus '"device=0"' \
    --ipc=host \
    --network=host \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -e HF_TOKEN="${HF_TOKEN:-}" \
    vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 \
    --model "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8100 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config '{"kv_connector":"P2pNcclConnector","kv_role":"kv_producer","kv_rank":0,"kv_parallel_size":2,"kv_buffer_size":"1e9","kv_port":"14579","kv_connector_extra_config":{"proxy_ip":"127.0.0.1","proxy_port":"30001","http_ip":"127.0.0.1","http_port":"8100","send_type":"PUT_ASYNC"}}'

# 4. 启动 Decode 容器
echo "🚀 [2/3] Launching Decode container on GPU 1..."
docker run -d \
    --name vllm-decode-node \
    --gpus '"device=1"' \
    --ipc=host \
    --network=host \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -e HF_TOKEN="${HF_TOKEN:-}" \
    vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 \
    --model "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port 8200 \
    --max-model-len 100 \
    --gpu-memory-utilization 0.8 \
    --trust-remote-code \
    --kv-transfer-config '{"kv_connector":"P2pNcclConnector","kv_role":"kv_consumer","kv_rank":1,"kv_parallel_size":2,"kv_buffer_size":"1e10","kv_port":"14580","kv_connector_extra_config":{"proxy_ip":"127.0.0.1","proxy_port":"30001","http_ip":"127.0.0.1","http_port":"8200","send_type":"PUT_ASYNC"}}'

# 5. 等待健康检测就绪
echo "⏳ Waiting for vLLM instances to load weights..."
until curl -s -f http://127.0.0.1:8100/v1/models >/dev/null 2>&1; do
    echo "  - Waiting for Prefill (8100)..."
    sleep 3
done
echo "  ✓ Prefill node is online!"

until curl -s -f http://127.0.0.1:8200/v1/models >/dev/null 2>&1; do
    echo "  - Waiting for Decode (8200)..."
    sleep 3
done
echo "  ✓ Decode node is online!"

# 6. 启动 Proxy 容器
echo "🚀 [3/3] Launching Proxy Server container..."
docker run -d \
    --name vllm-proxy-node \
    --network=host \
    disagg-proxy:v1 \
    --host 0.0.0.0 \
    --port 8000 \
    --prefill-url http://127.0.0.1:8100 \
    --decode-url http://127.0.0.1:8200 \
    --kv-host 127.0.0.1 \
    --prefill-kv-port 14579 \
    --decode-kv-port 14580

sleep 1
echo ""
echo "🎉 Cluster initialized successfully!"
echo "➡️  Endpoint: http://localhost:8000/v1/completions"
