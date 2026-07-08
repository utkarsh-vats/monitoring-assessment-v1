import time
try:
    from typing import override
except ImportError:
    from typing_extensions import override
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.context import (
    request_id_ctx_var,
    inject_fault_ctx_var,
)
from app.observability.logger import get_logger
from app.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    APP_EXCEPTIONS_TOTAL,
)

logger = get_logger("app.middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        endpoint = request.url.path
        method = request.method

        # Extract X-Request-ID from incoming headers or generate a UUID4
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4()}"
        fault_injection = request.headers.get("X-Inject-Fault")

        # Set context variables for this async execution context
        token_id = request_id_ctx_var.set(request_id)
        token_fault = inject_fault_ctx_var.set(fault_injection)

        try:
            response: Response = await call_next(request)
            duration = time.perf_counter() - start_time
            status_code = str(response.status_code)

            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

            logger.info(
                f"{method} {endpoint} completed with status {status_code} in {round(duration * 1000, 2)}ms",
                extra={
                    "event": "http_request_completed",
                    "duration_ms": round(duration * 1000, 2),
                    "metadata": {"method": method, "endpoint": endpoint, "status_code": status_code}
                }
            )

            # Ensure X-Request-ID header is always returned on output response
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code="500").inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            APP_EXCEPTIONS_TOTAL.labels(exception_type=type(exc).__name__, endpoint=endpoint).inc()

            logger.exception(
                f"Unhandled exception during {method} {endpoint}: {exc}",
                extra={"event": "http_request_failed", "metadata": {"method": method, "endpoint": endpoint}}
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": str(exc),
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
        finally:
            request_id_ctx_var.reset(token_id)
            inject_fault_ctx_var.reset(token_fault)
