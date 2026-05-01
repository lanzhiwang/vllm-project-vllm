# Using Docker

* https://docs.vllm.ai/en/v0.20.0/deployment/docker

## Pre-built images

[NVIDIA CUDA](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#nvidia-cuda)[AMD ROCm](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#amd-rocm)[Intel XPU  英特尔 XPU](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#intel-xpu)

Currently, we release prebuilt XPU images at docker [hub](https://hub.docker.com/r/intel/vllm/tags) based on vLLM released version. For more information, please refer release [note](https://github.com/intel/ai-containers/blob/main/vllm). 
目前, 我们基于 vLLM 的发布版本, 在 Docker [Hub](https://hub.docker.com/r/intel/vllm/tags) 上发布了预构建的 XPU 镜像. 更多信息, 请参阅发布[说明](https://github.com/intel/ai-containers/blob/main/vllm). 

## Build image from source  从源构建镜像[¶](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#build-image-from-source "Permanent link")

[NVIDIA CUDA](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#nvidia-cuda_1)[AMD ROCm](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#amd-rocm_1)[Intel XPU  英特尔 XPU](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#intel-xpu_1)

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-1)docker build -f docker/Dockerfile.xpu -t vllm-xpu-env --shm-size=4g. [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-2)docker run -it \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-3) --rm \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-4) --network=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-5) --device /dev/dri:/dev/dri \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-6) -v /dev/dri/by-path:/dev/dri/by-path \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-7) --ipc=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-8) --privileged \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-18-9) vllm-xpu-env`

February 6, 2026  2026年2月6日