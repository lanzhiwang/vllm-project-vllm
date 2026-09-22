# 基础镜像
ARG BASE_IMAGE=vllm/vllm-openai:v0.22.0-cu129-ubuntu2404
FROM ${BASE_IMAGE}

LABEL maintainer="vLLM Chaos Engineering Team"
LABEL description="vLLM OpenAI server with Chaos Fault Injection Middleware and Proxy"

# 确保 python 输出无缓冲, 保证实时日志打印
ENV PYTHONUNBUFFERED=1
ENV VLLM_LOGGING_LEVEL=DEBUG
ENV VLLM_DEBUG_LOG_API_SERVER_RESPONSE=TRUE
ENV TORCH_SHOW_CPP_STACKTRACES=1

# 将中间件目录加入 PYTHONPATH, 便于 vLLM 动态加载
ENV PYTHONPATH="/app/chaos:${PYTHONPATH}"

# 安装代理所需的依赖 (aiohttp)
# RUN pip install --no-cache-dir aiohttp

WORKDIR /app/chaos

# 拷贝组件
COPY chaos_middleware.py /app/chaos/chaos_middleware.py
COPY chaos_proxy.py /app/chaos/chaos_proxy.py
COPY entrypoint.sh /app/chaos/entrypoint.sh

# 授权执行权限
RUN chmod +x /app/chaos/entrypoint.sh

# 暴露端口: 8000 (vLLM 原生/中间件), 8001 (Chaos Proxy 网络截断)
EXPOSE 8000 8001

ENTRYPOINT ["/app/chaos/entrypoint.sh"]
