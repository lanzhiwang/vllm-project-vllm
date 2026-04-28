```bash
conda create --name my-vllm python=3.10 -y
conda activate my-vllm
conda deactivate

pip -v install uv -i https://pypi.tuna.tsinghua.edu.cn/simple

uv pip -v install --index https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -e ".[bench,tensorizer,fastsafetensors,runai,audio,video,flashinfer]" --torch-backend=auto

uv pip -v install --index https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple modelscope "black[jupyter]"

$ python
Python 3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
>>> import torch
>>> torch.cuda.is_available()
True
>>> torch.cuda.device_count()
8
>>>

find . -name __pycache__ -exec rm -rf {} \;

modelscope download --model facebook/opt-125m --local_dir ./

INFO 08-21 14:08:26 [launcher.py:28] Available routes are:
INFO 08-21 14:08:26 [launcher.py:36] Route: /openapi.json, Methods: GET, HEAD
INFO 08-21 14:08:26 [launcher.py:36] Route: /docs, Methods: GET, HEAD
INFO 08-21 14:08:26 [launcher.py:36] Route: /docs/oauth2-redirect, Methods: GET, HEAD
INFO 08-21 14:08:26 [launcher.py:36] Route: /redoc, Methods: GET, HEAD
INFO 08-21 14:08:26 [launcher.py:36] Route: /health, Methods: GET
INFO 08-21 14:08:26 [launcher.py:36] Route: /load, Methods: GET
INFO 08-21 14:08:26 [launcher.py:36] Route: /ping, Methods: GET, POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /tokenize, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /detokenize, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/models, Methods: GET
INFO 08-21 14:08:26 [launcher.py:36] Route: /version, Methods: GET
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/chat/completions, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/completions, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/embeddings, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /pooling, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /score, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/score, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/audio/transcriptions, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /rerank, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v1/rerank, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /v2/rerank, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /invocations, Methods: POST
INFO 08-21 14:08:26 [launcher.py:36] Route: /metrics, Methods: GET

$ curl http://localhost:8080/version -H "Authorization: Bearer 123456"
{"version":"0.8.5.post1"}

$ curl http://localhost:8080/v1/models -H "Authorization: Bearer 123456"
{
    "object": "list",
    "data": [
        {
            "id": "embed",
            "object": "model",
            "created": 1755757370,
            "owned_by": "vllm",
            "root": "/root/LLaMA-Factory/models/Jerry0/text2vec-large-chinese",
            "parent": null,
            "max_model_len": 512,
            "permission": [
                {
                    "id": "modelperm-c57d74fc740d45179d8a228dfb879b90",
                    "object": "model_permission",
                    "created": 1755757370,
                    "allow_create_engine": false,
                    "allow_sampling": true,
                    "allow_logprobs": true,
                    "allow_search_indices": false,
                    "allow_view": true,
                    "allow_fine_tuning": false,
                    "organization": "*",
                    "group": null,
                    "is_blocking": false
                }
            ]
        }
    ]
}

模型

Taichu-LLM-2B
Taichu-LLM-7B
Taichu-LLM-14B
Taichu-LLM-32B
deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B
deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
Qwen/Qwen3-0.6B
Qwen/Qwen3-1.7B
Qwen/Qwen3-4B
Qwen/Qwen3-8B
Qwen/Qwen3-32B

Jerry0/text2vec-large-chinese
maidalun/bce-embedding-base_v1
BAAI/bge-m3
Qwen/Qwen3-Embedding-0.6B
Qwen/Qwen3-Embedding-8B


modelscope download --model facebook/opt-125m --local_dir ./

vllm serve /root/LLaMA-Factory/models/Jerry0/text2vec-large-chinese \
--host 0.0.0.0 \
--port 8080 \
--block-size 16 \
--api-key 123456 \
--dtype auto \
--trust-remote-code \
--served-model-name embed \
--enable-prefix-caching \
--gpu-memory-utilization 0.9 \
--max-model-len 512 \
--task embed \
--disable-log-requests

curl -X POST http://localhost:8080/v1/embeddings -H "Authorization: Bearer 123456" -H "Content-Type: application/json" -d '{"input":["The best thing about vLLM is that it supports many different models","不可以, 早晨喝牛奶不科学"],"model":"embed"}'

find . -name __pycache__ -exec rm -rf {} \;

```


# taichu docker

```bash

# gpu
docker run -ti -d --rm --name test-embedding \
--gpus all \
-p 0.0.0.0:8090:8080 \
-e vllm__task="embedding" \
-e vllm__model="/mnt/publish-data/train_data/models/Jerry0/text2vec-large-chinese" \
-v /root/LLaMA-Factory/models/Jerry0/text2vec-large-chinese:/mnt/publish-data/train_data/models/Jerry0/text2vec-large-chinese \
tck-xinan-registry.cn-chengdu.cr.aliyuncs.com/wair/vllm-taichu:0.9.2.taichu1

curl -X POST http://localhost:8090/v1/embeddings -H "Content-Type: application/json" -d '{"input":["The best thing about vLLM is that it supports many different models","不可以, 早晨喝牛奶不科学"],"model":"taichu"}'

# npu
docker run -it -d -u root --name test-embedding \
--ipc=host \
--device=/dev/davinci2 \
--device=/dev/davinci3 \
--device=/dev/davinci4 \
--device=/dev/davinci5 \
--device=/dev/davinci6 \
--device=/dev/davinci7 \
--device=/dev/davinci_manager \
--device=/dev/devmm_svm \
--device=/dev/hisi_hdc \
-v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
-v /usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/common \
-v /usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/driver \
-v /etc/ascend_install.info:/etc/ascend_install.info \
-v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
-v /usr/local/Ascend/driver/tools:/usr/local/Ascend/driver/tools \
-v /data:/data \
-p 0.0.0.0:8090:8080 \
-e vllm__task="embedding" \
-e vllm__model="/data/alluxio/publish-data/train_data/text2vec-large-chinese" \
tck-xinan-registry.cn-chengdu.cr.aliyuncs.com/wair/vllm-ascend-taichu:0.9.2rc1.taichu1

curl -X POST http://localhost:8090/v1/embeddings -H "Content-Type: application/json" -d '{"input":["The best thing about vLLM is that it supports many different models","不可以, 早晨喝牛奶不科学"],"model":"taichu"}'

```

