FROM vllm/vllm-openai:v0.22.0-cu129-ubuntu2404

# 切换为 root 安装额外依赖
USER root

# 安装代理所需异步网络库
RUN pip install --no-cache-dir quart

WORKDIR /app

# 拷贝启动脚本与代理服务器
COPY disagg_prefill_proxy_server.py /app/
COPY entrypoint.sh /app/

RUN chmod +x /app/entrypoint.sh

# 暴露 Proxy 服务端口及各内部通信端口
EXPOSE 8000 8100 8200 14579 14580

ENTRYPOINT ["/app/entrypoint.sh"]
