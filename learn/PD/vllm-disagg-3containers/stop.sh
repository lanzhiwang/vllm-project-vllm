#!/bin/bash
echo "Stopping all 3 containers..."
docker rm -f vllm-proxy-node vllm-decode-node vllm-prefill-node 2>/dev/null || true
echo "All containers removed and resources cleaned up."
