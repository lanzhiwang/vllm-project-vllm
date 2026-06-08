```bash
(base) root@k8s-a40-node02:~# docker run -ti --rm --security-opt seccomp=unconfined --gpus '"device=1, 7"' --name vllm-client vllm/vllm-openai:v0.22.0-cu129-ubuntu2404 --help=all
usage: vllm serve [model_tag] [options]

Launch a local OpenAI-compatible API server to serve LLM
completions via HTTP. Defaults to Qwen/Qwen3-0.6B if no model is specified.

Search by using: `--help=<ConfigGroup>` to explore options by section (e.g.,
--help=ModelConfig, --help=Frontend)
  Use `--help=all` to show all available flags at once.

positional arguments:
  model_tag             The model tag to serve (optional if specified in config) (default: None)

options:

  ###########################################################################################

  --aggregate-engine-logging
                        Log aggregate rather than per-engine statistics when using data parallelism. (default: False)
  含义: 在启用数据并行(Data Parallelism, DP)时, 将多个推理引擎(Engine)各自的统计信息合并为一条日志进行汇总输出, 而不是每个引擎独立打印.
  使用方法: 直接附加在启动命令中. 例如, 在两路 DP 的实例上:
    ```bash
    vllm serve <model_path> --dp-size 2 --aggregate-engine-logging
    ```
  使用场景: 高并发多卡/多节点分布式部署. 在未开启该参数时(默认 `False`), 每个 GPU 推理引擎都会高频打印自己的吞吐量、KVCache 占用率、队列长度等, 在多卡多实例部署下会导致终端日志严重"刷屏"并增加磁盘 I/O. 开启后, 可获得整洁的、反映整个集群服务水平的聚合指标, 便于接入 ELK、Grafana Loki 等集中式日志管理系统.

  ###########################################################################################

  --api-server-count API_SERVER_COUNT, -asc API_SERVER_COUNT
                        How many API server processes to run. Defaults to data_parallel_size if not specified. (default: None)
  含义: 启动多少个并行的 API 接口服务进程(FastAPI / Uvicorn 进程). 若不指定, 默认会匹配 `data_parallel_size`.
  使用方法: 指定整型数值:
    ```bash
    vllm serve <model_path> --api-server-count 4
    ```
  使用场景: 超高 QPS(每秒请求数)场景. 由于 Python 存在全局解释器锁(GIL)以及单线程事件循环(Event Loop)的性能上限, 当外部并发网络请求非常多时, 单个 FastAPI 进程会因为忙于处理网络 I/O、HTTP 协议编解码、JSON 序列化/反序列化等 CPU 密集任务, 进而导致 GPU 处于等待(Starvation)状态. 通过设置多进程, 可以将这部分网络负载分摊到多个 API Server 进程中, 后端则统一共享 GPU 推理引擎.

  ###########################################################################################

  --config CONFIG       Read CLI options from a config file. Must be a YAML with the following options: https://docs.vllm.ai/en/latest/configuration/serve_args.html (default:
                        None)
  含义: 通过读取一个 YAML 配置文件来替代命令行中漫长的 CLI 参数.
  使用方法:
    ```bash
    vllm serve --config my_serve_config.yaml
    ```
  使用场景: 生产环境自动化部署与基础设施即代码 (IaC). 当生产环境所需的参数非常多(如需要精细配置 Tensor Parallel、Pipeline Parallel、KV Cache 显存比例、Speculative Decoding 投机模型、多卡配置等)时, 将参数硬编码在 Shell 脚本中不便维护. 使用 YAML 配置文件不仅结构清晰, 还可以将其作为 K8s 中的 `ConfigMap` 进行挂载和版本控制, 非常适合 Docker 化部署.

  ###########################################################################################

  --disable-log-stats   Disable logging statistics. (default: False)
  含义: 禁用 vLLM 周期性输出的推理指标统计日志(即不打印当前 running/swapped/pending 的请求数、系统吞吐量等).
  使用方法:
    ```bash
    vllm serve <model_path> --disable-log-stats
    ```
  使用场景: 极致性能调优或精简生产日志. 如果您在生产中已经配置了 Prometheus + Grafana 等监控外设(vLLM 会通过暴露 `/metrics` 端口来采集指标), 此时控制台的文本指标日志即属于重复打印, 关闭它可以减少不必要的 CPU 和磁盘 I/O 开销, 使控制台日志更干净.

  ###########################################################################################

  --enable-log-requests, --no-enable-log-requests
                        Enable logging request information, dependent on log level:
                        - INFO: Request ID, parameters and LoRA request.
                        - DEBUG: Prompt inputs (e.g: text, token IDs). You can set the minimum log level via `VLLM_LOGGING_LEVEL`. (default: False)
  含义: 控制是否记录每个请求的详细日志.
      在 `INFO` 日志级别下: 记录 Request ID、采样参数(如 Temperature)以及 LoRA 请求信息.
      在 `DEBUG` 日志级别下: 会进一步打印提示词(Prompt)文本、Token IDs 等.
  使用方法:
    ```bash
    vllm serve <model_path> --enable-log-requests
    ```
  使用场景: 开发、测试与问题排查. 当模型在测试中出现生成异常、格式混乱或生成超时时, 开启此参数可以追踪到具体的请求内容; 但在生产环境或涉及强隐私保护的业务中, 应当保持默认关闭(`False`), 以防敏感的用户对话数据被泄露在日志系统中.

  ###########################################################################################

  --fail-on-environ-validation, --no-fail-on-environ-validation
                        If set, the engine will raise an error if environment validation fails. (default: False)
  含义: 决定在初始化阶段, 如果环境验证(例如 CUDA/PyTorch 版本、驱动、显存预估或 NCCL 配置等)未能完全通过, 是否立刻终止服务并报错退出.
  使用方法:
    ```bash
    vllm serve <model_path> --fail-on-environ-validation
    ```
  使用场景: 生产级弹性伸缩(K8s HPA)或分布式多卡集群. 默认配置(`False`)下, 环境即使存在非致命性不匹配, vLLM 也会尝试继续加载运行, 这可能导致在推理到一半时发生硬件或 NCCL 崩溃. 在严格的生产集群里, 推荐开启此选项(Fail-fast 机制). 若某台机器的软硬件环境有潜在问题, 让它在启动阶段立刻报错退出, 这可以方便 K8s 及时捕捉到容器的 `CrashLoopBackOff`, 从而自动重启、下线或重新调度, 避免"带病上岗".

  ###########################################################################################

  --gdn-prefill-backend {flashinfer,triton,cutedsl}
                        Select GDN prefill backend. (default: None)
  含义: 专门用于指定带有 GDN (Gated Decoupled Network / Gated Attention 混合架构模型, 如新型的 Mamba 或某些 Linear Attention 混合模型中涉及的 GDN 算子) 的 Prefill(预填充)阶段计算后端.
  使用方法:
    ```bash
    vllm serve <model_path> --gdn-prefill-backend flashinfer
    ```
  使用场景: 运行特定新型混合架构模型(如 Qwen2.5-Mamba, Jamba 等混合网络). 这些模型不同于纯 Transformer 的注意力机制, 包含特殊的 GDN 线性注意力算子.
      `flashinfer`: 一般情况下在支持的 GPU 硬件上能提供极高的性能.
      `triton`: 在跨平台或需要调试算子时具备更好的通用性.
      如果不手动指定(默认 `None`), vLLM 会根据当前显卡架构和驱动情况自动做出最优匹配.

  ###########################################################################################

  --grpc                Launch a gRPC server instead of the HTTP OpenAI-compatible server. Requires: pip install vllm[grpc]. (default: False)
  含义: 启动一个 gRPC 服务器来替代默认的、兼容 OpenAI 的 HTTP/JSON 接口服务器. 使用前需通过 `pip install vllm[grpc]` 安装依赖.
  使用方法:
    ```bash
    vllm serve <model_path> --grpc
    ```
  使用场景: 微服务架构的内部通信. 如果您的 LLM 服务是作为公司内部的一个微服务节点运行, 且调用方(如网关、中台应用)同样支持 gRPC, 使用 gRPC 可以大幅降低 HTTP 协议栈带来的网络延迟和 CPU 编解码开销, 特别是在高并发的流式传输(Streaming)中, gRPC 基于 HTTP/2 的双向流会比 Server-Sent Events (SSE) 更具效率与连接稳定性.

  ###########################################################################################

  --headless            Run in headless mode. See multi-node data parallel documentation for more details. (default: False)
  含义: 以"无头模式"运行, 专用于多节点分布式计算.
  使用方法:
    ```bash
    vllm serve <model_path> --headless
    ```
  使用场景: 多机多卡分布式部署(如 Multi-node Tensor/Pipeline Parallel 或 Multi-node DP). 在这种分布式架构中, 我们只需要 Master 节点(主节点)对外暴露 Web 服务端口并接收外部流量, 而处于其他节点(Worker 节点)上的推理实例则不需要开启 API 端口. 在 Worker 节点上启动 vLLM 时附带 `--headless`, 能确保它们仅加入底层的通信组(如 Ray、NCCL 等)参与计算, 而不对外暴露 API 服务.

  ###########################################################################################

  --shutdown-timeout SHUTDOWN_TIMEOUT
                        Shutdown timeout in seconds. 0 = abort, >0 = wait. (default: 0)
  含义: 设置服务器在收到关闭信号(如 SIGTERM / SIGINT)后, 优雅关闭(Graceful Shutdown)的等待超时时间.
      设置为 `0`: 立即中止(abort), 正在处理中的请求直接被截断中断.
      设置为 `>0`: 服务会停止接收新请求, 并等待最多 N 秒以让当前队列中正在生成的请求输出完毕.
  使用方法:
    ```bash
    vllm serve <model_path> --shutdown-timeout 30
    ```
  使用场景: 高可用服务的滚动更新或容器重新调度. 在 Kubernetes 中更新模型版本或重启 Pod 时, K8s 会先向容器发送 `SIGTERM`. 若将此值设为 30 或 60 秒(并匹配 K8s 的 `terminationGracePeriodSeconds`), 能够保证已经在生成回答的用户不会遇到连接突然被中断的窘境, 大幅提升客户端的用户体验.

  ###########################################################################################

  -h, --help            show this help message and exit

  ###########################################################################################

Frontend:
  Arguments for the OpenAI-compatible frontend server.

  ###########################################################################################

  --allow-credentials, --no-allow-credentials
                        Allow credentials. (default: False)
  含义: 是否允许客户端在跨域请求中携带 Credentials(如 Cookie、HTTP 认证信息等).
  使用方法: 默认 `False`. 若需要开启: `--allow-credentials`.
  使用场景: 当您的 Web 前端与 vLLM 服务部署在不同域名下, 且前端需要跨域发送 Session Cookie 或特定的安全凭证时使用.

  ###########################################################################################

  --allowed-headers ALLOWED_HEADERS
                        Allowed headers. (default: ['*'])
  --allowed-methods ALLOWED_METHODS
                        Allowed methods. (default: ['*'])
  --allowed-origins ALLOWED_ORIGINS
                        Allowed origins. (default: ['*'])
  含义: 配置跨域资源共享(CORS)的白名单. 分别对应允许的 HTTP 请求头、请求方法(如 POST, GET, OPTIONS)以及允许访问的源域名.
  使用方法:
    ```bash
    # 仅允许来自 mydomain.com 的 POST 请求
    --allowed-origins "https://mydomain.com" --allowed-methods "POST" --allowed-headers "Content-Type,Authorization"
    ```
  使用场景: Web 应用前端直接调用后端 vLLM. 在生产环境中, 出于安全考虑, 强烈建议将默认的 `['*']`(允许任意来源)修改为具体的业务域名, 以防止跨站脚本(XSS)或恶意第三方调用.

  ###########################################################################################

  --api-key API_KEY [API_KEY ...]
                        If provided, the server will require one of these keys to be presented in the header. (default: None)
  含义: 为 OpenAI 兼容接口设置访问密钥.
  使用方法: `--api-key my_secret_token_123`
  使用场景: 当服务直接暴露在公网, 或者在多租户平台中需要进行基础的身份鉴权时.
  含义: 为 vLLM 服务配置一个或多个 API Key. 设置后, 客户端请求必须在 Header 中携带 `Authorization: Bearer <your_key>` 才能通过验证.
  使用方法:
    ```bash
    --api-key sk-vllm-secret-123 sk-another-key
    ```
  使用场景: 简单鉴权与多租户隔离. 在没有部署复杂 API 网关的中小型企业内网或测试环境, 可以使用该参数对不同业务团队发放不同的 key, 从而低成本地实现基本的访问权限控制.

  ###########################################################################################

  --chat-template CHAT_TEMPLATE
  --chat-template-content-format {auto,openai,string}
  含义:
      `--chat-template`: 指向外部 Jinja2 模板文件的路径, 或直接传入 Jinja2 字符串.
      `--chat-template-content-format` (`auto`, `openai`, `string`): 控制传入的 messages 列表内容的解析格式.
      `--default-chat-template-kwargs`: 用于向 Jinja2 模板渲染器传递全局默认参数(JSON 格式).
  使用方法:
    ```bash
    --chat-template ./my_custom_template.jinja --default-chat-template-kwargs '{"add_generation_prompt": true}'
    ```
  使用场景: 微调模型适配. 当您部署一个非主流的开源微调模型, 而其 HuggingFace 配置文件中缺失 `chat_template` 时, 可以通过此参数强行指定标准的 Llama-3、Qwen 或自定义模板, 避免生成格式崩塌.

  ###########################################################################################

  --data-parallel-supervisor-port DATA_PARALLEL_SUPERVISOR_PORT
                        HTTP port for aggregated health endpoints in multi-port external LB mode. (default: 9256)
  含义:
      `--data-parallel-supervisor-port`: 汇总健康状况端点的 HTTP 端口(默认 9256).
      `--dp-supervisor-probe...`: 用于配置监管器对子进程(各引擎)健康探针的检测间隔、超时和重试失败阈值.
  使用场景: 多卡 Data Parallel (DP) 生产集群集成. 在采用多端口外部负载均衡的复杂多卡部署中, 这组参数通过健康检查监管器统一协调所有引擎的状态. 外部 LB(如 F5、Nginx 或 K8s Readiness Probe)可以直接探测 9256 端口, 当任意一个子卡引擎发生 OOM 或死锁达到阈值时, 监管器会快速对外报告 unhealthy, 实现流量平滑切走.

  ###########################################################################################

  --default-chat-template-kwargs DEFAULT_CHAT_TEMPLATE_KWARGS
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)
  含义:
      `--chat-template`: 指向外部 Jinja2 模板文件的路径, 或直接传入 Jinja2 字符串.
      `--chat-template-content-format` (`auto`, `openai`, `string`): 控制传入的 messages 列表内容的解析格式.
      `--default-chat-template-kwargs`: 用于向 Jinja2 模板渲染器传递全局默认参数(JSON 格式).
  使用方法:
    ```bash
    --chat-template ./my_custom_template.jinja --default-chat-template-kwargs '{"add_generation_prompt": true}'
    ```
  使用场景: 微调模型适配. 当您部署一个非主流的开源微调模型, 而其 HuggingFace 配置文件中缺失 `chat_template` 时, 可以通过此参数强行指定标准的 Llama-3、Qwen 或自定义模板, 避免生成格式崩塌.

  ###########################################################################################

  --disable-access-log-for-endpoints DISABLE_ACCESS_LOG_FOR_ENDPOINTS
                        Comma-separated list of endpoint paths to exclude from uvicorn access logs. This is useful to reduce log noise from high-frequency endpoints like
                        health checks. Example: "/health,/metrics,/ping". When set, access logs for requests to these paths will be suppressed while keeping logs for other
                        endpoints. (default: None)
  含义: 指定一组排除在 Uvicorn 访问日志之外的 API 路径.
  使用方法: `--disable-access-log-for-endpoints "/health,/metrics"`
  使用场景: 容器云健康检查降噪. 在 Kubernetes 中, Liveness 和 Readiness 探针可能每隔 2 秒就请求一次 `/health`, 这会导致容器日志中充斥大量的 `GET /health 200 OK`, 严重干扰对真实业务请求日志的排查. 配置此项可实现日志清净.

  ###########################################################################################

  --disable-fastapi-docs, --no-disable-fastapi-docs
                        Disable FastAPI's OpenAPI schema, Swagger UI, and ReDoc endpoint. (default: False)
  含义:
      `--disable-fastapi-docs`: 禁用默认生成的 `/docs` (Swagger UI) 和 `/redoc` 页面.
      `--enable-offline-docs`: 允许在离线/无公网环境中使用 Swagger 页面(内部打包了必需的静态资源 JS/CSS 文件).
  使用场景: 生产环境合规要求. 建议在生产环境通过 `--disable-fastapi-docs` 关闭文档入口, 防止外部对系统 API 结构进行扫描; 如果是专网隔离环境(Air-gapped), 则利用 `--enable-offline-docs` 保持调试文档的可用性.

  ###########################################################################################

  --disable-uvicorn-access-log, --no-disable-uvicorn-access-log
                        Disable uvicorn access log. (default: False)
  含义: 用于微调 FastAPI 的基础 Web 引擎(Uvicorn)和 Python Logging 日志系统.
  使用场景: 极致高并发下, Uvicorn 打印每条请求的磁盘 I/O 可能会成为瓶颈, 可以通过 `--disable-uvicorn-access-log` 关闭.

  ###########################################################################################

  --dp-supervisor-probe-failure-threshold DP_SUPERVISOR_PROBE_FAILURE_THRESHOLD
                        Number of consecutive connection-error retries before a child health probe is declared failed in multi-port external LB mode. (default: 3)
  --dp-supervisor-probe-interval-s DP_SUPERVISOR_PROBE_INTERVAL_S
                        Seconds between aggregated health probes in multi-port external LB mode. (default: 5.0)
  --dp-supervisor-probe-timeout-s DP_SUPERVISOR_PROBE_TIMEOUT_S
                        Seconds to wait between retries when a child health probe fails with a connection error in multi-port external LB mode. (default: 5.0)
  含义:
      `--data-parallel-supervisor-port`: 汇总健康状况端点的 HTTP 端口(默认 9256).
      `--dp-supervisor-probe...`: 用于配置监管器对子进程(各引擎)健康探针的检测间隔、超时和重试失败阈值.
  使用场景: 多卡 Data Parallel (DP) 生产集群集成. 在采用多端口外部负载均衡的复杂多卡部署中, 这组参数通过健康检查监管器统一协调所有引擎的状态. 外部 LB(如 F5、Nginx 或 K8s Readiness Probe)可以直接探测 9256 端口, 当任意一个子卡引擎发生 OOM 或死锁达到阈值时, 监管器会快速对外报告 unhealthy, 实现流量平滑切走.

  ###########################################################################################

  --enable-auto-tool-choice, --no-enable-auto-tool-choice

  ###########################################################################################

  --enable-flash-late-interaction, --no-enable-flash-late-interaction
                        If set, run pooling score MaxSim on GPU in the API server process. Can significantly improve late-interaction scoring performance. (default: True)
  含义: 是否在 API 服务器进程的 GPU 上运行多向量 Pooling Score MaxSim 计算(默认 `True`).
  使用场景: 基于 ColBERT 架构的高性能检索/重排(Rerank)服务. 当使用 vLLM 部署 late-interaction 多向量检索模型(如 BGE-M3)时, 开启该参数可以直接在 GPU 上高效完成 MaxSim 打分, 相比传统的 CPU 串行处理, 能大幅降低向量检索与重排阶段的延迟.

  ###########################################################################################

  --enable-force-include-usage, --no-enable-force-include-usage
  含义: 强制在流式响应(SSE)的最后一帧、甚至是中途出错的帧中, 都带上 `usage`(Token 消耗统计)字段.
  使用场景: 兼容严格的第三方 SDK. 某些语言(如 Java/Go)的第三方 OpenAI SDK 在解析 Streaming 响应时, 如果某一帧缺少 `usage` 字段就会抛出空指针或解析异常. 开启该选项可提供更好的鲁棒性.

  ###########################################################################################

  --enable-log-deltas, --no-enable-log-deltas
  --enable-log-outputs, --no-enable-log-outputs
  含义:
      `--enable-log-deltas`: 打印流式(Streaming)输出时每一次产出的 Token 增量.
      `--enable-log-outputs`: 在控制台日志中打印最终生成的完整文本.
      `--max-log-len`: 限制日志中单次打印 Prompt 和 Response 的最大字符长度.
  使用场景: 当您在处理长文本生成(例如 32K 上下文)时, 完整输出会迅速撑爆日志盘或导致控制台卡死, 限制 `--max-log-len 512` 可以在保留必要调试信息的同时, 极大地保护宿主机磁盘空间.

  ###########################################################################################

  --enable-offline-docs, --no-enable-offline-docs
                        Enable offline FastAPI documentation for air-gapped environments. Uses vendored static assets bundled with vLLM. (default: False)
  含义:
      `--disable-fastapi-docs`: 禁用默认生成的 `/docs` (Swagger UI) 和 `/redoc` 页面.
      `--enable-offline-docs`: 允许在离线/无公网环境中使用 Swagger 页面(内部打包了必需的静态资源 JS/CSS 文件).
  使用场景: 生产环境合规要求. 建议在生产环境通过 `--disable-fastapi-docs` 关闭文档入口, 防止外部对系统 API 结构进行扫描; 如果是专网隔离环境(Air-gapped), 则利用 `--enable-offline-docs` 保持调试文档的可用性.

  ###########################################################################################

  --enable-prompt-tokens-details, --no-enable-prompt-tokens-details
  含义:
      `--enable-prompt-tokens-details`: 在响应中额外返回 prompt tokens 的 Logprobs、命中缓存情况等深度细节.
      `--return-tokens-as-token-ids`: 让 API 返回底层的 Token ID 数组而不是解码后的文本字符串.
  使用场景: 用于构建高级 LLM 开发者工具、调试 Prompt 缓存命中率(Prompt Cache Debugging)或开发高度定制化的流式客户端.

  ###########################################################################################

  --enable-request-id-headers, --no-enable-request-id-headers
                        If specified, API server will add X-Request-Id header to responses. (default: False)

  ###########################################################################################

  --enable-server-load-tracking, --no-enable-server-load-tracking
  含义:
      `--enable-tokenizer-info-endpoint`: 暴露特殊的端点(如获取词表大小、Tokenizer 配置).
      `--enable-server-load-tracking`: 允许接口暴露当前的队列压力和 GPU 负载详情.
  使用场景: 构建智能负载均衡与自适应前端. 前端应用(如 Chat UI)可以先请求 Tokenizer 信息以便在本地进行精确的 Token 计算; 网关层则可以通过跟踪 Server Load 来实现动态过载保护.

  ###########################################################################################

  --enable-ssl-refresh, --no-enable-ssl-refresh
                        Refresh SSL Context when SSL certificate files change (default: False)
  `--ssl-certfile` / `--ssl-keyfile`: SSL 证书与私钥路径.
  `--ssl-ca-certs` / `--ssl-cert-reqs`: 配置 CA 证书及是否强制客户端证书验证(0 表示不需要, 1 表示可选, 2 表示强制).
  `--ssl-ciphers`: 指定允许的加密套件.
  `--enable-ssl-refresh`: 当检测到证书文件更新时, 自动热重载 SSL 上下文.
  使用场景: 双向 TLS (mTLS) 零信任架构. 在安全性要求极高的金融或政企网络中, 通常不允许明文 HTTP 传输. 通过上述参数可以使 vLLM 直接支持 HTTPS, 配合 `--enable-ssl-refresh` 可实现证书的无缝热更新, 避免因证书过期更换导致服务中断.

  ###########################################################################################

  --enable-tokenizer-info-endpoint, --no-enable-tokenizer-info-endpoint
  含义:
      `--enable-tokenizer-info-endpoint`: 暴露特殊的端点(如获取词表大小、Tokenizer 配置).
      `--enable-server-load-tracking`: 允许接口暴露当前的队列压力和 GPU 负载详情.
  使用场景: 构建智能负载均衡与自适应前端. 前端应用(如 Chat UI)可以先请求 Tokenizer 信息以便在本地进行精确的 Token 计算; 网关层则可以通过跟踪 Server Load 来实现动态过载保护.

  ###########################################################################################

  --exclude-tools-when-tool-choice-none, --no-exclude-tools-when-tool-choice-none
  含义: 当客户端显式请求不使用工具(`tool_choice: "none"`)时, 在组装 System Prompt 时强制将 tools 定义剔除.
  使用场景: 节省上下文开销. 某些 Agent 框架默认会把长篇累牍的 Tool Schema 全量塞入请求中. 当当前轮次不需要调用工具时, 开启该参数可以显著节省 Prompt Token 开销, 加速推理.

  ###########################################################################################

  --fingerprint-mode {custom,full,hash,none}
  --fingerprint-value FINGERPRINT_VALUE
  含义: 配置返回的系统指纹(`system_fingerprint`, 兼容 OpenAI), 可选择哈希模式(`hash`)、自定义静态值(`custom`)等.
  使用场景: 在进行 A/B 测试或灰度发布时, 使客户端能够通过指纹来追踪当前请求实际上是由哪一个微调模型版本、或者是哪一个特定的 GPU 实例架构处理的, 以此确保生成结果的确定性归属.

  ###########################################################################################

  --h11-max-header-count H11_MAX_HEADER_COUNT
                        Maximum number of HTTP headers allowed in a request for h11 parser. Helps mitigate header abuse. Default: 256. (default: 256)
  --h11-max-incomplete-event-size H11_MAX_INCOMPLETE_EVENT_SIZE
                        Maximum size (bytes) of an incomplete HTTP event (header or body) for h11 parser. Helps mitigate header abuse. Default: 4194304 (4 MB). (default:
                        4194304)
  含义: 配置 h11 HTTP 解析器的限制. 分别限制请求中允许的最大 Header 数量以及单个未完成 HTTP 事件(如巨型 Header 或超大 Body)的最大字节数(默认 4MB).
  使用方法: 根据需要调大或保持默认: `--h11-max-header-count 512`.
  使用场景: 防范 HTTP 慢速攻击(Slowloris)与畸形包注入. 在高并发且直接暴露在外部网络的边缘节点上, 通过调低限制可提升抗攻击能力; 相反, 如果业务系统需要传输极大的自定义 Header(如包含复杂的 JWT Token), 则需要适当调大.

  ###########################################################################################

  --host HOST           Host name. (default: None)
  含义: 服务监听的 IP 地址和端口.
  使用方法: `--host 0.0.0.0 --port 8000`
  使用场景: 在 Docker 容器或 Kubernetes Pod 中运行时, 通常需要设为 `0.0.0.0` 以便容器外部能够访问服务.
  含义:
      `--host`: 绑定的网卡 IP 地址.
      `--port`: 监听的端口.
      `--root-path`: 当服务处于基于路径转发的逆向代理(如 Nginx, Traefik, K8s Ingress)后方时, 需填入反代路径(如 `/vllm-service`).
  使用方法:
    ```bash
    --host 0.0.0.0 --port 8000 --root-path /vllm-api
    ```
  使用场景: 配合微服务网关路由. `--root-path` 可以确保 FastAPI 内部生成的 Swagger 文档、URL 重定向等能够正确识别前缀, 避免路由丢失.

  ###########################################################################################

  --log-config-file LOG_CONFIG_FILE
  --log-error-stack, --no-log-error-stack
  含义: 用于微调 FastAPI 的基础 Web 引擎(Uvicorn)和 Python Logging 日志系统.
  使用场景: 极致高并发下, Uvicorn 打印每条请求的磁盘 I/O 可能会成为瓶颈, 可以通过 `--disable-uvicorn-access-log` 关闭.

  ###########################################################################################

  --lora-modules LORA_MODULES [LORA_MODULES ...]
  含义: 在启动时预加载一个或多个 LoRA 微调适配器, 并赋予唯一名称.
  使用方法:
    ```bash
    --lora-modules task-translate=/models/lora_trans task-summary=/models/lora_sum
    ```
  使用场景: 多任务多租户共用单张显卡. 您只需要在底层加载一个庞大的 Base Model(如 Llama-3-70B), 然后通过此参数预挂载多个轻量级的 LoRA. 客户端只需在请求中通过 `"model": "task-translate"` 即可实时调度不同的微调模型, 极大地节省了显存开销与冷启动时间.

  ###########################################################################################

  --max-log-len MAX_LOG_LEN
  含义:
      `--enable-log-deltas`: 打印流式(Streaming)输出时每一次产出的 Token 增量.
      `--enable-log-outputs`: 在控制台日志中打印最终生成的完整文本.
      `--max-log-len`: 限制日志中单次打印 Prompt 和 Response 的最大字符长度.
  使用场景: 当您在处理长文本生成(例如 32K 上下文)时, 完整输出会迅速撑爆日志盘或导致控制台卡死, 限制 `--max-log-len 512` 可以在保留必要调试信息的同时, 极大地保护宿主机磁盘空间.

  ###########################################################################################

  --middleware MIDDLEWARE
                        Additional ASGI middleware to apply to the app. We accept multiple
                        --middleware arguments. The value should be an import path. If a function is provided, vLLM will add it to the server using `@app.middleware('http')`.
                        If a class is provided, vLLM will add it to the server using `app.add_middleware()`. (default: [])
  含义: 向 FastAPI 实例注册自定义的 ASGI 中间件.
  使用方法: 传入 Python 类的导入路径, 例如: `--middleware my_module.RateLimitMiddleware`.
  使用场景: 无缝嵌入业务逻辑. 可用于在 vLLM 前端网关层快速实现自定义的: 请求审计、基于令牌的精细化速率限制(Rate Limiting)、多租户计量计费等.

  ###########################################################################################

  --port PORT           Port number. (default: 8000)
  含义: 服务监听的 IP 地址和端口.
  使用方法: `--host 0.0.0.0 --port 8000`
  使用场景: 在 Docker 容器或 Kubernetes Pod 中运行时, 通常需要设为 `0.0.0.0` 以便容器外部能够访问服务.
  含义: 服务监听的 IP 地址和端口.
  使用方法: `--host 0.0.0.0 --port 8000`
  使用场景: 在 Docker 容器或 Kubernetes Pod 中运行时, 通常需要设为 `0.0.0.0` 以便容器外部能够访问服务.
  含义:
      `--host`: 绑定的网卡 IP 地址.
      `--port`: 监听的端口.
      `--root-path`: 当服务处于基于路径转发的逆向代理(如 Nginx, Traefik, K8s Ingress)后方时, 需填入反代路径(如 `/vllm-service`).
  使用方法:
    ```bash
    --host 0.0.0.0 --port 8000 --root-path /vllm-api
    ```
  使用场景: 配合微服务网关路由. `--root-path` 可以确保 FastAPI 内部生成的 Swagger 文档、URL 重定向等能够正确识别前缀, 避免路由丢失.

  ###########################################################################################

  --response-role RESPONSE_ROLE
  含义: 在 API 返回的 Chat Completion 响应中, 指定助理角色的名称(默认为 `assistant`).
  使用场景: 兼容老旧的下游自研 Agent 系统, 有些老系统硬编码只识别 `bot` 或 `AI` 作为回复角色.

  ###########################################################################################

  --return-tokens-as-token-ids, --no-return-tokens-as-token-ids
  含义:
      `--enable-prompt-tokens-details`: 在响应中额外返回 prompt tokens 的 Logprobs、命中缓存情况等深度细节.
      `--return-tokens-as-token-ids`: 让 API 返回底层的 Token ID 数组而不是解码后的文本字符串.
  使用场景: 用于构建高级 LLM 开发者工具、调试 Prompt 缓存命中率(Prompt Cache Debugging)或开发高度定制化的流式客户端.

  ###########################################################################################

  --root-path ROOT_PATH
                        FastAPI root_path when app is behind a path based routing proxy. (default: None)
  含义:
      `--host`: 绑定的网卡 IP 地址.
      `--port`: 监听的端口.
      `--root-path`: 当服务处于基于路径转发的逆向代理(如 Nginx, Traefik, K8s Ingress)后方时, 需填入反代路径(如 `/vllm-service`).
  使用方法:
    ```bash
    --host 0.0.0.0 --port 8000 --root-path /vllm-api
    ```
  使用场景: 配合微服务网关路由. `--root-path` 可以确保 FastAPI 内部生成的 Swagger 文档、URL 重定向等能够正确识别前缀, 避免路由丢失.

  ###########################################################################################

  --ssl-ca-certs SSL_CA_CERTS
                        The CA certificates file. (default: None)
  --ssl-cert-reqs SSL_CERT_REQS
                        Whether client certificate is required (see stdlib ssl module's). (default: 0)
  --ssl-certfile SSL_CERTFILE
                        The file path to the SSL cert file. (default: None)
  --ssl-ciphers SSL_CIPHERS
                        SSL cipher suites for HTTPS (TLS 1.2 and below only). Example: 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305' (default: None)
  --ssl-keyfile SSL_KEYFILE
                        The file path to the SSL key file. (default: None)
  `--ssl-certfile` / `--ssl-keyfile`: SSL 证书与私钥路径.
  `--ssl-ca-certs` / `--ssl-cert-reqs`: 配置 CA 证书及是否强制客户端证书验证(0 表示不需要, 1 表示可选, 2 表示强制).
  `--ssl-ciphers`: 指定允许的加密套件.
  `--enable-ssl-refresh`: 当检测到证书文件更新时, 自动热重载 SSL 上下文.
  使用场景: 双向 TLS (mTLS) 零信任架构. 在安全性要求极高的金融或政企网络中, 通常不允许明文 HTTP 传输. 通过上述参数可以使 vLLM 直接支持 HTTPS, 配合 `--enable-ssl-refresh` 可实现证书的无缝热更新, 避免因证书过期更换导致服务中断.

  ###########################################################################################

  --tokens-only, --no-tokens-only
  含义:
      `--enable-prompt-tokens-details`: 在响应中额外返回 prompt tokens 的 Logprobs、命中缓存情况等深度细节.
      `--return-tokens-as-token-ids`: 让 API 返回底层的 Token ID 数组而不是解码后的文本字符串.
  使用场景: 用于构建高级 LLM 开发者工具、调试 Prompt 缓存命中率(Prompt Cache Debugging)或开发高度定制化的流式客户端.

  ###########################################################################################

  --tool-call-parser {apertus,cohere_command3,cohere_command4,deepseek_v3,deepseek_v31,deepseek_v32,deepseek_v4,ernie45,functiongemma,gemma4,gigachat3,glm45,glm47,granite,granite-20b-fc,granite4,hermes,hunyuan_a13b,hy_v3,internlm,jamba,kimi_k2,lfm2,llama3_json,llama4_json,llama4_pythonic,longcat,mimo,minimax,minimax_m2,mistral,olmo3,openai,phi4_mini_json,poolside_v1,pythonic,qwen3_coder,qwen3_xml,seed_oss,step3,step3p5,xlam} or name registered in --tool-parser-plugin
  含义: 指定工具调用(Tool Calling / Function Calling)的解析器.
  使用方法: `--tool-call-parser qwen3_xml` 或 `--tool-call-parser deepseek_v3`
  使用场景: 构建 Agent(智能体)工作流时, 确保 API 能够准确将模型的文本输出解析为结构化的 JSON/XML 工具调用参数.
  含义: 指定解析模型输出的工具调用格式(例如 `deepseek_v3`、`llama3_json`、`openai`、`qwen3_xml` 等).
  使用场景: 多模型 Agent 统一网关. 不同的开源模型(如 DeepSeek-V3 或 Qwen2.5)输出 Tool Call 的原始文本格式各不相同. 通过该参数, vLLM 会在前端将特定模型的私有工具输出, 自适应地转换、包装成标准的 OpenAI JSON 格式输出, 使下游 Agent 框架(如 LangChain、AutoGPT)无需做任何代码修改.

  ###########################################################################################

  --tool-parser-plugin TOOL_PARSER_PLUGIN
  --tool-server TOOL_SERVER
  含义:
      `--tool-parser-plugin`: 允许注册自定义的解析插件来提取工具调用.
      `--tool-server`: 绑定一个外部的工具执行服务器.
  使用场景: 专门用于企业内部私有定义的闭源 Agent 工具流解析.

  ###########################################################################################

  --trust-request-chat-template, --no-trust-request-chat-template
  含义: 是否信任并使用客户端在 API 请求体中携带的自定义 `chat_template`.
  使用方法: 默认 `False`(不信任).
  使用场景: 默认出于安全性(防范 Jinja2 模板注入攻击)考虑建议关闭. 如果是在受信任的内部实验环境中, 需要动态对比不同 Prompt 格式的生成效果, 可以临时开启.

  ###########################################################################################

  --uds UDS             Unix domain socket path. If set, host and port arguments are ignored. (default: None)
  含义: Unix Domain Socket(域套接字)路径. 若设置, 将忽略 host 和 port.
  使用方法: `--uds /tmp/vllm.sock`
  使用场景: 当同一个物理节点/容器内的前端反向代理(如 Nginx、Envoy)与 vLLM 部署在同机, 使用 UDS 传输可以绕过 TCP/IP 协议栈, 降低网络延迟并提高吞吐量.
  含义: 指定 Unix Domain Socket(UDS)的文件路径. 设置后, 将不再监听 TCP 主机和端口.
  使用方法:
    ```bash
    --uds /tmp/vllm.sock
    ```
  使用场景: 单机极速通信. 如果您的网关(如本地 Nginx 或 Sidecar 容器)与 vLLM 部署在同一台物理机或同一个 Pod 内, 通过 UDS 进行通信可以绕过 TCP/IP 协议栈的开销, 降低请求延迟并提升吞吐量, 同时天然杜绝了来自网络的外部扫描风险.

  ###########################################################################################

  --uvicorn-log-level {critical,debug,error,info,trace,warning}
                        Log level for uvicorn. (default: info)
  含义: 用于微调 FastAPI 的基础 Web 引擎(Uvicorn)和 Python Logging 日志系统.
  使用场景: 极致高并发下, Uvicorn 打印每条请求的磁盘 I/O 可能会成为瓶颈, 可以通过 `--disable-uvicorn-access-log` 关闭.

  ###########################################################################################

ModelConfig:
  Configuration for the model.

  ###########################################################################################

  --allow-deprecated-quantization, --no-allow-deprecated-quantization
                        Whether to allow deprecated quantization methods. (default: False)
  含义:
      `--quantization`: 显式指定加载的量化格式(如 `awq`, `gptq`, `fp8`, `squeezellm`, `marlin`).
      `--quantization-config`: 传递针对不同层(如线性层、MoE层)的特定量化配置.
      `--allow-deprecated-quantization`: 是否允许加载已被社区淘汰的旧版量化算法格式.
  使用方法: `--quantization awq`
  使用场景: 显存受限情况下的低成本部署. 量化可以大幅压减显存占用(如 4-bit 量化), 允许在单张 24G 显卡(如 RTX 4090)上跑原本需要 80G 显存的大模型.

  ###########################################################################################

  --allowed-local-media-path ALLOWED_LOCAL_MEDIA_PATH
                        Allowing API requests to read local images or videos from directories specified by the server file system. This is a security risk. Should only be
                        enabled in trusted environments. (default: )
  含义: 允许 API 请求直接读取服务器本地文件系统指定目录下的图像、视频等多媒体文件.
  使用方法: `--allowed-local-media-path /data/media_files/`(默认不开启)
  使用场景: 本地局域网多模态处理.
      安全警示: 此参数存在严重的安全风险(Prompt Injection 可能会使恶意用户通过提示词窥探宿主机的本地文件). 只有在完全受信任的内网或私有测试环境中, 为了避免在 HTTP 请求中传输巨大的 Base64 图片, 才建议指定可读取的安全目录.

  ###########################################################################################

  --allowed-media-domains ALLOWED_MEDIA_DOMAINS [ALLOWED_MEDIA_DOMAINS ...]
                        If set, only media URLs that belong to this domain can be used for multi-modal inputs. (default: None)
  含义: 限制多模态输入中, 允许远程下载图片或视频的域名白名单.
  使用方法: `--allowed-media-domains mycompany.com s3.amazonaws.com`
  使用场景: 防止 SSRF(服务端请求伪造)攻击. 当用户上传带图片链接的多模态请求时, vLLM 服务器会主动发起网络请求去拉取图片. 为了防止黑客利用此特性扫描内网或请求恶意服务, 建议绑定企业内网或对象存储域名.

  ###########################################################################################

  --code-revision CODE_REVISION
                        The specific revision to use for the model code on the Hugging Face Hub. It can be a branch name, a tag name, or a commit id. If unspecified, will use
                        the default version. (default: None)
  含义: 分别代表从 Hugging Face 加载模型权重和模型代码时指定的 Git 分支、Tag 或 Commit ID.
  使用方法: `--revision main --code-revision 8c3a2ef`
  使用场景: 生产版本锁死与安全审计. 防止模型作者在 HuggingFace Hub 上更新代码或权重时引入不兼容的变更, 通常在生产环境中锁死一个具体的 Commit ID.

  ###########################################################################################

  --config-format ['auto', 'hf', 'mistral']
                        The format of the model config to load:
                        - "auto" will try to load the config in hf format if available after trying to load in mistral format.
                        - "hf" will load the config in hf format.
                        - "mistral" will load the config in mistral format. (default: auto)
  含义:
      `--hf-config-path`: 单独指定要加载的 HuggingFace 配置文件(`config.json`)路径.
      `--config-format` (`auto`, `hf`, `mistral`): 读取模型配置文件的解析格式.
      `--hf-overrides`: 在启动时动态覆盖 HuggingFace 的配置参数(JSON 字符串).
  使用方法: `--hf-overrides '{"max_position_embeddings": 8192}'`
  使用场景: 动态微调运行期配置. 当模型配置文件中存在错漏, 或者需要临时扩展其 context 长度(如 `max_position_embeddings`)进行极限测试时, 无需手动修改磁盘上的 `config.json` 文件.

  ###########################################################################################

  --convert {auto,classify,embed,none}
                        Convert the model using adapters defined in [vllm.model_executor.models.adapters][]. The most common use case is to adapt a text generation model to be
                        used for pooling tasks. (default: auto)
  含义: 利用特定的适配器结构, 将原本用于文本生成的模型(Causal LM)强制转换为池化任务模型(如 Embedding 嵌入模型、分类模型).
  使用场景: 在检索增强生成(RAG)系统中, 可以用同一个大模型(如 Llama3)通过该参数转换, 既作为向量数据库的 Embedding 计算服务, 又作为最终的生成服务, 实现架构层面的资源复用.

  ###########################################################################################

  --disable-cascade-attn, --no-disable-cascade-attn
                        Disable cascade attention for V1. While cascade attention does not change the mathematical correctness, disabling it could be useful for preventing
                        potential numerical issues. This defaults to True, so users must opt in to cascade attention by setting this to False. Even when this is set to False,
                        cascade attention will only be used when the heuristic tells that it's beneficial. (default: True)
  含义: 是否禁用 V1 引擎中的级联注意力机制(Cascade Attention). 默认 `True`, 即不开启.
  使用场景: 级联注意力可以在某些长序列场景下提升推理吞吐, 但可能在一些特定数值精度敏感的模型中引入微小的数值误差. 出于安全和数学准确性考虑, 默认保持禁用, 除非确定要在超长文本中压榨极限性能.

  ###########################################################################################

  --disable-sliding-window, --no-disable-sliding-window
                        Whether to disable sliding window. If True, we will disable the sliding window functionality of the model, capping to sliding window size. If the model
                        does not support sliding window, this argument is ignored. (default: False)
  含义: 是否禁用滑动窗口注意力(Sliding Window Attention).
  使用场景: 某些模型(如 Mistral)原生支持滑动窗口. 如果强行禁用它(`True`), vLLM 将采用全量 Attention 机制, 这会大幅增加显存开销, 但在某些长文本微调变体上, 禁用滑动窗口能换取更佳的生成连贯度.

  ###########################################################################################

  --dtype {auto,bfloat16,float,float16,float32,half}
                        Data type for model weights and activations:
                        - "auto" will use FP16 precision for FP32 and FP16 models, and BF16 precision for BF16 models.
                        - "half" for FP16. Recommended for AWQ quantization.
                        - "float16" is the same as "half".
                        - "bfloat16" for a balance between precision and range.
                        - "float" is shorthand for FP32 precision.
                        - "float32" for FP32 precision. (default: auto)
  含义: 权重与激活值的数值精度(`auto`, `bfloat16`, `float16` 等).
  使用方法: `--dtype bfloat16`
  使用场景:
    若 GPU 支持(安培及之后架构, 如 A100、A40、H100 等), 强烈推荐使用 `bfloat16`, 相比 `float16` 它能有效防止溢出.
    `half` / `float16` 常用于老一代 GPU(如 T4、V100)或特定的 AWQ 量化模型.
  含义: 指定模型权重和激活值的计算精度.
  使用方法: 对于 Ampere/Hopper 架构(A100, H100 等)建议使用 `--dtype bfloat16`.
  使用场景: 控制计算精度与显存开销. `bfloat16` 拥有与 `float32` 相同的指数范围, 能大幅降低数值溢出(Overflow)的风险; 而较老架构的显卡(如 V100)若不支持 BF16, 则应指定为 `float16`.

  ###########################################################################################

  --enable-cumem-allocator, --no-enable-cumem-allocator
                        Enable the custom cumem allocator to leverage advanced GPU memory allocation features such as multi-node NVLink support.
                        Sleep mode automatically enables this allocator. Only cuda and hip platforms are supported. (default: False)
  含义:
      `--enable-cumem-allocator`: 启用 vLLM 自研的高级内存分配器, 可极好支持多节点 NVLink 等高级硬件特性.
      `--enable-sleep-mode`: 启用引擎的"休眠模式"(仅支持 CUDA/HIP).
  使用场景: 大规模集群资源优化与节能. 当服务部署在大型多卡/多节点分布式环境上, 在业务低谷期(如深夜), 模型长期处于闲置状态. 配合这两个参数, vLLM 会在空闲时进入"休眠模式", 利用自定义内存分配器无感且高效地释放或缩减 GPU 显存预占, 大幅降低闲置功耗与系统开销.

  ###########################################################################################

  --enable-prompt-embeds, --no-enable-prompt-embeds
                        If `True`, enables passing text embeddings as inputs via the `prompt_embeds` key.
                        WARNING: The vLLM engine may crash if incorrect shape of embeddings is passed. Only enable this flag for trusted users! (default: False)
  含义: 是否允许客户端在请求体中直接传入预计算好的文本词向量(Prompt Embeddings), 而非原始文本字符串.
  使用方法: 默认 `False`.
  使用场景:
      安全警示: 传错向量形状(Shape)极易导致 vLLM 引擎发生致命 Crash.
      应用场景: 在客户端需要进行极其复杂的 Prompt 级预处理(如结合额外的离线检索和融合, 或在传输前对 Token 进行了混淆加密), 可以将提取好的 Embeddings 直接提交给 vLLM 加速计算.

  ###########################################################################################

  --enable-return-routed-experts, --no-enable-return-routed-experts
                        Whether to return routed experts. (default: False)
  含义: 是否返回混合专家模型(MoE)中每个 Token 路由到具体哪些专家(Experts)的信息.
  使用场景: 用于深度调试 MoE 模型(如 DeepSeek-V3 或 Mixtral), 监控在不同 Prompt 下专家负载的分布情况.

  ###########################################################################################

  --enable-sleep-mode, --no-enable-sleep-mode
                        Enable sleep mode for the engine (only cuda and hip platforms are supported). (default: False)
  含义:
      `--enable-cumem-allocator`: 启用 vLLM 自研的高级内存分配器, 可极好支持多节点 NVLink 等高级硬件特性.
      `--enable-sleep-mode`: 启用引擎的"休眠模式"(仅支持 CUDA/HIP).
  使用场景: 大规模集群资源优化与节能. 当服务部署在大型多卡/多节点分布式环境上, 在业务低谷期(如深夜), 模型长期处于闲置状态. 配合这两个参数, vLLM 会在空闲时进入"休眠模式", 利用自定义内存分配器无感且高效地释放或缩减 GPU 显存预占, 大幅降低闲置功耗与系统开销.

  ###########################################################################################

  --enforce-eager, --no-enforce-eager
                        Whether to always use eager-mode PyTorch. If True, we will disable CUDA graph and always execute the model in eager mode. If False, we will use CUDA
                        graph and eager execution in hybrid for maximal performance and flexibility. (default: False)
  含义: 强制使用 PyTorch 的 Eager 模式, 禁用 CUDA Graph.
  使用方法: `--enforce-eager`
  使用场景:
    默认推荐关闭(即使用 CUDA Graph 以获得最高性能).
    开启场景: 当由于 CUDA Graph 导致显存严重不足, 或者在使用某些包含复杂控制流的定制模型、LoRA 频繁切换导致系统频繁重构 CUDA Graph 时, 开启此项可避免编译耗时.
  含义: 是否强制始终使用 PyTorch 的 Eager 模式执行模型. 默认 `False`, 表示会使用性能更高的 CUDA Graph 进行计算.
  使用方法: 如果显存吃紧, 使用 `--enforce-eager`.
  使用场景:
      极致性能: 默认不开启(使用 CUDA Graph), 可以显著降低小 batch 尺寸下的 GPU 调度延迟, 大幅提升吞吐.
      节省显存/排查故障: CUDA Graph 需要额外预占一部分显存. 如果因显存耗尽(OOM)无法启动, 或遇到了与 CUDA Graph 相关的底层驱动 Bug, 开启此参数强制回退到 Eager 模式可以换取更稳定的运行状态.

  ###########################################################################################

  --generation-config GENERATION_CONFIG
                        The folder path to the generation config. Defaults to `"auto"`, the generation config will be loaded from model path. If set to `"vllm"`, no generation
                        config is loaded, vLLM defaults will be used. If set to a folder path, the generation config will be loaded from the specified folder path. If
                        `max_new_tokens` is specified in generation config, then it sets a server-wide limit on the number of output tokens for all requests. (default: auto)
  含义: 指定推理超参数(如 `temperature`, `top_p`)的读取配置文件或进行实时覆盖.
  使用方法: `--override-generation-config '{"temperature": 0.3, "max_new_tokens": 4096}'`
  使用场景: 在服务器级别统一给所有请求施加最高长度约束(`max_new_tokens`)或限制默认随机度, 防止某些恶意或失控的请求导致服务器超载.

  ###########################################################################################

  --hf-config-path HF_CONFIG_PATH
                        Name or path of the Hugging Face config to use. If unspecified, model name or path will be used. (default: None)
  --hf-overrides HF_OVERRIDES
                        If a dictionary, contains arguments to be forwarded to the Hugging Face config. If a callable, it is called to update the HuggingFace config. (default:
                        {})
  含义:
      `--hf-config-path`: 单独指定要加载的 HuggingFace 配置文件(`config.json`)路径.
      `--config-format` (`auto`, `hf`, `mistral`): 读取模型配置文件的解析格式.
      `--hf-overrides`: 在启动时动态覆盖 HuggingFace 的配置参数(JSON 字符串).
  使用方法: `--hf-overrides '{"max_position_embeddings": 8192}'`
  使用场景: 动态微调运行期配置. 当模型配置文件中存在错漏, 或者需要临时扩展其 context 长度(如 `max_position_embeddings`)进行极限测试时, 无需手动修改磁盘上的 `config.json` 文件.

  ###########################################################################################

  --hf-token [HF_TOKEN]
                        The token to use as HTTP bearer authorization for remote files . If `True`, will use the token generated when running `hf auth login` (stored in
                        `~/.cache/huggingface/token`). (default: None)
  含义: 用于访问远程 HuggingFace 私有仓库或受限模型(如 Llama 3 官方模型)的 Bearer Token.
  使用方法: `--hf-token hf_xxxxxxxx` 或设为 `True`(自动读取本地 cache 凭证).
  使用场景: 部署需要官方授权许可或企业内部托管在 Hugging Face 上的私有微调模型.

  ###########################################################################################

  --io-processor-plugin IO_PROCESSOR_PLUGIN
                        IOProcessor plugin name to load at model startup (default: None)
  含义: 加载自定义的 I/O 处理器插件.
  使用场景: 专门用于在模型接受输入数据(如特定格式的图像、音频或传感器原始数据)之后, 正式进入 Token 编解码之前, 进行格式转换或二次清洗.

  ###########################################################################################

  --logits-processors LOGITS_PROCESSORS [LOGITS_PROCESSORS ...]
                        One or more logits processors' fully-qualified class names or class definitions (default: None)
  --logprobs-mode {processed_logits,processed_logprobs,raw_logits,raw_logprobs}
                        Indicates the content returned in the logprobs and prompt_logprobs. Supported mode: 1) raw_logprobs, 2) processed_logprobs, 3) raw_logits, 4)
                        processed_logits. Raw means the values before applying any logit processors, like bad words. Processed means the values after applying all processors,
                        including temperature and top_k/top_p. (default: raw_logprobs)
  --max-logprobs MAX_LOGPROBS
                        Maximum number of log probabilities to return when `logprobs` is specified in `SamplingParams`. The default value comes the default for the OpenAI Chat
                        Completions API. -1 means no cap, i.e. all (output_length * vocab_size) logprobs are allowed to be returned and it may cause OOM. (default: 20)
  含义:
      `--logits-processors`: 加载自定义的 Logits 后处理器类.
      `--logprobs-mode` (`raw_logprobs`, `processed_logprobs`...): 控制返回的对数概率和概率值是应用 Logits 处理器(如温度、罚项)前(raw)还是后(processed).
      `--max-logprobs`: 控制 API 能返回的最大 logprobs 候选数量(默认 20).
  使用场景: 模型对齐研究与安全过滤. 通过加载自定义 Logits 处理器, 可以在输出前强制压制违规词、政治不正确词汇的概率(Bad Words Filtering), 或用于学术分析.

  ###########################################################################################

  --max-model-len MAX_MODEL_LEN
                        Model context length (prompt and output). If unspecified, will be automatically derived from the model config.
                        When passing via `--max-model-len`, supports k/m/g/K/M/G in human-readable format. Examples:
                        - 1k -> 1000
                        - 1K -> 1024
                        - 25.6k -> 25,600
                        - -1 or 'auto' -> Automatically choose the maximum model length that fits in GPU memory. This will use the model's maximum context length if it fits,
                        otherwise it will find the largest length that can be accommodated.
                        Parse human-readable integers like '1k', '2M', etc. Including decimal values with decimal multipliers. Also accepts -1 or 'auto' as a special value for
                        auto-detection.
                            Examples:
                            - '1k' -> 1,000
                            - '1K' -> 1,024
                            - '25.6k' -> 25,600
                            - '-1' or 'auto' -> -1 (special value for auto-detection) (default: None)
  含义: 限制模型的最大上下文长度(包含 Prompt 和输出).
  使用方法: `--max-model-len 8k` 或 `--max-model-len 8192`
  使用场景: 防止因过长的请求导致显存溢出(OOM). 当服务的模型默认支持长上下文(如 32K 或 128K), 但实际业务只需要 8K 且显存紧张时, 可以通过此参数强制截断.
  含义: 模型可处理的最大上下文长度(Prompt + Response ). 支持 `128k` 等人性化简写, 以及 `auto` 自动检测.
  使用方法: `--max-model-len 32K` 或 `--max-model-len auto`
  使用场景: 控制 KV Cache 显存占用. 模型的上下文越长, KV Cache 占用的显存呈线性甚至几何级上升. 如果显存溢出, 可以通过调小此参数(例如从 128k 限制到 16k)来释放显存, 允许承载更大的并发 Batch 数量.

  ###########################################################################################

  --model MODEL         Name or path of the Hugging Face model to use. It is also used as the content for `model_name` tag in metrics output when `served_model_name` is not
                        specified. (default: Qwen/Qwen3-0.6B)
  含义: 指定要加载的模型和分词器路径(可以是 Hugging Face Hub 的 ID 或本地绝对路径).
  使用方法: `--model /path/to/model --tokenizer /path/to/tokenizer`
  使用场景: 基础启动参数. 离线环境推荐指向本地挂载的权重路径.
  含义: 要加载的模型路径或 HuggingFace Hub 上的模型名称.
  使用方法: 指向本地磁盘路径或 HF 仓库名: `--model Qwen/Qwen2.5-7B-Instruct`
  使用场景: 启动服务最核心的基础参数, 指定需要部署的具体基座模型.

  ###########################################################################################

  --model-impl ['auto', 'terratorch', 'transformers', 'vllm']
                        Which implementation of the model to use:
                        - "auto" will try to use the vLLM implementation, if it exists, and fall back to the Transformers implementation if no vLLM implementation is
                        available.
                        - "vllm" will use the vLLM model implementation.
                        - "transformers" will use the Transformers model implementation.
                        - "terratorch" will use the TerraTorch model implementation. (default: auto)
  含义: 显式指定使用哪种底层的模型网络结构实现.
  使用方法: `--model-impl vllm`
  使用场景: 默认 `auto` 会自动优先使用 vLLM 深度定制优化过的极速版模型架构. 如果某个小众模型在 vLLM 下出现兼容性 bug, 可以手动回退到 `transformers` 实现, 以牺牲部分性能为代价换取高兼容性.

  ###########################################################################################

  --override-attention-dtype OVERRIDE_ATTENTION_DTYPE
                        Override dtype for attention (default: None)
  含义: 单独覆盖 Attention 算子内部计算使用的精度.
  使用场景: 用于排查数值稳定性问题. 当在 FP16 精度下模型出现 `NaN`(非数值报错)时, 可以尝试强制将注意力层设定为 `float32` 计算.

  ###########################################################################################

  --override-generation-config OVERRIDE_GENERATION_CONFIG
                        Overrides or sets generation config. e.g. `{"temperature": 0.5}`. If used with `--generation-config auto`, the override parameters will be merged with
                        the default config from the model. If used with `--generation-config vllm`, only the override parameters are used.
                        Should either be a valid JSON string or JSON keys passed individually. (default: {})
  含义: 指定推理超参数(如 `temperature`, `top_p`)的读取配置文件或进行实时覆盖.
  使用方法: `--override-generation-config '{"temperature": 0.3, "max_new_tokens": 4096}'`
  使用场景: 在服务器级别统一给所有请求施加最高长度约束(`max_new_tokens`)或限制默认随机度, 防止某些恶意或失控的请求导致服务器超载.

  ###########################################################################################

  --pooler-config POOLER_CONFIG
                        Pooler config which controls the behaviour of output pooling in pooling models.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.PoolerConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)
  含义: 控制池化模型输出池化行为(如 Mean pooling, CLS pooling)的 JSON 配置参数.
  使用场景: 在部署自研文本向量化(Embedding)或重排(Reranker)模型时, 精确调整向量提取模式.

  ###########################################################################################

  --quantization QUANTIZATION, -q QUANTIZATION
                        Method used to quantize the weights. If `None`, we first check the `quantization_config` attribute in the model config file. If that is `None`, we
                        assume the model weights are not quantized and use `dtype` to determine the data type of the weights. (default: None)
  含义: 指定权重加载的量化算法(如 `awq`, `gptq`, `fp8` 等).
  使用方法: `--quantization fp8`
  使用场景: 在显存有限但需要加载大模型(例如在 A40 上加载 70B 模型)时, 通过量化降低显存占用并提升生成速度.

  --quantization-config QUANTIZATION_CONFIG
                        User-facing quantization configuration. Carries per-layer-kind specs (linear, moe) and ignore patterns; see :class:`QuantizationConfigArgs`. Auto-
                        populated from the matching online shorthand when `quantization` is one of the values in `ONLINE_QUANT_SHORTHAND_NAMES`.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.QuantizationConfigArgs
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)
  含义:
      `--quantization`: 显式指定加载的量化格式(如 `awq`, `gptq`, `fp8`, `squeezellm`, `marlin`).
      `--quantization-config`: 传递针对不同层(如线性层、MoE层)的特定量化配置.
      `--allow-deprecated-quantization`: 是否允许加载已被社区淘汰的旧版量化算法格式.
  使用方法: `--quantization awq`
  使用场景: 显存受限情况下的低成本部署. 量化可以大幅压减显存占用(如 4-bit 量化), 允许在单张 24G 显卡(如 RTX 4090)上跑原本需要 80G 显存的大模型.

  ###########################################################################################

  --renderer-num-workers RENDERER_NUM_WORKERS
                        Number of worker threads in the renderer thread pool. The pool is consumed by the async renderer path (e.g. the OpenAI-compatible API server started by
                        `vllm serve`) to parallelize tokenization, chat template rendering, and multimodal preprocessing across concurrent requests.
                        The offline `LLM` entrypoint uses the synchronous renderer path and processes prompts (including multimodal preprocessing) serially, so this setting
                        has no effect there. (default: 1)
  含义: 渲染线程池中的工作线程数量, 用于并行处理并发请求的 Token 编码、Jinja 对话模板渲染以及多模态数据预处理.
  使用方法: 增加数值, 如 `--renderer-num-workers 4`
  使用场景: 高并发、多模态或超长 Prompt 输入场景. 在传统的单线程模式下, 当并发请求激增时, CPU 进行多轮对话模板渲染、多模态图像/视频格式转换与裁剪会形成严重的瓶颈, 使得 GPU 长时间等待. 多线程渲染可以有效解决这一 CPU 端的"入水阀"瓶颈.

  ###########################################################################################

  --revision REVISION   The specific model version to use. It can be a branch name, a tag name, or a commit id. If unspecified, will use the default version. (default: None)
  含义: 分别代表从 Hugging Face 加载模型权重和模型代码时指定的 Git 分支、Tag 或 Commit ID.
  使用方法: `--revision main --code-revision 8c3a2ef`
  使用场景: 生产版本锁死与安全审计. 防止模型作者在 HuggingFace Hub 上更新代码或权重时引入不兼容的变更, 通常在生产环境中锁死一个具体的 Commit ID.

  ###########################################################################################

  --runner {auto,draft,generate,pooling}
                        The type of model runner to use. Each vLLM instance only supports one model runner, even if the same model can be used for multiple types. (default:
                        auto)
  含义: 决定当前 vLLM 实例充当什么类型的模型运行器.
  使用场景:
      `draft`: 用于投机采样(Speculative Decoding)中充当快速草稿模型.
      `pooling`: 将生成式模型转为仅输出 Pooling 向量的表示模型.
      `generate`: 常规文本生成.

  ###########################################################################################

  --seed SEED           Random seed for reproducibility.
                        We must set the global seed because otherwise, different tensor parallel workers would sample different tokens, leading to inconsistent results.
                        (default: 0)
  含义: 全局随机数种子.
  使用场景: 多卡张量并行(Tensor Parallel)的一致性保障. 张量并行下, 不同卡上的 Worker 必须同步进行 Token 采样. 设置固定的全局 seed 能够防止并行 Worker 间由于采样分歧导致结果崩塌.

  ###########################################################################################

  --served-model-name SERVED_MODEL_NAME [SERVED_MODEL_NAME ...]
                        The model name(s) used in the API. If multiple names are provided, the server will respond to any of the provided names. The model name in the model
                        field of a response will be the first name in this list. If not specified, the model name will be the same as the `--model` argument. Noted that this
                        name(s) will also be used in `model_name` tag content of prometheus metrics, if multiple names provided, metrics tag will take the first one. (default:
                        None)
  含义: 对外暴露的 API 模型名称. 支持指定多个别名, 首个名称会作为指标监控(Prometheus)中的标识.
  使用方法: `--served-model-name gpt-4o-mini qwen-7b`
  使用场景: 平替第三方 API 或灰度发布. 如果需要用自研模型无缝替换业务代码中原有的 `gpt-4o` 接口, 可以通过此参数将本地模型命名为 `gpt-4o`, 无需修改客户端代码.

  ###########################################################################################

  --skip-tokenizer-init, --no-skip-tokenizer-init
                        Skip initialization of tokenizer and detokenizer. Expects valid `prompt_token_ids` and `None` for prompt from the input. The generated output will
                        contain token ids. (default: False)
  含义: 跳过服务器端分词器和反分词器的初始化.
  使用方法: 开启后, 输入参数必须直接为 `prompt_token_ids`(整数数组), 服务也只输出 Token ID.
  使用场景: 极低延迟的网关集成. 将 Tokenization 剥离并运行在独立的 CPU 服务(如 Node.js 边缘网关)上, vLLM 服务器只纯粹处理 GPU 上的 Token 矩阵计算, 极限压缩网络传输和 Python 编解码耗时.

  ###########################################################################################

  --tokenizer TOKENIZER
                        Name or path of the Hugging Face tokenizer to use. If unspecified, model name or path will be used. (default: None)
  含义: 指定要加载的模型和分词器路径(可以是 Hugging Face Hub 的 ID 或本地绝对路径).
  使用方法: `--model /path/to/model --tokenizer /path/to/tokenizer`
  使用场景: 基础启动参数. 离线环境推荐指向本地挂载的权重路径.
  含义: 指定 Tokenizer 的名称或路径(默认与模型路径一致).
  使用场景: 在一些多语言或特化微调任务中, 模型和分词器被拆分托管. 可以用该参数指定一个扩展了特殊 Token 的分词器.

  ###########################################################################################

  --tokenizer-mode ['auto', 'deepseek_v32', 'deepseek_v4', 'hf', 'mistral', 'slow']
                        Tokenizer mode:
                        - "auto" will use the tokenizer from `mistral_common` for Mistral models if available, otherwise it will use the "hf" tokenizer.
                        - "hf" will use the fast tokenizer if available.
                        - "slow" will always use the slow tokenizer.
                        - "mistral" will always use the tokenizer from `mistral_common`.
                        - "deepseek_v32" will always use the tokenizer from `deepseek_v32`.
                        - "deepseek_v4" will always use the tokenizer from `deepseek_v4`.
                        - "qwen_vl" will always use the tokenizer from `qwen_vl`.
                        - Other custom values can be supported via plugins.
                        To swap the Rust BPE backend that powers HF fast tokenizers for the [fastokens](https://github.com/crusoecloud/fastokens) implementation, set
                        `VLLM_USE_FASTOKENS=1` instead — that override applies to any mode that loads an HF fast tokenizer (`hf`, `deepseek_v32`, `deepseek_v4`, `qwen_vl`, …).
                        (default: auto)
  含义: 控制分词器引擎的选择.
  使用场景: 运行特定厂商模型(如 DeepSeek V3/V4, Mistral)时, 选用其深度优化的特化分词器, 不仅能保证特殊 Token(如 Tool Call 等特殊控制符)解析完全正确, 还能利用更高效的分词实现提升吞吐.

  ###########################################################################################

  --tokenizer-revision TOKENIZER_REVISION
                        The specific revision to use for the tokenizer on the Hugging Face Hub. It can be a branch name, a tag name, or a commit id. If unspecified, will use
                        the default version. (default: None)
  含义: 指定 Tokenizer 的名称或路径(默认与模型路径一致).
  使用场景: 在一些多语言或特化微调任务中, 模型和分词器被拆分托管. 可以用该参数指定一个扩展了特殊 Token 的分词器.

  ###########################################################################################

  --trust-remote-code, --no-trust-remote-code
                        Trust remote code (e.g., from HuggingFace) when downloading the model and tokenizer. (default: False)
  含义: 是否信任从远端(如 HuggingFace)下载的模型中包含的自定义 Python 代码.
  使用方法: 默认 `False`. 启动自定义模型时需开启: `--trust-remote-code`
  使用场景: 运行一些尚未合并到 `transformers` 官方库中的新型模型(如最新发布的非标准架构模型). 在不受信任的环境中, 出于安全考虑建议关闭.

  ###########################################################################################

  --use-fp64-gumbel, --no-use-fp64-gumbel
                        Whether to use FP64 (instead of FP32) for the Gumbel noise used by the sampler. FP64 reduces the chance of ties in Gumbel-max sampling at the cost of
                        significantly lower kernel throughput on most GPUs. (default: False)
  含义: 在采样器的 Gumbel-max 随机采样中, 强制使用双精度浮点数(FP64)计算噪声, 而非默认的单精度(FP32).
  使用场景: 避免在极端高吞吐和特定采样参数下, 由于单精度数值精度不足产生"概率平局"(ties)而导致的生成重复或崩溃. 它会轻微降低内核吞吐, 但能提供更严谨的统计一致性.

  ###########################################################################################

LoadConfig:
  Configuration for loading the model weights.

  ###########################################################################################

  --download-dir DOWNLOAD_DIR
                        Directory to download and load the weights, default to the default cache directory of Hugging Face. (default: None)
  含义: 指定模型权重的下载与缓存目录. 默认使用 Hugging Face 的默认缓存路径(通常是 `~/.cache/huggingface/hub`).
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --download-dir /data/model_cache
    ```
  使用场景:
      磁盘空间管理: 系统盘(如 `/`)空间不足, 需要将模型下载到挂载的大容量数据盘(如 `/data` 或 `/mnt`).
      容器化部署(Docker/K8s): 在宿主机上准备一个持久化目录, 通过 Docker 卷(Volume)映射到容器内, 并使用此参数指向该路径, 避免容器重建时重复下载模型.

  ###########################################################################################

  --ignore-patterns IGNORE_PATTERNS [IGNORE_PATTERNS ...]
                        The list of patterns to ignore when loading the model. Default to "original/**/*" to avoid repeated loading of llama's checkpoints. (default:
                        ['original/**/*'])
  含义: 在下载或加载模型时需要忽略的文件匹配模式. 默认值为 `['original//*']`, 用于避免重复加载 LLaMA 原始格式的权重.
  使用方法:
    ```bash
    # 忽略所有 PyTorch 格式的 .bin 文件, 只加载 .safetensors 文件
    vllm serve facebook/opt-125m --ignore-patterns "*.bin" "*.pth"
    ```
  使用场景:
      节省带宽与存储: 当 Hugging Face 仓库中同时存在 `.safetensors` 和旧版的 `.bin` / `.pth` 格式时, 可以通过此参数显式忽略不需要的格式, 从而减少下载时间并节省磁盘空间.

  ###########################################################################################

  --load-format LOAD_FORMAT
                        The format of the model weights to load.
                        - "auto" will try to load the weights in the safetensors format and fall back to the pytorch bin format if safetensors format is not available.
                        - "pt" will load the weights in the pytorch bin format.
                        - "safetensors" will load the weights in the safetensors format.
                        - "instanttensor" will load the Safetensors weights on CUDA devices using InstantTensor, which enables distributed loading with pipelined prefetching
                        and fast direct I/O.
                        - "npcache" will load the weights in pytorch format and store a numpy cache to speed up the loading.
                        - "dummy" will initialize the weights with random values, which is mainly for profiling.
                        - "tensorizer" will use CoreWeave's tensorizer library for fast weight loading. See the Tensorize vLLM Model script in the Examples section for more
                        information.
                        - "runai_streamer" will load the Safetensors weights using Run:ai Model Streamer.
                        - "runai_streamer_sharded" will load weights from pre-sharded checkpoint files using Run:ai Model Streamer.
                        - "bitsandbytes" will load the weights using bitsandbytes quantization.
                        - "sharded_state" will load weights from pre-sharded checkpoint files, supporting efficient loading of tensor-parallel models.
                        - "gguf" will load weights from GGUF format files (details specified in https://github.com/ggml-org/ggml/blob/master/docs/gguf.md).
                        - "mistral" will load weights from consolidated safetensors files used by Mistral models.
                        - "modelexpress" will load weights using ModelExpress.
                        - Other custom values can be supported via plugins. (default: auto)
  含义: 指定模型权重的加载格式和对应的加载器(Loader).
  常见可选项及使用场景:
      `auto`(默认): 优先加载 `safetensors`, 若没有则回退到 `pt`(PyTorch bin). 适用于多数通用场景.
      `pt`: 强制以 PyTorch pickle 格式加载. 通常用于较旧的模型库.
      `safetensors`: 安全且快速的零拷贝张量格式, 推荐用于生产环境.
      `dummy`: 使用随机值初始化权重, 不实际下载或加载模型. 场景: 主要用于性能基准测试、吞吐量评估(Profiling)或排查框架层面的 OOM 问题, 无需等待大模型漫长的下载和加载过程.
      `tensorizer`: 利用 CoreWeave 的 `tensorizer` 库, 支持直接从 HTTP/S3 等对象存储快速序列化加载. 场景: Serverless 架构下的冷启动优化.
      `sharded_state`: 从预分片的 checkpoint 文件中并行加载. 场景: 在多 GPU(Tensor Parallelism)环境下, 极大缩短超大规模模型的初始化时间.
      `instanttensor` / `runai_streamer`: 高级流水线化、并行化或流式加载器. 场景: 需要极致缩短容器冷启动时间的超大规模 GPU 集群.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --load-format safetensors
    ```

  ###########################################################################################

  --model-loader-extra-config MODEL_LOADER_EXTRA_CONFIG
                        Extra config for model loader. This will be passed to the model loader corresponding to the chosen load_format. (default: {})
  含义: 为指定的模型加载器(通过 `--load-format` 选择)提供额外的配置参数, 接收一个 JSON 格式的字符串.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --load-format tensorizer --model-loader-extra-config '{"tensorizer_uri": "s3://my-bucket/model.trenz"}'
    ```
  使用场景:
      高级自定义加载: 在使用非标准加载器(如 `tensorizer`、`runai_streamer` 等第三方插件)时, 需要传递特定的凭证、连接地址或特殊控制参数.

  ###########################################################################################

  --pt-load-map-location PT_LOAD_MAP_LOCATION
                        The map location for loading pytorch checkpoint, to support loading checkpoints can only be loaded on certain devices like "cuda", this is equivalent
                        to `{"": "cuda"}`. Another supported format is mapping from different devices like from GPU 1 to GPU 0: `{"cuda:1": "cuda:0"}`. Note that when passed
                        from command line, the strings in dictionary need to be double quoted for json parsing. For more details, see the original doc for `map_location`
                        parameter in [`torch.load`][] parameter. (default: cpu)
  含义: 加载 PyTorch `.bin` 格式权重时, 映射张量的目标设备(类似于 `torch.load` 中的 `map_location`). 默认为 `cpu`.
  使用方法:
    ```bash
    # 将模型直接加载到 GPU 0
    vllm serve facebook/opt-125m --pt-load-map-location '{"": "cuda:0"}'
    ```
  使用场景:
      缓解主机内存(CPU RAM)不足: 默认情况下, PyTorch 加载器先将权重序列化到主机内存(CPU RAM), 然后再移动到 GPU. 如果主机内存较小(例如在某些高 GPU、低 CPU 内存配比的容器实例中), 可能会触发主机端 OOM. 通过将其映射到特定的 `cuda` 设备, 可以尝试直接在 GPU 显存上反序列化(需确保显存足够).

  ###########################################################################################

  --safetensors-load-strategy SAFETENSORS_LOAD_STRATEGY
                        Specifies the loading strategy for safetensors weights.
                        - None (default): Uses memory-mapped (lazy) loading. When an NFS filesystem is detected and the total checkpoint size fits within 90%% of available
                        RAM, prefetching is enabled automatically.
                        - "lazy": Weights are memory-mapped from the file. This enables on-demand loading and is highly efficient for models on local storage. Unlike the
                        default (None), auto-prefetch on NFS is not performed.
                        - "eager": The entire file is read into CPU memory upfront before loading. This is recommended for models on network filesystems (e.g., Lustre, NFS) as
                        it avoids inefficient random reads, significantly speeding up model initialization. However, it uses more CPU RAM.
                        - "prefetch": Checkpoint files are read into the OS page cache before workers load them, speeding up the model loading phase. Useful on network or
                        high-latency storage.
                        - "torchao": Weights are loaded in upfront and then reconstructed into torchao tensor subclasses. This is used when the checkpoint was quantized using
                        torchao and saved using safetensors. Needs `torchao >= 0.14.0`. (default: None)
  含义: `safetensors` 格式权重的加载策略(`lazy`, `eager`, `prefetch`).
  使用方法: `--safetensors-load-strategy eager`
  使用场景: 如果模型权重存储在网络存储(如 NFS、GPFS、Lustre)上, 网络随机小 IO 极其缓慢. 此时设置为 `eager`, 会将整个权重文件一次性整块读入内存, 能大幅缩短冷启动时的模型加载时间.
  含义: 控制加载 `safetensors` 权重时的 I/O 行为策略, 是优化加载速度的核心参数.
  常见选项与场景:
      `None`(默认): 如果检测到网络文件系统(NFS)且可用系统内存(RAM)足够(占权重大小的 90% 以上), 则会自动开启预取(Prefetching); 否则使用内存映射(lazy).
      `lazy`: 基于内存映射(mmap)按需加载. 场景: 模型存储在本地快速 SSD(如 NVMe)上. 这是最高效的方式, 几乎不占用多余的 CPU 内存.
      `eager`: 一次性将整个权重文件读取到 CPU 内存中, 然后再加载. 场景: 模型存储在网络文件系统(如 NFS, Lustre, NAS)上. 网络文件系统对碎片化的随机读取(Lazy loading 常常触发)性能极差, 而顺序读取整块文件(Eager)速度要快得多, 尽管这会消耗双倍的 CPU 内存.
      `prefetch`: 利用后台线程提前将文件读入操作系统页缓存(Page Cache). 场景: 介于本地和高延迟网络存储之间的情况, 既想缩短加载时间, 又不想像 `eager` 那样瞬间占用大量 CPU 物理内存.
      `torchao`: 专用于配合 `torchao` 量化的模型权重.
  使用方法:
    ```bash
    # 在 NFS 环境下部署
    vllm serve facebook/opt-125m --safetensors-load-strategy eager
    ```

  ###########################################################################################

  --safetensors-prefetch-block-size SAFETENSORS_PREFETCH_BLOCK_SIZE
                        Read size in bytes for each safetensors checkpoint file prefetch.
                        Parse human-readable integers like '1k', '2M', etc. Including decimal values with decimal multipliers.
                            Examples:
                            - '1k' -> 1,000
                            - '1K' -> 1,024
                            - '25.6k' -> 25,600 (default: 16777216)
  --safetensors-prefetch-num-threads SAFETENSORS_PREFETCH_NUM_THREADS
                        Number of worker threads used to prefetch safetensors checkpoint files into the OS page cache when safetensors prefetching is enabled. (default: 8)
  含义:
      `--safetensors-prefetch-block-size`: 开启预取时, 每次读取文件的块大小(字节数). 默认 16MB(`16777216`).
      `--safetensors-prefetch-num-threads`: 预取文件到操作系统页缓存时的后台工作线程数. 默认 8.
  使用方法:
    ```bash
    # 使用 16 个线程, 每次读取 32MB 块, 以压榨高速网络存储的带宽
    vllm serve facebook/opt-125m \
      --safetensors-load-strategy prefetch \
      --safetensors-prefetch-block-size 32M \
      --safetensors-prefetch-num-threads 16
    ```
  使用场景:
      高带宽网络存储吞吐优化: 在拥有高速网络(如 100GbE / InfiniBand)的高性能计算(HPC)或 K8s 集群中, 默认的单线程或小数据块可能无法占满网络带宽. 调大这两个参数, 可以用并行多线程大块读取的方式, 显著缩短数十 G 甚至数百 G 模型的加载耗时.

  ###########################################################################################

  --use-tqdm-on-load, --no-use-tqdm-on-load
                        Whether to enable tqdm for showing progress bar when loading model weights. (default: True)
  含义: 是否在控制台中显示加载模型权重的 `tqdm` 进度条. 默认开启(`True`).
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --no-use-tqdm-on-load
    ```
  使用场景:
      生产日志清洁: 在生产环境(如 Kubernetes、AWS Elastic Beanstalk 等)中, 日志通常会被收集到中心化日志系统(如 ELK, Grafana Loki, CloudWatch). `tqdm` 进度条在非交互式终端中往往会产生大量带有控制字符(如 `\r`)的冗余日志, 破坏日志格式. 在生产环境的启动脚本中, 建议加入 `--no-use-tqdm-on-load` 以保持日志的整洁和可读性.

  ###########################################################################################

AttentionConfig:
  Configuration for attention mechanisms in vLLM.

  ###########################################################################################

  --attention-backend ATTENTION_BACKEND
                        Attention backend to use. Use "auto" or None for automatic selection. (default: None)

  ###########################################################################################

MambaConfig:
  Configuration for Mamba SSM backends.

  --enable-mamba-cache-stochastic-rounding, --no-enable-mamba-cache-stochastic-rounding
                        Enable stochastic rounding when writing SSM state to fp16 cache. Uses random bits to unbias the rounding error, which can improve numerical stability
                        for long sequences. (default: False)
  --mamba-backend MAMBA_BACKEND
                        Mamba SSU backend to use. (default: MambaBackendEnum.TRITON)
  --mamba-cache-philox-rounds MAMBA_CACHE_PHILOX_ROUNDS
                        Number of Philox PRNG rounds for stochastic rounding random number generation. 0 uses the Triton default. Higher values improve randomness quality at
                        the cost of compute. (default: 0)

  ###########################################################################################

StructuredOutputsConfig:
  Dataclass which contains structured outputs config for the engine.

  --reasoning-parser REASONING_PARSER
                        Select the reasoning parser depending on the model that you're using. This is used to parse the reasoning content into OpenAI API format. (default: )
  --reasoning-parser-plugin REASONING_PARSER_PLUGIN
                        Path to a dynamically reasoning parser plugin that can be dynamically loaded and registered. (default: )

  ###########################################################################################

ParallelConfig:
  Configuration for the distributed execution.

  ###########################################################################################

  --all2all-backend {allgather_reducescatter,deepep_high_throughput,deepep_low_latency,flashinfer_all2allv,flashinfer_nvlink_one_sided,flashinfer_nvlink_two_sided,mori,naive,nixl_ep,pplx}
                        All2All backend for MoE expert parallel communication. Available options:
                        - "allgather_reducescatter": All2all based on allgather and reducescatter
                        - "deepep_high_throughput": Use deepep high-throughput kernels
                        - "deepep_low_latency": Use deepep low-latency kernels
                        - "mori": Use mori kernels
                        - "nixl_ep": Use nixl-ep kernels
                        - "flashinfer_nvlink_two_sided": Use flashinfer two-sided kernels for mnnvl
                        - "flashinfer_nvlink_one_sided": Use flashinfer high-throughput a2a kernels (default: allgather_reducescatter)
  含义: 在 MoE 专家分发时, 指定使用低延迟的 `deepep`(DeepSeek EP 通信库)作为 All2All 通信后端.
  原因: 专家并行(EP)需要在 GPU 之间传输 Token 的路由数据(All-to-All 通信). 采用 `deepep_low_latency` 内核能够绕过标准的 NCCL 重型通信栈, 利用 NVLink 建立极低延迟的非阻塞通信通道, 从而缓解 EP 部署中的通信瓶颈.
  含义: 专家并行中核心通信算子 All-to-All 的底座后端.
  常见可选项:
      `allgather_reducescatter`: 兼容性最好的标准实现(默认值).
      `deepep_high_throughput` / `deepep_low_latency`: DeepSeek 开源的 DeepEP 优化内核, 针对高吞吐或低延迟场景定制.
      `flashinfer_nvlink_one_sided` / `two_sided`: 针对 NVLink 硬件架构优化的 FlashInfer 高速 All2All 通信内核.
  使用场景:
      在 NVLink 互联的 H100/A100 八卡机器上运行 DeepSeek 系列模型时, 推荐将其设为 `deepep_low_latency` 或 `flashinfer_nvlink_one_sided`, 可大幅压缩 All2All 的通信耗时, 提升 Token 输出速度.

  ###########################################################################################

  --cp-kv-cache-interleave-size CP_KV_CACHE_INTERLEAVE_SIZE
                        Interleave size of kv_cache storage while using DCP or PCP. For `total_cp_rank = pcp_rank * dcp_world_size + dcp_rank`, and `total_cp_world_size =
                        pcp_world_size * dcp_world_size`. store interleave_size tokens on total_cp_rank i, then store next interleave_size tokens on total_cp_rank i+1.
                        Interleave_size=1: token-level alignment, where token `i` is stored on total_cp_rank `i % total_cp_world_size`. Interleave_size=block_size: block-level
                        alignment, where tokens are first populated to the preceding ranks. Tokens are then stored in (rank i+1, block j) only after (rank i, block j) is fully
                        occupied. Block_size should be greater than or equal to cp_kv_cache_interleave_size. Block_size should be divisible by cp_kv_cache_interleave_size.
                        (default: 1)
  含义: 使用 CP(DCP 或 PCP)时, KV Cache 的交错存储大小(取代了旧的 `--dcp-kv-cache-interleave-size`).
  使用方法:
      设置为 `1` 表示 Token 级别交错(Token 0 在 Rank 0, Token 1 在 Rank 1 ...).
      设置为 `block_size`(通常为 16 或 32)表示 Block 级别交错, 先填满当前 Rank 的 Block 再填下一个.
  使用场景: 用于平衡和优化跨卡 KV Cache 的负载. 通常在长文本生成中, Block 级别(如 16)可以获得更好的内存布局连续性.

  ###########################################################################################

  --cpu-distributed-timeout-seconds CPU_DISTRIBUTED_TIMEOUT_SECONDS
                        Timeout (in seconds) for cpu communication groups. If None, PyTorch's default timeout is used (1800s for gloo). (default: None)
  含义: CPU 通信组(如 Gloo 后端)的超时时间. 默认 `None`(即 PyTorch 默认的 1800 秒).
  使用场景: 通常无需调整, 但在非常缓慢的 CPU 跨机同步或极其拥堵的网络环境中可以视情况调大.

  ###########################################################################################

  --data-parallel-address DATA_PARALLEL_ADDRESS, -dpa DATA_PARALLEL_ADDRESS
                        Address of data parallel cluster head-node. (default: None)
  `--data-parallel-external-lb` (外部LB模式): 用于 K8s 环境下"一 Pod 一 Rank"的 wide-EP 架构(即一个 Pod 对应 EP 的一个分片), 通过外部 LB 进行流量分发.
  `--data-parallel-hybrid-lb` (混合LB模式): 在单节点内由 vLLM 本地负载均衡, 在跨节点间由外部 LB 进行负载均衡.
  `--data-parallel-multi-port-external-lb` (多端口外部LB): 节点内启动一个 Supervisor, 为每个 DP 实例暴露一个独立的外部 API 端口, 并统一监控健康状态.
  `--data-parallel-rank` / `--data-parallel-start-rank` / `--data-parallel-size-local` / `--data-parallel-rpc-port` / `--data-parallel-address`:
      用途: 用于在多机/复杂 K8s 容器环境下, 显式地向各个容器实例指派其在 DP 组中的 Rank、本地 DP 实例数、以及用于 RPC 同步的端口和主节点地址.
  `--disable-nccl-for-dp-synchronization`
      含义: 强制 DP 同步逻辑使用 Gloo(CPU)而不是 NCCL(GPU)进行 All-Reduce.
      使用场景: 异步调度(Async Scheduling)启用时, 为避免 DP 同步操作抢占 GPU 上的 NCCL 流, 从而导致推理计算被阻塞.

  ###########################################################################################

  --data-parallel-backend DATA_PARALLEL_BACKEND, -dpb DATA_PARALLEL_BACKEND
                        Backend for data parallel, either "mp" or "ray". (default: mp)
  含义: 数据并行的底座后端(`mp` 或 `ray`).
  使用方法: `-dpb mp`.
  使用场景: 单机多卡内多副本推荐用 `mp`; 多机多副本推荐用 `ray`.

  ###########################################################################################

  --data-parallel-external-lb, --no-data-parallel-external-lb, -dpe
                        Whether to use "external" DP LB mode. Applies only to online serving and when data_parallel_size > 0. This is useful for a "one-pod-per-rank" wide-EP
                        setup in Kubernetes. Supported only for MoE deployments; non-MoE models should use independent vLLM instances without --data-parallel-* arguments. Set
                        implicitly when --data-parallel-rank is provided explicitly to vllm serve. (default: False)
  --data-parallel-hybrid-lb, --no-data-parallel-hybrid-lb, -dph
                        Whether to use "hybrid" DP LB mode. Applies only to online serving and when data_parallel_size > 0. Enables running an AsyncLLM and API server on a
                        "per-node" basis where vLLM load balances between local data parallel ranks, but an external LB balances between vLLM nodes/replicas. Set explicitly in
                        conjunction with
                        --data-parallel-start-rank. (default: False)
  --data-parallel-multi-port-external-lb, -dpm
                        Run a node-local supervisor that launches one external-LB API server per local data parallel rank and exposes aggregated health on a supervisor port.
                        (default: False)
  --data-parallel-rank DATA_PARALLEL_RANK, -dpn DATA_PARALLEL_RANK
                        Data parallel rank of this instance. When set, enables external load balancer mode for MoE data-parallel deployments. Unsupported for non-MoE models;
                        launch independent vLLM instances instead. (default: None)
  --data-parallel-rpc-port DATA_PARALLEL_RPC_PORT, -dpp DATA_PARALLEL_RPC_PORT
                        Port for data parallel RPC communication. (default: None)
  `--data-parallel-external-lb` (外部LB模式): 用于 K8s 环境下"一 Pod 一 Rank"的 wide-EP 架构(即一个 Pod 对应 EP 的一个分片), 通过外部 LB 进行流量分发.
  `--data-parallel-hybrid-lb` (混合LB模式): 在单节点内由 vLLM 本地负载均衡, 在跨节点间由外部 LB 进行负载均衡.
  `--data-parallel-multi-port-external-lb` (多端口外部LB): 节点内启动一个 Supervisor, 为每个 DP 实例暴露一个独立的外部 API 端口, 并统一监控健康状态.
  `--data-parallel-rank` / `--data-parallel-start-rank` / `--data-parallel-size-local` / `--data-parallel-rpc-port` / `--data-parallel-address`:
      用途: 用于在多机/复杂 K8s 容器环境下, 显式地向各个容器实例指派其在 DP 组中的 Rank、本地 DP 实例数、以及用于 RPC 同步的端口和主节点地址.
  `--disable-nccl-for-dp-synchronization`
      含义: 强制 DP 同步逻辑使用 Gloo(CPU)而不是 NCCL(GPU)进行 All-Reduce.
      使用场景: 异步调度(Async Scheduling)启用时, 为避免 DP 同步操作抢占 GPU 上的 NCCL 流, 从而导致推理计算被阻塞.

  ###########################################################################################

  --data-parallel-size DATA_PARALLEL_SIZE, -dp DATA_PARALLEL_SIZE
                        Number of data parallel groups. MoE layers will be sharded according to the product of the tensor parallel size and data parallel size. (default: 1)
  含义: 数据并行度(运行多个独立的基础模型实例, 各自处理不同的请求).
  使用方法: `--data-parallel-size 2`
  使用场景:
    如果加载的模型较小(如 Qwen-7B), 单张 A40 显存绰绰有余. 此时设置 `-dp 2`(或结合部署多个单卡 vLLM 实例), 可以创建两个完全独立的推理引擎, 大幅提高服务在高并发场景下的 QPS(每秒请求数).
  含义: 数据并行(DP)组的数量. 在 MoE 模型中, MoE 层会根据 `TP * DP` 的乘积进行分片.
  使用方法: `--data-parallel-size 2`.
  使用场景: 高并发高吞吐在线 serving 场景. 通过运行多个 DP 实例, 共同消费请求队列.

  ###########################################################################################

  --data-parallel-size-local DATA_PARALLEL_SIZE_LOCAL, -dpl DATA_PARALLEL_SIZE_LOCAL
                        Number of data parallel replicas to run on this node. (default: None)
  --data-parallel-start-rank DATA_PARALLEL_START_RANK, -dpr DATA_PARALLEL_START_RANK
                        Starting data parallel rank for secondary nodes. (default: None)
  `--data-parallel-external-lb` (外部LB模式): 用于 K8s 环境下"一 Pod 一 Rank"的 wide-EP 架构(即一个 Pod 对应 EP 的一个分片), 通过外部 LB 进行流量分发.
  `--data-parallel-hybrid-lb` (混合LB模式): 在单节点内由 vLLM 本地负载均衡, 在跨节点间由外部 LB 进行负载均衡.
  `--data-parallel-multi-port-external-lb` (多端口外部LB): 节点内启动一个 Supervisor, 为每个 DP 实例暴露一个独立的外部 API 端口, 并统一监控健康状态.
  `--data-parallel-rank` / `--data-parallel-start-rank` / `--data-parallel-size-local` / `--data-parallel-rpc-port` / `--data-parallel-address`:
      用途: 用于在多机/复杂 K8s 容器环境下, 显式地向各个容器实例指派其在 DP 组中的 Rank、本地 DP 实例数、以及用于 RPC 同步的端口和主节点地址.
  `--disable-nccl-for-dp-synchronization`
      含义: 强制 DP 同步逻辑使用 Gloo(CPU)而不是 NCCL(GPU)进行 All-Reduce.
      使用场景: 异步调度(Async Scheduling)启用时, 为避免 DP 同步操作抢占 GPU 上的 NCCL 流, 从而导致推理计算被阻塞.

  ###########################################################################################

  --dbo-decode-token-threshold DBO_DECODE_TOKEN_THRESHOLD
                        The threshold for dual batch overlap for batches only containing decodes. If the number of tokens in the request is greater than this threshold,
                        microbatching will be used. Otherwise, the request will be processed in a single batch. (default: 32)
  --dbo-prefill-token-threshold DBO_PREFILL_TOKEN_THRESHOLD
                        The threshold for dual batch overlap for batches that contain one or more prefills. If the number of tokens in the request is greater than this
                        threshold, microbatching will be used. Otherwise, the request will be processed in a single batch. (default: 512)
  含义: 触发 DBO 微批次切分的 Token 数量阈值.
  使用场景: 当 Batch 中的 Token 总数大于设定值(默认 Decode 32, Prefill 512)时, 才会启用微批次重叠. 如果 Token 数太少, 拆分微批次带来的调度开销(Overhead)反而会大于通信重叠的收益, 此时单批次直接计算效率更高.

  ###########################################################################################

  --dcp-comm-backend {a2a,ag_rs}
                        Communication backend for Decode Context Parallel (DCP).
                        - "ag_rs": AllGather + ReduceScatter (default, existing behavior)
                        - "a2a": All-to-All exchange of partial outputs + LSE, then combine with Triton kernel. Reduces NCCL calls from 3 to 2 per layer for MLA models.
                        (default: ag_rs)
  含义: Decode 上下文并行(DCP)的通信后端, 可选 `ag_rs`(AllGather + ReduceScatter)或 `a2a`(All-to-All).
  使用方法: `--dcp-comm-backend a2a`.
  使用场景: 如果使用的是 MLA(Multi-head Latent Attention) 架构的模型(如 DeepSeek 架构), 使用 `a2a` 可以通过 Triton 算子将 NCCL 通信次数从每层 3 次减少到 2 次, 从而显著降低 Decode 阶段的通信延迟.

  ###########################################################################################

  --dcp-kv-cache-interleave-size DCP_KV_CACHE_INTERLEAVE_SIZE
                        Interleave size of kv_cache storage while using DCP. dcp_kv_cache_interleave_size has been replaced by cp_kv_cache_interleave_size, and will be
                        deprecated when PCP is fully supported. (default: 1)

  ###########################################################################################

  --decode-context-parallel-size DECODE_CONTEXT_PARALLEL_SIZE, -dcp DECODE_CONTEXT_PARALLEL_SIZE
                        Number of decode context parallel groups, because the world size does not change by dcp, it simply reuse the GPUs of TP group, and tp_size needs to be
                        divisible by dcp_size. (default: 1)
  含义: Decode(后续 Token 生成)阶段的上下文并行大小.
  使用方法: `-dcp 2`.
  使用场景: 极长文本生成或多轮对话场景下, Decode 阶段随着 KV Cache 增长, 单卡显存无法承载时.

  ###########################################################################################

  --disable-custom-all-reduce, --no-disable-custom-all-reduce
                        Disable the custom all-reduce kernel and fall back to NCCL. (default: False)
  含义: 禁用 vLLM 自研的自定义 All-Reduce 算子, 回退到原生 NCCL.
  使用场景: 在某些特殊的硬件环境、国产 GPU 或特定虚拟化容器中, vLLM 的自定义 CUDA Kernel All-Reduce 可能会产生报错(如 Bus Error)或性能不升反降. 如果遇到此类分布式通信 Bug, 将其设为 `True` 可以提高系统稳定性.

  ###########################################################################################

  --disable-nccl-for-dp-synchronization, --no-disable-nccl-for-dp-synchronization
                        Forces the dp synchronization logic in vllm/v1/worker/dp_utils.py  to use Gloo instead of NCCL for its all reduce.
                        Defaults to True when async scheduling is enabled, False otherwise. (default: None)
  `--data-parallel-external-lb` (外部LB模式): 用于 K8s 环境下"一 Pod 一 Rank"的 wide-EP 架构(即一个 Pod 对应 EP 的一个分片), 通过外部 LB 进行流量分发.
  `--data-parallel-hybrid-lb` (混合LB模式): 在单节点内由 vLLM 本地负载均衡, 在跨节点间由外部 LB 进行负载均衡.
  `--data-parallel-multi-port-external-lb` (多端口外部LB): 节点内启动一个 Supervisor, 为每个 DP 实例暴露一个独立的外部 API 端口, 并统一监控健康状态.
  `--data-parallel-rank` / `--data-parallel-start-rank` / `--data-parallel-size-local` / `--data-parallel-rpc-port` / `--data-parallel-address`:
      用途: 用于在多机/复杂 K8s 容器环境下, 显式地向各个容器实例指派其在 DP 组中的 Rank、本地 DP 实例数、以及用于 RPC 同步的端口和主节点地址.
  `--disable-nccl-for-dp-synchronization`
      含义: 强制 DP 同步逻辑使用 Gloo(CPU)而不是 NCCL(GPU)进行 All-Reduce.
      使用场景: 异步调度(Async Scheduling)启用时, 为避免 DP 同步操作抢占 GPU 上的 NCCL 流, 从而导致推理计算被阻塞.

  ###########################################################################################

  --distributed-executor-backend ['external_launcher', 'mp', 'ray', 'uni']
                        Backend to use for distributed model workers, either "ray" or "mp" (multiprocessing). If the product of pipeline_parallel_size and tensor_parallel_size
                        is less than or equal to the number of GPUs available, "mp" will be used to keep processing on a single host. Otherwise, an error will be raised. To
                        use "mp" you must also set nnodes, and to use "ray" you must manually set distributed_executor_backend to "ray".
                        Note: [TPU](https://docs.vllm.ai/projects/tpu/en/latest/) platform only supports Ray for distributed inference. (default: None)
  含义: 多卡进程管理的后端, 支持 `mp` (Multiprocessing) 或 `ray`.
  使用方法: `--distributed-executor-backend mp`
  使用场景:
    单机多卡: 强烈推荐使用 `mp`. 它避免了拉起整个 Ray 集群的额外系统开销, 启动速度更快且稳定性更好.
    多机多卡: 必须选择 `ray`.
  含义: 分布式执行器后端. 可选值为 `mp`(Multiprocessing, 多进程)或 `ray`.
  使用方法: `--distributed-executor-backend mp`.
  使用场景:
      当并行的 GPU 数量在单机范围内时, 建议使用 `mp`, 其进程间通信开销通常低于 Ray.
      当需要进行多机(Multi-node)分布式推理, 且 GPU 数量超过单机限制时, 可以使用 `ray` 进行集群级别的资源调度.

  ###########################################################################################

  --distributed-timeout-seconds DISTRIBUTED_TIMEOUT_SECONDS
                        Timeout in seconds for distributed operations (e.g., init_process_group). If set, this value is passed to torch.distributed.init_process_group as the
                        timeout parameter. If None, PyTorch's default timeout is used (600s for NCCL). Increase this for multi-node setups where model downloads may be slow.
                        (default: None)
  含义: 分布式初始化(如 `init_process_group`)的超时时间(秒).
  使用方法: `--distributed-timeout-seconds 1200`
  使用场景: 多机环境或网络较差的场景. 在初始化时, 如果某些节点下载模型权重较慢导致握手超时, 可以增大此值(默认 NCCL 为 600s).

  ###########################################################################################

  --enable-dbo, --no-enable-dbo
                        Enable dual batch overlap for the model executor. (default: False)
  含义: 启用双批次重叠(Dual Batch Overlap, DBO). 它通过微批次(Microbatch, ubatch)技术, 将一个大 Batch 拆分成多个微批次(其大小由 `--ubatch-size` 指定), 使前一个微批次的通信(如 All-Reduce / All-to-All)与后一个微批次的计算在时间上重叠(Overlap).
  使用方法: `--enable-dbo True --ubatch-size 4`.
  使用场景: 通信受限(Communication-bound)的多卡分布式场景. 通过重叠计算和通信来隐藏通信延迟, 从而提升高并发下的整体吞吐量.

  ###########################################################################################

  --enable-elastic-ep, --no-enable-elastic-ep
                        Enable elastic expert parallelism with stateless NCCL groups for DP/EP. (default: False)
  含义: 启用弹性专家并行. 使用无状态的 NCCL 通信组.
  使用场景: 动态调整集群规模或在容错/抢占式实例(Spot Instances)集群中运行大规模 MoE 时的弹性扩缩容.

  ###########################################################################################

  --enable-ep-weight-filter, --no-enable-ep-weight-filter
                        Skip non-local expert weights during model loading when expert parallelism is active.  Each rank only reads its own expert shard from disk, which can
                        drastically reduce storage I/O for MoE models with per-expert weight tensors (e.g. DeepSeek, Mixtral, Kimi-K2.5).  Has no effect on 3D fused-expert
                        checkpoints (e.g. GPT-OSS) or non-MoE models. (default: False)
  含义: 开启专家权重过滤加载.
  使用方法: `--enable-ep-weight-filter True`.
  使用场景: 极度实用. 当部署 DeepSeek-V3 等拥有数百 GB 权重的超大 MoE 模型时, 开启此参数后, 每个 GPU Rank 在加载模型时只会从磁盘读取并加载属于它自己的 Expert 权重, 其他不属于它的 Expert 权重直接跳过. 这可以极大节省主机内存(RAM), 并缩短模型冷启动的磁盘 I/O 时间.

  ###########################################################################################

  --enable-eplb, --no-enable-eplb
                        Enable expert parallelism load balancing for MoE layers. (default: False)
  含义: 启用并配置专家并行负载均衡(Expert Parallelism Load Balancing).
  使用场景: MoE 模型在推理时, 某些 Expert(如常识、标点符号专家)被激活的频次可能远高于其他 Expert, 导致 GPU 负载不均(负载高的卡拖慢整组卡). EPLB 通过动态路由和副本机制平衡各张卡的计算压力.

  ###########################################################################################

  --enable-expert-parallel, --no-enable-expert-parallel, -ep
                        Use expert parallelism instead of tensor parallelism for MoE layers. (default: False)
  含义: 在 MoE(混合专家模型)层启用专家并行, 而不是默认的张量并行.
  原因: 在 MoE 模型中, 不同的 Token 会被路由到不同的专家(Expert)上进行计算. 如果使用张量并行, 每个专家的权重会被切分到不同 GPU 上, 每次计算都需要进行跨卡全连接通信. 启用专家并行后, 会将不同的专家完整地部署在不同的 GPU 上, Token 路由到对应 GPU 上进行完整计算, 从而大幅减少跨卡的通信数据量.
  含义: 开启专家并行. MoE 层的各个 Expert 不在卡间做矩阵切分, 而是完整地把不同 Expert 放置在不同卡上.
  使用方法: `--enable-expert-parallel True`.
  使用场景: 部署 DeepSeek-V3/R1 或 Mixtral 等含有大量专家的 MoE 模型, 能显著降低通信开销, 提升吞吐.

  ###########################################################################################

  --eplb-config EPLB_CONFIG
                        Expert parallelism configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.EPLBConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: EPLBConfig(window_size=1000, step_interval=3000,
                        num_redundant_experts=0, log_balancedness=False, log_balancedness_interval=1, use_async=False, policy='default', communicator=None))
  含义: 启用并配置专家并行负载均衡(Expert Parallelism Load Balancing).
  使用场景: MoE 模型在推理时, 某些 Expert(如常识、标点符号专家)被激活的频次可能远高于其他 Expert, 导致 GPU 负载不均(负载高的卡拖慢整组卡). EPLB 通过动态路由和副本机制平衡各张卡的计算压力.

  ###########################################################################################

  --expert-placement-strategy {linear,round_robin}
                        The expert placement strategy for MoE layers:
                        - "linear": Experts are placed in a contiguous manner. For example, with 4 experts and 2 ranks, rank 0 will have experts [0, 1] and rank 1 will have
                        experts [2, 3].
                        - "round_robin": Experts are placed in a round-robin manner. For example, with 4 experts and 2 ranks, rank 0 will have experts [0, 2] and rank 1 will
                        have experts [1, 3]. This strategy can help improve load balancing for grouped expert models with no redundant experts. (default: linear)
  含义: 专家分配策略.
      `linear`: 连续分配(如 4 个专家 2 张卡, 卡 0 放 `[0,1]`, 卡 1 放 `[2,3]`).
      `round_robin`: 循环分配(卡 0 放 `[0,2]`, 卡 1 放 `[1,3]`).
  使用场景: 配合某些特定的 MoE 路由设计. 通常 `round_robin` 能为某些没有冗余专家的模型带来更好的自然负载均衡.

  ###########################################################################################

  --master-addr MASTER_ADDR
                        distributed master address for multi-node distributed  inference when distributed_executor_backend is mp. (default: 127.0.0.1)
  --master-port MASTER_PORT
                        distributed master port for multi-node distributed  inference when distributed_executor_backend is mp. (default: 29501)
  含义: 多机 `mp` 后端所需的分布式主节点地址、端口、总节点数以及当前节点 Rank.
  使用方法:
      主节点(Rank 0): `--master-addr 10.0.0.1 --master-port 29501 --nnodes 2 --node-rank 0`
      从节点(Rank 1): `--master-addr 10.0.0.1 --master-port 29501 --nnodes 2 --node-rank 1`
      通常需要在两台机器上分别启动.
  使用场景: 在不依赖 Ray 的情况下, 使用原生 PyTorch 多进程进行跨机分布式推理.

  ###########################################################################################

  --max-parallel-loading-workers MAX_PARALLEL_LOADING_WORKERS
                        Maximum number of parallel loading workers when loading model sequentially in multiple batches. To avoid RAM OOM when using tensor parallel and large
                        models. (default: None)
  含义: 限制并发加载权重的 CPU 线程/进程最大数量.
  使用场景: 当在单台机器上加载超大模型(如 70B+)且 TP 较大时, 如果每个 GPU 对应的进程都同时从磁盘将权重读入系统内存(RAM), 极易导致主机系统内存溢出(RAM OOM). 限制该值(如设为 `2` 或 `4`)可以让 Worker 串行/分批加载, 确保平稳启动.

  ###########################################################################################

  --nnodes NNODES, -n NNODES
                        num of nodes for multi-node distributed inference when distributed_executor_backend is mp. (default: 1)
  --node-rank NODE_RANK, -r NODE_RANK
                        distributed node rank for multi-node distributed  inference when distributed_executor_backend is mp. (default: 0)
  含义: 多机 `mp` 后端所需的分布式主节点地址、端口、总节点数以及当前节点 Rank.
  使用方法:
      主节点(Rank 0): `--master-addr 10.0.0.1 --master-port 29501 --nnodes 2 --node-rank 0`
      从节点(Rank 1): `--master-addr 10.0.0.1 --master-port 29501 --nnodes 2 --node-rank 1`
      通常需要在两台机器上分别启动.
  使用场景: 在不依赖 Ray 的情况下, 使用原生 PyTorch 多进程进行跨机分布式推理.

  ###########################################################################################

  --numa-bind, --no-numa-bind
                        Enable NUMA binding for GPU worker subprocesses. (default: False)
  --numa-bind-cpus NUMA_BIND_CPUS [NUMA_BIND_CPUS ...]
                        Optional CPU lists to bind each GPU worker to.
                        Specify one CPU list per visible GPU, for example `["0-3", "4-7", "8-11", "12-15"]`. When set, vLLM uses `numactl --physcpubind` instead of
                        `--cpunodebind`. This is useful for custom policies such as binding to PCT or other high-frequency cores. Each entry must use `numactl --physcpubind`
                        CPU-list syntax, for example `"0-3"` or `"0,2,4-7"`. (default: None)
  --numa-bind-nodes NUMA_BIND_NODES [NUMA_BIND_NODES ...]
                        NUMA node to bind each GPU worker to.
                        Specify one NUMA node per visible GPU, for example `[0, 0, 1, 1]` for a 4-GPU system with GPUs 0-1 on NUMA node 0 and GPUs 2-3 on NUMA node 1. If unset
                        and `numa_bind=True`, vLLM auto-detects the GPU-to-NUMA topology. The values are passed to `numactl --membind` and `--cpunodebind`, so they must be
                        valid `numactl` NUMA node indices. (default: None)
  含义: NUMA(非一致性内存访问)绑定配置.
  使用方法: `--numa-bind True`, 或指定具体的节点绑定 `--numa-bind-nodes 0 0 1 1`.
  使用场景: 多路 CPU + 多 GPU 系统的标准优化(例如双路 AMD EPYC 处理器搭配 8 张 H100).
      如果不进行绑定, 运行在 GPU 3 上的 Worker 进程可能会去读取挂载在 CPU 0 内存通道上的数据, 导致跨 CPU 插槽(Socket)的 PCIe 延迟, 造成性能抖动.
      开启此参数可以保证每个 GPU 的控制进程(Worker)绑定在其物理距离最近的 CPU 核心和内存节点(NUMA Node)上, 大幅减少内存和 PCIe 延迟.

  ###########################################################################################

  --pipeline-parallel-size PIPELINE_PARALLEL_SIZE, -pp PIPELINE_PARALLEL_SIZE
                        Number of pipeline parallel groups. (default: 1)
  含义: 流水线并行度(将模型按层纵向切分, 不同的层放在不同的 GPU 上).
  使用方法: `--pipeline-parallel-size 2`
  使用场景: 跨节点(如通过慢速网络连接的服务器)或者不适合做 TP(由于卡间带宽太低, 如 PCIe 限制)的超大模型推理. 在单机多卡内, 通常优先选择 TP 而非 PP, 因为 PP 的 GPU 利用率(气泡问题)相对较低.
  含义: 流水线并行(Pipeline Parallelism)大小, 将模型的不同层(Layers)分段放置在不同的 GPU 组上.
  使用方法: `--pipeline-parallel-size 2`(将模型层一分为二, 运行在两组 GPU 上).
  使用场景: 超大规模模型(如数百 B 级别)单机显存无法容纳, 必须跨机部署时, 通常结合 TP 使用(例如: 8 卡 TP + 2 机 PP).

  ###########################################################################################

  --prefill-context-parallel-size PREFILL_CONTEXT_PARALLEL_SIZE, -pcp PREFILL_CONTEXT_PARALLEL_SIZE
                        Number of prefill context parallel groups. (default: 1)
  含义: Prefill(首字生成)阶段的上下文并行大小.
  使用方法: `-pcp 2`(与 `-tp` 共享 GPU, 要求 `tp_size` 能被 `pcp_size` 整除).
  使用场景: 极长文本输入场景, Prefill 阶段由于序列太长导致单卡显存溢出(OOM)或 Attention 计算变慢.

  ###########################################################################################

  --ray-workers-use-nsight, --no-ray-workers-use-nsight
                        Whether to profile Ray workers with nsight, see https://docs.ray.io/en/latest/ray-observability/user-guides/profiling.html#profiling-nsight-profiler.
                        (default: False)
  含义: 决定是否使用 NVIDIA Nsight Systems 性能分析工具对 Ray Worker 进程进行 Profile.
  使用场景: 开发者进行分布式性能瓶颈调优、算子耗时排查时使用.

  ###########################################################################################

  --tensor-parallel-size TENSOR_PARALLEL_SIZE, -tp TENSOR_PARALLEL_SIZE
                        Number of tensor parallel groups. (default: 1)
  含义: 张量并行度(将单层网络横向切分到多个 GPU 上同步计算).
  使用方法: `--tensor-parallel-size 2`
  使用场景:
    针对您的双卡环境, 如果运行一个单卡显存(48GB A40)装不下的中大型模型(例如 32B 或 70B 浮点模型), 应该设置 `-tp 2`, 让两张卡协同工作, 显存开销平分.
  含义: 张量并行(Tensor Parallelism)大小, 将单层网络矩阵乘法切分到多个 GPU 上并行计算.
  使用方法: `--tensor-parallel-size 8`(单机 8 卡全分片).
  使用场景: 模型单卡显存无法容纳, 或者需要利用多卡并行来降低单次推理(Prefill 阶段)的延迟(Latency).

  ###########################################################################################

  --ubatch-size UBATCH_SIZE
                        Number of ubatch size. (default: 0)
  含义: 启用双批次重叠(Dual Batch Overlap, DBO). 它通过微批次(Microbatch, ubatch)技术, 将一个大 Batch 拆分成多个微批次(其大小由 `--ubatch-size` 指定), 使前一个微批次的通信(如 All-Reduce / All-to-All)与后一个微批次的计算在时间上重叠(Overlap).
  使用方法: `--enable-dbo True --ubatch-size 4`.
  使用场景: 通信受限(Communication-bound)的多卡分布式场景. 通过重叠计算和通信来隐藏通信延迟, 从而提升高并发下的整体吞吐量.

  ###########################################################################################

  --worker-cls WORKER_CLS
                        The full name of the worker class to use. If "auto", the worker class will be determined based on the platform. (default: auto)
  --worker-extension-cls WORKER_EXTENSION_CLS
                        The full name of the worker extension class to use. The worker extension class is dynamically inherited by the worker class. This is used to inject new
                        attributes and methods to the worker class for use in collective_rpc calls. (default: )
  含义: 允许用户动态注入和覆盖 vLLM 底层的 Worker 类.
  使用场景: 高级二次开发. 如果你针对特定硬件平台定制了 Worker, 或需要在 collective_rpc 通信中注入自定义的 Hook 逻辑, 可以通过这两个参数动态加载你的 Python 类.

  ###########################################################################################

CacheConfig:
  Configuration for the KV cache.

  ###########################################################################################

  --block-size BLOCK_SIZE
                        Size of a contiguous cache block in number of tokens. Accepts None (meaning "use default"). After construction, always int. (default: None)
  含义: PagedAttention 机制中, 一个物理连续缓存块(Block)所容纳的 Token 数量. 其逻辑类似于操作系统的虚拟内存"页"大小. 默认情况下, 通常为 16(在较新的版本或某些模型中也有 None, 由 vLLM 自动推导).
  使用方法: `--block-size 16` 或 `--block-size 32`.
  使用场景:
      小 Block(如 16): 可以有效减少内存碎片(即请求结束时最后一个 Block 未填满造成的显存浪费), 更适合高并发、短文本生成场景.
      大 Block(如 32): 可以提高 GPU 的显存连续访问效率(合并访存), 在超长上下文(Long-context)或高吞吐批处理(High Batch Size)下, 有时能带来性能提升. 一般情况下建议维持默认值.

  ###########################################################################################

  --calculate-kv-scales, --no-calculate-kv-scales
                        Deprecated: This option is deprecated and will be removed in v0.19. It enables dynamic calculation of `k_scale` and `v_scale` when kv_cache_dtype is
                        fp8. If `False`, the scales will be loaded from the model checkpoint if available. Otherwise, the scales will default to 1.0. (default: False)
  含义: [已弃用] 用于在 KV Cache 设为 FP8 时, 是否开启动态计算 scale(缩放因子). 若为 False, 则从模型 Checkpoint 加载, 或默认使用 1.0.
  使用场景: 该选项已被废弃(并将在 v0.19 移除), 目前不建议显式调用. 当前的 vLLM 推荐使用 checkpoint 预存的量化 scale 或默认退回 1.0.

  ###########################################################################################

  --enable-prefix-caching, --no-enable-prefix-caching
                        Whether to enable prefix caching. (default: None)
  含义: 启用前缀缓存(Prefix Caching), 自动缓存多轮对话中相同的系统提示词或历史文本的 KV 缓存.
  使用方法: `--enable-prefix-caching`
  使用场景:
    强推在 多轮对话、RAG(检索增强生成)、智能客服 场景中开启.
    开启后, 后续请求中只要前缀(如 System Prompt)一致, 就能直接复用已有 KV 缓存, 省去 Prefill(预填充)阶段的计算, 大幅降低首字延迟(TTFT).
  含义: 是否启用前缀缓存(也叫 RadixAttention). 该机制可以在不同请求之间自动复用相同 Prompt 前缀(如 System Prompt、Few-shot 示例等)的 KV Cache.
  使用方法: `--enable-prefix-caching`
  使用场景:
      多轮对话(Multi-turn Chatbots): 用户在多轮交互中无需在每次生成时都重新预填充(Prefill)之前的历史对话, 响应延迟(首字延迟 TTFT)大幅降低.
      长 System Prompt 任务、Agent 工作流、少量样本(Few-shot)提示词: 只要多个独立并发请求共享同一段前缀, 就能减少大量的重复计算和显存占用.

  ###########################################################################################

  --gpu-memory-utilization GPU_MEMORY_UTILIZATION
                        The fraction of GPU memory to be used for the model executor, which can range from 0 to 1. For example, a value of 0.5 would imply 50% GPU memory
                        utilization. If unspecified, will use the default value of 0.92. This is a per-instance limit, and only applies to the current vLLM instance. It does
                        not matter if you have another vLLM instance running on the same GPU. For example, if you have two vLLM instances running on the same GPU, you can set
                        the GPU memory utilization to 0.5 for each instance. (default: 0.92)
  含义: 分配给 vLLM 使用的 GPU 显存上限比例(默认 0.92).
  使用方法: `--gpu-memory-utilization 0.90`
  使用场景:
    剩余的显存(如默认下的 8%)会被用于 CUDA Graph 捕获及 PyTorch 临时变量.
    如果在同一张 GPU 上还需要运行其他进程(如 Triton 语音、Embedding 模型、Docker 监控), 需要降低该值(例如 `0.70`), 防止显存挤爆.
  含义: 分配给当前 vLLM 实例(包括模型权重、KV Cache 和临时计算空间)的 GPU 显存比例上限(0 到 1 之间). 默认值为 `0.92`.
  使用方法: `--gpu-memory-utilization 0.90`
  使用场景:
      单模型独占 GPU: 建议设为较高的值(如 `0.92` - `0.95`), 以便腾出尽可能多的显存给 KV Cache, 从而支持更高的并发.
      单卡多实例/混合部署: 例如在一张卡上同时运行两个 vLLM 实例, 或者卡上还有 Embedding / Reranker 等服务. 此时应当手动将两者的显存占比调低(例如各分配 `0.45`), 以防止相互抢占导致 Out Of Memory (OOM) 崩溃.

  ###########################################################################################

  --kv-cache-dtype {auto,bfloat16,float16,fp8,fp8_ds_mla,fp8_e4m3,fp8_e5m2,fp8_inc,fp8_per_token_head,int8_per_token_head,nvfp4,turboquant_3bit_nc,turboquant_4bit_nc,turboquant_k3v4_nc,turboquant_k8v4}
                        Data type for kv cache storage. If "auto", will use model data type. CUDA 11.8+ supports fp8 (=fp8_e4m3) and fp8_e5m2. ROCm (AMD GPU) supports fp8
                        (=fp8_e4m3). Intel Gaudi (HPU) supports fp8 (using fp8_inc). Some models (namely DeepSeekV3.2) default to fp8, set to bfloat16 to use bfloat16 instead,
                        this is an invalid option for models that do not default to fp8. (default: auto)
  含义: KV Cache 的存储精度(支持 `auto`, `fp8`, `bfloat16` 等).
  使用方法: `--kv-cache-dtype fp8`
  使用场景: 在高并发场景下, 显存中的大部分空间会被 KV 缓存占用. 将其设为 `fp8`(通常在 Ada/Hopper 或支持 FP8 的 Ampere 卡上), 可以使 KV 缓存占用空间几乎减半, 从而允许成倍提升最大并发 Batch Size, 大幅提升吞吐量.
  含义: KV Cache 存储的数据类型. 默认是 `auto`(使用模型本身的原始精度, 如 BF16/FP16). 支持 FP8(如 `fp8`、`fp8_e4m3`、`fp8_e5m2`)、INT8 等低精度格式.
  使用方法: `--kv-cache-dtype fp8`
  使用场景:
      极长上下文或超高并发场景: 当显存难以承受大量的长序列 KV Cache 时, 开启 FP8 格式可以使 KV Cache 占用的显存空间几乎折半.
      硬件支持: 在 NVIDIA Hopper/Ada Lovelace 架构(如 H100, L40S, RTX 4090)或 Ampere 架构(A100)上, FP8 KV Cache 能在损失极微小精度的情况下大幅释放显存. 另外, 像 DeepSeek-V3/R1 这类模型原生默认就需要 FP8, 若强制设为 bfloat16 可能会导致显存不足.

  ###########################################################################################

  --kv-cache-dtype-skip-layers KV_CACHE_DTYPE_SKIP_LAYERS [KV_CACHE_DTYPE_SKIP_LAYERS ...]
                        Layer patterns to skip KV cache quantization. Accepts layer indices (e.g., '0', '2', '4') or attention type names (e.g., 'sliding_window'). (default:
                        [])
  含义: 在对 KV Cache 进行量化(如转为 FP8)时, 指定跳过哪些层或哪些注意力类型, 使其保持模型本身的原始高精度(如 BF16).
  使用方法: `--kv-cache-dtype-skip-layers 0 1 31 sliding_window` (跳过第 0、1、31 层, 以及滑动窗口注意力层).
  使用场景:
      精度敏感型任务: 部分模型在进行全局 FP8 量化后, 其首尾几层(对上下文理解或指令遵循至关重要)或特定结构的层(如滑动窗口层)容易出现数值不稳定. 通过此参数针对性地让这些敏感层保持高精度, 可以在保留绝大部分量化显存红利的同时, 最大化保障模型输出质量.

  ###########################################################################################

  --kv-cache-memory-bytes KV_CACHE_MEMORY_BYTES
                        Size of KV Cache per GPU in bytes. By default, this is set to None and vllm can automatically infer the kv cache size based on gpu_memory_utilization.
                        However, users may want to manually specify the kv cache memory size. kv_cache_memory_bytes allows more fine-grain control of how much memory gets used
                        when compared with using gpu_memory_utilization. Note that kv_cache_memory_bytes (when not-None) ignores gpu_memory_utilization
                        Parse human-readable integers like '1k', '2M', etc. Including decimal values with decimal multipliers.
                            Examples:
                            - '1k' -> 1,000
                            - '1K' -> 1,024
                            - '25.6k' -> 25,600 (default: None)
  含义: 手动直接指定每个 GPU 分配给 KV Cache 的物理显存大小(字节), 而不是通过比例估算. 此参数一旦设定, 会直接覆盖并忽略 `--gpu-memory-utilization` 对 KV Cache 的推导逻辑. 支持 `1k`, `2M`, `12G` 等人类可读格式.
  使用方法: `--kv-cache-memory-bytes 16G`
  使用场景:
      严苛的生产级容器环境(Docker/K8s): 在企业级容器调度中, 为防止 vLLM 启动时的动态 Profiling 产生不可控的显存抖动, 或者为了让系统能够精准计算并预留宿主机/容器的物理显存限制, 推荐采用此参数硬性指定 KV Cache 的精确大小, 能够有效规避 K8s 的 OOM Killer.

  ###########################################################################################

  --kv-offloading-backend {lmcache,native}
                        The backend to use for KV cache offloading. Supported backends include 'native' (vLLM native CPU offloading), 'lmcache'. KV offloading is only
                        activated when kv_offloading_size is set. (default: native)
  含义: 指定 KV Cache 卸载至 CPU 的后端. 可选 `native`(vLLM 内置 CPU 卸载)或 `lmcache`(一种支持多级分布式/本地共享的缓存中间件).
  使用方法: `--kv-offloading-backend lmcache`
  使用场景:
      `native`: 单节点部署, 逻辑简单, 系统直接负责显存与系统内存的交换.
      `lmcache`: 在更大规模的分布式集群或多实例中, `lmcache` 可以跨节点、跨进程共享卸载的 KV Cache, 提高多实例集群整体的首字响应效率.

  ###########################################################################################

  --kv-offloading-size KV_OFFLOADING_SIZE
                        Size of the KV cache offloading buffer in GiB. When TP > 1, this is the total buffer size summed across all TP ranks. By default, this is set to None,
                        which means no KV offloading is enabled. When set, vLLM will enable KV cache offloading to CPU using the kv_offloading_backend. (default: None)
  含义: 指定卸载到 CPU RAM 的 KV Cache 缓冲区大小(单位: GiB). 默认为 None(即不启用 CPU 卸载).
  使用方法: `--kv-offloading-size 32`(允许分配 32GB 的 CPU 内存用于缓存).
  使用场景:
      低成本超长文本推理: 在 GPU 显存有限(如单张 24GB VRAM)但系统 CPU 内存充裕(如 128GB RAM)的环境下, 如需处理数十万 Token 的单次极大上下文推理, 此参数可以让模型在不崩溃(避免 OOM)的前提下完成推理, 适合非高实时性、高容忍度、长文本分析的批处理场景.

  ###########################################################################################

  --kv-sharing-fast-prefill, --no-kv-sharing-fast-prefill
                        This feature is work in progress and no prefill optimization takes place with this flag enabled currently.
                        In some KV sharing setups, e.g. YOCO (https://arxiv.org/abs/2405.05254), some layers can skip tokens corresponding to prefill. This flag enables
                        attention metadata for eligible layers to be overridden with metadata necessary for implementing this optimization in some models (e.g. Gemma3n)
                        (default: False)
  含义: [实验性] 针对支持 KV 共享的特定架构模型(例如 YOCO、Gemma3n), 允许在部分层中跳过预填充阶段的 Token 缓存优化.
  使用场景: 目前属于 WIP(开发中), 常规 Transformer 模型不需要配置此项. 仅在测试特定支持该硬件级/算法级优化、有特定层 metadata 覆盖需求的创新型模型时使用.

  ###########################################################################################

  --mamba-block-size MAMBA_BLOCK_SIZE
                        Size of a contiguous cache block in number of tokens for mamba cache. Can be set only when prefix caching is enabled. Value must be a multiple of 8 to
                        align with causal_conv1d kernel. (default: None)
  含义: Mamba 缓存的物理块大小(Token 数量), 只有在前缀缓存启用时才生效. 必须是 8 的倍数(以匹配 `causal_conv1d` 内核的对齐要求).
  使用场景: 在部署 Mamba 系列混合模型并需要使用前缀缓存(Prefix Caching)时, 用来平衡对齐与颗粒度.

  ###########################################################################################

  --mamba-cache-dtype {auto,bfloat16,float16,float32}
                        The data type to use for the Mamba cache (both the conv as well as the ssm state). If set to 'auto', the data type will be inferred from the model
                        config. (default: auto)
  含义:
      `--mamba-cache-dtype`: 设定 Mamba 卷积和 SSM 状态的统一精度类型(FP16/BF16/FP32/Auto).
      `--mamba-ssm-cache-dtype`: 专为 SSM 状态指定精度类型.
  使用场景: Mamba 类模型在无限长度生成中, SSM 状态的数值累积容易发生精度漂移. 通过将该值显式设为 `float32` 可以增强数值稳定性; 若显存吃紧, 设为 `float16` 或 `bfloat16` 则可以降低状态缓存开销.

  ###########################################################################################

  --mamba-cache-mode {align,all,none}
                        The cache strategy for Mamba layers.
                        - "none": set when prefix caching is disabled.
                        - "all": cache the mamba state of all tokens at position i * block_size. This is the default behavior (for models that support it) when prefix caching
                        is enabled.
                        - "align": only cache the mamba state of the last token of each scheduler step and when the token is at position i * block_size. (default: none)
  含义: Mamba 层在前缀缓存下的缓存策略.
      `none`: 关闭 Mamba 前缀缓存.
      `all`: 在每个 `i * block_size` 的位置缓存所有 Token 的 Mamba 状态(默认行为).
      `align`: 仅在每个调度器步骤的最后一个 Token, 且满足 `i * block_size` 对齐时缓存.
  使用场景: 调整 Mamba 类模型的 Prefix Caching 开销. `all` 能带来更好的 Prefill 加速效果, 而 `align` 则在内存和缓存查找频率上更轻量.

  ###########################################################################################

  --mamba-ssm-cache-dtype {auto,bfloat16,float16,float32}
                        The data type to use for the Mamba cache (ssm state only, conv state will still be controlled by mamba_cache_dtype). If set to 'auto', the data type
                        for the ssm state will be determined by mamba_cache_dtype. (default: auto)
  含义:
      `--mamba-cache-dtype`: 设定 Mamba 卷积和 SSM 状态的统一精度类型(FP16/BF16/FP32/Auto).
      `--mamba-ssm-cache-dtype`: 专为 SSM 状态指定精度类型.
  使用场景: Mamba 类模型在无限长度生成中, SSM 状态的数值累积容易发生精度漂移. 通过将该值显式设为 `float32` 可以增强数值稳定性; 若显存吃紧, 设为 `float16` 或 `bfloat16` 则可以降低状态缓存开销.

  ###########################################################################################

  --num-gpu-blocks-override NUM_GPU_BLOCKS_OVERRIDE
                        Number of GPU blocks to use. This overrides the profiled `num_gpu_blocks` if specified. Does nothing if `None`. Used for testing preemption. (default:
                        None)
  含义: 手动强行覆盖经自动 Profiling 算出的物理 GPU block 数量.
  使用方法: `--num-gpu-blocks-override 512`
  使用场景:
      开发、测试与极端边界模拟: 该参数主要用于 vLLM 的核心系统开发与功能测试. 例如模拟极度有限的显存环境, 以强制触发系统的 KV Cache 抢占(Preemption)或换入换出(Swap)机制, 验证高负载下系统的稳定性和调度逻辑. 在实际生产和日常业务部署中, 强烈不建议显式设置此参数.

  ###########################################################################################

  --prefix-caching-hash-algo {sha256,sha256_cbor,xxhash,xxhash_cbor}
                        Set the hash algorithm for prefix caching:
                        - "sha256" uses Pickle for object serialization before hashing. This is the current default, as SHA256 is the most secure choice to avoid potential
                        hash collisions.
                        - "sha256_cbor" provides a reproducible, cross-language compatible hash. It serializes objects using canonical CBOR and hashes them with SHA-256.
                        - "xxhash" uses Pickle serialization with xxHash (128-bit) for faster, non-cryptographic hashing. Requires the optional ``xxhash`` package. IMPORTANT:
                        Use of a hashing algorithm that is not considered  cryptographically secure theoretically increases the risk of hash collisions, which can cause
                        undefined behavior or even leak private information in multi-tenant environments. Even if collisions are still very unlikely, it is important to
                        consider your security risk tolerance against the performance benefits before turning this on.
                        - "xxhash_cbor" combines canonical CBOR serialization with xxHash for reproducible hashing. Requires the optional ``xxhash`` package. (default: sha256)
  含义: 前缀缓存中对 Prompt Token 序列进行哈希识别和匹配的算法. 可选 `sha256`、`sha256_cbor`、`xxhash`、`xxhash_cbor`. 默认是 `sha256`.
  使用方法: `--prefix-caching-hash-algo xxhash`
  使用场景:
      `sha256`(安全加密级): 由于其防碰撞特性, 非常适合多租户、公有云等安全边界高的生产部署, 以杜绝发生哈希碰撞导致读取其他用户私有前缀缓存的安全漏洞.
      `xxhash`(高速非加密级): 在私有化、受信的内网、单用户或对吞吐/延迟要求极高、高并发请求的生产环境, 可以使用 `xxhash`. 它由 CPU 执行时的开销极低, 能提高匹配速度, 但在极少情况下理论上存在碰撞风险.

  ###########################################################################################

OffloadConfig:
  Configuration for model weight offloading to reduce GPU memory usage.

  ###########################################################################################

  --cpu-offload-gb CPU_OFFLOAD_GB
                        The space in GiB to offload to CPU, per GPU. Default is 0, which means no offloading. Intuitively, this argument can be seen as a virtual way to
                        increase the GPU memory size. For example, if you have one 24 GB GPU and set this to 10, virtually you can think of it as a 34 GB GPU. Then you can
                        load a 13B model with BF16 weight, which requires at least 26GB GPU memory. Note that this requires fast CPU-GPU interconnect, as part of the model is
                        loaded from CPU memory to GPU memory on the fly in each model forward pass. This uses UVA (Unified Virtual Addressing) for zero-copy access. (default:
                        0)
  含义: 将部分模型参数卸载到系统内存(CPU RAM)中, 借此运行超出 GPU 物理显存大小的模型.
  使用方法: `--cpu-offload-gb 10`
  使用场景: 极度缺乏显存时的妥协手段. 例如, 在一张 24G 显卡上, 想要运行一个需要 30G 显存的模型, 可以把多出的参数 offload 到 CPU. 由于涉及频繁的 PCIe 传输, 这会严重降低推理速度, 仅适合非延迟敏感的测试.
  含义: 每个 GPU 允许卸载到系统 CPU 内存中的最大权重大小(单位为 GiB). 默认值为 `0`, 即不启用.
      原理: 它像是一个虚拟的显存扩展. 比如您有一张 24GB 显存的显卡, 设置该参数为 `10`, 系统在初始化模型时会认为可用显存空间扩大到了 34GB. 其中 10GB 的模型权重会被加载到 CPU 内存中.
  使用场景:
      当模型的总体尺寸(加上 KV Cache 预留空间)刚好处在临界点上. 例如: 使用单张 24GB 显卡(如 RTX 3090/4090/5090)加载一个 BF16 格式、实际需要约 26GB 显存的 13B 稠密模型.
  使用方法:
    ```bash
    vllm serve meta-llama/Llama-2-13b-chat-hf --cpu-offload-gb 10
    ```

  ###########################################################################################

  --cpu-offload-params CPU_OFFLOAD_PARAMS [CPU_OFFLOAD_PARAMS ...]
                        The set of parameter name segments to target for CPU offloading. Unmatched parameters are not offloaded. If this set is empty, parameters are offloaded
                        non-selectively until the memory limit defined by `cpu_offload_gb` is reached. Examples:
                            - For parameter name "mlp.experts.w2_weight":
                                - "experts" or "experts.w2_weight" will match.
                                - "expert" or "w2" will NOT match (must be exact segments). This allows distinguishing parameters like "w2_weight" and "w2_weight_scale".
                        (default: set())
  含义: 指定仅对满足特定名称段的参数进行 CPU 卸载, 未匹配的参数必须留在 GPU 中. 参数名匹配使用的是精确的分段(Segment)匹配.
      例如: 设置为 `experts` 时, 能匹配 `mlp.experts.w2_weight`, 但无法匹配 `expert` 或仅匹配 `w2`(必须是完整的单词分段). 如果不指定(默认空集合), 则会不加选择地卸载参数, 直到达到 `--cpu-offload-gb` 设定的上限.
  使用场景:
      混合专家模型(MoE): MoE 模型(如 Mixtral 8x7B, Qwen2.5-MoE)的 Expert 参数极其庞大. 您可以选择将高频使用的 Self-Attention 权重保留在 GPU 显存中以确保吞吐, 而将庞大且稀疏激活的 Expert 权重(`experts`)卸载到 CPU.
  使用方法:
    ```bash
    vllm serve Qwen/Qwen2.5-14B-Instruct-GPTQ-Int4 --cpu-offload-gb 8 --cpu-offload-params experts
    ```

  ###########################################################################################

  --offload-backend {auto,prefetch,uva}
                        The backend for weight offloading. Options:
                        - "auto": Selects based on which sub-config has non-default values (prefetch if offload_group_size > 0, uva if cpu_offload_gb > 0).
                        - "uva": UVA (Unified Virtual Addressing) zero-copy offloading.
                        - "prefetch": Async prefetch with group-based layer offloading. (default: auto)
  含义: 指定权重卸载的底层后端. 可选值为 `auto`(默认)、`uva`、`prefetch`.
      `auto`: vLLM 会根据其他参数的配置自动选择. 如果设置了 `--cpu-offload-gb > 0`, 则自动选择 `uva`; 如果设置了 `--offload-group-size > 0`, 则选择 `prefetch`.
      `uva`: 利用 CUDA 的统一虚拟寻址(Unified Virtual Addressing), 将参数放置在锁页 CPU 内存(Pinned Memory)中, GPU 可以跨 PCIe 总线"零拷贝"直接访问, 或者在每次前向传播时按需加载.
      `prefetch`: 通过设置 Layer Group, 利用 CUDA Stream 异步地将即将计算的层从 CPU 预取(Prefetch)到 GPU 中, 试图用计算时间来掩盖(Hide)传输延迟.
  使用方法: 通常保持默认 `auto` 即可, 根据您填写的其他具体配置自动生效.

  ###########################################################################################

  --offload-group-size OFFLOAD_GROUP_SIZE
                        Group every N layers together. Offload last `offload_num_in_group` layers of each group. Default is 0 (disabled). Example: group_size=8, num_in_group=2
                        offloads layers 6,7,14,15,22,23,... Unlike cpu_offload_gb, this uses explicit async prefetching to hide transfer latency. (default: 0)
  含义: 指定层分组的周期(以 $N$ 层为一组).
  使用场景: 当您需要对稠密模型进行规律性的分段卸载时. 例如: 一个模型有 32 层, 若设为 `8`, 则模型会被划分为 4 个 Group.

  ###########################################################################################

  --offload-num-in-group OFFLOAD_NUM_IN_GROUP
                        Number of layers to offload per group. Must be <= offload_group_size. Default is 1. (default: 1)
  含义: 在每一个 Group(包含 $N$ 层)中, 从后往前选择多少层卸载到 CPU. 该值必须小于或等于 `--offload-group-size`.
  使用方法与工作流:
      假设 `--offload-group-size 8` 且 `--offload-num-in-group 2`:
      在每个包含 8 层的组中, 最后的 2 层会被卸载.
      这意味着: 第 6, 7 层(第一组末尾)、第 14, 15 层(第二组末尾)等将被放置在 CPU 中, 其余层留在 GPU 中.
  使用场景:
      用于对模型的显存占用进行微调. 如果您只需要释放 15%~20% 左右的显存, 这种精细的"组内部分卸载"可以在保障大部分层驻留 GPU 的同时, 将少量层卸载, 配合预取最大化减小性能损失.

  ###########################################################################################

  --offload-params OFFLOAD_PARAMS [OFFLOAD_PARAMS ...]
                        The set of parameter name segments to target for prefetch offloading. Unmatched parameters are not offloaded. If this set is empty, ALL parameters of
                        each offloaded layer are offloaded. Uses segment matching: "w13_weight" matches "mlp.experts.w13_weight" but not "mlp.experts.w13_weight_scale".
                        (default: set())
  含义: 在被指定卸载的层中, 进一步筛选哪些参数名字段需要被预取卸载.
      如果为空, 则默认将这些被选层中的所有参数全部卸载.
  使用场景:
      精细化控制. 比如只预取卸载指定层中的 MLP 部分(如 `w13_weight`), 而将注意力机制(Attention)相关的权重常驻 GPU.

  ###########################################################################################

  --offload-prefetch-step OFFLOAD_PREFETCH_STEP
                        Number of layers to prefetch ahead. Higher values hide more latency but use more GPU memory. Default is 1. (default: 1)
  含义: 提前多少层开始异步预取. 默认值为 `1`.
      原理解析: 当 GPU 正在计算第 $L$ 层时, vLLM 的异步线程已经在后台开始将第 $L + \text{prefetch\_step}$ 层的权重从 CPU 内存传输到 GPU.
      较大的数值: 能给 PCIe 传输留出更宽裕的时间, 从而更完整地"掩盖"传输延迟, 但代价是需要在 GPU 显存中开辟更大的缓冲区来存放多个提前载入的层.
  使用场景:
      如果您的系统配备了 PCIe Gen4 / Gen5, 且发现推理时卡顿(传输未完成), 可以尝试将其调大至 `2`. 但这需要确保 GPU 有额外的空闲显存来充当预取缓冲区.

  ###########################################################################################

MultiModalConfig:
  Controls the behavior of multimodal models.

  --enable-mm-embeds, --no-enable-mm-embeds
                        If `True`, enables passing multimodal embeddings: for `LLM` class, this refers to tensor inputs under `multi_modal_data`; for the OpenAI-compatible
                        server, this refers to chat messages with content `"type": "*_embeds"`.
                        When enabled with `--limit-mm-per-prompt` set to 0 for a modality, precomputed embeddings skip count validation for that modality,  saving memory by
                        not loading encoder modules while still enabling  embeddings as an input. Limits greater than 0 still apply to embeddings.
                        WARNING: The vLLM engine may crash if incorrect shape of embeddings is passed. Only enable this flag for trusted users! (default: False)
  含义: 允许客户端越过原始媒体文件, 直接向 vLLM 传递预先在前端提取出的 Embedding 浮点数张量.
  使用方法: `--enable-mm-embeds` 配合 `--limit-mm-per-prompt '{"image": 0}'` 使用.
  使用场景: 当您在云端建立了一个"前置视觉提取节点", 在客户端或特定专用服务器完成了图片的 ViT 提取, 而 vLLM 节点只需要接收提取后的 Tensor 进行 LLM 解码. 此时, vLLM 甚至可以不加载 Vision Encoder 模块, 极大降低显存并能保障服务的绝对安全(避免用户利用畸形大图刷爆显存).

  ###########################################################################################

  --interleave-mm-strings, --no-interleave-mm-strings
                        Enable fully interleaved support for multimodal prompts, while using
                        --chat-template-content-format=string. (default: False)
  含义: 允许在使用文本聊天模版(`--chat-template-content-format=string`)的前提下, 完全支持交错排版的多模态 Prompt.
  使用方法: `--interleave-mm-strings`
  使用场景: 多轮、图文交错对话. 比如输入"请问图片1 `<image>` 和图片2 `<image>` 有什么异同点？"等复杂交错排版的提示词(Prompt)格式.

  ###########################################################################################

  --language-model-only, --no-language-model-only
                        If True, disables all multimodal inputs by setting all modality limits to 0. Equivalent to setting `--limit-mm-per-prompt` to 0 for every modality.
                        (default: False)
  含义: 强制关闭该多模态模型的一切视觉/多模态能力, 仅作为纯文本大语言模型(LLM)来运行.
  使用方法: `--language-model-only`
  使用场景: 多模态模型作为兜底纯文本服务. 当您拥有多模态模型(如 Qwen-VL), 但部分业务节点仅需要处理文本且面临极大的高并发时, 开启此项能避免初始化视觉处理组件, 将全部显存保留给文本 KV Cache.

  ###########################################################################################

  --limit-mm-per-prompt LIMIT_MM_PER_PROMPT
                        The maximum number of input items and options allowed per prompt for each modality.
                        Defaults to 999 for each modality.
                        Legacy format (count only): {"image": 16, "video": 2}
                        Configurable format (with options): {"video": {"count": 1, "num_frames": 32, "width": 512, "height": 512}, "image": {"count": 5, "width": 512,
                        "height": 512}}
                        Mixed format (combining both): {"image": 16, "video": {"count": 1, "num_frames": 32, "width": 512, "height": 512}}
                        Should either be a valid JSON string or JSON keys passed individually. (default: {})
  含义: 限制单个请求中包含的多模态输入(如图像或视频)数量.
  使用方法: `--limit-mm-per-prompt '{"image": 5}'`
  使用场景: 部署多模态大模型(如 Qwen-VL、Llama-Vision)时, 限制用户单次上传图片或视频帧的上限, 防止因多模态特征过大导致的显存爆炸.
  含义: 限制单个推理请求中, 各模态(图片、视频、音频等)允许输入的最大数量和对应的分辨率规格.
  使用方法:
      基础计数限制: `--limit-mm-per-prompt '{"image": 16, "video": 2}'` (最多输入 16 张图, 2 个视频)
      高级分辨率限制: `--limit-mm-per-prompt '{"video": {"count": 1, "num_frames": 32, "width": 512, "height": 512}, "image": {"count": 5, "width": 512, "height": 512}}'`
  使用场景: 生产环境的防刷与过载保护. 如果不对该参数进行严格限制, 一旦有用户尝试上传超高分辨率图片或 4K 视频, 极易在 Vision Encoder 前向传播或 KV Cache 阶段导致容器崩溃.

  ###########################################################################################

  --media-io-kwargs MEDIA_IO_KWARGS
                        Additional args passed to process media inputs, keyed by modalities. For example, to set num_frames for video, set `--media-io-kwargs '{"video":
                        {"num_frames": 40} }'`
                        Should either be a valid JSON string or JSON keys passed individually. (default: {})
  含义: 传递给媒体解析和载入库(如处理视频、图像加载)的额外配置项, 一般用于统一规范多媒体资源的读取方式.
  使用方法: `--media-io-kwargs '{"video": {"num_frames": 40}}'`
  使用场景: 视频处理精细控制. 在部署多模态长视频模型时, 如果不限制帧数, 不仅编解码耗时, 显存也无法承受. 通过它强制每次解码固定的 40 帧, 可在算法效果和计算延迟中取得理想的平衡.

  ###########################################################################################

  --mm-encoder-attn-backend MM_ENCODER_ATTN_BACKEND
                        Optional override for the multi-modal encoder attention backend when using vision transformers. Accepts any value from
                        `vllm.v1.attention.backends.registry.AttentionBackendEnum` (e.g. `FLASH_ATTN`). (default: None)
  含义: 手动强制覆盖多模态模型中 Vision Transformer 注意力机制的底层计算后端, 如 FlashAttention (`FLASH_ATTN`) 或 Triton (`TRITON_ATTN`).
  使用方法: `--mm-encoder-attn-backend FLASH_ATTN`
  使用场景: 解决硬件死锁和兼容性问题. 例如, 部分老旧硬件(如 V100/T4)或非标平台在运行 Triton 视觉注意力计算时, 容易在服务启动时陷入死锁, 此时通过手动指定其他稳定后端可以避免挂起.

  ###########################################################################################

  --mm-encoder-attn-dtype {fp8,None}
                        Optional dtype override for ViT encoder attention. Set to `"fp8"` to enable FP8 quantization via the FlashInfer cuDNN backend. When set to `"fp8"`
                        without a scale file, dynamic scaling is used automatically. See docs/features/quantization/fp8_vit_attn.md for details. (default: None)
  含义: 对 ViT 编码器的自注意力层进行精度强制覆盖, 设定为 `fp8` 可以实现视觉部分的 FP8 低精度量化推理.
  使用方法: `--mm-encoder-attn-dtype fp8`
  使用场景: 在保证精度前提下, 极大压榨视觉层前向计算效率、缩短图片解析耗时, 并节省显存.

  ###########################################################################################

  --mm-encoder-fp8-scale-path MM_ENCODER_FP8_SCALE_PATH
                        Path to a JSON file containing per-layer FP8 Q/K/V scales for ViT encoder attention. When provided (with `mm_encoder_attn_dtype="fp8"`), static scaling
                        is used. When omitted, dynamic scaling is used. (default: None)
  --mm-encoder-fp8-scale-save-margin MM_ENCODER_FP8_SCALE_SAVE_MARGIN
                        Safety margin multiplied onto scales when auto-saving. A value > 1 leaves headroom so that inputs with larger activations than the calibration set do
                        not overflow FP8 range. Default 1.5. (default: 1.5)
  --mm-encoder-fp8-scale-save-path MM_ENCODER_FP8_SCALE_SAVE_PATH
                        When set with dynamic FP8 scaling (`mm_encoder_attn_dtype="fp8"` and no `mm_encoder_fp8_scale_path`), saves the calibrated scales to this file after
                        the amax history buffer is full. The saved file can then be used as `mm_encoder_fp8_scale_path` in subsequent runs. (default: None)
  含义: 针对多模态 FP8 注意力机制的校准(Calibration)管理参数.
      `scale-path`: 已离线提取好的 FP8 缩放因子(Static Scaling JSON)存储路径.
      `save-path`: 在动态收集量化范围时, 若校准缓冲区满了, 自动保存静态因子以便下次直接使用.
      `save-margin`: 存储缩放因子时预留的安全边界倍数(如 1.5), 防止推理过程中的异常激活值溢出.
  使用方法:
    1. 第一步(校准收集): `--mm-encoder-attn-dtype fp8 --mm-encoder-fp8-scale-save-path /app/vit_scales.json`
    2. 第二步(静态运行): `--mm-encoder-attn-dtype fp8 --mm-encoder-fp8-scale-path /app/vit_scales.json`
  使用场景: 在严格、严苛的高吞吐生产环境, 使用静态 FP8 量化加速 ViT 推理, 从而绕过"动态缩放计算(Dynamic Scaling)"对算力的损耗.

  ###########################################################################################

  --mm-encoder-only, --no-mm-encoder-only
                        When enabled, skips the language component of the model.
                        This is usually only valid in disaggregated Encoder process. (default: False)
  含义: 指示此实例只运行多模态模型中的视觉编码器(ViT)部分, 略过语言模型骨干.
  使用方法: `--mm-encoder-only`
  使用场景: 解耦式算力架构(Disaggregated Prefill / Prefill-Decode Separation). 在海量节点的集群服务中, 将提取图片的"Prefill阶段"(视觉编码部分)单独部署到一台计算节点, 而语言模型部署到另一台机器, 专卡专用、精细化资源控制.

  ###########################################################################################

  --mm-encoder-tp-mode {data,weights}
                        Indicates how to optimize multi-modal encoder inference using tensor parallelism (TP).
                        - `"weights"`: Within the same vLLM engine, split the weights of each layer across TP ranks. (default TP behavior)
                        - `"data"`: Within the same vLLM engine, split the batched input data across TP ranks to process the data in parallel, while hosting the full weights
                        on each TP rank. This batch-level DP is not to be confused with API request-level DP (which is controlled by `--data-parallel-size`). This is only
                        supported on a per-model basis and falls back to `"weights"` if the encoder does not support DP. (default: weights)
  含义: 决定视觉编码器(Vision Transformer, ViT)在多卡张量并行(Tensor Parallelism, TP)时的运行行为.
      `weights` (默认): 将 ViT 的权重均匀切分到每个 GPU 卡上. 计算时, ViT 的每一层前向传播结束, 都会在多卡间进行昂贵的 All-Reduce 网络通信.
      `data` (Batch 级数据并行): 多卡不切分 ViT 权重, 即在每个 GPU 上完整保留一份 ViT, 将输入的图片 Batch 按卡并行分发计算, 中途无任何通信.
  使用方法: `--mm-encoder-tp-mode data`
  使用场景: 多卡部署(如 4 卡、8 卡)时极力推荐的优化参数. ViT 视觉模型一般比大语言模型本身小得多, 将其切分(`weights` 模式)会由于高频的 All-Reduce 产生严重的通信延迟. 采用 `data` 模式进行 Batch 数据分发, 可将 ViT 运行时间的通信耗时直接降到零, 大幅降低多卡场景下的首字延迟(TTFT).
  注意: 每一张卡都会额外吃一份完整的 ViT 权重显存, 但在大卡(如 A100/H100)上, ViT 几百兆到两三 G 的显存占用换取 TTFT 的极速提升非常划算.

  ###########################################################################################

  --mm-processor-cache-gb MM_PROCESSOR_CACHE_GB
                        The size (in GiB) of the multi-modal processor cache, which is used to avoid re-processing past multi-modal inputs.
                        This cache is duplicated for each API process and engine core process, resulting in a total memory usage of `mm_processor_cache_gb * (api_server_count
                        + data_parallel_size)`.
                        Set to `0` to disable this cache completely (not recommended). (default: 4)
  含义: 为多模态前处理器的缓存分配最大内存容量(GiB), 用于暂存已经经过处理的图片/视频 Tensor.
  使用方法: `--mm-processor-cache-gb 8` (默认 4)
  使用场景: 多轮对话且含大量相同图片的场景(如电商客服、多轮图片问答、同一页文档的连续追问). 开启后, 多次请求相同图片时无需重复耗费 CPU 进行繁重的图像尺寸调整和特征提取.
  注意: 缓存是按 API 进程和引擎进程副本分配的, 实际占用内存为 `mm_processor_cache_gb * (api_server_count + data_parallel_size)`.

  ###########################################################################################

  --mm-processor-cache-type {lru,shm}
                        Type of cache to use for the multi-modal preprocessor/mapper. If `shm`, use shared memory FIFO cache. If `lru`, use mirrored LRU cache. (default: lru)
  含义: 缓存的底层实现方式. 可选 `lru`(每个 worker 进程维护独立的缓存镜像)或 `shm`(通过共享内存 FIFO 队列共享一份缓存).
  使用方法: `--mm-processor-cache-type shm`
  使用场景: 多卡 TP(Tensor Parallelism)部署. 当 `TP > 1` 时, 每个 GPU 的 worker 都会启动, 选择 `shm` 可以通过共享内存实现零拷贝, 避免每个卡都重复存一份图像缓存, 极大节约宿主机内存.

  ###########################################################################################

  --mm-processor-kwargs MM_PROCESSOR_KWARGS
                        Arguments to be forwarded to the model's processor for multi-modal data, e.g., image processor. Overrides for the multi-modal processor obtained from
                        `transformers.AutoProcessor.from_pretrained`.
                        The available overrides depend on the model that is being run.
                        For example, for Phi-3-Vision: `{"num_crops": 4}`.
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)
  含义: 直接向下游的 `AutoProcessor.from_pretrained` 传递特定参数, 用以覆盖模型默认的图像切片和预处理策略.
  使用方法: `--mm-processor-kwargs '{"num_crops": 4}'` (以 Phi-3-Vision 为例)
  使用场景: 针对特定模型做视觉切图优化. 例如, 为了提升 OCR 或小字识别精度, 可以通过增加切图(crops)数来获取高分辨率视觉特征, 或者降低切片数来追求更低的推理耗时.

  ###########################################################################################

  --mm-shm-cache-max-object-size-mb MM_SHM_CACHE_MAX_OBJECT_SIZE_MB
                        Size limit (in MiB) for each object stored in the multi-modal processor shared memory cache. Only effective when `mm_processor_cache_type` is `"shm"`.
                        (default: 128)
  含义: 在 `shm` 缓存类型下, 限制存入共享内存中单个对象的最大容量(MiB).
  使用方法: `--mm-shm-cache-max-object-size-mb 128`
  使用场景: 通常伴随 `shm` 共同使用. 如果您的业务需要处理大批高分辨率(如 4K 级)的大图或高分辨率视频剪辑, 需适度调大该值.

  ###########################################################################################

  --mm-tensor-ipc {direct_rpc,torch_shm}
                        IPC (inter-process communication) method for multimodal tensors.
                        - "direct_rpc": Use msgspec serialization via RPC
                        - "torch_shm": Use torch.multiprocessing shared memory for zero-copy IPC Defaults to "direct_rpc". (default: direct_rpc)
  含义: 控制 API 服务进程(负责接收网络请求、处理图像)与 vLLM 核心计算引擎之间, 如何传输大体积图像 Tensor. `direct_rpc` 采用序列化通信, 而 `torch_shm` 采用 PyTorch 共享内存实现零拷贝.
  使用方法: `--mm-tensor-ipc torch_shm`
  使用场景: 大图或大 Batch 密集服务. 如果服务前处理吞吐非常高, 将 IPC 协议更改为 `torch_shm` 可以有效规避多进程序列化的开销, 降低请求在前处理到进入模型阶段的系统延迟.

  ###########################################################################################

  --skip-mm-profiling, --no-skip-mm-profiling
                        When enabled, skips multimodal memory profiling and only profiles with language backbone model during engine initialization.
                        This reduces engine startup time but shifts the responsibility to users for estimating the peak memory usage of the activation of multimodal encoder
                        and embedding cache. (default: False)
  含义: 跳过 vLLM 启动阶段对多模态编码器显存占用的性能画像测试.
  使用方法: `--skip-mm-profiling`
  使用场景:
    1. 极大加快冷启动时间. 默认情况下, 多模态模型启动要花很长时间做前向图像模拟, 开启此项能秒级拉起服务.
    2. 规避老卡 Bug. 部分老卡(如 V100 等)在做启动时显存画像往往直接死锁, 设置此参数能正常启动服务.
    权衡(Trade-off): 跳过之后, 您需要手动配置合理、保守的 `--gpu-memory-utilization`, 否则可能有运行时因激活值过大而 OOM 的风险.

  ###########################################################################################

  --video-pruning-rate VIDEO_PRUNING_RATE
                        Sets pruning rate for video pruning via Efficient Video Sampling. Value sits in range [0;1) and determines fraction of media tokens from each video to
                        be pruned. (default: None)
  含义: 视频 Token 剪枝比例(范围 `[0, 1)`), 通过视频时空冗余采样剔除不重要的视觉 Token.
  使用方法: `--video-pruning-rate 0.5` (剪除 50% 视觉特征)
  使用场景: 超长视频理解. 输入包含多张长视频或一个超长监控片段时, 如果不做剪枝, 视觉 Token 数将直接淹没模型的 KV Cache. 通过此功能可以极大缓解首字延迟、加速推理, 并挽救内存.

  ###########################################################################################

LoRAConfig:
  Configuration for LoRA.

  ###########################################################################################

  --default-mm-loras DEFAULT_MM_LORAS
                        Dictionary mapping specific modalities to LoRA model paths; this field is only applicable to multimodal models and should be leveraged when a model
                        always expects a LoRA to be active when a given modality is present. Note that currently, if a request provides multiple additional modalities, each of
                        which have their own LoRA, we do NOT apply default_mm_loras because we currently only support one lora adapter per prompt. When run in offline mode,
                        the lora IDs for n modalities will be automatically assigned to 1-n with the names of the modalities in alphabetic order.
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)
  含义: 针对多模态(Multimodal, MM)模型, 指定当特定模态输入存在时, 默认自动加载和激活的 LoRA 模型路径映射关系.
  使用方法(传入 JSON 字符串):
    ```bash
    vllm serve Qwen/Qwen2-VL-7B-Instruct --enable-lora --default-mm-loras '{"image": "/path/to/image_special_lora"}'
    ```
  使用场景: 在多模态服务中, 当您希望只要输入中包含"图片"或"视频", 就自动套用特定的图像增强或视频理解 LoRA 适配器, 而无需客户端在每次 API 请求中显式带上 `lora` 的 ID. 需要注意的是, 目前 vLLM 在单次请求中通常只支持应用一个 LoRA 适配器, 如果请求中传入了多种不同的模态且它们都有各自的默认 LoRA, 系统为了避免冲突将不会应用这些默认 LoRA.

  ###########################################################################################

  --enable-lora, --no-enable-lora
                        If True, enable handling of LoRA adapters. (default: None)
  含义: 启用 LoRA 适配器支持, 并设置单批次中能同时并发激活的最大 LoRA 数量.
  使用方法: `--enable-lora --max-loras 4`
  使用场景:
    适用于"一个基座模型 + 多个微调任务"的低成本部署方案.
    客户端可以在 API 请求中携带 `lora_name` 动态路由到不同的微调分支. `--max-loras` 控制显存中预留给动态 LoRA 权重的空间.
  含义: 是否启用 LoRA 适配器处理. 默认为 `None`(实际行为等同于 `False`, 即默认不启用).
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora
    ```
  使用场景: 任何需要动态加载或在线推理 LoRA 模型的场景. 如果不开启此参数, 即使在请求中传入了 `lora_int` 等参数, vLLM 也会拒绝服务或报错.

  ###########################################################################################

  --enable-mixed-moe-lora-format, --no-enable-mixed-moe-lora-format
                        If True, force the engine to use the universal 2D MoE LoRA wrapper (`FusedMoEWithLoRA`) regardless of the model's `is_3d_moe_weight` flag, so that
                        2D-format and 3D-format MoE LoRA adapters can be served in the same deployment. Only meaningful forMoE models; ignored otherwise. Default False  keeps
                        the existing model-driven behavior. (default: False)
  含义: 强制引擎使用统一的 2D MoE LoRA 包装器(`FusedMoEWithLoRA`), 而不受模型自身 `is_3d_moe_weight` 标志的限制. 默认值为 `False`.
  使用方法:
    ```bash
    vllm serve mistralai/Mixtral-8x7B-v0.1 --enable-lora --enable-mixed-moe-lora-format
    ```
  使用场景: 在服务混合专家模型(MoE, 如 Mixtral 或 DeepSeek)时, 不同的 LoRA 适配器可能会有不同的参数排布格式(有些是以 2D 矩阵形式保存, 有些是 3D 堆叠形式). 开启此参数可以将它们统一用 2D 格式的融合算子处理, 从而允许在同一个服务实例中混合部署和调用不同格式训练出来的 MoE LoRA 适配器.

  ###########################################################################################

  --enable-tower-connector-lora, --no-enable-tower-connector-lora
                        If `True`, LoRA support for the tower (vision encoder) and connector  of multimodal models will be enabled. This is an experimental feature and
                        currently only supports some MM models such as the Qwen VL series. The default  is False. (default: False)
  含义: 是否允许对多模态模型中的视觉编码器(Vision Tower)和连接器(Connector/Projector)应用 LoRA. 默认值为 `False`(这是一个实验性功能).
  使用方法:
    ```bash
    vllm serve Qwen/Qwen2-VL-7B-Instruct --enable-lora --enable-tower-connector-lora
    ```
  使用场景: 当您在微调多模态大模型时, 不仅对 LLM 骨干网络(Backbone)进行了 LoRA 微调, 还对视觉特征提取器(如 ViT)或连接视觉与语言空间的 Connector 进行了 LoRA 微调(例如 Qwen-VL 系列的微调). 开启此开关可以支持这部分非 LLM 模块的 LoRA 权重动态加载.

  ###########################################################################################

  --fully-sharded-loras, --no-fully-sharded-loras
                        By default, only half of the LoRA computation is sharded with tensor parallelism. Enabling this will use the fully sharded layers. At high sequence
                        length, max rank or tensor parallel size, this is likely faster. (default: False)
  含义: 控制在张量并行(Tensor Parallel, TP)多卡部署时, LoRA 计算的切分策略. 默认情况下(False), 只有一半的 LoRA 计算在多卡间切分. 启用后(True), 将对整个 LoRA 算子进行完全切分(Fully Sharded).
  使用方法:
    ```bash
    vllm serve meta-llama/Meta-Llama-3-70B-Instruct --tensor-parallel-size 4 --enable-lora --fully-sharded-loras
    ```
  使用场景: 当您使用多张 GPU 进行张量并行(TP)推理, 且面临长文本(high sequence length)、高 Rank(max rank)或者 TP 规模较大(如 TP=4 或 TP=8)的场景. 在这种情况下, 完全切分可以减少单卡的计算瓶颈, 虽然会增加卡间通信次数, 但整体计算速度通常会有明显提升.

  ###########################################################################################

  --lora-dtype {auto,bfloat16,float16}
                        Data type for LoRA. If auto, will default to base model dtype. (default: auto)
  含义: 指定 LoRA 权重的计算精度. 支持 `{auto, bfloat16, float16}`, 默认为 `auto`(即自动匹配基座模型的精度).
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --lora-dtype float16
    ```
  使用场景: 通常建议保持 `auto`. 如果您的基座模型是 `float16`, 但您希望强制将 LoRA 权重转为 `bfloat16` 计算以防溢出(或者反之, 为了在特定显卡上获得更好的加速), 可以手动指定.

  ###########################################################################################

  --lora-target-modules LORA_TARGET_MODULES [LORA_TARGET_MODULES ...]
                        Restrict LoRA to specific module suffixes (e.g., ["o_proj", "qkv_proj"]). If None, all supported LoRA modules are used. This allows deployment-time
                        control over which modules have LoRA applied, useful for performance tuning. (default: None)
  含义: 限制 LoRA 作用的具体模块. 如果不指定(默认 None), vLLM 会对适配器中包含的所有支持的模块(如 `q_proj`, `v_proj` 等)进行预分配和激活.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --lora-target-modules q_proj v_proj
    ```
  使用场景: 性能调优. 如果您训练的 LoRA 仅作用于 `q_proj` 和 `v_proj`, 而在启动时显式限制, 可以防止 vLLM 为不需要的模块(如 `o_proj` 或 `gate_proj`)预分配多余的显存和生成算子, 从而节省显存并加快初始化.

  ###########################################################################################

  --max-cpu-loras MAX_CPU_LORAS
                        Maximum number of LoRAs to store in CPU memory. Must be >= than `max_loras`. (default: None)
  含义: 在主机内存(CPU RAM)中缓存的最大 LoRA 数量. 该值必须大于或等于 `max_loras`.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --max-loras 4 --max-cpu-loras 64
    ```
  使用场景: 当您有大量的 LoRA 适配器(例如几十个甚至上百个), 但 GPU 显存有限, 无法将它们全部常驻在显存中. 通过此参数, vLLM 会把不常用的 LoRA 缓存在 CPU 内存中. 当有新请求需要某个 LoRA 时, 再快速从 CPU 交换(Swap)到 GPU 显存, 避免了频繁读取磁盘的 IO 瓶颈.

  ###########################################################################################

  --max-lora-rank {1,8,16,32,64,128,256,320,512}
                        Max LoRA rank. (default: 16)
  含义: 系统支持的 LoRA 最大秩(Rank/`r`). 默认值为 `16`. 可选值通常为 2 的幂(如 1, 8, 16, 32, 64, 128 等).
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --max-lora-rank 64
    ```
  使用场景: 当您训练的 LoRA 模型的 Rank 超过了默认的 16(例如使用 Rank=32 或 64 训练的 LoRA)时, 必须在启动服务时显式指定这个参数, 否则 vLLM 在加载高 Rank LoRA 时会因为显存预分配不足而报错. 如果所有 LoRA 的 Rank 都很小(例如 8), 可以将其调小以节省显存.

  ###########################################################################################

  --max-loras MAX_LORAS
                        Max number of LoRAs in a single batch. (default: 1)
  含义: 启用 LoRA 适配器支持, 并设置单批次中能同时并发激活的最大 LoRA 数量.
  使用方法: `--enable-lora --max-loras 4`
  使用场景:
    适用于"一个基座模型 + 多个微调任务"的低成本部署方案.
    客户端可以在 API 请求中携带 `lora_name` 动态路由到不同的微调分支. `--max-loras` 控制显存中预留给动态 LoRA 权重的空间.
  含义: 在单个 Batch(批处理)中, 允许同时激活和计算的最大不同 LoRA 适配器数量. 默认值为 `1`.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --max-loras 4
    ```
  使用场景: 高并发多租户服务. 例如, 部署了一个基础模型, 有多个用户同时发送请求, 用户 A 使用微调版 A(LoRA_A), 用户 B 使用微调版 B(LoRA_B). 如果 `max_loras` 设为 4, vLLM 可以把针对 4 种不同 LoRA 的请求放在同一个 batch 里合并计算. 设得越大, 并发合并能力越强, 但显存占用也越高.

  ###########################################################################################

  --specialize-active-lora, --no-specialize-active-lora
                        Whether to construct lora kernel grid by the number of active LoRA adapters. When set to True, separate cuda graphs will be captured for different
                        counts of active LoRAs (powers of 2 up to max_loras), which can improve performance for variable LoRA usage patterns at the cost of increased startup
                        time and memory usage. Only takes effect when cudagraph_specialize_lora is True. (default: False)
  含义: 是否根据当前活跃的 LoRA 数量来特异化构建 CUDA Graph 的网格(Grid). 只有当 `cudagraph_specialize_lora` 也为 `True` 时, 该参数才会生效. 默认值为 `False`.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-lora --specialize-active-lora
    ```
  使用场景: 动态且高并发的 LoRA 推理场景. CUDA Graph 推理能够显著降低 CPU 提交任务给 GPU 的开销, 但它的结构通常是静态的. 当活跃的 LoRA 数量(例如, 当前 batch 里有 1 个、2 个或 4 个不同的 LoRA 正在被计算)频繁变化时, CUDA 算子的形状会变. 如果开启此参数, vLLM 会针对不同数量(通常以 2 的幂次方递增, 如 1, 2, 4 等直至 `max_loras`)的活跃 LoRA 预先捕获多套独立的 CUDA Graphs.
      权衡(Trade-off): 它可以提升变动负载下的推理性能, 但是会增加服务的启动时间(Startup Time)以及消耗更多的显存.

  ###########################################################################################

ObservabilityConfig:
  Configuration for observability - metrics and tracing.

  ###########################################################################################

  --collect-detailed-traces {all,model,worker,None} [{all,model,worker,None} ...]
                        It makes sense to set this only if `--otlp-traces-endpoint` is set. If set, it will collect detailed traces for the specified modules. This involves
                        use of possibly costly and or blocking operations and hence might have a performance impact.
                        Note that collecting detailed timing information for each request can be expensive. (default: None)
  含义: 控制收集哪些模块的详细追踪信息(可选择 `all`、`model`、`worker` 或不收集 `None`). 必须首先设置 `--otlp-traces-endpoint`. 由于收集详细的耗时和调用栈包含部分阻塞或开销较高的操作, 可能会对生产环境性能产生一定负面影响.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m \
      --otlp-traces-endpoint http://localhost:4317 \
      --collect-detailed-traces model worker
    ```
  使用场景: 深入性能调优和瓶颈排查. 当发现推理延迟(Time-to-First-Token 或 Inter-Token Latency)有异常抖动时, 在测试环境开启此参数, 可以清晰地看出延迟是由模型计算(`model`)引起, 还是多卡/多机通信(`worker` 之间的 NCCL 交互)引起的. 生产环境一般建议设为 `None` 或仅在低流量时谨慎开启.

  ###########################################################################################

  --cudagraph-metrics, --no-cudagraph-metrics
                        Enable CUDA graph metrics (number of padded/unpadded tokens, runtime cudagraph dispatch modes, and their observed frequencies at every logging
                        interval). (default: False)
  含义: 启用或禁用 CUDA Graph(CUDA 图)相关的监控指标. 开启后会收集被填充(padded)和未填充(unpadded)的 Token 数量、CUDA 图的调度分发模式(dispatch modes)以及在每次日志输出间隔内的观测频率.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --cudagraph-metrics
    ```
  使用场景: CUDA Graph 优化与显存/计算平衡分析. vLLM 默认使用 CUDA Graph 来消除 PyTorch 算子发射的 CPU 开销, 但 CUDA Graph 要求输入 Shape 是静态或分桶的, 这会导致填充(Padding)浪费. 通过监控此指标, 您可以评估当前设置的 `gpu_memory_utilization` 和模型输入分布是否导致了过多的 Padding, 从而协助优化分桶策略.

  ###########################################################################################

  --enable-layerwise-nvtx-tracing, --no-enable-layerwise-nvtx-tracing
                        Enable layerwise NVTX tracing. This traces the execution of each layer or module in the model and attach information such as input/output shapes to
                        nvtx range markers. Noted that this doesn't work with CUDA graphs enabled. (default: False)
  含义: 启用或禁用逐层(layerwise)的 NVTX 追踪. 它会在每个 Transformer 层或模块的执行边界插入 NVTX 标记(Range Markers), 并在标记中附加输入/输出张量的 Shape 等元数据. 注意: 此功能与 CUDA Graph 冲突, 无法同时生效.
  使用方法:
    需要显式禁用 CUDA Graph(如使用 eager 模式)并配合 NVIDIA Nsight Systems 进行 Profile:
    ```bash
    # 启动 vLLM 服务
    vllm serve facebook/opt-125m --enforce-eager --enable-layerwise-nvtx-tracing

    # 或者使用 nsys 启动
    nsys profile -o my_profile_report vllm serve facebook/opt-125m --enforce-eager --enable-layerwise-nvtx-tracing
    ```
  使用场景: 算子级和层级深度性能剖析. 多用于性能优化工程师. 当您需要使用 NVIDIA Nsight Systems (nsys) 或 PyTorch Profiler 导出 timeline 视图时, 此参数能在可视化时间线中清晰标出 "Attention"、"MLP"、"LayerNorm" 等模块的具体边界与 Shape, 方便精细化诊断某个特定自定义算子(如 FlashAttention 或 FP8 算子)的瓶颈.

  ###########################################################################################

  --enable-logging-iteration-details, --no-enable-logging-iteration-details
                        Enable detailed logging of iteration details. If set, vllm EngineCore will log iteration details This includes number of context/generation requests
                        and tokens and the elapsed cpu time for the iteration. (default: False)
  含义: 启用或禁用详细的迭代级(iteration)日志输出. 开启后, vLLM 的引擎核心(EngineCore)会在日志中打印每次迭代的详细信息, 包括当前正在处理的 Prefill(上下文)请求数、Decode(生成)请求数、Token 数量以及该次迭代消耗的 CPU 时间.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-logging-iteration-details
    ```
  使用场景: 调度器(Scheduler)行为诊断. 在测试高并发或复杂 Prompt 场景(如混合长短文本、开启 Chunked Prefill 等)时, 可以通过这些日志观察 vLLM 的连续批处理(Continuous Batching)调度器是否工作符合预期, 判断系统是在做密集的 Prefill 还是 Decode, 以及 CPU 调度层是否存在过大的开销.

  ###########################################################################################

  --enable-mfu-metrics, --no-enable-mfu-metrics
                        Enable Model FLOPs Utilization (MFU) metrics. (default: False)
  含义: 启用或禁用模型 FLOPs 利用率(Model FLOPs Utilization, MFU)指标计算. MFU 衡量的是硬件实际计算吞吐占 GPU 理论半精度(或对应精度)峰值算力的百分比.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --enable-mfu-metrics
    ```
  使用场景: 硬件效率与性价比评估. 在私有化部署、高并发压测时, 通过 Prometheus 监控 MFU. 如果 MFU 偏低(例如低于 20%), 说明硬件算力未被充分榨干, 可能是受限于带宽、调度、或 KV Cache 频繁换入换出, 提示需要调整 `max_model_len` 或 `max_num_seqs`.

  ###########################################################################################

  --kv-cache-metrics, --no-kv-cache-metrics
                        Enable KV cache residency metrics (lifetime, idle time, reuse gaps). Uses sampling to minimize overhead. Requires log stats to be enabled (i.e.,
                        --disable-log-stats not set). (default: False)
  --kv-cache-metrics-sample KV_CACHE_METRICS_SAMPLE
                        Sampling rate for KV cache metrics (0.0, 1.0]. Default 0.01 = 1% of blocks. (default: 0.01)
  含义:
      `--kv-cache-metrics`: 启用或禁用 KV Cache 块动态变化的指标监控(包括 block 的生命周期、闲置时间、重用间隔等). 必须确保 `--disable-log-stats` 未被设置(即允许统计日志输出).
      `--kv-cache-metrics-sample`: 设置 KV Cache 监控的采样率, 取值范围为 `(0.0, 1.0]`, 默认值为 `0.01`(即对 1% 的 block 进行采样跟踪), 以尽量减少对服务性能的干扰.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --kv-cache-metrics --kv-cache-metrics-sample 0.05
    ```
  使用场景: KV Cache 与 Prefix Caching(前缀缓存)优化. 在使用 RadixAttention(自动前缀缓存)或处理长文本多轮对话的多用户场景下, 这两个参数非常重要. 它们可以帮助您分析缓存的命中率(Hit Rate)、物理块被闲置多久才被释放或重用. 这能为您调整 `gpu_memory_utilization` 或优化系统提示词(System Prompt)复用提供有力的数据支持.

  ###########################################################################################

  --otlp-traces-endpoint OTLP_TRACES_ENDPOINT
                        Target URL to which OpenTelemetry traces will be sent. (default: None)
  含义: 将 OpenTelemetry 链路追踪数据发送到指定的接收端.
  使用方法: `--otlp-traces-endpoint http://jaeger-collector:4317`
  使用场景: 企业级微服务监控. 配合 Prometheus/Jaeger 收集和分析每个请求在 vLLM 内部各个阶段(分词、排队、Prefill、Decode)的耗时.
  含义: 指定 OpenTelemetry (OTel) 追踪数据发送的接收端 URL. 支持 gRPC 或 HTTP 协议.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --otlp-traces-endpoint http://localhost:4317
    ```
    (通常配合 Jaeger、Zipkin、Tempo 或 Datadog Collector 等分布式追踪后端使用.)
  使用场景: 分布式追踪与全链路监控. 在微服务架构中, 当请求通过 API 网关、业务后端最终到达 vLLM 服务时, 可以使用此参数进行全链路 Trace 监控, 分析请求在 vLLM 内部各个阶段(如调度、推理、后处理)的耗时比例.

  ###########################################################################################

  --show-hidden-metrics-for-version SHOW_HIDDEN_METRICS_FOR_VERSION
                        Enable deprecated Prometheus metrics that have been hidden since the specified version. For example, if a previously deprecated metric has been hidden
                        since the v0.7.0 release, you use `--show-hidden-metrics-for-version=0.7` as a temporary escape hatch while you migrate to new metrics. The metric is
                        likely to be removed completely in an upcoming release. (default: None)
  含义: 临时开启从指定版本起被废弃并隐藏的 Prometheus 指标. 这是一个向后兼容的临时过渡开关. 例如, 如果某个指标在 v0.7.0 版本中被废弃并隐藏了, 但您的监控基础设施尚未迁移, 可以使用该参数来使其重新显示.
  使用方法:
    ```bash
    vllm serve facebook/opt-125m --show-hidden-metrics-for-version=0.7
    ```
  使用场景: 生产环境平滑升级. 当您将 vLLM 从旧版本升级到新版本时, 现有的 Grafana 仪表盘或自动化告警可能依赖了已被 vLLM 废弃的旧指标名称. 此时可利用此参数作为临时过渡手段, 避免升级后监控大屏出现断崖或误告警, 争取时间去修改和适配新的指标标准.

  ###########################################################################################

SchedulerConfig:
  Scheduler configuration.

  ###########################################################################################

  --async-scheduling, --no-async-scheduling
                        If set to False, disable async scheduling. Async scheduling helps to avoid gaps in GPU utilization, leading to better latency and throughput. (default:
                        None)
  参数含义: 控制是否开启异步调度. 若启用, CPU 调度器会在 GPU 执行当前 Iteration 的前向传播时, 提前在后台异步计算下一个 Iteration 的调度决策(打包哪些请求、分配哪些 Block), 从而消除 CPU-GPU 之间的交替等待空闲(Gap).
  使用方法: `--async-scheduling`.
  使用场景:
    线上高吞吐 serving 服务: 在大规模并发请求、多 GPU Tensor Parallel (TP) 或 Pipeline Parallel (PP) 的分布式服务中, 开启此参数能有效减少 GPU 气泡(Bubbles), 最大化硬件利用率.

  ###########################################################################################

  --disable-chunked-mm-input, --no-disable-chunked-mm-input
                        If set to true and chunked prefill is enabled, we do not want to partially schedule a multimodal item. Only used in V1 This ensures that if a request
                        has a mixed prompt (like text tokens TTTT followed by image tokens IIIIIIIIII) where only some image tokens can be scheduled (like TTTTIIIII, leaving
                        IIIII), it will be scheduled as TTTT in one step and IIIIIIIIII in the next. (default: False)
  参数含义: 在 vLLM V1 引擎中, 如果启用了 Chunked Prefill, 该参数决定是否禁止对多模态输入(如图像 Token)进行分块调度. 若设为 True, 混合输入中的图像 Token 将作为整体, 不会被切分到不同的步骤中.
  使用方法: `--disable-chunked-mm-input`.
  使用场景:
    多模态模型(VLM)服务: 当服务包含图像或视频输入(如 Qwen-VL、LLaVA)且开启了 Chunked Prefill 时. 如果图像 Token 被强行切分处理, 可能会引入额外的视觉编码对齐开销. 开启此参数可确保多模态元素在单一推理步骤中完整处理, 保障图像特征计算的一致性.

  ###########################################################################################

  --disable-hybrid-kv-cache-manager, --no-disable-hybrid-kv-cache-manager
                        If set to True, KV cache manager will allocate the same size of KV cache for all attention layers even if there are multiple type of attention layers
                        like full attention and sliding window attention. If set to None, the default value will be determined based on the environment and starting
                        configuration. (default: None)
  参数含义: 混合 KV 缓存管理器主要用于处理"同时包含 Full Attention 层与高效高效注意力层(如 Sliding Window Attention 滑动窗口注意力, 类似 Mistral/Gemma 模型)"的混合架构模型.
    若为 None/False(默认): vLLM 自动开启 HMA(Hybrid Memory Allocation), 对滑动窗口层分配更小的 KV 缓存, 对 Full Attention 分配标准缓存, 从而节省大量显存.
    若设为 True: 强制所有层分配相同尺寸的 KV 缓存.
  使用方法: `--disable-hybrid-kv-cache-manager`.
  使用场景:
    特殊功能兼容/排错: 目前在启用某些高级特性(例如将 KV 缓存换出到系统内存 `Spill-to-RAM`, 或者在使用某些不支持 HMA 动态块对齐的第三方 KV 传输/优化插件, 如 NIXL、LMCache 等)时, 系统可能会抛出不支持 HMA 的报错. 此时, 需要通过指定该参数为 True 来屏蔽 HMA 机制以确保程序正常启动.

  ###########################################################################################

  --enable-chunked-prefill, --no-enable-chunked-prefill
                        If True, prefill requests can be chunked based on the remaining `max_num_batched_tokens`.
                        The default value here is mainly for convenience when testing. In real usage, this should be set in `EngineArgs.create_engine_config`. (default: None)
  含义: 启用分块预填充(Chunked Prefill).
  使用方法: `--enable-chunked-prefill`
  使用场景:
    在长文本(如长文档问答)与短文本混合输入的场景下.
    默认情况下, 一个超长 Prompt 会占用整个 GPU 的计算资源进行 Prefill, 导致此时其他已在 Decode(生成)阶段的短请求卡顿. 开启分块后, 大 Prompt 会被拆细, 与 Decode 任务流水线式并发执行, 能极大改善服务在长文本混合输入下的首字延迟和整体响应流畅度.
  参数含义: 是否启用分块预填充. 开启后, 长 Prompt 会被切分为若干个小 Chunk(大小受限于 `max_num_batched_tokens`), 分步在多个调度周期内完成 Prefill. 这使得 Prefill 和 Decode 可以混合在一个 Batch 中执行.
  使用方法: 通过 `--enable-chunked-prefill` 显式开启.
  使用场景:
    长文本与短文本混杂的线上服务: 如 RAG 检索问答、长文档分析. 如果不开启, 一个 32K 的大文档 Prefill 会直接霸占 GPU 资源数秒, 导致其他处于 Decode 阶段的短请求出现明显的卡顿(逐字输出暂停). 开启后可显著优化 ITL(Inter-Token Latency, Token 间延迟).

  ###########################################################################################

  --long-prefill-token-threshold LONG_PREFILL_TOKEN_THRESHOLD
                        For chunked prefill, a request is considered long if the prompt is longer than this number of tokens. (default: 0)
  参数含义: 定义一个 Prompt 的 Token 长度达到多少时, 才被认定为"长 Prefill 请求".
  使用方法: 设置整数值, 例如 `--long-prefill-token-threshold 1024`(默认值为 0, 表示只要开启了 Chunked Prefill, 所有请求都可能被分块).
  使用场景:
    混合任务调度细化: 用于区分短查询(如 "Hello")与长分析(如 2000 字论文). 将该阈值设为合理的值(如 1024), 可以让短查询避免不必要的分块调度开销, 直接一次性完成 Prefill, 保障极短的 TTFT(Time-To-First-Token).

  ###########################################################################################

  --max-long-partial-prefills MAX_LONG_PARTIAL_PREFILLS
                        For chunked prefill, the maximum number of prompts longer than long_prefill_token_threshold that will be prefilled concurrently. Setting this less than
                        max_num_partial_prefills will allow shorter prompts to jump the queue in front of longer prompts in some cases, improving latency. (default: 1)
  参数含义: 在 Chunked Prefill 模式下, 允许同时进行分块预填充的、长度超过 `long-prefill-token-threshold` 的"特长请求"的最大并发数.
  使用方法: `--max-long-partial-prefills 1`(默认值为 1).
  使用场景:
    防队列堵塞(Head-of-Line Blocking): 当此值设得比 `--max-num-partial-prefills` 小时, 如果已经有一个特长文本在占着通道做分块 Prefill, 新进来的中等长度 Prompt(低于 threshold)可以"插队"抢先完成 Prefill. 这非常适用于保障中短请求的响应延迟, 避免其被个别超长文档任务无限期

  ###########################################################################################

  --max-num-batched-tokens MAX_NUM_BATCHED_TOKENS
                        Maximum number of tokens that can be processed in a single iteration.
                        The default value here is mainly for convenience when testing. In real usage, this should be set in `EngineArgs.create_engine_config`.
                        Parse human-readable integers like '1k', '2M', etc. Including decimal values with decimal multipliers.
                            Examples:
                            - '1k' -> 1,000
                            - '1K' -> 1,024
                            - '25.6k' -> 25,600 (default: None)
  参数含义: 单次推理迭代中, 允许处理的最大 Token 总数(包括所有请求的预填充 prefill token 和生成 decode token 的总和).
  使用方法: 可输入带单位的值, 如 `--max-num-batched-tokens 2k`(2,000)或 `--max-num-batched-tokens 16K`(16,384).
  使用场景:
    吞吐量优先: 设置为较大的值(如 4096 或更高)可以使 vLLM 尽可能多地打包 Token 进行批处理, 充分压榨 GPU 算力.
    延迟与显存控制: 若遇到 CUDA 报告激活值(Activation Memory)或算子开销过大, 可适当调低此值以减少单词迭代的计算延迟和峰值显存.

  ###########################################################################################

  --max-num-partial-prefills MAX_NUM_PARTIAL_PREFILLS
                        For chunked prefill, the maximum number of sequences that can be partially prefilled concurrently. (default: 1)
  参数含义: 在 Chunked Prefill 模式下, 允许同时处于"部分预填充(即尚未完成全部 Prefill)"状态的最大请求序列数.
  使用方法: `--max-num-partial-prefills 2`(默认值为 1).
  使用场景:
    微调分块并发: 如果线上服务有多个并行的长文本请求, 将其设置为大于 1 的值可以允许 vLLM 在单次迭代中, 同时为两个不同的长请求计算它们各自的 Prefill 块. 但这会占用更多的 Batch 槽位, 通常需要配合 GPU 算力精细调整.

  ###########################################################################################

  --max-num-seqs MAX_NUM_SEQS
                        Maximum number of sequences to be processed in a single iteration.
                        The default value here is mainly for convenience when testing. In real usage, this should be set in `EngineArgs.create_engine_config`. (default: None)
  参数含义: 控制单次推理迭代中, 可同时处理的最大序列(请求)数量. 这决定了 decode(生成阶段)的最大并发 batch size.
  使用方法: 通常在启动命令行中设置, 如 `--max-num-seqs 256`. 若不设置, vLLM 会根据默认值进行测试(实际生产建议显式配置).
  使用场景:
    高并发轻量级任务: 如简短的单轮对话、分类任务, 可调高该值(如 256 或 512)以利用 GPU 的并行计算能力, 提升整体吞吐量.
    重度长文本/高显存压力任务: 如果模型本身很大, 或者请求的上下文极长, 调低该值(如 16 或 32)可以防止瞬时并发过高导致显存溢出(OOM)或频繁的抢占(Preemption).

  ###########################################################################################

  --scheduler-cls SCHEDULER_CLS
                        The scheduler class to use. "vllm.v1.core.sched.scheduler.Scheduler" is the default scheduler. Can be a class directly or the path to a class of form
                        "mod.custom_class". (default: None)
  参数含义: 允许指定自定义的 Python 调度器类路径, 替代默认的 vLLM 调度器核心.
  使用方法: `--scheduler-cls "my_module.MyCustomScheduler"`.
  使用场景:
    学术研究与企业深度定制: 当您作为高级研究员, 需要实现一套更复杂的调度算法(例如基于强化学习的动态负载均衡、SLO 敏感型调度, 或者需要与其他调度系统深度融合时).

  ###########################################################################################

  --scheduler-reserve-full-isl, --no-scheduler-reserve-full-isl
                        If True, the scheduler checks whether the full input sequence length fits in the KV cache before admitting a new request, rather than only checking the
                        first chunk. Prevents over-admission and KV cache thrashing with chunked prefill. (default: True)
  参数含义: ISL 代表 Input Sequence Length(输入序列长度). 当设为 True(默认值)时, 调度器在决定接纳(Admit)一个新请求进行 Chunked Prefill 之前, 会先检查 KV Cache 剩余空间是否装得下其完整的最大预估序列长度, 而不仅仅是检查能不能塞下第一个 Chunk.
  使用方法: `--scheduler-reserve-full-isl` 或 `--no-scheduler-reserve-full-isl`.
  使用场景:
    稳定推理防抢占(默认推荐): 设置为 True(默认)能彻底防止"超额准入"(Over-admission). 如果新请求在执行到一半时因为显存耗尽而被抢占/驱逐, 会产生高昂的重新计算代价.
    高并发极致压榨(需谨慎): 若您确信用户的实际输出长度远小于最大限制, 或者愿意承担因显存不足导致部分请求被暂停/换出的风险, 可以将其关闭以提升瞬时接纳率. 但注意, 在一些极端的超长模型配置下, 关闭此选项可能导致请求卡死在等待队列中.

  ###########################################################################################

  --scheduling-policy {fcfs,priority}
                        The scheduling policy to use:
                        - "fcfs" means first come first served, i.e. requests are handled in order  of arrival.
                        - "priority" means requests are handled based on given priority (lower value means earlier handling) and time of arrival deciding any ties). (default:
                        fcfs)
  参数含义: 调度队列中请求的优先级排序策略.
    `fcfs`: 先来先服务(First-Come-First-Served), 根据请求到达的时间顺序进行调度.
    `priority`: 优先级调度, 根据请求中附带的 priority 值(数值越低优先级越高)进行排序调度, 相同优先级的再按时间排序.
  使用方法: `--scheduling-policy priority`.
  使用场景:
    FCFS: 标准的开放式公共大模型 API 场景.
    Priority: 适用于多租户 SaaS 平台、智能体(Agent)工作流服务. 例如: 给"付费 VIP 用户"或"需要即时响应的 Tool-Call 节点"分配高优先级, 而将"异步文档翻译任务"或"免费用户"设为低优先级, 从而在系统高负载时确保关键业务的 SLA.

  ###########################################################################################

  --stream-interval STREAM_INTERVAL
                        The interval (or buffer size) for streaming in terms of token length. A smaller value (1) makes streaming smoother by sending each token immediately,
                        while a larger value (e.g., 10) reduces host overhead and may increase throughput by batching multiple tokens before sending. (default: 1)
  参数含义: 流式输出时的 Token 缓冲区大小(间隔). 若设为 1, 生成一个 Token 就立即向客户端发送一次; 若设为 5, 则在引擎内部积攒 5 个 Token 后再统一发送给客户端.
  使用方法: `--stream-interval 1`(默认值为 1).
  使用场景:
    极致打字机交互(流式对话): 使用默认值 1, 可以让用户感知到最灵敏的输出速度.
    非交互式/后台批量处理: 若用户不需要实时观看打字过程(如后台 RAG 向量提取、Agent 链条自动执行、批量文本翻译), 推荐调大此值(如 4 或 8). 这样能显著降低网络 I/O、HTTP 序列化和事件循环的系统调用开销, 提高服务端的整体处理吞吐量.

  ###########################################################################################

CompilationConfig:
  Configuration for compilation.

      You must pass CompilationConfig to VLLMConfig constructor.
      VLLMConfig's post_init does further initialization. If used outside of the
      VLLMConfig, some fields will be left in an improper state.

      It contains PassConfig, which controls the custom fusion/transformation passes.
      The rest has three parts:

      - Top-level Compilation control:
          - [`mode`][vllm.config.CompilationConfig.mode]
          - [`debug_dump_path`][vllm.config.CompilationConfig.debug_dump_path]
          - [`cache_dir`][vllm.config.CompilationConfig.cache_dir]
          - [`backend`][vllm.config.CompilationConfig.backend]
          - [`custom_ops`][vllm.config.CompilationConfig.custom_ops]
          - [`splitting_ops`][vllm.config.CompilationConfig.splitting_ops]
          - [`compile_mm_encoder`][vllm.config.CompilationConfig.compile_mm_encoder]
      - CudaGraph capture:
          - [`cudagraph_mode`][vllm.config.CompilationConfig.cudagraph_mode]
          - [`cudagraph_capture_sizes`]
          [vllm.config.CompilationConfig.cudagraph_capture_sizes]
          - [`max_cudagraph_capture_size`]
          [vllm.config.CompilationConfig.max_cudagraph_capture_size]
          - [`cudagraph_num_of_warmups`]
          [vllm.config.CompilationConfig.cudagraph_num_of_warmups]
          - [`cudagraph_copy_inputs`]
          [vllm.config.CompilationConfig.cudagraph_copy_inputs]
      - Inductor compilation:
          - [`compile_sizes`][vllm.config.CompilationConfig.compile_sizes]
          - [`compile_ranges_endpoints`]
              [vllm.config.CompilationConfig.compile_ranges_endpoints]
          - [`inductor_compile_config`]
          [vllm.config.CompilationConfig.inductor_compile_config]
          - [`inductor_passes`][vllm.config.CompilationConfig.inductor_passes]
          - custom inductor passes

      Why we have different sizes for cudagraph and inductor:
      - cudagraph: a cudagraph captured for a specific size can only be used
          for the same size. We need to capture all the sizes we want to use.
      - inductor: a graph compiled by inductor for a general shape can be used
          for different sizes. Inductor can also compile for specific sizes,
          where it can have more information to optimize the graph with fully
          static shapes. However, we find the general shape compilation is
          sufficient for most cases. It might be beneficial to compile for
          certain small batchsizes, where inductor is good at optimizing.


  ###########################################################################################

  --cudagraph-capture-sizes CUDAGRAPH_CAPTURE_SIZES [CUDAGRAPH_CAPTURE_SIZES ...]
                        Sizes to capture cudagraph.
                        - None (default): capture sizes are inferred from vllm config.
                        - list[int]: capture sizes are specified as given. (default: None)

  ###########################################################################################

  --max-cudagraph-capture-size MAX_CUDAGRAPH_CAPTURE_SIZE
                        The maximum cudagraph capture size.
                        If cudagraph_capture_sizes is specified, this will be set to the largest size in that list (or checked for consistency if specified). If
                        cudagraph_capture_sizes is not specified, the list of sizes is generated automatically following the pattern:
                            [1, 2, 4] + list(range(8, 256, 8)) + list( range(256, max_cudagraph_capture_size + 1, 16))
                        If not specified, max_cudagraph_capture_size is set to min(max_num_seqs*2, 512) by default. This voids OOM in tight memory scenarios with small
                        max_num_seqs, and prevents capture of many large graphs (>512) that would greatly increase startup time with limited performance benefit. (default:
                        None)

  ###########################################################################################

KernelConfig:
  Configuration for kernel selection and warmup behavior.

  ###########################################################################################

  --enable-flashinfer-autotune, --no-enable-flashinfer-autotune
                        If True, run FlashInfer autotuning during kernel warmup. (default: None)

  ###########################################################################################

  --ir-op-priority IR_OP_PRIORITY
                        vLLM IR op priority for dispatching/lowering during the forward pass. Platform defaults appended automatically during VllmConfig.__post_init__.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.IrOpPriorityConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: IrOpPriorityConfig(rms_norm=[], fused_add_rms_norm=[]))

  ###########################################################################################

  --linear-backend {aiter,auto,conch,cutlass,deep_gemm,emulation,exllama,fbgemm,flashinfer_cudnn,flashinfer_cutlass,flashinfer_trtllm,machete,marlin,torch,triton}
                        Backend for quantized linear layer GEMM kernels. Available options:
                        - "auto": Automatically select the best backend based on model and hardware
                        - "cutlass": Use CUTLASS-based kernels
                        - "flashinfer_cutlass": Use FlashInfer with CUTLASS kernels
                        - "flashinfer_trtllm": Use FlashInfer with TensorRT-LLM kernels
                        - "flashinfer_cudnn": Use FlashInfer with cuDNN kernels
                        - "marlin": Use Marlin kernels
                        - "triton": Use Triton-based kernels
                        - "deep_gemm": Use DeepGEMM kernels
                        - "torch": Use PyTorch native scaled_mm kernels
                        - "aiter": Use AMD AITer kernels (ROCm only)
                        - "machete": Use Machete kernels (mixed-precision)
                        - "fbgemm": Use FBGEMM kernels
                        - "conch": Use Conch mixed-precision kernels
                        - "exllama": Use Exllama mixed-precision kernels
                        - "emulation": Use slow dequant-to-BF16 emulation (for testing only) (default: auto)
  含义: 指定 quantized 线性层与混合专家模型(MoE)的计算内核后端.
  使用方法: `--linear-backend deep_gemm`
  使用场景:
    在运行特定大模型(如 DeepSeek-V3/R1 架构模型)时, 指定高性能算子库(如 `deep_gemm` 或者是 `flashinfer_cutlass`)可以显著压榨硬件算力, 优化矩阵乘法效率.

  ###########################################################################################

  --moe-backend {aiter,auto,cutlass,deep_gemm,deep_gemm_mega_moe,emulation,flashinfer_b12x,flashinfer_cutedsl,flashinfer_cutlass,flashinfer_trtllm,humming,marlin,triton,triton_unfused}
                        Backend for MoE expert computation kernels. Available options:
                        - "auto": Automatically select the best backend based on model and hardware
                        - "triton": Use Triton-based fused MoE kernels
                        - "deep_gemm": Use DeepGEMM kernels (FP8 block-quantized only)
                        - "deep_gemm_mega_moe": Use DeepGEMM mega MoE kernels
                        - "cutlass": Use vLLM CUTLASS kernels
                        - "flashinfer_trtllm": Use FlashInfer with TRTLLM-GEN kernels
                        - "flashinfer_cutlass": Use FlashInfer with CUTLASS kernels
                        - "flashinfer_cutedsl": Use FlashInfer with CuteDSL kernels (FP4 only)
                        - "flashinfer_b12x": Use FlashInfer CuteDSL fused MoE for SM12x (RTX Pro 6000 / DGX Spark)
                        - "marlin": Use Marlin kernels (weight-only quantization)
                        - "humming": Use Humming Mixed Precision kernels
                        - "triton_unfused": Use Triton unfused MoE kernels
                        - "aiter": Use AMD AITer kernels (ROCm only)
                        - "emulation": use BF16/FP16 GEMM, dequantizing weights and running QDQ on activations. (default: auto)
  含义: 指定 quantized 线性层与混合专家模型(MoE)的计算内核后端.
  使用方法: `--linear-backend deep_gemm`
  使用场景:
    在运行特定大模型(如 DeepSeek-V3/R1 架构模型)时, 指定高性能算子库(如 `deep_gemm` 或者是 `flashinfer_cutlass`)可以显著压榨硬件算力, 优化矩阵乘法效率.

  ###########################################################################################

VllmConfig:
  Dataclass which contains all vllm-related configuration. This
      simplifies passing around the distinct configurations in the codebase.

  ###########################################################################################

  --additional-config ADDITIONAL_CONFIG
                        Additional config for specified platform. Different platforms may support different configs. Make sure the configs are valid for the platform you are
                        using. Contents must be hashable. (default: {})

  ###########################################################################################

  --attention-config ATTENTION_CONFIG, -ac ATTENTION_CONFIG
                        Attention configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.AttentionConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: AttentionConfig(backend=None, flash_attn_version=None,
                        use_prefill_decode_attention=False, flash_attn_max_num_splits_for_cuda_graph=32, tq_max_kv_splits_for_cuda_graph=32, use_trtllm_attention=None,
                        disable_flashinfer_q_quantization=False, mla_prefill_backend=None, use_prefill_query_quantization=False, use_fp4_indexer_cache=False,
                        use_non_causal=False, flex_attn_block_m=None, flex_attn_block_n=None, flex_attn_q_block_size=None, flex_attn_kv_block_size=None))

  ###########################################################################################

  --compilation-config COMPILATION_CONFIG, -cc COMPILATION_CONFIG
                        `torch.compile` and cudagraph capture configuration for the model.
                        As a shorthand, one can append compilation arguments via
                        -cc.parameter=argument such as `-cc.mode=3` (same as `-cc='{"mode":3}'`).
                        You can specify the full compilation config like so: `{"mode": 3, "cudagraph_capture_sizes": [1, 2, 4, 8]}`
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.CompilationConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: {'mode': None, 'debug_dump_path': None, 'cache_dir': '',
                        'compile_cache_save_format': 'binary', 'backend': 'inductor', 'custom_ops': [], 'ir_enable_torch_wrap': None, 'splitting_ops': None,
                        'compile_mm_encoder': False, 'cudagraph_mm_encoder': False, 'encoder_cudagraph_token_budgets': [], 'encoder_cudagraph_max_vision_items_per_batch': 0,
                        'encoder_cudagraph_max_frames_per_batch': None, 'compile_sizes': None, 'compile_ranges_endpoints': None, 'inductor_compile_config':
                        {'enable_auto_functionalized_v2': False, 'size_asserts': False, 'alignment_asserts': False, 'scalar_asserts': False, 'combo_kernels': True,
                        'benchmark_combo_kernel': True}, 'inductor_passes': {}, 'cudagraph_mode': None, 'cudagraph_num_of_warmups': 0, 'cudagraph_capture_sizes': None,
                        'cudagraph_copy_inputs': False, 'cudagraph_specialize_lora': True, 'use_inductor_graph_partition': None, 'pass_config': {},
                        'max_cudagraph_capture_size': None, 'dynamic_shapes_config': {'type': <DynamicShapesType.BACKED: 'backed'>, 'evaluate_guards': False,
                        'assume_32_bit_indexing': False}, 'local_cache_dir': None, 'fast_moe_cold_start': None, 'static_all_moe_layers': []})

  ###########################################################################################

  --ec-transfer-config EC_TRANSFER_CONFIG
                        The configurations for distributed EC cache transfer.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.ECTransferConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

  --kernel-config KERNEL_CONFIG
                        Kernel configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.KernelConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: KernelConfig(ir_op_priority=IrOpPriorityConfig(rms_norm=[],
                        fused_add_rms_norm=[]), enable_flashinfer_autotune=None, moe_backend='auto', linear_backend='auto'))

  ###########################################################################################

  --kv-events-config KV_EVENTS_CONFIG
                        The configurations for event publishing.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.KVEventsConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

  --kv-transfer-config KV_TRANSFER_CONFIG
                        The configurations for distributed KV cache transfer.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.KVTransferConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

  --optimization-level OPTIMIZATION_LEVEL
                        The optimization level. These levels trade startup time cost for performance, with -O0 having the best startup time and -O3 having the best
                        performance. -O2 is used by default. See OptimizationLevel for full description. (default: 2)

  ###########################################################################################

  --performance-mode {balanced,interactivity,throughput}
                        Performance mode for runtime behavior, 'balanced' is the default. 'interactivity' favors low end-to-end per-request latency at small batch sizes (fine-
                        grained CUDA graphs, latency-oriented kernels). 'throughput' favors aggregate tokens/sec at high concurrency (larger CUDA graphs, more aggressive
                        batching, throughput-oriented kernels). (default: balanced)
  含义: 快速设定运行时的整体性能倾向(`balanced`, `interactivity`, `throughput`).
  使用方法: `--performance-mode throughput`
  使用场景:
    `interactivity`(交互优化): 适用于实时聊天机器人, 追求极低的单个请求首字延迟和生成延迟.
    `throughput`(吞吐优化): 适用于批量离线数据处理、翻译、总结等, 通过最大化批处理(Batching)来提高每秒输出的 Token 总量.

  ###########################################################################################

  --profiler-config PROFILER_CONFIG
                        Profiling configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.ProfilerConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: ProfilerConfig(profiler=None, torch_profiler_dir='',
                        torch_profiler_with_stack=True, torch_profiler_with_flops=False, torch_profiler_use_gzip=True, torch_profiler_dump_cuda_time_total=True,
                        torch_profiler_record_shapes=False, torch_profiler_with_memory=False, ignore_frontend=False, delay_iterations=0, max_iterations=0, warmup_iterations=0,
                        active_iterations=5, wait_iterations=0))

  ###########################################################################################

  --reasoning-config REASONING_CONFIG
                        The configurations for reasoning model.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.ReasoningConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

  --spec-method {custom_class,deepseek_mtp,dflash,draft_model,eagle,eagle3,ernie_mtp,exaone4_5_mtp,exaone_moe_mtp,extract_hidden_states,gemma4_mtp,glm4_moe_lite_mtp,glm4_moe_mtp,glm_ocr_mtp,hy_v3_mtp,longcat_flash_mtp,medusa,mimo_mtp,mimo_v2_mtp,mlp_speculator,mtp,nemotron_h_mtp,ngram,ngram_gpu,pangu_ultra_moe_mtp,qwen3_5_mtp,qwen3_next_mtp,step3p5_mtp,suffix,None}
                        The name of the speculative method to use. If users provide and set the `model` param, the speculative method type will be detected automatically if
                        possible, if `model` param is not provided, the method name must be provided.
                        If using `ngram` method, the related configuration `prompt_lookup_max` and `prompt_lookup_min` should be considered. (default: None)
  含义: 启用投机采样(Speculative Decoding), 并指定一个小规模的草稿模型(Draft Model).
  原因: 大模型(72B)生成 Token 时受限于 GPU 显存带宽, 速度较慢. 投机采样让小模型(1.5B)快速尝试生成 `--spec-tokens 5`(5个候选 Token), 然后由 72B 主模型在一次 Forward 过程中进行并行验证. 如果验证通过, 则可以一次性输出多个 Token. 这种方式利用了计算资源换取时间, 能显著降低逐字生成的延迟(ITL).

  --spec-model SPEC_MODEL
                        The name of the draft model, eagle head, or additional weights, if provided. (default: None)
  含义: 启用投机采样(Speculative Decoding), 并指定一个小规模的草稿模型(Draft Model).
  原因: 大模型(72B)生成 Token 时受限于 GPU 显存带宽, 速度较慢. 投机采样让小模型(1.5B)快速尝试生成 `--spec-tokens 5`(5个候选 Token), 然后由 72B 主模型在一次 Forward 过程中进行并行验证. 如果验证通过, 则可以一次性输出多个 Token. 这种方式利用了计算资源换取时间, 能显著降低逐字生成的延迟(ITL).

  --spec-tokens SPEC_TOKENS
                        The number of speculative tokens, if provided. It will default to the number in the draft model config if present, otherwise, it is required. (default:
                        None)

  --speculative-config SPECULATIVE_CONFIG, -sc SPECULATIVE_CONFIG
                        Speculative decoding configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.SpeculativeConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

  --structured-outputs-config STRUCTURED_OUTPUTS_CONFIG
                        Structured outputs configuration.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.StructuredOutputsConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: StructuredOutputsConfig(backend='auto', disable_any_whitespace=False,
                        disable_additional_properties=False, reasoning_parser='', reasoning_parser_plugin='', enable_in_reasoning=False))

  ###########################################################################################

  --weight-transfer-config WEIGHT_TRANSFER_CONFIG
                        The configurations for weight transfer during RL training.
                        API docs: https://docs.vllm.ai/en/v0.22.0/api/vllm/config/#vllm.config.WeightTransferConfig
                        Should either be a valid JSON string or JSON keys passed individually. (default: None)

  ###########################################################################################

When passing JSON CLI arguments, the following sets of arguments are equivalent:
   --json-arg '{"key1": "value1", "key2": {"key3": "value2"}}'
   --json-arg.key1 value1 --json-arg.key2.key3 value2

Additionally, list elements can be passed individually using +:
   --json-arg '{"key4": ["value3", "value4", "value5"]}'
   --json-arg.key4+ value3 --json-arg.key4+='value4,value5'
(base) root@k8s-a40-node02:~#
```
