#!/bin/bash

set -ex

export HOST_MODEL_PATH="/data/model/gemma-4-31B-it"
export CONTAINER_MODEL_PATH="/model/gemma-4-31B-it"
export IMAGE_NAME="vllm-disagg-proxy:latest"

# 自动获取本机物理 IP
export HOST_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')
[ -z "$HOST_IP" ] && export HOST_IP=$(hostname -I | awk '{print $1}')
echo "===> 检测到本机物理 IP: ${HOST_IP} <==="

# 清理旧容器
docker rm -f vllm-proxy vllm-decode vllm-prefill 2>/dev/null || true

# 1. 启动 Prefill
echo "启动 vllm-prefill..."
docker run -d --name vllm-prefill --restart unless-stopped --ipc=host --net=host --gpus '"device=0,1"' \
    -e MODEL_NAME="${CONTAINER_MODEL_PATH}" -e CUDA_VISIBLE_DEVICES=0 \
    -e VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=1 -e VLLM_LOGGING_LEVEL=INFO \
    -e NCCL_DEBUG=INFO -e NCCL_DEBUG_SUBSYS=INIT,P2P,ENV -e NCCL_IB_DISABLE=1 \
    -e NCCL_P2P_DISABLE=0 -e NCCL_SHM_DISABLE=0 -e CUDA_DEVICE_ORDER=PCI_BUS_ID -e NCCL_NET_GDR_LEVEL=0 \
    -v "${HOST_MODEL_PATH}:${CONTAINER_MODEL_PATH}:ro" --entrypoint /bin/bash "${IMAGE_NAME}" \
    -c "vllm serve \"\$MODEL_NAME\" --trust-remote-code --use-tqdm-on-load --host 0.0.0.0 --port 8100 --gpu-memory-utilization 0.88 --max-model-len 2048 --max-num-batched-tokens 8192 --enable-log-requests --kv-transfer-config '{\"kv_connector\": \"P2pNcclConnector\", \"kv_role\": \"kv_producer\", \"kv_rank\": 0, \"kv_parallel_size\": 2, \"kv_ip\": \"${HOST_IP}\", \"kv_port\": 14579, \"kv_buffer_size\": \"2e9\", \"kv_connector_extra_config\": {\"send_type\": \"PUT_ASYNC\", \"nccl_num_channels\": \"8\"}}'"

# 2. 启动 Decode
echo "启动 vllm-decode..."
docker run -d --name vllm-decode --restart unless-stopped --ipc=host --net=host --gpus '"device=0,1"' \
    -e MODEL_NAME="${CONTAINER_MODEL_PATH}" -e CUDA_VISIBLE_DEVICES=1 \
    -e VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=1 -e VLLM_LOGGING_LEVEL=INFO \
    -e NCCL_DEBUG=INFO -e NCCL_DEBUG_SUBSYS=INIT,P2P,ENV -e NCCL_IB_DISABLE=1 \
    -e NCCL_P2P_DISABLE=0 -e NCCL_SHM_DISABLE=0 -e CUDA_DEVICE_ORDER=PCI_BUS_ID -e NCCL_NET_GDR_LEVEL=0 \
    -v "${HOST_MODEL_PATH}:${CONTAINER_MODEL_PATH}:ro" --entrypoint /bin/bash "${IMAGE_NAME}" \
    -c "vllm serve \"\$MODEL_NAME\" --trust-remote-code --use-tqdm-on-load --host 0.0.0.0 --port 8200 --gpu-memory-utilization 0.88 --max-model-len 2048 --max-num-batched-tokens 8192 --enable-log-requests --kv-transfer-config '{\"kv_connector\": \"P2pNcclConnector\", \"kv_role\": \"kv_consumer\", \"kv_rank\": 1, \"kv_parallel_size\": 2, \"kv_ip\": \"${HOST_IP}\", \"kv_port\": 14580, \"kv_buffer_size\": \"4e9\", \"kv_connector_extra_config\": {\"send_type\": \"PUT_ASYNC\", \"nccl_num_channels\": \"8\"}}'"

# 3. 健康检查探活
echo "等待引擎加载权重..."
until curl -s -f http://127.0.0.1:8100/v1/models >/dev/null 2>&1; do sleep 5; done
echo "✅ Prefill 已就绪!"
until curl -s -f http://127.0.0.1:8200/v1/models >/dev/null 2>&1; do sleep 5; done
echo "✅ Decode 已就绪!"

# 4. 启动 Proxy
echo "启动 vllm-proxy..."
docker run -d --name vllm-proxy --restart unless-stopped --net=host --entrypoint python3 "${IMAGE_NAME}" \
    /app/disagg_prefill_proxy_server.py --host 0.0.0.0 --port 8000 --prefill-url http://127.0.0.1:8100 --decode-url http://127.0.0.1:8200 --kv-host "${HOST_IP}" --prefill-kv-port 14579 --decode-kv-port 14580

echo "🎉 集群已全部就绪! 统一服务端口: http://localhost:8000"
