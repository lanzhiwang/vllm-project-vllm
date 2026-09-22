#!/usr/bin/env bash
set -Eeuo pipefail
set -x

# 默认环境变量(支持外部 docker run -e 动态覆盖)
export MODEL_PATH="${MODEL_PATH:-/model/Qwen2.5-7B-Instruct}"
export SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-Qwen2.5-7B-Instruct}"
export FAIL_AFTER_CHUNKS="${FAIL_AFTER_CHUNKS:-5}"
export PROXY_PORT="${PROXY_PORT:-8001}"
export UPSTREAM_VLLM_URL="http://127.0.0.1:8000"

echo "=========================================================="
echo "          Starting vLLM Chaos Injection Cluster           "
echo "=========================================================="
echo "Model Path:         ${MODEL_PATH}"
echo "Served Model Name:  ${SERVED_MODEL_NAME}"
echo "Fail After Chunks:  ${FAIL_AFTER_CHUNKS}"
echo "=========================================================="

# 1. 启动 Chaos Proxy 后台进程
python3 /app/chaos/chaos_proxy.py &
PROXY_PID=$!
echo "[Entrypoint] Chaos Proxy started with PID: ${PROXY_PID}"

# 2. 信号处理: 捕获 docker stop (SIGTERM / SIGINT), 确保优雅停止子进程
cleanup() {
    echo -e "\n[Entrypoint] Intercepted shutdown signal. Stopping services cleanly..."
    kill -TERM "${PROXY_PID}" 2>/dev/null || true
    kill -TERM "${VLLM_PID}" 2>/dev/null || true
    wait "${VLLM_PID}" 2>/dev/null || true
    wait "${PROXY_PID}" 2>/dev/null || true
    echo "[Entrypoint] All processes stopped. Exiting."
    exit 0
}
trap cleanup SIGTERM SIGINT

# 3. 启动 vLLM Serve 引擎进程
# 如果外部有传参给容器, 直接追加在命令行末尾 ($@)
vllm serve "${MODEL_PATH}" \
    --served-model-name "${SERVED_MODEL_NAME}" \
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
    --middleware chaos_middleware.chaos_fault_injection_middleware \
    "$@" &

VLLM_PID=$!
echo "[Entrypoint] vLLM Server started with PID: ${VLLM_PID}"

# 4. 监听子进程: 任何一个进程异常崩溃, 容器整体退出
wait -n "${VLLM_PID}" "${PROXY_PID}"
cleanup
