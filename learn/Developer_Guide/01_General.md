# Contributing to vLLM

* https://docs.vllm.ai/en/v0.20.0/contributing/

Thank you for your interest in contributing to vLLM! Our community is open to everyone and welcomes all kinds of contributions, no matter how small or large. There are several ways you can contribute to the project:
感谢您对 vLLM 项目的关注! 我们的社区面向所有人开放, 欢迎各种形式的贡献, 无论大小. 您可以通过以下几种方式为项目做出贡献:

- Identify and report any issues or bugs.
  发现并报告任何问题或漏洞.

- Request or add support for a new model.
  请求或添加对新模型的支持.

- Suggest or implement new features.
  提出或实现新功能.

- Improve documentation or contribute a how-to guide.
  改进文档或贡献操作指南.

We also believe in the power of community support; thus, answering queries, offering PR reviews, and assisting others are also highly regarded and beneficial contributions.
我们也相信社区支持的力量; 因此, 回答问题、提供公关评论和帮助他人也是备受重视和有益的贡献.

Finally, one of the most impactful ways to support us is by raising awareness about vLLM. Talk about it in your blog posts and highlight how it's driving your incredible projects. Express your support on social media if you're using vLLM, or simply offer your appreciation by starring our repository!
最后, 支持我们最有效的方式之一就是提高大家对 vLLM 的认知度. 请在您的博客文章中谈谈 vLLM, 并重点介绍它如何推动您开展精彩的项目. 如果您正在使用 vLLM, 请在社交媒体上表达您的支持, 或者简单地为我们的代码库点赞以示感谢!

## Job Board

Unsure on where to start? Check out the following links for tasks to work on:  
不知道从哪里开始? 请查看以下链接, 了解可以完成的任务: 

- [Good first issues 
  好的开篇之作](https://github.com/vllm-project/vllm/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22)
  -  [Selected onboarding tasks 
    选定的入职任务](https://github.com/orgs/vllm-project/projects/6)
- [New model requests 
  新模型需求](https://github.com/vllm-project/vllm/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22new-model%22)
  -  [Models with multi-modal capabilities 
    具有多模式能力的模型](https://github.com/orgs/vllm-project/projects/10)

## License  执照[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#license "Permanent link")

See  [LICENSE](https://github.com/vllm-project/vllm/blob/main/LICENSE).  
看[执照](https://github.com/vllm-project/vllm/blob/main/LICENSE) . 

## Developing  发展[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#developing "Permanent link")

The first step of contributing to vLLM is to clone the GitHub repository:  
为 vLLM 做贡献的第一步是克隆 GitHub 代码库: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-0-1)git clone https://github.com/vllm-project/vllm.git [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-0-2)cd vllm`

Then, configure your Python virtual environment.  
然后, 配置你的 Python 虚拟环境. 

It's recommended to use [uv](https://docs.astral.sh/uv/), a very fast Python environment manager, to create and manage Python environments. Please follow the [documentation](https://docs.astral.sh/uv/#getting-started) to install `uv`. After installing `uv`, you can create a new Python environment using the following commands:  
建议使用 [uv](https://docs.astral.sh/uv/) （一款速度非常快的 Python 环境管理器）来创建和管理 Python 环境. 请按照[文档](https://docs.astral.sh/uv/#getting-started)安装 `uv` . 安装 `uv` 后, 您可以使用以下命令创建新的 Python 环境: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-1-1)uv venv --python 3.12 --seed --managed-python [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-1-2)source .venv/bin/activate`

If you are only developing vLLM's Python code, install vLLM using:  
如果您仅开发 vLLM 的 Python 代码, 请使用以下命令安装 vLLM: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-2-1)VLLM_USE_PRECOMPILED=1 uv pip install -e .`

If you are developing vLLM's Python and CUDA/C++ code, install Pytorch first:  
如果您正在开发 vLLM 的 Python 和 CUDA/C++ 代码, 请先安装 Pytorch: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-3-1)uv pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu129`

Then install the necessary build dependencies from `requirements/build/cuda.txt`, skipping `torch` as it was installed in the previous step:  
然后从 `requirements/build/cuda.txt` 安装必要的构建依赖项, 跳过 `torch` 因为它在上一步中已经安装好了: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-4-1)grep -v '^torch==' requirements/build/cuda.txt | uv pip install -r -`

Finally install vLLM using:  
最后使用以下命令安装 vLLM: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-5-1)uv pip install -e . --no-build-isolation`

For more details about installing from source and installing for other hardware, check out the [installation instructions](https://docs.vllm.ai/en/v0.20.0/getting_started/installation/) for your hardware and head to the "Build wheel from source" section.  
有关从源代码安装和为其他硬件安装的更多详细信息, 请查看您的硬件的[安装说明](https://docs.vllm.ai/en/v0.20.0/getting_started/installation/) , 并前往“从源代码构建 wheel”部分. 

For an optimized workflow when iterating on C++/CUDA kernels, see the [Incremental Compilation Workflow](https://docs.vllm.ai/en/v0.20.0/contributing/incremental_build/) for recommendations.  
为了优化 C++/CUDA 内核迭代的工作流程, 请参阅[增量编译工作流程](https://docs.vllm.ai/en/v0.20.0/contributing/incremental_build/)以获取建议. 

Tip  提示

vLLM is compatible with Python versions 3.10 to 3.13. However, vLLM's default  [Dockerfile](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile) ships with Python 3.12 and tests in CI (except `mypy`) are run with Python 3.12.  
vLLM 与 Python 版本 3.10 至 3.13 兼容. 但是, vLLM 的默认设置 [Dockerfile](https://github.com/vllm-project/vllm/blob/main/docker/Dockerfile) 附带 Python 3.12, CI 中的测试（ `mypy` 除外）均使用 Python 3.12 运行. 

Therefore, we recommend developing with Python 3.12 to minimise the chance of your local environment clashing with our CI environment.  
因此, 我们建议使用 Python 3.12 进行开发, 以最大程度地减少本地环境与我们的 CI 环境发生冲突的可能性. 

### Linting  绒毛[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#linting "Permanent link")

vLLM uses `pre-commit` to lint and format the codebase. See [pre-commit](https://pre-commit.com/#usage) if `pre-commit` is new to you. Setting up `pre-commit` is as easy as:  
vLLM 使用 `pre-commit` 来检查和格式化代码库. 如果您不熟悉 `pre-commit` 请参阅 [pre-commit](https://pre-commit.com/#usage) . 设置 `pre-commit` 非常简单: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-6-1)uv pip install pre-commit>=4.5.1 [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-6-2)pre-commit install`

vLLM's `pre-commit` hooks will now run automatically every time you commit.  
vLLM 的 `pre-commit` hooks 现在会在每次提交时自动运行. 

Tips  尖端

You can manually run the `pre-commit` hooks using:  
您可以使用以下命令手动运行 `pre-commit` 钩子: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-7-1)pre-commit run # runs on staged files [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-7-2)pre-commit run -a # runs on all files (short for --all-files)`

---

Some `pre-commit` hooks only run in CI. If you need to, you can run them locally with:  
某些 `pre-commit` 钩子仅在 CI 环境中运行. 如有需要, 您可以使用以下命令在本地运行它们: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-8-1)pre-commit run --hook-stage manual mypy-3.10`

### Documentation  文档[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#documentation "Permanent link")

MkDocs is a fast, simple and downright gorgeous static site generator that's geared towards building project documentation. Documentation source files are written in Markdown, and configured with a single YAML configuration file,  [mkdocs.yaml](https://github.com/vllm-project/vllm/blob/main/mkdocs.yaml).  
MkDocs 是一款快速、简单且界面精美的静态网站生成器, 专为构建项目文档而设计. 文档源文件使用 Markdown 编写, 并通过单个 YAML 配置文件进行配置.  [mkdocs.yaml](https://github.com/vllm-project/vllm/blob/main/mkdocs.yaml) . 

Get started with:  开始操作: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-9-1)uv pip install -r requirements/docs.txt`

Tip  提示

Ensure that your Python version is compatible with the plugins (e.g., `mkdocs-awesome-nav` requires Python 3.10+)  
请确保您的 Python 版本与插件兼容（例如,  `mkdocs-awesome-nav` 需要 Python 3.10+）. 

MkDocs comes with a built-in dev-server that lets you preview your documentation as you work on it. From the root of the repository, run:  
MkDocs 自带一个内置的开发服务器, 允许您在编辑文档的同时预览文档. 在仓库根目录下运行: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-10-1)mkdocs serve # with API ref (~10 minutes) [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-10-2)API_AUTONAV_EXCLUDE=vllm mkdocs serve # API ref off (~15 seconds)`

Once you see `Serving on http://127.0.0.1:8000/` in the logs, the live preview is ready! Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser to see it.  
当您在日志中看到 `Serving on http://127.0.0.1:8000/` 时, 实时预览就准备就绪了! 请在浏览器中打开 [http://127.0.0.1:8000/](http://127.0.0.1:8000/) 查看. 

For additional features and advanced configurations, refer to the:  
如需了解更多功能和高级配置, 请参阅: 

- [MkDocs documentation  MkDocs 文档](https://www.mkdocs.org/)
- [Material for MkDocs documentation](https://squidfunk.github.io/mkdocs-material/) (the MkDocs theme we use)  
  [MkDocs 文档的素材](https://squidfunk.github.io/mkdocs-material/) （我们使用的 MkDocs 主题）

### Testing  测试[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#testing "Permanent link")

vLLM uses `pytest` to test the codebase.  
vLLM 使用 `pytest` 来测试代码库. 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-1)# Install the test dependencies used in CI (CUDA only) [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-2)uv pip install -r requirements/common.txt -r requirements/dev.txt --torch-backend=auto [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-3)[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-4)# Install some common test dependencies (hardware agnostic) [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-5)uv pip install pytest pytest-asyncio [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-6)[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-7)# Run all tests [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-8)pytest tests/ [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-9)[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-10)# Run tests for a single test file with detailed output [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-11-11)pytest -s -v tests/test_logger.py`

Install python3-dev if Python.h is missing  
如果缺少 Python.h, 请安装 python3-dev. 

If any of the above commands fails with `Python.h: No such file or directory`, install `python3-dev` with `sudo apt install python3-dev`.  
如果上述任何命令失败并出现 `Python.h: No such file or directory` , 请使用 `sudo apt install python3-dev` `python3-dev` 安装 python3-dev. 

Warnings  警告

Currently, the repository is not fully checked by `mypy`.  
目前,  `mypy` 尚未对该存储库进行全面检查. 

---

Currently, not all unit tests pass when run on CPU platforms. If you don't have access to a GPU platform to run unit tests locally, rely on the continuous integration system to run the tests for now.  
目前, 并非所有单元测试都能在 CPU 平台上通过. 如果您没有 GPU 平台在本地运行单元测试, 请暂时依赖持续集成系统来运行测试. 

## Issues  问题[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#issues "Permanent link")

If you encounter a bug or have a feature request, please [search existing issues](https://github.com/vllm-project/vllm/issues?q=is%3Aissue) first to see if it has already been reported. If not, please [file a new issue](https://github.com/vllm-project/vllm/issues/new/choose), providing as much relevant information as possible.  
如果您遇到错误或有功能请求, 请先[搜索现有问题](https://github.com/vllm-project/vllm/issues?q=is%3Aissue) , 看看是否已被报告. 如果没有, 请[提交新的问题](https://github.com/vllm-project/vllm/issues/new/choose) , 并尽可能提供相关信息. 

Important  重要的

If you discover a security vulnerability, please follow the instructions  [here](https://github.com/vllm-project/vllm/blob/main/SECURITY.md).  
如果您发现安全漏洞, 请按照以下说明操作.  [这里](https://github.com/vllm-project/vllm/blob/main/SECURITY.md) . 

## Pull Requests & Code Reviews

拉取请求和代码审查[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#pull-requests-code-reviews "Permanent link")

Thank you for your contribution to vLLM! Before submitting the pull request, please ensure the PR meets the following criteria. This helps vLLM maintain the code quality and improve the efficiency of the review process.  
感谢您对 vLLM 的贡献! 提交拉取请求前, 请确保拉取请求符合以下标准. 这有助于 vLLM 维护代码质量并提高代码审查效率. 

### DCO and Signed-off-by  DCO 和签字人[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#dco-and-signed-off-by "Permanent link")

When contributing changes to this project, you must agree to the  [DCO](https://github.com/vllm-project/vllm/blob/main/DCO). Commits must include a `Signed-off-by:` header which certifies agreement with the terms of the DCO.  
当您向本项目提交更改时, 您必须同意以下条款:  [DCO](https://github.com/vllm-project/vllm/blob/main/DCO) . 提交必须包含 `Signed-off-by:` 标头, 以证明同意 DCO 的条款. 

Using `-s` with `git commit` will automatically add this header.  
使用 `git commit` 的 `-s` 会自动添加此标头. 

Tip  提示

You can enable automatic sign-off via your IDE:  
您可以通过 IDE 启用自动注销: 

- **PyCharm**: Click on the `Show Commit Options` icon to the right of the `Commit and Push...` button in the `Commit` window. It will bring up a `git` window where you can modify the `Author` and enable `Sign-off commit`.  
  **PyCharm** : 在 `Commit` 窗口中,  `Commit and Push...` 按钮右侧, 点击 `Show Commit Options` 图标. 这将打开一个 `git` 窗口, 您可以在其中修改 `Author` 并启用 `Sign-off commit` . 
- **VSCode**: Open the [Settings editor](https://code.visualstudio.com/docs/configure/settings) and enable the `Git: Always Sign Off` (`git.alwaysSignOff`) field.  
  **VSCode** : 打开[设置编辑器](https://code.visualstudio.com/docs/configure/settings) , 启用 `Git: Always Sign Off` ( `git.alwaysSignOff` ) 字段. 

### AI Assisted Contributions

人工智能辅助贡献[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#ai-assisted-contributions "Permanent link")

Before making an AI assisted contribution, you must:  
在进行人工智能辅助捐款之前, 您必须: 

1. **Be involved**: Do not submit "pure agent" PRs. The human submitter is responsible for reviewing all changed lines, validating behavior end-to-end, and running relevant tests.  
  **积极参与** : 请勿提交“纯代理”PR. 提交者需负责审核所有修改行, 验证端到端行为, 并运行相关测试. 
2. **Ensure significance**: Avoid one-off "busywork" PRs (single typo, isolated style cleanup, one mutable default fix, etc.). Bundle mechanical cleanups into a clear, systematic scope.  
  **确保重要性** : 避免一次性的“无意义”PR（例如单个拼写错误、孤立的样式清理、单个可变默认值修复等）. 将机械性的清理工作整合到一个清晰、系统的范围内. 

When AI tools provide non-trivial assistance in generating or modifying code, you must:  
当人工智能工具在生成或修改代码方面提供重要的帮助时, 您必须: 

1. **Review thoroughly**: You remain responsible for all code you submit. Review and understand AI-generated code with the same care as code you write manually.  
  **仔细审查** : 您始终对提交的所有代码负责. 请像对待自己编写的代码一样认真审查和理解人工智能生成的代码. 
2. **Disclose in PR**: Always mention when a pull request includes AI-generated code. Add a note in the PR description.  
  **在 PR 中披露** : 当拉取请求包含 AI 生成的代码时, 务必注明. 在 PR 描述中添加注释. 
3. **Mark commits**: Add attribution using commit trailers such as `Co-authored-by:` (other projects use `Assisted-by:` or `Generated-by:`). For example:  
  **标记提交** : 使用提交尾部添加署名, 例如 `Co-authored-by:` （其他项目使用 `Assisted-by:` 或 `Generated-by:` ”）. 例如: 

`[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-1)Your commit message here [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-2)[](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-3)Co-authored-by: GitHub Copilot [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-4)Co-authored-by: Claude [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-5)Co-authored-by: gemini-code-assist [](https://docs.vllm.ai/en/v0.20.0/contributing/#__codelineno-12-6)Signed-off-by: Your Name <your.email@example.com>`

AI-assisted code must meet all quality standards: proper testing, documentation, adherence to style guides, and thorough review. Attribution helps reviewers evaluate contributions in context and maintains legal clarity for the project.  
人工智能辅助编写的代码必须符合所有质量标准: 适当的测试、文档、遵循风格指南以及全面的审查. 署名有助于审查人员在上下文中评估贡献, 并维护项目的法律清晰度. 

### PR Title and Classification

公关标题和分类[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#pr-title-and-classification "Permanent link")

Only specific types of PRs will be reviewed. The PR title is prefixed appropriately to indicate the type of change. Please use one of the following:  
我们只会审核特定类型的 PR. PR 标题会添加相应的前缀以表明更改类型. 请使用以下格式之一: 

- `[Bugfix]` for bug fixes.  
  `[Bugfix]` 用于修复错误. 
- `[CI/Build]` for build or continuous integration improvements.  
  `[CI/Build]` 用于构建或持续集成改进. 
- `[Doc]` for documentation fixes and improvements.  
  `[Doc]` 用于文档修复和改进. 
- `[Model]` for adding a new model or improving an existing model. Model name should appear in the title.  
  `[Model]` 用于添加新模型或改进现有模型. 模型名称应出现在标题中. 
- `[Frontend]` For changes on the vLLM frontend (e.g., OpenAI API server, [`LLM`](https://docs.vllm.ai/en/v0.20.0/api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM "LLM") class, etc.)  
  `[Frontend]` 用于 vLLM 前端的更改（例如, OpenAI API 服务器、 [`LLM`](https://docs.vllm.ai/en/v0.20.0/api/vllm/entrypoints/llm/#vllm.entrypoints.llm.LLM "LLM") 类等）
- `[Kernel]` for changes affecting CUDA kernels or other compute kernels.  
  `[Kernel]` 用于影响 CUDA 内核或其他计算内核的更改. 
- `[Core]` for changes in the core vLLM logic (e.g., [`LLMEngine`](https://docs.vllm.ai/en/v0.20.0/api/vllm/v1/engine/llm_engine/#vllm.v1.engine.llm_engine.LLMEngine "LLMEngine"), `AsyncLLMEngine`, `Scheduler`, etc.)  
  `[Core]` 用于更改核心 vLLM 逻辑（例如,  [`LLMEngine`](https://docs.vllm.ai/en/v0.20.0/api/vllm/v1/engine/llm_engine/#vllm.v1.engine.llm_engine.LLMEngine "LLMEngine") 、 `AsyncLLMEngine` 、 `Scheduler` 等）
- `[Hardware][Vendor]` for hardware-specific changes. Vendor name should appear in the prefix (e.g., `[Hardware][AMD]`).  
  `[Hardware][Vendor]` 用于硬件相关的更改. 供应商名称应出现在前缀中（例如,  `[Hardware][AMD]` ）. 
- `[Misc]` for PRs that do not fit the above categories. Please use this sparingly.  
  `[Misc]` 用于不属于上述类别的 PR. 请谨慎使用此功能. 

Note  笔记

If the PR spans more than one category, please include all relevant prefixes.  
如果 PR 涉及多个类别, 请包含所有相关的前缀. 

### Code Quality  代码质量[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#code-quality "Permanent link")

The PR needs to meet the following code quality standards:  
该 PR 需要符合以下代码质量标准: 

- We adhere to [Google Python style guide](https://google.github.io/styleguide/pyguide.html) and [Google C++ style guide](https://google.github.io/styleguide/cppguide.html).  
  我们遵循 [Google Python 风格指南](https://google.github.io/styleguide/pyguide.html)和 [Google C++ 风格指南](https://google.github.io/styleguide/cppguide.html) . 
- Pass all linter checks.  
  通过所有代码检查. 
- The code needs to be well-documented to ensure future contributors can easily understand the code.  
  代码需要有完善的文档, 以确保未来的贡献者能够轻松理解代码. 
- Include sufficient tests to ensure the project stays correct and robust. This includes both unit tests and integration tests.  
  编写足够的测试用例, 确保项目正确且稳健. 这包括单元测试和集成测试. 
- Please add documentation to `docs/` if the PR modifies the user-facing behaviors of vLLM. It helps vLLM users understand and utilize the new features or changes.  
  如果 PR 修改了 vLLM 的用户界面行为, 请在 `docs/` 下添加文档. 这有助于 vLLM 用户理解和使用新功能或变更. 

### Adding or Changing Kernels

添加或更改内核[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#adding-or-changing-kernels "Permanent link")

When actively developing or modifying kernels, using the [Incremental Compilation Workflow](https://docs.vllm.ai/en/v0.20.0/contributing/incremental_build/) is highly recommended for faster build times. Each custom kernel needs a schema and one or more implementations to be registered with PyTorch.  
在积极开发或修改内核时, 强烈建议使用[增量编译工作流](https://docs.vllm.ai/en/v0.20.0/contributing/incremental_build/)以加快构建速度. 每个自定义内核都需要一个模式以及一个或多个需要注册到 PyTorch 的实现. 

- Make sure custom ops are registered following PyTorch guidelines: [Custom C++ and CUDA Operators](https://pytorch.org/tutorials/advanced/cpp_custom_ops.html#cpp-custom-ops-tutorial) and [The Custom Operators Manual](https://docs.google.com/document/d/1_W62p8WJOQQUzPsJYa7s701JXt0qf2OfLub2sbkHOaU).  
  确保按照 PyTorch 指南注册自定义操作:  [自定义 C++ 和 CUDA 操作符](https://pytorch.org/tutorials/advanced/cpp_custom_ops.html#cpp-custom-ops-tutorial)以及[自定义操作符手册](https://docs.google.com/document/d/1_W62p8WJOQQUzPsJYa7s701JXt0qf2OfLub2sbkHOaU) . 
- Custom operations that return `Tensors` require meta-functions. Meta-functions should be implemented and registered in Python so that dynamic dims can be handled automatically. See above documents for a description of meta-functions.  
  返回 `Tensors` 自定义操作需要使用元函数. 元函数应在 Python 中实现并注册, 以便自动处理动态维度. 有关元函数的描述, 请参阅上述文档. 
- Use [torch.library.opcheck()](https://pytorch.org/docs/stable/library.html#torch.library.opcheck) to test the function registration and meta-function for any registered ops. See `tests/kernels` for examples.  
  使用 [torch.library.opcheck()](https://pytorch.org/docs/stable/library.html#torch.library.opcheck) 测试所有已注册操作的函数注册和元函数. 有关示例, 请参阅 `tests/kernels` . 
- When changing the C++ signature of an existing op, the schema must be updated to reflect the changes.  
  当更改现有操作的 C++ 签名时, 必须更新模式以反映这些更改. 
- If a new custom type is needed, see the following document: [Custom Class Support in PT2](https://docs.google.com/document/d/18fBMPuOJ0fY5ZQ6YyrHUppw9FA332CpNtgB6SOIgyuA).  
  如果需要新的自定义类型, 请参阅以下文档:  [PT2 中的自定义类支持](https://docs.google.com/document/d/18fBMPuOJ0fY5ZQ6YyrHUppw9FA332CpNtgB6SOIgyuA) . 

### Notes for Large Changes  重大变更须知[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#notes-for-large-changes "Permanent link")

Please keep the changes as concise as possible. For major architectural changes (>500 LOC excluding kernel/data/config/test), we would expect a GitHub issue (RFC) discussing the technical design and justification. Otherwise, we will tag it with `rfc-required` and might not go through the PR.  
请尽量保持修改简洁. 对于重大架构变更（500 行代码, 不包括 kernel/data/config/test）, 我们希望您提交一个 GitHub issue（RFC）, 详细讨论技术设计和理由. 否则, 我们会将其标记为 `rfc-required` , 并且可能不会审核您的 PR. 

### What to Expect for the Reviews

评论预期内容[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#what-to-expect-for-the-reviews "Permanent link")

The goal of the vLLM team is to be a *transparent reviewing machine*. We would like to make the review process transparent and efficient and make sure no contributor feels confused or frustrated. However, the vLLM team is small, so we need to prioritize some PRs over others. Here is what you can expect from the review process:  
vLLM 团队的目标是打造一个*透明的代码审查机制* . 我们希望审查过程透明高效, 确保所有贡献者都不会感到困惑或沮丧. 然而, vLLM 团队规模较小, 因此我们需要对一些 PR 进行优先级排序. 以下是您对审查流程的预期: 

- After the PR is submitted, the PR will be assigned to a reviewer. Every reviewer will pick up the PRs based on their expertise and availability.  
  PR 提交后, 系统会将 PR 分配给一位审阅者. 每位审阅者都会根据自己的专业知识和时间安排来选择审阅的 PR. 
- After the PR is assigned, the reviewer will provide status updates every 2-3 days. If the PR is not reviewed within 7 days, please feel free to ping the reviewer or the vLLM team.  
  PR 分配后, 审核人员将每 2-3 天提供一次状态更新. 如果 PR 在 7 天内没有得到审核, 请随时联系审核人员或 vLLM 团队. 
- After the review, the reviewer will put an `action-required` label on the PR if there are changes required. The contributor should address the comments and ping the reviewer to re-review the PR.  
  审核结束后, 如果需要修改, 审核者会在 PR 上添加 `action-required` 标签. 贡献者应根据评论进行修改, 并通知审核者重新审核 PR. 
- Please respond to all comments within a reasonable time frame. If a comment isn't clear or you disagree with a suggestion, feel free to ask for clarification or discuss the suggestion.  
  请在合理的时间范围内回复所有评论. 如果评论不够清晰或您不同意某个建议, 请随时提出疑问或进行讨论. 
- Note that not all CI checks will be executed due to limited computational resources. The reviewer will add `ready` label to the PR when the PR is ready to merge or a full CI run is needed.  
  请注意, 由于计算资源有限, 并非所有持续集成 (CI) 检查都会执行. 当 PR 准备好合并或需要运行完整的 CI 时, 审核人员会将 `ready` 标签添加到 PR 中. 

## Thank You  谢谢[¶](https://docs.vllm.ai/en/v0.20.0/contributing/#thank-you "Permanent link")

Finally, thank you for taking the time to read these guidelines and for your interest in contributing to vLLM. All of your contributions help make vLLM a great tool and community for everyone!  
最后, 感谢您抽出时间阅读这些指南, 也感谢您对 vLLM 的贡献. 您的每一份贡献都有助于将 vLLM 打造成一个对所有人而言都非常棒的工具和社区! 

April 10, 2026  2026年4月10日