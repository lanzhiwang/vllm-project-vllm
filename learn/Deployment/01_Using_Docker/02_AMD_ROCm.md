# Using Docker

* https://docs.vllm.ai/en/v0.20.0/deployment/docker

## Pre-built images

[NVIDIA CUDA](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#nvidia-cuda)[AMD ROCm](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#amd-rocm)[Intel XPU  英特尔 XPU](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#intel-xpu)

vLLM offers official Docker images for deployment. The images can be used to run OpenAI compatible server and are available on Docker Hub as [vllm/vllm-openai-rocm](https://hub.docker.com/r/vllm/vllm-openai-rocm/tags). 
vLLM 提供官方的 Docker 镜像用于部署. 这些镜像可用于运行与 OpenAI 兼容的服务器, 并可在 Docker Hub 上找到, 文件名为 [vllm/vllm-openai-rocm](https://hub.docker.com/r/vllm/vllm-openai-rocm/tags). 

- `vllm/vllm-openai-rocm:latest` — stable release  
  `vllm/vllm-openai-rocm:latest` — 稳定版本
- `vllm/vllm-openai-rocm:nightly` — preview build from the latest development branch, use this if you want the latest features and fixes  
  `vllm/vllm-openai-rocm:nightly` — 来自最新开发分支的预览版本, 如果您想要最新的功能和修复, 请使用此版本. 

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-1)docker run --rm \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-2) --group-add=video \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-3) --cap-add=SYS_PTRACE \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-4) --security-opt seccomp=unconfined \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-5) --device /dev/kfd \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-6) --device /dev/dri \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-7) -v ~/.cache/huggingface:/root/.cache/huggingface \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-8) --env "HF_TOKEN=$HF_TOKEN" \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-9) -p 8000:8000 \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-10) --ipc=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-11) vllm/vllm-openai-rocm:<tag> \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-5-12) --model Qwen/Qwen3-0.6B`

To use the docker image as base for development, you can launch it in interactive session through overriding the entrypoint. 
要使用 Docker 镜像作为开发基础, 您可以通过覆盖入口点在交互式会话中启动它. 

Commands  命令

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-1)docker run --rm -it \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-2) --group-add=video \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-3) --cap-add=SYS_PTRACE \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-4) --security-opt seccomp=unconfined \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-5) --device /dev/kfd \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-6) --device /dev/dri \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-7) -v ~/.cache/huggingface:/root/.cache/huggingface \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-8) --env "HF_TOKEN=$HF_TOKEN" \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-9) --network=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-10) --ipc=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-11) --entrypoint /bin/bash \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-6-12) vllm/vllm-openai-rocm:<tag>`

#### Use AMD's Docker Images (Deprecated)

使用 AMD 的 Docker 镜像(已弃用)[¶](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#use-amds-docker-images-deprecated "Permanent link")

Deprecated  已弃用

AMD's Docker images (`rocm/vllm` and `rocm/vllm-dev`) are deprecated in favor of the official vLLM Docker images above (`vllm/vllm-openai-rocm`). Please migrate to the official images. 
AMD 的 Docker 镜像( `rocm/vllm` 和 `rocm/vllm-dev` )已被弃用, 请使用上述官方 vLLM Docker 镜像( `vllm/vllm-openai-rocm` ). 请迁移到官方镜像. 

Prior to January 20th, 2026 when the official docker images became available on [upstream vLLM docker hub](https://hub.docker.com/v2/repositories/vllm/vllm-openai-rocm/tags/), the [AMD Infinity hub for vLLM](https://hub.docker.com/r/rocm/vllm/tags) offered a prebuilt, optimized docker image designed for validating inference performance on the AMD Instinct MI300X™ accelerator. AMD also offered nightly prebuilt docker image from [Docker Hub](https://hub.docker.com/r/rocm/vllm-dev), which has vLLM and all its dependencies installed. The entrypoint of this docker image is `/bin/bash` (different from the vLLM's Official Docker Image). 
在 2026 年 1 月 20 日官方 Docker 镜像在[上游 vLLM Docker Hub](https://hub.docker.com/v2/repositories/vllm/vllm-openai-rocm/tags/) 上发布之前,  [AMD Infinity Hub for vLLM](https://hub.docker.com/r/rocm/vllm/tags) 提供了一个预构建的、经过优化的 Docker 镜像, 该镜像专为验证 AMD Instinct MI300X™ 加速器上的推理性能而设计. AMD 还通过 [Docker Hub](https://hub.docker.com/r/rocm/vllm-dev) 提供了一个每日更新的预构建 Docker 镜像, 其中已安装了 vLLM 及其所有依赖项. 该 Docker 镜像的入口点为 `/bin/bash` (与 vLLM 官方 Docker 镜像不同). 

Tip  提示

Please check [LLM inference performance validation on AMD Instinct MI300X](https://rocm.docs.amd.com/en/latest/how-to/performance-validation/mi300x/vllm-benchmark.html) for instructions on how to use this prebuilt docker image. 
请查阅 [AMD Instinct MI300X 上的 LLM 推理性能验证](https://rocm.docs.amd.com/en/latest/how-to/performance-validation/mi300x/vllm-benchmark.html) , 了解如何使用此预构建的 docker 镜像. 

## Build image from source  从源构建镜像[¶](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#build-image-from-source "Permanent link")

[NVIDIA CUDA](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#nvidia-cuda_1)[AMD ROCm](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#amd-rocm_1)[Intel XPU  英特尔 XPU](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#intel-xpu_1)

You can build and run vLLM from source via the provided [docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm). 
您可以通过提供的 [docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm) 从源代码构建和运行 vLLM. 

(Optional) Build an image with ROCm software stack  
(可选)使用 ROCm 软件堆栈构建映像

Build a docker image from [docker/Dockerfile.rocm_base](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm_base) which setup ROCm software stack needed by the vLLM. **This step is optional as this rocm_base image is usually prebuilt and store at [Docker Hub](https://hub.docker.com/r/rocm/vllm-dev) under tag `rocm/vllm-dev:base` to speed up user experience.** If you choose to build this rocm_base image yourself, the steps are as follows.

It is important that the user kicks off the docker build using buildkit. Either the user put `DOCKER_BUILDKIT=1` as environment variable when calling docker build command, or the user needs to set up buildkit in the docker daemon configuration `/etc/docker/daemon.json` as follows and restart the daemon:

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-12-1){ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-12-2) "features": { [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-12-3) "buildkit": true [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-12-4) } [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-12-5)}`

To build vllm on ROCm 7.0 for MI200 and MI300 series, you can use the default:

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-13-1)DOCKER_BUILDKIT=1 docker build \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-13-2) -f docker/Dockerfile.rocm_base \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-13-3) -t rocm/vllm-dev:base.`

First, build a docker image from [docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm) and launch a docker container from the image. It is important that the user kicks off the docker build using buildkit. Either the user put `DOCKER_BUILDKIT=1` as environment variable when calling docker build command, or the user needs to set up buildkit in the docker daemon configuration /etc/docker/daemon.json as follows and restart the daemon:  
首先, 根据 [docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm) 构建 Docker 镜像, 并从该镜像启动 Docker 容器. 用户必须使用 BuildKit 启动 Docker 构建. 用户可以在调用 docker build 命令时将 `DOCKER_BUILDKIT=1` 设置为环境变量, 或者需要在 Docker 守护进程配置文件 /etc/docker/daemon.json 中按如下方式配置 BuildKit, 然后重启守护进程: 

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-14-1){ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-14-2) "features": { [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-14-3) "buildkit": true [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-14-4) } [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-14-5)}`

[docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm) uses ROCm 7.0 by default, but also supports ROCm 5.7, 6.0, 6.1, 6.2, 6.3, and 6.4, in older vLLM branches. It provides flexibility to customize the build of docker image using the following arguments:  
[docker/Dockerfile.rocm](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm) 默认使用 ROCm 7.0, 但也支持旧版 vLLM 分支中的 ROCm 5.7、6.0、6.1、6.2、6.3 和 6.4. 它提供了使用以下参数自定义 Docker 镜像构建的灵活性: 

- `BASE_IMAGE`: specifies the base image used when running `docker build`. The default value `rocm/vllm-dev:base` is an image published and maintained by AMD. It is being built using [docker/Dockerfile.rocm_base](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm_base)  
  `BASE_IMAGE` : 指定运行 `docker build` 时使用的基础镜像. 默认值为 `rocm/vllm-dev:base` , 该镜像由 AMD 发布和维护, 并使用 [docker/Dockerfile.rocm_base](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile.rocm_base) 构建. 
- `ARG_PYTORCH_ROCM_ARCH`: Allows to override the gfx architecture values from the base docker image  
  `ARG_PYTORCH_ROCM_ARCH` : 允许覆盖基础 Docker 镜像中的图形架构值. 

Their values can be passed in when running `docker build` with `--build-arg` options. 
运行 `docker build` 时, 可以使用 `--build-arg` 选项传入这些值. 

To build vllm on ROCm 7.0 for MI200 and MI300 series, you can use the default (which build a docker image with `vllm serve` as entrypoint):  
要在 ROCm 7.0 上为 MI200 和 MI300 系列构建 vllm, 可以使用默认方法(该方法会构建一个以 `vllm serve` 作为入口点的 docker 镜像): 

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-15-1)DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile.rocm -t vllm/vllm-openai-rocm.`

To run vLLM with the custom-built Docker image:  
使用自定义构建的 Docker 镜像运行 vLLM: 

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-1)docker run --rm \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-2) --group-add=video \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-3) --cap-add=SYS_PTRACE \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-4) --security-opt seccomp=unconfined \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-5) --device /dev/kfd \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-6) --device /dev/dri \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-7) -v ~/.cache/huggingface:/root/.cache/huggingface \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-8) --env "HF_TOKEN=$HF_TOKEN" \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-9) -p 8000:8000 \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-10) --ipc=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-16-11) vllm/vllm-openai-rocm <args...>`

The argument `vllm/vllm-openai-rocm` specifies the image to run, and should be replaced with the name of the custom-built image (the `-t` tag from the build command). 
参数 `vllm/vllm-openai-rocm` 指定要运行的镜像, 应替换为自定义构建镜像的名称(来自构建命令的 `-t` 标签). 

To use the docker image as base for development, you can launch it in interactive session through overriding the entrypoint. 
要使用 Docker 镜像作为开发基础, 您可以通过覆盖入口点在交互式会话中启动它. 

Commands  命令

`[](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-1)docker run --rm -it \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-2) --group-add=video \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-3) --cap-add=SYS_PTRACE \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-4) --security-opt seccomp=unconfined \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-5) --device /dev/kfd \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-6) --device /dev/dri \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-7) -v ~/.cache/huggingface:/root/.cache/huggingface \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-8) --env "HF_TOKEN=$HF_TOKEN" \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-9) --network=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-10) --ipc=host \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-11) --entrypoint bash \ [](https://docs.vllm.ai/en/v0.20.0/deployment/docker/#__codelineno-17-12) vllm/vllm-openai-rocm`

February 6, 2026  2026年2月6日