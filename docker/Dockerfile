# The vLLM Dockerfile is used to construct vLLM image that can be directly used
# to run the OpenAI compatible server.
# vLLM Dockerfile 用于构建 vLLM 镜像, 该镜像可直接用于
# 运行兼容 OpenAI 接口的服务端.

# Please update any changes made here to
# docs/contributing/dockerfile/dockerfile.md and
# docs/assets/contributing/dockerfile-stages-dependency.png
# 请将此处所做的任何更改同步更新至:
# docs/contributing/dockerfile/dockerfile.md
# 以及 docs/assets/contributing/dockerfile-stages-dependency.png

# =============================================================================
# VERSION MANAGEMENT
# 版本管理
# =============================================================================
# ARG defaults in this Dockerfile are the source of truth for pinned versions.
# 本 Dockerfile 中的 ARG 默认值是固定版本(pinned versions)的唯一权威来源.
# docker/versions.json is auto-generated for use with docker buildx bake.
# 文件 docker/versions.json 是自动生成的, 专供 docker buildx bake 命令使用.
#
# When updating versions:
# 1. Edit the ARG defaults below
# 2. Run: python tools/generate_versions_json.py
# 更新版本时, 请执行以下步骤:
# 1. 编辑下方列出的 ARG 默认值.
# 2. 运行命令: python tools/generate_versions_json.py
#
# To query versions programmatically:
#   jq -r '.variable.CUDA_VERSION.default' docker/versions.json
# 若需以编程方式查询版本信息, 可执行:
#   jq -r '.variable.CUDA_VERSION.default' docker/versions.json
#
# To build with bake:
#   docker buildx bake -f docker/docker-bake.hcl -f docker/versions.json
# 若需使用 bake 命令进行构建, 可执行:
#   docker buildx bake -f docker/docker-bake.hcl -f docker/versions.json
# =============================================================================

ARG CUDA_VERSION=13.0.2
ARG PYTHON_VERSION=3.12
ARG UBUNTU_VERSION=22.04

# By parameterizing the base images, we allow third-party to use their own
# base images. One use case is hermetic builds with base images stored in
# private registries that use a different repository naming conventions.
# 通过将基础镜像参数化, 我们允许第三方使用其自有的基础镜像.
# 其中一个应用场景是"封闭式构建"(Hermetic Builds): 即基础镜像存储在
# 私有镜像仓库中, 且该仓库采用了不同于常规的仓库命名规范.
#
# Example:
# docker build --build-arg BUILD_BASE_IMAGE=registry.acme.org/mirror/nvidia/cuda:${CUDA_VERSION}-devel-ubuntu20.04

# Important: We build with an old version of Ubuntu to maintain broad
# compatibility with other Linux OSes. The main reason for this is that the
# glibc version is baked into the distro, and binaries built with one glibc
# version are not backwards compatible with OSes that use an earlier version.
# 重要提示: 我们特意选用旧版本的 Ubuntu 进行构建, 旨在确保与
# 其他 Linux 操作系统之间保持广泛的兼容性. 主要原因在于: glibc
# 版本是作为发行版的一部分被固化在系统中的; 而使用某一特定 glibc
# 版本编译生成的二进制文件, 无法向后兼容那些使用了更早版本 glibc 的操作系统.
ARG BUILD_BASE_IMAGE=nvidia/cuda:${CUDA_VERSION}-devel-ubuntu22.04
# Using cuda base image with minimal dependencies necessary for JIT compilation (FlashInfer, DeepGEMM, EP kernels)
ARG FINAL_BASE_IMAGE=nvidia/cuda:${CUDA_VERSION}-base-ubuntu${UBUNTU_VERSION}

# By parameterizing the Deadsnakes repository URL, we allow third-party to use
# their own mirror. When doing so, we don't benefit from the transparent
# installation of the GPG key of the PPA, as done by add-apt-repository, so we
# also need a URL for the GPG key.
# 通过将 Deadsnakes 仓库的 URL 参数化, 我们允许第三方使用其自建的镜像.
# 在这种情况下, 我们将无法享受到 `add-apt-repository` 命令所提供的 PPA GPG 密钥自动安装的便利,
# 因此我们还需要额外提供一个用于获取 GPG 密钥的 URL.
ARG DEADSNAKES_MIRROR_URL
ARG DEADSNAKES_GPGKEY_URL

# The PyPA get-pip.py script is a self contained script+zip file, that provides
# both the installer script and the pip base85-encoded zip archive. This allows
# bootstrapping pip in environment where a distribution package does not exist.
#
# By parameterizing the URL for get-pip.py installation script, we allow
# third-party to use their own copy of the script stored in a private mirror.
# We set the default value to the PyPA owned get-pip.py script.
#
# Reference: https://pip.pypa.io/en/stable/installation/#get-pip-py
# PyPA 的 get-pip.py 脚本是一个自包含的"脚本+ZIP 文件"组合体,
# 它同时提供了安装脚本以及经过 Base85 编码的 pip 归档文件.
# 这一设计使得我们能够在尚无现成分发包的环境中, 实现 pip 的引导式安装(bootstrapping).
#
# 通过将 get-pip.py 安装脚本的 URL 参数化, 我们允许
# 第三方使用其私有镜像中存储的脚本副本.
# 我们将该参数的默认值设定为 PyPA 官方维护的 get-pip.py 脚本.
#
# 参考资料: https://pip.pypa.io/en/stable/installation/#get-pip-py
ARG GET_PIP_URL="https://bootstrap.pypa.io/get-pip.py"

# PIP supports fetching the packages from custom indexes, allowing third-party
# to host the packages in private mirrors. The PIP_INDEX_URL and
# PIP_EXTRA_INDEX_URL are standard PIP environment variables to override the
# default indexes. By letting them empty by default, PIP will use its default
# indexes if the build process doesn't override the indexes.
#
# Uv uses different variables. We set them by default to the same values as
# PIP, but they can be overridden.
# PIP 支持从自定义索引源获取软件包, 从而允许第三方在私有镜像中托管软件包.
# PIP_INDEX_URL 和 PIP_EXTRA_INDEX_URL 是标准的 PIP 环境变量, 用于覆盖默认的索引源.
# 默认情况下, 我们将这些变量留空; 这样一来, 如果构建过程未显式覆盖索引源设置, PIP 就会使用其自身的默认索引源.
#
# Uv 使用的是不同的环境变量. 默认情况下, 我们将这些变量设置为与 PIP 相同的值, 但这些设置是可以被覆盖的.
ARG PIP_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG UV_INDEX_URL=${PIP_INDEX_URL}
ARG UV_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL}

# PyTorch provides its own indexes for standard and nightly builds
# PyTorch 为标准版和每夜构建版提供了其专属的索引
ARG PYTORCH_CUDA_INDEX_BASE_URL=https://download.pytorch.org/whl

# PIP supports multiple authentication schemes, including keyring
# By parameterizing the PIP_KEYRING_PROVIDER variable and setting it to
# disabled by default, we allow third-party to use keyring authentication for
# their private Python indexes, while not changing the default behavior which
# is no authentication.
#
# Reference: https://pip.pypa.io/en/stable/topics/authentication/#keyring-support
# PIP 支持多种认证方案, 其中包括 keyring.
# 通过将 PIP_KEYRING_PROVIDER 变量参数化, 并将其默认设置为"disabled"(禁用),
# 我们允许第三方为其私有 Python 索引使用 keyring 认证,
# 同时又不改变 PIP 默认的"无认证"行为.
#
# 参考资料: https://pip.pypa.io/en/stable/topics/authentication/#keyring-support
ARG PIP_KEYRING_PROVIDER=disabled
ARG UV_KEYRING_PROVIDER=${PIP_KEYRING_PROVIDER}

# Flag enables built-in KV-connector dependency libs into docker images
ARG INSTALL_KV_CONNECTORS=false

#################### BASE BUILD IMAGE ####################
# prepare basic build environment
FROM ${BUILD_BASE_IMAGE} AS base
# [base  1/10] FROM docker.io/nvidia/cuda:13.0.2-devel-ubuntu22.04@sha256:1c517d4fb96528c8999e14e6e6b16d7e2ff9ae8d194fd788d60fdc88e693e982

ARG CUDA_VERSION
ARG PYTHON_VERSION

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including build tools
RUN set -eux && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        # 开启编译器缓存, 加速重复构建
        ccache \
        software-properties-common \
        git \
        curl \
        sudo \
        python3-pip \
        # RDMA/InfiniBand 支持, 多机通信必备
        libibverbs-dev \
        # Upgrade to GCC 10 to avoid https://gcc.gnu.org/bugzilla/show_bug.cgi?id=92519
        # as it was causing spam when compiling the CUTLASS kernels
        # 明确指定 GCC 10, 避免 CUTLASS 等库在高版本 GCC 下产生的编译噪声和错误
        gcc-10 \
        g++-10 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 110 --slave /usr/bin/g++ g++ /usr/bin/g++-10 \
    # Install python dev headers if available (needed for cmake FindPython on Ubuntu 24.04
    # which ships cmake 3.28 and requires Development.SABIModule; silently skipped on
    # Ubuntu 20.04/22.04 where python3.x-dev is not available without a PPA)
    && (apt-get install -y --no-install-recommends python${PYTHON_VERSION}-dev 2>/dev/null || true) \
    && rm -rf /var/lib/apt/lists/* \
    # 使用 uv 创建虚拟环境
    # 目的: 将 Python 环境隔离在 /opt/venv, 方便后续阶段直接拷贝整个环境.
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && $HOME/.local/bin/uv venv /opt/venv --python ${PYTHON_VERSION} \
    && rm -f /usr/bin/python3 /usr/bin/python3-config /usr/bin/pip \
    && ln -s /opt/venv/bin/python3 /usr/bin/python3 \
    && ln -s /opt/venv/bin/python3-config /usr/bin/python3-config \
    && ln -s /opt/venv/bin/pip /usr/bin/pip \
    && python3 --version && python3 -m pip --version
# [base  2/10] RUN
# set -eux &&
# apt-get update -y &&
# apt-get install -y --no-install-recommends ccache software-properties-common git curl sudo python3-pip libibverbs-dev gcc-10 g++-10 &&
# update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 110 --slave /usr/bin/g++ g++ /usr/bin/g++-10 &&
# (apt-get install -y --no-install-recommends python3.12-dev 2>/dev/null || true) &&
# rm -rf /var/lib/apt/lists/* &&
# curl -LsSf https://astral.sh/uv/install.sh | sh &&
# $HOME/.local/bin/uv venv /opt/venv --python 3.12 &&
# rm -f /usr/bin/python3 /usr/bin/python3-config /usr/bin/pip &&
# ln -s /opt/venv/bin/python3 /usr/bin/python3 &&
# ln -s /opt/venv/bin/python3-config /usr/bin/python3-config &&
# ln -s /opt/venv/bin/pip /usr/bin/pip &&
# python3 --version &&
# python3 -m pip --version

# Activate virtual environment and add uv to PATH
ENV PATH="/opt/venv/bin:/root/.local/bin:$PATH"
ENV VIRTUAL_ENV="/opt/venv"

# Environment for uv
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
ENV UV_LINK_MODE=copy

# Verify GCC version
RUN gcc --version
# [base  3/10] RUN gcc --version

# Enable CUDA forward compatibility by setting '-e VLLM_ENABLE_CUDA_COMPATIBILITY=1'
# Only needed for datacenter/professional GPUs with older drivers.
# See: https://docs.nvidia.com/deploy/cuda-compatibility/
# 通过设置 '-e VLLM_ENABLE_CUDA_COMPATIBILITY=1' 启用 CUDA 前向兼容性
# 仅适用于驱动版本较旧的数据中心/专业级 GPU.
# 参阅: https://docs.nvidia.com/deploy/cuda-compatibility/
ENV VLLM_ENABLE_CUDA_COMPATIBILITY=0

# ============================================================
# SLOW-CHANGING DEPENDENCIES BELOW
# These are the expensive layers that we want to cache
# 下方为缓慢变化的依赖项
# 这些是开销较大的层, 我们希望对其进行缓存
# ============================================================

# Install PyTorch and core CUDA dependencies
# This is ~2GB and rarely changes
ARG PYTORCH_CUDA_INDEX_BASE_URL

WORKDIR /workspace
# [base  4/10] WORKDIR /workspace

# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install build and runtime dependencies, including PyTorch
# Check whether to install torch nightly instead of release for this build
COPY requirements/common.txt requirements/common.txt
# [base  5/10] COPY requirements/common.txt requirements/common.txt

COPY requirements/cuda.txt requirements/cuda.txt
# [base  6/10] COPY requirements/cuda.txt requirements/cuda.txt

COPY use_existing_torch.py use_existing_torch.py
# [base  7/10] COPY use_existing_torch.py use_existing_torch.py

COPY pyproject.toml pyproject.toml
# [base  8/10] COPY pyproject.toml pyproject.toml

# 挂载缓存目录, 加速 uv 下载
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    # 支持安装开发版 Torch, 方便研究员测试新技术
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        echo "Installing torch nightly..." \
        && uv pip install --python /opt/venv/bin/python3 torch torchaudio torchvision --pre \
        --index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') \
        && echo "Installing other requirements..." \
        && /opt/venv/bin/python3 use_existing_torch.py --prefix \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/cuda.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    else \
        uv pip install --python /opt/venv/bin/python3 -r requirements/cuda.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    fi
# [base  9/10] RUN --mount=type=cache,target=/root/.cache/uv set -eux &&
# if [ "${PYTORCH_NIGHTLY}" = "1" ]; then
#     echo "Installing torch nightly..." &&
#     uv pip install --python /opt/venv/bin/python3 torch torchaudio torchvision --pre --index-url https://download.pytorch.org/whl/nightly/cu$(echo 13.0.2 | cut -d. -f1,2 | tr -d '.') &&
#     echo "Installing other requirements..." &&
#     /opt/venv/bin/python3 use_existing_torch.py --prefix &&
#     uv pip install --python /opt/venv/bin/python3 -r requirements/cuda.txt --extra-index-url https://download.pytorch.org/whl/nightly/cu$(echo 13.0.2 | cut -d. -f1,2 | tr -d '.');
# else
#     uv pip install --python /opt/venv/bin/python3 -r requirements/cuda.txt --extra-index-url https://download.pytorch.org/whl/cu$(echo 13.0.2 | cut -d. -f1,2 | tr -d '.');
# fi

# [ 0 = 1 ]
# echo 13.0.2 | cut -d. -f1,2 | tr -d .
# uv pip install --python /opt/venv/bin/python3 -r requirements/cuda.txt --extra-index-url https://download.pytorch.org/whl/cu130

# Track PyTorch lib versions used during build and match in downstream instances.
# We do this for both nightly and release so we can strip dependencies/*.txt as needed.
# Otherwise library dependencies can upgrade/downgrade torch incorrectly.
# 追踪构建过程中使用的 PyTorch 库版本, 并在下游实例中进行匹配.
# 我们对每夜构建(Nightly)和正式发布(Release)版本均执行此操作, 以便在需要时移除 `dependencies/*.txt` 文件.
# 否则, 库依赖项可能会导致 Torch 版本发生错误的升级或降级.
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    uv pip freeze | grep -i "^torch=\|^torchvision=\|^torchaudio=" > torch_lib_versions.txt \
    && TORCH_LIB_VERSIONS=$(cat torch_lib_versions.txt | xargs) \
    && echo "Installed torch libs: ${TORCH_LIB_VERSIONS}"
# [base 10/10] RUN --mount=type=cache,target=/root/.cache/uv set -eux &&
# uv pip freeze | grep -i "^torch=\|^torchvision=\|^torchaudio=" > torch_lib_versions.txt &&
# TORCH_LIB_VERSIONS=$(cat torch_lib_versions.txt | xargs) &&
# echo "Installed torch libs: ${TORCH_LIB_VERSIONS}"
# TORCH_LIB_VERSIONS=torch==2.11.0+cu130 torchaudio==2.11.0+cu130 torchvision==0.26.0+cu130

# CUDA arch list used by torch
# Explicitly set the list to avoid issues with torch 2.2
# See https://github.com/pytorch/pytorch/pull/123243
# From versions.json: .torch.cuda_arch_list
ARG torch_cuda_arch_list='7.5 8.0 8.6 8.9 9.0 10.0 11.0 12.0+PTX'
ENV TORCH_CUDA_ARCH_LIST=${torch_cuda_arch_list}
#################### BUILD BASE IMAGE ####################

#################### CSRC BUILD IMAGE ####################
FROM base AS csrc-build
ARG TARGETPLATFORM

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL
ARG PYTORCH_CUDA_INDEX_BASE_URL

# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install build dependencies
COPY requirements/build/cuda.txt requirements/build/cuda.txt
# [csrc-build  1/13] COPY requirements/build/cuda.txt requirements/build/cuda.txt

COPY use_existing_torch.py use_existing_torch.py
# [csrc-build  2/13] COPY use_existing_torch.py use_existing_torch.py

COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt
# [csrc-build  3/13] COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
# Reference: https://github.com/astral-sh/uv/pull/1694
# 在通过 uv 安装某些依赖项时, 此超时设置(以秒为单位)是必要的, 因为安装过程极易因超时而失败.
# 参考: https://github.com/astral-sh/uv/pull/1694
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
# Use copy mode to avoid hardlink failures with Docker cache mounts
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        echo "Installing build requirements without torch..." \
        && python3 use_existing_torch.py --prefix \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt \
        && echo "Installing torch nightly..." \
        && uv pip install --python /opt/venv/bin/python3 $(cat torch_lib_versions.txt | grep -i "^torch=" | xargs) --pre \
        --index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    else \
        echo "Installing build requirements..." \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    fi
# [csrc-build  4/13] RUN --mount=type=cache,target=/root/.cache/uv set -eux &&
# if [ "0" = "1" ]; then
#     echo "Installing build requirements without torch..." &&
#     python3 use_existing_torch.py --prefix &&
#     uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt &&
#     echo "Installing torch nightly..." &&
#     uv pip install --python /opt/venv/bin/python3 $(cat torch_lib_versions.txt | grep -i "^torch=" | xargs) --pre --index-url https://download.pytorch.org/whl/nightly/cu$(echo 13.0.2 | cut -d. -f1,2 | tr -d '.');
# else
#     echo "Installing build requirements..." &&
#     uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt --extra-index-url https://download.pytorch.org/whl/cu$(echo 13.0.2 | cut -d. -f1,2 | tr -d '.');
# fi
# uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt --extra-index-url https://download.pytorch.org/whl/cu130

WORKDIR /workspace
# [csrc-build  5/13] WORKDIR /workspace

COPY pyproject.toml setup.py CMakeLists.txt ./
# [csrc-build  6/13] COPY pyproject.toml setup.py CMakeLists.txt ./

COPY cmake cmake/
# [csrc-build  7/13] COPY cmake cmake/

COPY csrc csrc/
# [csrc-build  8/13] COPY csrc csrc/

COPY vllm/envs.py vllm/envs.py
# [csrc-build  9/13] COPY vllm/envs.py vllm/envs.py

COPY vllm/__init__.py vllm/__init__.py
# [csrc-build 10/13] COPY vllm/__init__.py vllm/__init__.py

# max jobs used by Ninja to build extensions
# 限制并行任务数 (max_jobs), 防止在多核机器上编译时内存溢出 (OOM)
ARG max_jobs=2
ENV MAX_JOBS=${max_jobs}
# number of threads used by nvcc
ARG nvcc_threads=8
ENV NVCC_THREADS=$nvcc_threads

ARG USE_SCCACHE
ARG SCCACHE_DOWNLOAD_URL
ARG SCCACHE_ENDPOINT
ARG SCCACHE_BUCKET_NAME=vllm-build-sccache
ARG SCCACHE_REGION_NAME=us-west-2
ARG SCCACHE_S3_NO_CREDENTIALS=0

# Flag to control whether to use pre-built vLLM wheels
ARG VLLM_USE_PRECOMPILED=""
ARG VLLM_MERGE_BASE_COMMIT=""
ARG VLLM_MAIN_CUDA_VERSION=""

# Use dummy version for csrc-build wheel (only .so files are extracted, version doesn't matter)
ENV SETUPTOOLS_SCM_PRETEND_VERSION="0.0.0+csrc.build"

# Use existing torch for nightly builds
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        python3 use_existing_torch.py --prefix; \
    fi
# [csrc-build 11/13] RUN --mount=type=cache,target=/root/.cache/uv set -eux &&
# if [ "0" = "1" ]; then
#     python3 use_existing_torch.py --prefix;
# fi

# Build the vLLM wheel
# if USE_SCCACHE is set, use sccache to speed up compilation
# AWS credentials mounted at ~/.aws/credentials for sccache S3 auth (optional)
# 引入 sccache: 这是分布式编译器缓存.
# 目的: 如果你在 CI/CD 环境中构建, sccache 可以将编译好的 .o 文件存入 S3,
# 下次构建时如果代码没变, 直接下载二进制文件, 编译时间从 20 分钟降到 1 分钟.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=aws-credentials,target=/root/.aws/credentials,required=false \
    set -eux && \
    if [ "$USE_SCCACHE" = "1" ]; then \
        echo "Installing sccache..." \
        && case "${TARGETPLATFORM}" in \
          linux/arm64) SCCACHE_ARCH="aarch64" ;; \
          linux/amd64) SCCACHE_ARCH="x86_64" ;; \
          *) echo "Unsupported TARGETPLATFORM for sccache: ${TARGETPLATFORM}" >&2; exit 1 ;; \
        esac \
        && export SCCACHE_DOWNLOAD_URL="${SCCACHE_DOWNLOAD_URL:-https://github.com/mozilla/sccache/releases/download/v0.8.1/sccache-v0.8.1-${SCCACHE_ARCH}-unknown-linux-musl.tar.gz}" \
        && curl -L -o sccache.tar.gz ${SCCACHE_DOWNLOAD_URL} \
        && tar -xzf sccache.tar.gz \
        && sudo mv sccache-v0.8.1-${SCCACHE_ARCH}-unknown-linux-musl/sccache /usr/bin/sccache \
        && rm -rf sccache.tar.gz sccache-v0.8.1-${SCCACHE_ARCH}-unknown-linux-musl \
        && if [ ! -z ${SCCACHE_ENDPOINT} ] ; then export SCCACHE_ENDPOINT=${SCCACHE_ENDPOINT} ; fi \
        && export SCCACHE_BUCKET=${SCCACHE_BUCKET_NAME} \
        && export SCCACHE_REGION=${SCCACHE_REGION_NAME} \
        && export SCCACHE_S3_NO_CREDENTIALS=${SCCACHE_S3_NO_CREDENTIALS} \
        && export SCCACHE_IDLE_TIMEOUT=0 \
        && export CMAKE_BUILD_TYPE=Release \
        && export VLLM_USE_PRECOMPILED="${VLLM_USE_PRECOMPILED}" \
        && export VLLM_PRECOMPILED_WHEEL_COMMIT="${VLLM_MERGE_BASE_COMMIT}" \
        && export VLLM_MAIN_CUDA_VERSION="${VLLM_MAIN_CUDA_VERSION}" \
        && export VLLM_DOCKER_BUILD_CONTEXT=1 \
        && sccache --show-stats \
        && python3 setup.py bdist_wheel --dist-dir=dist --py-limited-api=cp38 \
        && sccache --show-stats; \
    fi

ARG vllm_target_device="cuda"
ENV VLLM_TARGET_DEVICE=${vllm_target_device}
ENV CCACHE_DIR=/root/.cache/ccache
RUN --mount=type=cache,target=/root/.cache/ccache \
    --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    if [ "$USE_SCCACHE" != "1" ]; then \
        # Clean any existing CMake artifacts
        rm -rf .deps && \
        mkdir -p .deps && \
        export VLLM_USE_PRECOMPILED="${VLLM_USE_PRECOMPILED}" && \
        export VLLM_PRECOMPILED_WHEEL_COMMIT="${VLLM_MERGE_BASE_COMMIT}" && \
        export VLLM_DOCKER_BUILD_CONTEXT=1 && \
        python3 setup.py bdist_wheel --dist-dir=dist --py-limited-api=cp38; \
    fi

#################### CSRC BUILD IMAGE ####################

#################### EXTENSIONS BUILD IMAGE ####################
# Build DeepEP - runs in PARALLEL with csrc-build
# This stage is independent and doesn't affect csrc cache
# 为什么要独立出一个阶段?
# 这样 DeepEP 的构建可以和 vLLM 主体的 CSRC 编译并行执行, 充分利用多核服务器性能.
FROM base AS extensions-build
ARG CUDA_VERSION

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
ENV UV_LINK_MODE=copy

WORKDIR /workspace
# [extensions-build 1/3] WORKDIR /workspace

# Build DeepEP wheels
COPY tools/ep_kernels/install_python_libraries.sh /tmp/install_python_libraries.sh
# [extensions-build 2/3] COPY tools/ep_kernels/install_python_libraries.sh /tmp/install_python_libraries.sh

# Defaults moved here from tools/ep_kernels/install_python_libraries.sh for centralized version management
ARG DEEPEP_COMMIT_HASH=73b6ea4
ARG NVSHMEM_VER
RUN --mount=type=cache,target=/root/.cache/uv \
    set -eux && \
    mkdir -p /tmp/ep_kernels_workspace/dist && \
    export TORCH_CUDA_ARCH_LIST='9.0a 10.0a' && \
    /tmp/install_python_libraries.sh \
        --workspace /tmp/ep_kernels_workspace \
        --mode wheel \
        ${DEEPEP_COMMIT_HASH:+--deepep-ref "$DEEPEP_COMMIT_HASH"} \
        ${NVSHMEM_VER:+--nvshmem-ver "$NVSHMEM_VER"} && \
    find /tmp/ep_kernels_workspace/nvshmem -name '*.a' -delete
#################### EXTENSIONS BUILD IMAGE ####################

#################### WHEEL BUILD IMAGE ####################
FROM base AS build
ARG TARGETPLATFORM

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL
ARG PYTORCH_CUDA_INDEX_BASE_URL

# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install build dependencies
COPY requirements/build/cuda.txt requirements/build/cuda.txt
COPY use_existing_torch.py use_existing_torch.py
COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
# Reference: https://github.com/astral-sh/uv/pull/1694
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
# Use copy mode to avoid hardlink failures with Docker cache mounts
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        echo "Installing build requirements without torch..." \
        && python3 use_existing_torch.py --prefix \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt \
        && echo "Installing torch nightly..." \
        && uv pip install --python /opt/venv/bin/python3 $(cat torch_lib_versions.txt | grep -i "^torch=" | xargs) --pre \
        --index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    else \
        echo "Installing build requirements..." \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/build/cuda.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    fi

WORKDIR /workspace

# Copy pre-built csrc wheel directly
COPY --from=csrc-build /workspace/dist /precompiled-wheels
COPY . .

ARG GIT_REPO_CHECK=0
RUN --mount=type=bind,source=.git,target=.git \
    if [ "$GIT_REPO_CHECK" != "0" ]; then bash tools/check_repo.sh ; fi

ARG vllm_target_device="cuda"
ENV VLLM_TARGET_DEVICE=${vllm_target_device}

# Skip adding +precompiled suffix to version (preserves git-derived version)
ENV VLLM_SKIP_PRECOMPILED_VERSION_SUFFIX=1

# Use existing torch for nightly builds
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        python3 use_existing_torch.py --prefix; \
    fi

# Build the vLLM wheel
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.git,target=.git \
    if [ "${vllm_target_device}" = "cuda" ]; then \
        export VLLM_PRECOMPILED_WHEEL_LOCATION=$(ls /precompiled-wheels/*.whl); \
    fi && \
    python3 setup.py bdist_wheel --dist-dir=dist --py-limited-api=cp38

# Copy extension wheels from extensions-build stage for later use
COPY --from=extensions-build /tmp/ep_kernels_workspace/dist /tmp/ep_kernels_workspace/dist

# Check the size of the wheel if RUN_WHEEL_CHECK is true
COPY .buildkite/check-wheel-size.py check-wheel-size.py
# sync the default value with .buildkite/check-wheel-size.py
ARG VLLM_MAX_SIZE_MB=500
ENV VLLM_MAX_SIZE_MB=$VLLM_MAX_SIZE_MB
ARG RUN_WHEEL_CHECK=true
RUN if [ "$RUN_WHEEL_CHECK" = "true" ]; then \
        python3 check-wheel-size.py dist; \
    else \
        echo "Skipping wheel size check."; \
    fi

#################### WHEEL BUILD IMAGE ####################

#################### DEV IMAGE ####################
FROM base AS dev

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL
ARG PYTORCH_CUDA_INDEX_BASE_URL

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
# Reference: https://github.com/astral-sh/uv/pull/1694
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
# Use copy mode to avoid hardlink failures with Docker cache mounts
ENV UV_LINK_MODE=copy

# Install libnuma-dev, required by fastsafetensors (fixes #20384)
RUN apt-get update && apt-get install -y --no-install-recommends libnuma-dev && rm -rf /var/lib/apt/lists/*


# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install development dependencies
COPY requirements/lint.txt requirements/lint.txt
COPY requirements/test/cuda.in requirements/test/cuda.in
COPY requirements/test/cuda.txt requirements/test/cuda.txt
COPY requirements/dev.txt requirements/dev.txt
COPY use_existing_torch.py use_existing_torch.py
COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        echo "Installing dev requirements plus torch nightly..." \
        && python3 use_existing_torch.py --prefix \
        && cat torch_lib_versions.txt >> requirements/test/cuda.in \
        && uv pip compile requirements/test/cuda.in -o requirements/test/cuda.txt --index-strategy unsafe-best-match \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') \
        && uv pip install --python /opt/venv/bin/python3 $(cat torch_lib_versions.txt | xargs) --pre \
        -r requirements/dev.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    else \
        echo "Installing dev requirements..." \
        && uv pip install --python /opt/venv/bin/python3 -r requirements/dev.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    fi

#################### DEV IMAGE ####################
#################### vLLM installation IMAGE ####################
# image with vLLM installed
FROM ${FINAL_BASE_IMAGE} AS vllm-base

ARG CUDA_VERSION
ARG PYTHON_VERSION
ARG DEADSNAKES_MIRROR_URL
ARG DEADSNAKES_GPGKEY_URL
ARG GET_PIP_URL

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /vllm-workspace


# Python version string for paths (e.g., "312" for 3.12)
RUN PYTHON_VERSION_STR=$(echo ${PYTHON_VERSION} | sed 's/\.//g') && \
    echo "export PYTHON_VERSION_STR=${PYTHON_VERSION_STR}" >> /etc/environment

# Install Python and system dependencies
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        software-properties-common \
        curl \
        sudo \
        ffmpeg \
        libsm6 \
        libxext6 \
        libgl1 \
    && if [ ! -z ${DEADSNAKES_MIRROR_URL} ] ; then \
        if [ ! -z "${DEADSNAKES_GPGKEY_URL}" ] ; then \
            mkdir -p -m 0755 /etc/apt/keyrings ; \
            curl -L ${DEADSNAKES_GPGKEY_URL} | gpg --dearmor > /etc/apt/keyrings/deadsnakes.gpg ; \
            sudo chmod 644 /etc/apt/keyrings/deadsnakes.gpg ; \
            echo "deb [signed-by=/etc/apt/keyrings/deadsnakes.gpg] ${DEADSNAKES_MIRROR_URL} $(lsb_release -cs) main" > /etc/apt/sources.list.d/deadsnakes.list ; \
        fi ; \
    else \
        for i in 1 2 3; do \
            add-apt-repository -y ppa:deadsnakes/ppa && break || \
            { echo "Attempt $i failed, retrying in 5s..."; sleep 5; }; \
        done ; \
    fi \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-dev \
        python${PYTHON_VERSION}-venv \
        libibverbs-dev \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --set python3 /usr/bin/python${PYTHON_VERSION} \
    && ln -sf /usr/bin/python${PYTHON_VERSION}-config /usr/bin/python3-config \
    && rm -f /usr/lib/python${PYTHON_VERSION}/EXTERNALLY-MANAGED \
    && curl -sS ${GET_PIP_URL} | python${PYTHON_VERSION} \
    && python3 --version && python3 -m pip --version

# Install CUDA development tools for runtime JIT compilation
# (FlashInfer, DeepGEMM, EP kernels all require compilation at runtime)
RUN CUDA_VERSION_DASH=$(echo $CUDA_VERSION | cut -d. -f1,2 | tr '.' '-') && \
    CUDA_VERSION_SHORT=$(echo $CUDA_VERSION | cut -d. -f1,2) && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends --allow-change-held-packages \
        cuda-nvcc-${CUDA_VERSION_DASH} \
        cuda-cudart-${CUDA_VERSION_DASH} \
        cuda-nvrtc-${CUDA_VERSION_DASH} \
        cuda-cuobjdump-${CUDA_VERSION_DASH} \
        libcurand-dev-${CUDA_VERSION_DASH} \
        libcublas-${CUDA_VERSION_DASH} \
        # Required by fastsafetensors (fixes #20384)
        libnuma-dev \
        # numactl CLI for NUMA binding at runtime
        numactl && \
    # Fixes nccl_allocator requiring nccl.h at runtime
    # https://github.com/vllm-project/vllm/blob/1336a1ea244fa8bfd7e72751cabbdb5b68a0c11a/vllm/distributed/device_communicators/pynccl_allocator.py#L22
    # NCCL packages don't use the cuda-MAJOR-MINOR naming convention,
    # so we pin the version to match our CUDA version
    NCCL_VER=$(apt-cache madison libnccl-dev | grep "+cuda${CUDA_VERSION_SHORT}" | head -1 | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}') && \
    apt-get install -y --no-install-recommends --allow-change-held-packages libnccl-dev=${NCCL_VER} libnccl2=${NCCL_VER} && \
    rm -rf /var/lib/apt/lists/*

# Install uv for faster pip installs
RUN python3 -m pip install uv

# Environment for uv
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
ENV UV_LINK_MODE=copy

# Enable CUDA forward compatibility by setting '-e VLLM_ENABLE_CUDA_COMPATIBILITY=1'
# Only needed for datacenter/professional GPUs with older drivers.
# See: https://docs.nvidia.com/deploy/cuda-compatibility/
ENV VLLM_ENABLE_CUDA_COMPATIBILITY=0

# ============================================================
# SLOW-CHANGING DEPENDENCIES BELOW
# These are the expensive layers that we want to cache
# ============================================================

# Install PyTorch and core CUDA dependencies
# This is ~2GB and rarely changes
ARG PYTORCH_CUDA_INDEX_BASE_URL
COPY requirements/common.txt /tmp/common.txt
COPY requirements/cuda.txt /tmp/requirements-cuda.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r /tmp/requirements-cuda.txt \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') && \
    rm /tmp/requirements-cuda.txt /tmp/common.txt

# Install FlashInfer JIT cache (requires CUDA-version-specific index URL)
# https://docs.flashinfer.ai/installation.html
# From versions.json: .flashinfer.version
ARG FLASHINFER_VERSION=0.6.8.post1
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system flashinfer-jit-cache==${FLASHINFER_VERSION} \
        --extra-index-url https://flashinfer.ai/whl/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') \
    && flashinfer show-config \
    && flashinfer download-cubin

# ============================================================
# OPENAI API SERVER DEPENDENCIES
# Pre-install these to avoid reinstalling on every vLLM wheel rebuild
# ============================================================

# Install gdrcopy (saves ~6s per build)
# TODO (huydhn): There is no prebuilt gdrcopy package on 12.9 at the moment
ARG GDRCOPY_CUDA_VERSION=12.8
ARG GDRCOPY_OS_VERSION=Ubuntu22_04
ARG TARGETPLATFORM
COPY tools/install_gdrcopy.sh /tmp/install_gdrcopy.sh
RUN set -eux; \
    case "${TARGETPLATFORM}" in \
      linux/arm64) UUARCH="aarch64" ;; \
      linux/amd64) UUARCH="x64" ;; \
      *) echo "Unsupported TARGETPLATFORM: ${TARGETPLATFORM}" >&2; exit 1 ;; \
    esac; \
    /tmp/install_gdrcopy.sh "${GDRCOPY_OS_VERSION}" "${GDRCOPY_CUDA_VERSION}" "${UUARCH}" && \
    rm /tmp/install_gdrcopy.sh

# Install vllm-openai dependencies (saves ~2.6s per build)
# These are stable packages that don't depend on vLLM itself
# From versions.json: .bitsandbytes.x86_64, .bitsandbytes.arm64
# From versions.json: .openai_server_extras.timm, .openai_server_extras.runai_model_streamer
ARG BITSANDBYTES_VERSION_X86=0.46.1
ARG BITSANDBYTES_VERSION_ARM64=0.42.0
ARG TIMM_VERSION=">=1.0.17"
ARG RUNAI_MODEL_STREAMER_VERSION=">=0.15.7"
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        BITSANDBYTES_VERSION="${BITSANDBYTES_VERSION_ARM64}"; \
    else \
        BITSANDBYTES_VERSION="${BITSANDBYTES_VERSION_X86}"; \
    fi; \
    uv pip install --system accelerate modelscope \
        "bitsandbytes>=${BITSANDBYTES_VERSION}" "timm${TIMM_VERSION}" "runai-model-streamer[s3,gcs,azure]${RUNAI_MODEL_STREAMER_VERSION}"

# ============================================================
# VLLM INSTALLATION (depends on build stage)
# ============================================================

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL
ARG PYTORCH_CUDA_INDEX_BASE_URL
ARG PIP_KEYRING_PROVIDER UV_KEYRING_PROVIDER

# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install vLLM wheel first, so that torch etc will be installed.
# Check whether to install torch nightly instead of release for this build.
COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt
RUN --mount=type=bind,from=build,src=/workspace/dist,target=/vllm-workspace/dist \
    --mount=type=cache,target=/root/.cache/uv \
    if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
        echo "Installing torch nightly..." \
        && uv pip install --system $(cat torch_lib_versions.txt | xargs) --pre \
        --index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') \
        && echo "Installing vLLM..." \
        && uv pip install --system dist/*.whl --verbose \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    else \
        echo "Installing vLLM..." \
        && uv pip install --system dist/*.whl --verbose \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
. /etc/environment && \
uv pip list

# Pytorch now installs NVSHMEM, setting LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Install EP kernels wheels (DeepEP) that have been built in the `build` stage
RUN --mount=type=bind,from=build,src=/tmp/ep_kernels_workspace/dist,target=/vllm-workspace/ep_kernels/dist \
    --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system ep_kernels/dist/*.whl --verbose \
        --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.')

# CUDA image changed from /usr/local/nvidia to /usr/local/cuda in 12.8 but will
# return to /usr/local/nvidia in 13.0 to allow container providers to mount drivers
# consistently from the host (see https://github.com/vllm-project/vllm/issues/18859).
# Until then, add /usr/local/nvidia/lib64 before the image cuda path to allow override.
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

# Copy examples and benchmarks at the end to minimize cache invalidation
COPY examples examples
COPY benchmarks benchmarks
COPY ./vllm/collect_env.py .
#################### vLLM installation IMAGE ####################
#################### TEST IMAGE ####################
# image to run unit testing suite
# note that this uses vllm installed by `pip`
FROM vllm-base AS test

ADD . /vllm-workspace/

ARG PYTHON_VERSION

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL
ARG PYTORCH_CUDA_INDEX_BASE_URL

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
# Reference: https://github.com/astral-sh/uv/pull/1694
ENV UV_HTTP_TIMEOUT=500
ENV UV_INDEX_STRATEGY="unsafe-best-match"
# Use copy mode to avoid hardlink failures with Docker cache mounts
ENV UV_LINK_MODE=copy

RUN apt-get update -y \
    && apt-get install -y git

# We can specify the standard or nightly build of PyTorch
ARG PYTORCH_NIGHTLY

# Install development dependencies (for testing)
COPY requirements/lint.txt requirements/lint.txt
COPY requirements/test/cuda.in requirements/test/cuda.in
COPY requirements/test/cuda.txt requirements/test/cuda.txt
COPY requirements/dev.txt requirements/dev.txt
COPY use_existing_torch.py use_existing_torch.py
COPY --from=base /workspace/torch_lib_versions.txt torch_lib_versions.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    CUDA_MAJOR="${CUDA_VERSION%%.*}"; \
    if [ "$CUDA_MAJOR" -ge 12 ]; then \
        if [ "${PYTORCH_NIGHTLY}" = "1" ]; then \
            echo "Installing dev requirements plus torch nightly..." \
            && python3 use_existing_torch.py --prefix \
            && cat torch_lib_versions.txt >> requirements/test/cuda.in \
            && uv pip compile requirements/test/cuda.in -o requirements/test/cuda.txt --index-strategy unsafe-best-match \
            --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.') \
            && uv pip install --system $(cat torch_lib_versions.txt | xargs) --pre \
            -r requirements/dev.txt \
            --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/nightly/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
        else \
            echo "Installing dev requirements..." \
            && uv pip install --system -r requirements/dev.txt \
            --extra-index-url ${PYTORCH_CUDA_INDEX_BASE_URL}/cu$(echo $CUDA_VERSION | cut -d. -f1,2 | tr -d '.'); \
        fi \
    fi

# install development dependencies (for testing)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -e tests/vllm_test_utils

# enable fast downloads from hf (for testing)
ENV HF_XET_HIGH_PERFORMANCE 1

# increase timeout for hf downloads (for testing)
ENV HF_HUB_DOWNLOAD_TIMEOUT 60

# Copy in the v1 package for testing (it isn't distributed yet)
COPY vllm/v1 /usr/local/lib/python${PYTHON_VERSION}/dist-packages/vllm/v1

# Source code is used in the `python_only_compile.sh` test
# We hide it inside `src/` so that this source code
# will not be imported by other tests
RUN mkdir src
RUN mv vllm src/vllm
#################### TEST IMAGE ####################

#################### OPENAI API SERVER ####################
# base openai image with additional requirements, for any subsequent openai-style images
FROM vllm-base AS vllm-openai-base
ARG TARGETPLATFORM
ARG INSTALL_KV_CONNECTORS=false
ARG CUDA_VERSION

ARG PIP_INDEX_URL UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL UV_EXTRA_INDEX_URL

# This timeout (in seconds) is necessary when installing some dependencies via uv since it's likely to time out
# Reference: https://github.com/astral-sh/uv/pull/1694
ENV UV_HTTP_TIMEOUT=500

# install kv_connectors if requested
ARG torch_cuda_arch_list='7.5 8.0 8.6 8.9 9.0 10.0 11.0 12.0+PTX'
ENV TORCH_CUDA_ARCH_LIST=${torch_cuda_arch_list}
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements/kv_connectors.txt,target=/tmp/kv_connectors.txt,ro \
    CUDA_MAJOR="${CUDA_VERSION%%.*}"; \
    CUDA_VERSION_DASH=$(echo $CUDA_VERSION | cut -d. -f1,2 | tr '.' '-'); \
    CUDA_HOME=/usr/local/cuda; \
    # lmcache requires explicit specifying CUDA_HOME
    BUILD_PKGS="libcusparse-dev-${CUDA_VERSION_DASH} \
                libcublas-dev-${CUDA_VERSION_DASH} \
                libcusolver-dev-${CUDA_VERSION_DASH}"; \
    if [ "$INSTALL_KV_CONNECTORS" = "true" ]; then \
        if [ "$CUDA_MAJOR" -ge 13 ]; then \
            uv pip install --system nixl-cu13; \
        fi; \
        uv pip install --system -r /tmp/kv_connectors.txt --no-build || ( \
            # if the above fails, install from source
            apt-get update -y && \
            apt-get install -y --no-install-recommends --allow-change-held-packages ${BUILD_PKGS} && \
            uv pip install --system -r /tmp/kv_connectors.txt --no-build-isolation && \
            apt-get purge -y ${BUILD_PKGS} && \
            # clean up -dev packages, keep runtime libraries
            rm -rf /var/lib/apt/lists/* \
        ); \
    fi

ENV VLLM_USAGE_SOURCE production-docker-image

# define sagemaker first, so it is not default from `docker build`
FROM vllm-openai-base AS vllm-sagemaker

COPY examples/online_serving/sagemaker-entrypoint.sh .
RUN chmod +x sagemaker-entrypoint.sh
ENTRYPOINT ["./sagemaker-entrypoint.sh"]

FROM vllm-openai-base AS vllm-openai

ENTRYPOINT ["vllm", "serve"]
#################### OPENAI API SERVER ####################
