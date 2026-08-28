"""
LLM 推理服务多功能探测与压测脚本
- 支持流式 (SSE) 与非流式请求 (8:2 动态路由)
- 自动提取 Envoy / CDS 网关头与推理性能指标 (TTFT, TPS, Predict Time)
- 细致的思考链 (Reasoning Content) 与最终结果解析
- 完备的异常处理机制 (网络、HTTP 状态码、协议解析)
- 采用原始字节读取 + 显式 UTF-8 严格解码
- 使用 print(..., flush=True) 确保 100% 时序准确性
"""

import datetime
import json
import random
import sys
import time
import traceback
from typing import Any, Dict, List, Optional
import requests
from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError as ReqConnectionError,
    ConnectTimeout,
    HTTPError,
    ReadTimeout,
    RequestException,
)

# ============================
# 1. 基础配置 (Service Configuration)
# ============================
SERVICE_URL = "http://172.16.10.55:24182/v1/chat/completions"
API_KEY = "kn49enthcjzklckavdwhhleo"
MODEL_NAME = "DEEPSEEK"

# 测试参数
TOTAL_REQUESTS = 10  # 总请求轮数
STREAM_RATIO = 0.8  # 流式请求比例 (80% stream, 20% non-stream)
CONNECT_TIMEOUT = 5.0  # 连接超时时间 (秒)
READ_TIMEOUT = 60.0  # 响应读取超时时间 (秒)
ENABLE_COLOR = True  # 若终端不支持彩色显示可设为 False

# ============================
# 2. 丰富多样的 Prompt 库 (Diverse Prompts Pool)
# ============================
PROMPT_POOL: List[str] = [
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    "什么是 Redis? 请简述其核心特性及常见使用场景.",
    # "用 Python 写一个高效的 LRU Cache 实现, 要求包含 get 和 put 操作, 并带有详细注释.",
    # "请详细分析深度学习中 Transformer 架构的 Self-Attention 机制, 并写出其数学计算公式.",
    # "假设一个分布式系统出现脑裂(Split-Brain), 通常有哪些解决和预防方案?",
    # "桌上有9个硬币, 其中一个是假的(质量稍轻), 用天平最少称几次能保证找出假币? 请给出详细推理过程.",
    # "请比较 Kafka 和 RabbitMQ 在架构、消息吞吐量、消息可靠性和延迟方面的区别.",
    # "编写一个 Dockerfile, 构建一个基于 multi-stage 的最小化 Go Web 应用镜像.",
    # "解释 Linux 内核中 epoll 的工作原理, 并对比 select 和 poll 的区别.",
    # "请写一首关于 GPU 加速大模型推理的五言绝句, 要求押韵并具有科技感.",
    # "请分析一下大语言模型推理中的 PagedAttention 机制是如何解决 KV Cache 内存碎片问题的?",
    # "如果一个微服务出现 CPU 100% 飙高, 你会按照怎样的步骤排查问题?",
    # "使用 C++ 实现一个无锁队列(Lock-free Queue)的基本思路是什么?",
]


# ============================
# 3. 严格时序保证的 Print 格式化输出系统
# ============================
class Logger:
    COLOR_DEBUG = "\033[90m" if ENABLE_COLOR else ""
    COLOR_INFO = "\033[36m" if ENABLE_COLOR else ""
    COLOR_WARN = "\033[33m" if ENABLE_COLOR else ""
    COLOR_ERROR = "\033[31m" if ENABLE_COLOR else ""
    COLOR_RESET = "\033[0m" if ENABLE_COLOR else ""

    @staticmethod
    def _now_str() -> str:
        """获取带毫秒的高精度时间戳"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    @classmethod
    def _print(cls, level: str, msg: str, color: str):
        # 强制指定输出到 stdout 且 flush=True 杜绝乱序
        formatted_msg = f"{color}{cls._now_str()} [{level}] {msg}{cls.COLOR_RESET}"
        print(formatted_msg, file=sys.stdout, flush=True)

    @classmethod
    def info(cls, msg: str):
        cls._print("INFO", msg, cls.COLOR_INFO)

    @classmethod
    def debug(cls, msg: str):
        cls._print("DEBUG", msg, cls.COLOR_DEBUG)

    @classmethod
    def warning(cls, msg: str):
        cls._print("WARN", msg, cls.COLOR_WARN)

    @classmethod
    def error(cls, msg: str):
        cls._print("ERROR", msg, cls.COLOR_ERROR)

    @classmethod
    def raw(cls, msg: str):
        print(msg, file=sys.stdout, flush=True)


# ============================
# 4. 推理客户端核心实现
# ============================
class LLMInferenceClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        # 使用 Session 复用 TCP 链接提升性能
        self.session = requests.Session()

    def _extract_gateway_headers(
        self, headers: requests.structures.CaseInsensitiveDict
    ) -> Dict[str, Any]:
        """提取并记录服务网关/Envoy返回的关键追踪头"""
        gw_info = {}
        trace_headers = [
            "x-cds-request-id",
            "trace-id",
            "x-envoy-upstream-service-time",
            "req-cost-time",
            "req-arrive-time",
            "resp-start-time",
            "server",
        ]
        for h in trace_headers:
            if h in headers:
                gw_info[h] = headers[h]
        return gw_info

    def send_non_stream_request(self, prompt: str, req_id: int) -> bool:
        """发送非流式请求 (stream: False)"""
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt}],
            "stream_options": {
                "include_usage": True,
            },
        }

        Logger.info(f"[{req_id}] >>> 发起[非流式]请求 | Prompt: {prompt[:30]}...")
        start_time = time.perf_counter()

        try:
            response = self.session.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )

            latency = time.perf_counter() - start_time
            gw_headers = self._extract_gateway_headers(response.headers)

            # 校验 HTTP 状态码
            if response.status_code != 200:
                self._handle_http_error_response(response, req_id, latency)
                return False

            # 强制指定 UTF-8 解码, 杜绝乱码
            response.encoding = "utf-8"

            try:
                res_data = response.json()
            except json.JSONDecodeError as jde:
                Logger.error(
                    f"[{req_id}] 响应 JSON 解析失败: {jde} | Raw: {response.text[:200]}"
                )
                return False

            # 提取模型推理产出
            choice = res_data.get("choices", [{}])[0]
            message = choice.get("message", {})
            reasoning_content = message.get("reasoning_content", "")
            content = message.get("content", "")
            finish_reason = choice.get("finish_reason", "unknown")
            usage = res_data.get("usage", {})
            metrics = res_data.get("metrics", {})

            # 详细打印返回信息
            Logger.info(
                f"[{req_id}] <<< [非流式]响应成功 | HTTP {response.status_code} | 总耗时: {latency:.3f}s"
            )
            Logger.debug(
                f"[{req_id}] 网关追踪信息: {json.dumps(gw_headers, ensure_ascii=False)}"
            )
            Logger.debug(
                f"[{req_id}] Token 使用情况: {json.dumps(usage, ensure_ascii=False)}"
            )
            if metrics:
                Logger.debug(
                    f"[{req_id}] 服务端 Metrics: {json.dumps(metrics, ensure_ascii=False)}"
                )

            if reasoning_content:
                Logger.info(
                    f"[{req_id}] [思考链 Reasoning (前150字)]:\n{reasoning_content[:150]}..."
                )
            Logger.info(f"[{req_id}] [最终回复 Content (前150字)]:\n{content[:150]}...")
            Logger.info(f"[{req_id}] 结束状态: finish_reason={finish_reason}")

            # 计算生成吞吐率 (TPS)
            completion_tokens = usage.get("completion_tokens", 0)
            if completion_tokens and latency > 0:
                Logger.info(
                    f"[{req_id}] 端到端输出吞吐: {completion_tokens / latency:.2f} tokens/s"
                )

            return True

        except Exception as e:
            self._handle_request_exception(
                e, req_id, latency=time.perf_counter() - start_time
            )
            return False

    def send_stream_request(self, prompt: str, req_id: int) -> bool:
        """发送流式请求 (stream: True, SSE)"""
        payload = {
            "model": self.model,
            "stream": True,
            "messages": [{"role": "user", "content": prompt}],
            "stream_options": {
                "include_usage": True,
            },
        }

        Logger.info(f"[{req_id}] >>> 发起[流式 SSE]请求 | Prompt: {prompt[:30]}...")
        start_time = time.perf_counter()
        ttft: Optional[float] = None
        first_chunk_received = False

        full_reasoning_content = []
        full_content = []
        chunk_count = 0
        final_usage = None
        final_metrics = None

        try:
            response = self.session.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                stream=True,
            )

            # 校验 HTTP 状态码
            if response.status_code != 200:
                latency = time.perf_counter() - start_time
                self._handle_http_error_response(response, req_id, latency)
                return False

            gw_headers = self._extract_gateway_headers(response.headers)
            Logger.debug(
                f"[{req_id}] 流式通道已建立 | 网关追踪信息: {json.dumps(gw_headers, ensure_ascii=False)}"
            )

            # 迭代 SSE 数据流
            for raw_line in response.iter_lines(decode_unicode=False):
                if not raw_line:
                    continue  # 过滤心跳空行

                # 显式使用 UTF-8 严格解码单行数据
                try:
                    line = raw_line.decode("utf-8")
                except UnicodeDecodeError as ude:
                    Logger.error(
                        f"[{req_id}] 行 UTF-8 解码失败: {ude} | Raw: {raw_line!r}"
                    )
                    continue

                if not first_chunk_received:
                    ttft = time.perf_counter() - start_time
                    first_chunk_received = True

                # Logger.debug(f"[{req_id}] SSE 数据流: {line}")

                # 处理 SSE 数据帧: data: {...}
                if line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    if data_str == "[DONE]":
                        Logger.debug(f"[{req_id}] 收到流结束标志 [DONE]")
                        break

                    try:
                        chunk = json.loads(data_str)
                        chunk_count += 1

                        if "usage" in chunk and chunk["usage"]:
                            final_usage = chunk["usage"]
                        if "metrics" in chunk and chunk["metrics"]:
                            final_metrics = chunk["metrics"]

                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})

                            # 提取增量思考内容
                            if (
                                "reasoning_content" in delta
                                and delta["reasoning_content"]
                            ):
                                full_reasoning_content.append(
                                    delta["reasoning_content"]
                                )

                            # 提取增量文本内容
                            if "content" in delta and delta["content"]:
                                full_content.append(delta["content"])

                    except json.JSONDecodeError as jde:
                        Logger.warning(
                            f"[{req_id}] 忽略畸形 SSE 帧: {jde} | Raw: {line}"
                        )
                        continue

            total_latency = time.perf_counter() - start_time
            reasoning_text = "".join(full_reasoning_content)
            content_text = "".join(full_content)

            # 打印流式返回摘要
            Logger.info(
                f"[{req_id}] <<< [流式]接收完毕 | 总耗时: {total_latency:.3f}s | TTFT: {ttft:.3f}s | Chunks: {chunk_count}"
            )
            if final_usage:
                Logger.debug(
                    f"[{req_id}] Token 使用情况: {json.dumps(final_usage, ensure_ascii=False)}"
                )
            if final_metrics:
                Logger.debug(
                    f"[{req_id}] 服务端 Metrics: {json.dumps(final_metrics, ensure_ascii=False)}"
                )

            if reasoning_text:
                Logger.info(
                    f"[{req_id}] [思考链 Reasoning 拼接 (前150字)]:\n{reasoning_text[:150]}..."
                )
            Logger.info(
                f"[{req_id}] [最终回复 Content 拼接 (前150字)]:\n{content_text[:150]}..."
            )

            if final_usage and "completion_tokens" in final_usage:
                gen_tokens = final_usage["completion_tokens"]
                gen_time = total_latency - (ttft or 0)
                if gen_time > 0:
                    Logger.info(
                        f"[{req_id}] 纯生成阶段吞吐: {gen_tokens / gen_time:.2f} tokens/s"
                    )

            return True

        except Exception as e:
            self._handle_request_exception(
                e, req_id, latency=time.perf_counter() - start_time
            )
            return False

    def _handle_http_error_response(
        self, response: requests.Response, req_id: int, latency: float
    ):
        """细致分析 HTTP 4xx / 5xx 错误"""
        status = response.status_code
        err_msg = ""
        try:
            response.encoding = "utf-8"
            err_json = response.json()
            err_msg = json.dumps(err_json, ensure_ascii=False)
        except Exception:
            err_msg = response.text[:300]

        if status == 400:
            Logger.error(
                f"[{req_id}] HTTP 400 Bad Request (参数或模型名错误) | 耗时: {latency:.3f}s | Detail: {err_msg}"
            )
        elif status == 401:
            Logger.error(
                f"[{req_id}] HTTP 401 Unauthorized (API Key 无效/未授权) | Detail: {err_msg}"
            )
        elif status == 404:
            Logger.error(
                f"[{req_id}] HTTP 404 Not Found (URL 路径或模型不存在) | Detail: {err_msg}"
            )
        elif status == 429:
            Logger.error(
                f"[{req_id}] HTTP 429 Too Many Requests (触发限流/并发超限) | Detail: {err_msg}"
            )
        elif status == 500:
            Logger.error(
                f"[{req_id}] HTTP 500 Internal Server Error (后端异常/显存 OOM) | Detail: {err_msg}"
            )
        elif status in (502, 503, 504):
            Logger.error(
                f"[{req_id}] HTTP {status} Gateway/Proxy Error (Envoy 上游不可用或超时) | Detail: {err_msg}"
            )
        else:
            Logger.error(f"[{req_id}] HTTP {status} 发生未知错误 | Detail: {err_msg}")

    def _handle_request_exception(self, e: Exception, req_id: int, latency: float):
        """细致捕获与分类网络与客户端底层异常"""
        if isinstance(e, ConnectTimeout):
            Logger.error(
                f"[{req_id}] 连接超时 (ConnectTimeout, >{CONNECT_TIMEOUT}s): 目标服务不可达! [{e}]"
            )
        elif isinstance(e, ReadTimeout):
            Logger.error(
                f"[{req_id}] 读取超时 (ReadTimeout, >{READ_TIMEOUT}s): 推理生成过慢挂起! [{e}]"
            )
        elif isinstance(e, ReqConnectionError):
            Logger.error(
                f"[{req_id}] 连接错误 (ConnectionError): 连接被拒绝或远端关闭 TCP 连接! [{e}]"
            )
        elif isinstance(e, ChunkedEncodingError):
            Logger.error(
                f"[{req_id}] 数据流中断 (ChunkedEncodingError): 流式响应在传输中被强制断开! [{e}]"
            )
        elif isinstance(e, HTTPError):
            Logger.error(f"[{req_id}] HTTP 请求异常: {e}")
        elif isinstance(e, RequestException):
            Logger.error(f"[{req_id}] 通用网络层异常 (RequestException): {e}")
        else:
            Logger.error(
                f"[{req_id}] 未知运行时异常: {type(e).__name__} - {e}\n{traceback.format_exc()}"
            )


# ============================
# 5. 执行主流程 (Main Workflow)
# ============================
def main():
    Logger.info("==================================================")
    Logger.info("  LLM 推理服务稳定性与指标检测脚本启动")
    Logger.info(f"  目标地址: {SERVICE_URL}")
    Logger.info(f"  测试模型: {MODEL_NAME}")
    Logger.info(
        f"  总轮数: {TOTAL_REQUESTS} | 流式期望比例: {int(STREAM_RATIO * 100)}%"
    )
    Logger.info("==================================================")

    client = LLMInferenceClient(base_url=SERVICE_URL, api_key=API_KEY, model=MODEL_NAME)

    success_count = 0
    fail_count = 0
    stream_count = 0
    non_stream_count = 0

    # 随机打乱 Prompt 列表, 确保每个请求 Prompt 尽量不同
    prompts = PROMPT_POOL.copy()
    random.shuffle(prompts)

    for i in range(1, TOTAL_REQUESTS + 1):
        # 循环获取不同的 prompt
        prompt = prompts[(i - 1) % len(prompts)]

        # 按照 8:2 的比例随机决定是否走流式
        is_stream = random.random() < STREAM_RATIO

        Logger.raw("\n" + "-" * 80)
        Logger.info(
            f"--- [Round {i}/{TOTAL_REQUESTS}] 模式: {'[流式 Stream]' if is_stream else '[非流式 Sync]'} ---"
        )

        if is_stream:
            stream_count += 1
            success = client.send_stream_request(prompt, req_id=i)
        else:
            non_stream_count += 1
            success = client.send_non_stream_request(prompt, req_id=i)

        if success:
            success_count += 1
        else:
            fail_count += 1

        # 每次请求之间增加微小随机抖动 (0.5s ~ 1.5s), 更贴近真实用户访问特征
        time.sleep(random.uniform(0.5, 1.5))

    # ============================
    # 汇总统计
    # ============================
    Logger.raw("\n" + "=" * 80)
    Logger.info("[测试结果汇总统计]")
    Logger.info(f"总请求数: {TOTAL_REQUESTS}")
    Logger.info(
        f"成功: {success_count} | 失败: {fail_count} | 成功率: {(success_count / TOTAL_REQUESTS) * 100:.2f}%"
    )
    Logger.info(
        f"流式请求数: {stream_count} (实际占比: {stream_count / TOTAL_REQUESTS * 100:.1f}%)"
    )
    Logger.info(
        f"非流式请求数: {non_stream_count} (实际占比: {non_stream_count / TOTAL_REQUESTS * 100:.1f}%)"
    )
    Logger.info("==================================================")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Logger.warning("\n[!] 收到用户中断信号 (Ctrl+C), 退出测试.")
        sys.exit(0)
