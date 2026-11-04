#!/bin/bash

# ./start.sh --build

# -e (errexit): 脚本中任何命令如果以非零状态码退出, 整个脚本立即终止, 防止雪崩与错误累积.
set -e
# -x (xtrace): 执行命令前把该行展开后的完整参数打印到标准输出, 生产环境容器排错必备.
set -x

# 1. 采用与 vLLM 底层相同的逻辑, 精准获取走默认网关的主网卡 IP
export HOST_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')

# 兜底: 如果是在无网关环境, 回退取第一个物理网卡 IP
if [ -z "$HOST_IP" ]; then
    export HOST_IP=$(hostname -I | awk '{print $1}')
fi

echo "===> [Auto-Detect] 当前宿主机物理 IP: ${HOST_IP} <==="

# 2. 拉起 Docker Compose (Compose 会自动把这个 HOST_IP 注入到所有容器中)
docker compose up -d "$@"
