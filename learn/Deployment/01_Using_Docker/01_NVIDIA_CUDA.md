# Using Docker

* https://docs.vllm.ai/en/v0.20.0/deployment/docker

## Pre-built images

### NVIDIA CUDA

vLLM offers an official Docker image for deployment. The image can be used to run OpenAI compatible server and is available on Docker Hub as [vllm/vllm-openai](https://hub.docker.com/r/vllm/vllm-openai/tags).
vLLM 提供官方的 Docker 镜像用于部署. 该镜像可用于运行与 OpenAI 兼容的服务器, 可在 Docker Hub 上找到, 镜像名为 vllm/vllm-openai.

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --env "HF_TOKEN=$HF_TOKEN" \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen3-0.6B
```

This image can also be used with other container engines such as [Podman](https://podman.io/).
该镜像也可以与其他容器引擎(例如 Podman) 一起使用.

```bash
podman run --device nvidia.com/gpu=all \
-v ~/.cache/huggingface:/root/.cache/huggingface \
--env "HF_TOKEN=$HF_TOKEN" \
-p 8000:8000 \
--ipc=host \
docker.io/vllm/vllm-openai:latest \
--model Qwen/Qwen3-0.6B
```

You can add any other [engine-args](https://docs.vllm.ai/en/latest/configuration/engine_args/) you need after the image tag (`vllm/vllm-openai:latest`).
您可以在图像标签( `vllm/vllm-openai:latest` )之后添加您需要的任何其他引擎参数.

> Note
> You can either use the `ipc=host` flag or `--shm-size` flag to allow the container to access the host's shared memory. vLLM uses PyTorch, which uses shared memory to share data between processes under the hood, particularly for tensor parallel inference.
> 您可以使用 `ipc=host` 标志或 `--shm-size` 标志来允许容器访问主机的共享内存. vLLM 使用 PyTorch, 而 PyTorch 在底层使用共享内存来在进程间共享数据, 尤其是在进行张量并行推理时.
>

> Note
> Optional dependencies are not included in order to avoid licensing issues (e.g. [Issue#8030](https://github.com/vllm-project/vllm/issues/8030)).
> 为了避免许可问题, 未包含可选依赖项(例如).
> If you need to use those dependencies (having accepted the license terms), create a custom Dockerfile on top of the base image with an extra layer that installs them:
> 如果您需要使用这些依赖项(并已接受许可条款), 请在基础镜像之上创建一个自定义 Dockerfile, 并添加一个额外的层来安装它们:
>

```dockerfile
FROM vllm/vllm-openai:v0.11.0

# e.g. install the `audio` optional dependencies
# NOTE: Make sure the version of vLLM matches the base image!
RUN uv pip install --system vllm[audio]==0.11.0
```

> Tip
> Some new models may only be available on the main branch of [HF Transformers](https://github.com/huggingface/transformers).
> 某些新型号可能仅在 HF Transformers 的主分支上提供.
> To use the development version of `transformers`, create a custom Dockerfile on top of the base image with an extra layer that installs their code from source:
> 要使用 `transformers` 的开发版本, 请在基础镜像之上创建一个自定义 Dockerfile, 并添加一个额外的层, 该层会从源代码安装其代码:
>

```dockerfile
FROM vllm/vllm-openai:latest

RUN uv pip install --system git+https://github.com/huggingface/transformers.git
```

#### Running on Systems with Older CUDA Drivers
在安装了旧版 CUDA 驱动程序的系统上运行

vLLM's Docker image comes with [CUDA compatibility libraries](https://docs.nvidia.com/deploy/cuda-compatibility/index.html) pre-installed. This allows you to run vLLM on systems with NVIDIA drivers that are older than the CUDA Toolkit version used in the image, but only supports select professional and datacenter NVIDIA GPUs.
vLLM 的 Docker 镜像预装了 CUDA 兼容库. 这使得您可以在 NVIDIA 驱动程序版本低于镜像中所用 CUDA 工具包版本的系统上运行 vLLM, 但仅支持部分专业级和数据中心级 NVIDIA GPU.

To enable this feature, set the `VLLM_ENABLE_CUDA_COMPATIBILITY` environment variable to `1` or `true` when running the container:
要启用此功能, 请在运行容器时将 `VLLM_ENABLE_CUDA_COMPATIBILITY` 环境变量设置为 `1` 或 `true`:

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --env "HF_TOKEN=<secret>" \
    --env "VLLM_ENABLE_CUDA_COMPATIBILITY=1" \
    vllm/vllm-openai <args...>
```

This will automatically configure `LD_LIBRARY_PATH` to point to the compatibility libraries before loading PyTorch and other dependencies.
这样会在加载 PyTorch 和其他依赖项之前, 自动配置 `LD_LIBRARY_PATH` 指向兼容库.

## Build image from source

### NVIDIA CUDA

You can build and run vLLM from source via the provided [docker/Dockerfile](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile). To build vLLM:
您可以使用提供的 Docker/Dockerfile 从源代码构建和运行 vLLM. 构建 vLLM 的步骤如下:

```bash
# optionally specifies: --build-arg max_jobs=8 --build-arg nvcc_threads=2
DOCKER_BUILDKIT=1 docker build . \
    --target vllm-openai \
    --tag vllm/vllm-openai \
    --file docker/Dockerfile
```

> Note
> By default vLLM will build for all GPU types for widest distribution. If you are just building for the current GPU type the machine is running on, you can add the argument `--build-arg torch_cuda_arch_list=""` for vLLM to find the current GPU type and build for that.
> 默认情况下, vLLM 会构建支持所有 GPU 类型的版本, 以实现最广泛的覆盖. 如果您只想构建支持当前机器所运行 GPU 类型的版本, 可以添加参数 `--build-arg torch_cuda_arch_list=""` , 以便 vLLM 查找当前 GPU 类型并进行相应的构建.
>
> If you are using Podman instead of Docker, you might need to disable SELinux labeling by adding `--security-opt label=disable` when running `podman build` command to avoid certain [existing issues](https://github.com/containers/buildah/discussions/4184).
> 如果您使用的是 Podman 而不是 Docker, 则可能需要在运行 `podman build` 命令时添加 `--security-opt label=disable` 来禁用 SELinux 标签, 以避免某些现有问题.
>

> Note
> If you have not changed any C++ or CUDA kernel code, you can use precompiled wheels to significantly reduce Docker build time.
> 如果您没有更改任何 C++ 或 CUDA 内核代码, 则可以使用预编译的 wheel 文件来显著减少 Docker 构建时间.
> - **Enable the feature** by adding the build argument: `--build-arg VLLM_USE_PRECOMPILED="1"`.
>   通过添加构建参数来启用该功能:  `--build-arg VLLM_USE_PRECOMPILED="1"`.
> - **How it works**: By default, vLLM automatically finds the correct wheels from our [Nightly Builds](https://docs.vllm.ai/en/latest/contributing/ci/nightly_builds/) by using the merge-base commit with the upstream `main` branch.
>   工作原理: 默认情况下, vLLM 通过使用与上游 `main` 分支的 merge-base 提交, 自动从我们的 [Nightly Builds](https://docs.vllm.ai/en/latest/contributing/ci/nightly_builds/) 中找到正确的 wheel 文件.
> - **Override commit**: To use wheels from a specific commit, provide the `--build-arg VLLM_PRECOMPILED_WHEEL_COMMIT=<commit_hash>` argument.
>   覆盖提交: 要使用特定提交中的 wheel, 请提供 `--build-arg VLLM_PRECOMPILED_WHEEL_COMMIT=<commit_hash>` 参数.
>
> For a detailed explanation, refer to the documentation on 'Set up using Python-only build (without compilation)' part in [Build wheel from source](https://docs.vllm.ai/en/latest/contributing/ci/nightly_builds/#precompiled-wheels-usage), these args are similar.
> 有关详细解释, 请参阅"从源代码构建 wheel" 中的"使用仅 Python 构建(无需编译)进行设置"部分文档, 这些参数类似.
>

#### Building vLLM's Docker Image from Source for Arm64/aarch64
从源代码构建适用于 Arm64/aarch64 的 vLLM Docker 镜像

A docker container can be built for aarch64 systems such as the Nvidia Grace-Hopper and Grace-Blackwell. Using the flag `--platform "linux/arm64"` will build for arm64.
可以为诸如 Nvidia Grace-Hopper 和 Grace-Blackwell 之类的 aarch64 系统构建 Docker 容器. 使用 `--platform "linux/arm64"` 标志将构建 arm64 版本的容器.

> Note
> Multiple modules must be compiled, so this process can take a while. Recommend using `--build-arg max_jobs=` & `--build-arg nvcc_threads=` flags to speed up build process. However, ensure your `max_jobs` is substantially larger than `nvcc_threads` to get the most benefits. Keep an eye on memory usage with parallel jobs as it can be substantial (see example below).
> 由于需要编译多个模块, 因此这个过程可能需要一些时间. 建议使用 `--build-arg max_jobs=` 和 `--build-arg nvcc_threads=` 参数来加快构建速度. 但是, 为了获得最佳效果, 请确保 `max_jobs` 值远大于 `nvcc_threads` 值. 并行作业时, 请密切关注内存使用情况, 因为内存使用量可能会很大(参见以下示例).

```bash
# Example of building on Nvidia GH200 server. (Memory usage: ~15GB, Build time: ~1475s / ~25 min, Image size: 6.93GB)
DOCKER_BUILDKIT=1 docker build . \
--file docker/Dockerfile \
--target vllm-openai \
--platform "linux/arm64" \
-t vllm/vllm-gh200-openai:latest \
--build-arg max_jobs=66 \
--build-arg nvcc_threads=2 \
--build-arg torch_cuda_arch_list="9.0 10.0+PTX" \
--build-arg RUN_WHEEL_CHECK=false
```

For (G)B300, we recommend using CUDA 13, as shown in the following command.
对于 (G)B300, 我们建议使用 CUDA 13, 如下面的命令所示.

```bash
DOCKER_BUILDKIT=1 docker build \
--build-arg CUDA_VERSION=13.0.1 \
--build-arg BUILD_BASE_IMAGE=nvidia/cuda:13.0.1-devel-ubuntu22.04 \
--build-arg max_jobs=256 \
--build-arg nvcc_threads=2 \
--build-arg RUN_WHEEL_CHECK=false \
--build-arg torch_cuda_arch_list='9.0 10.0+PTX' \
--platform "linux/arm64" \
--tag vllm/vllm-gb300-openai:latest \
--target vllm-openai \
-f docker/Dockerfile \
.
```

> Note
> If you are building the `linux/arm64` image on a non-ARM host (e.g., an x86_64 machine), you need to ensure your system is set up for cross-compilation using QEMU. This allows your host machine to emulate ARM64 execution.
> 如果您在非 ARM 主机(例如 x86_64 机器)上构建 `linux/arm64` 镜像, 则需要确保您的系统已配置为使用 QEMU 进行交叉编译. 这样, 您的主机就可以模拟 ARM64 的执行环境.
>
> Run the following command on your host machine to register QEMU user static handlers:
> 在主机上运行以下命令以注册 QEMU 用户静态处理程序:
>

```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

> After setting up QEMU, you can use the `--platform "linux/arm64"` flag in your `docker build` command.
> 设置好 QEMU 后, 您可以在 `docker build` 命令中使用 `--platform "linux/arm64"` 标志.
>

#### Use the custom-built vLLM Docker image
使用自定义构建的 vLLM Docker 镜像

To run vLLM with the custom-built Docker image:
使用自定义构建的 Docker 镜像运行 vLLM:

```bash
docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --env "HF_TOKEN=<secret>" \
    vllm/vllm-openai <args...>
```

The argument `vllm/vllm-openai` specifies the image to run, and should be replaced with the name of the custom-built image (the `-t` tag from the build command).
参数 `vllm/vllm-openai` 指定要运行的镜像, 应替换为自定义构建镜像的名称(来自构建命令的 `-t` 标签).

> Note
> **For version 0.4.1 and 0.4.2 only** - the vLLM docker images under these versions are supposed to be run under the root user since a library under the root user's home directory, i.e. `/root/.config/vllm/nccl/cu12/libnccl.so.2.18.1` is required to be loaded during runtime. If you are running the container under a different user, you may need to first change the permissions of the library (and all the parent directories) to allow the user to access it, then run vLLM with environment variable `VLLM_NCCL_SO_PATH=/root/.config/vllm/nccl/cu12/libnccl.so.2.18.1`.
> 仅适用于 0.4.1 和 0.4.2 版本 - 这些版本的 vLLM Docker 镜像应该以 root 用户身份运行, 因为运行时需要加载 root 用户主目录下的库文件, 即 `/root/.config/vllm/nccl/cu12/libnccl.so.2.18.1`. 如果您以其他用户身份运行容器, 则可能需要先更改该库文件(及其所有父目录)的权限, 以允许该用户访问它, 然后使用环境变量 `VLLM_NCCL_SO_PATH=/root/.config/vllm/nccl/cu12/libnccl.so.2.18.1` 运行 vLLM.

2026年2月6日
