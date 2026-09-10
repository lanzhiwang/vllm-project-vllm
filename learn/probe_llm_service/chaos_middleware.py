import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("vllm.entrypoints.openai.api_server")


async def chaos_fault_injection_middleware(request: Request, call_next):
    """
    Chaos Fault Injection Middleware:
    主动拦截请求并根据 X-Chaos-Fault 响应指定的 >=500 状态码或抛出异常
    """
    fault = request.headers.get("X-Chaos-Fault") or request.query_params.get(
        "chaos_fault"
    )
    if fault:
        logger.warning("Active chaos fault injection triggered with marker: %s", fault)

        # 1. 指定 HTTP >= 500 状态码 (例如 500, 502, 503, 504)
        if fault.isdigit() and int(fault) >= 500:
            status_code = int(fault)
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": {
                        "message": f"Injected Fault: Service returned HTTP {status_code} intentionally.",
                        "type": "chaos_fault_injection",
                        "param": None,
                        "code": status_code,
                    }
                },
            )
        # 2. 模拟抛出未捕获服务端严重异常, 验证异常处理机制
        elif fault.lower() in ("exception", "crash", "raise"):
            raise RuntimeError(
                "Injected Fault: Simulated unhandled server exception for chaos test."
            )

    return await call_next(request)
