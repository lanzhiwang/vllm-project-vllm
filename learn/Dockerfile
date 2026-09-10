FROM vllm/vllm-openai:v0.20.0-cu129-ubuntu2404

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN set -eux && apt-get update && \
    apt-get install -y --no-install-recommends vim openssh-client openssh-server systemd && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install jupyter_core notebook jupyterhub jupyterlab && \
    mkdir -p /run/sshd && \
    chmod 0755 /run/sshd
