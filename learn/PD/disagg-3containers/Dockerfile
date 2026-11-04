FROM vllm/vllm-openai:v0.22.0-cu129-ubuntu2404

# 切换为 root 安装额外依赖
USER root

# 安装代理所需异步网络库及工具
RUN pip install --no-cache-dir --progress-bar off --ignore-installed \
    quart \
    msgpack

WORKDIR /app

COPY disagg_prefill_proxy_server.py /app/

# 暴露 Proxy 服务端口
EXPOSE 8000

CMD ["python", "/app/disagg_prefill_proxy_server.py", "--host", "0.0.0.0", "--port", "8000"]
