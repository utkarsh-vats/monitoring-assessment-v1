from contextvars import ContextVar

# ContextVar to hold the request correlation ID across async calls
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="N/A")
inject_fault_ctx_var: ContextVar[str | None] = ContextVar("inject_fault", default=None)


def get_request_id() -> str:
    """Retrieve the current request correlation ID from context."""
    return request_id_ctx_var.get()


def get_injected_fault() -> str | None:
    """Retrieve optional fault injection header value for debugging/testing."""
    return inject_fault_ctx_var.get()
