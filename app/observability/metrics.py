from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Custom collector registry to maintain clean application namespaces
REGISTRY = CollectorRegistry()

# RED Metrics: Rate, Errors, Duration for HTTP API
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Latency distribution of HTTP requests in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
    registry=REGISTRY,
)

# AI Engine Specific Performance & Token Consumption Metrics
AI_INFERENCE_DURATION_SECONDS = Histogram(
    "ai_inference_duration_seconds",
    "Latency distribution of LLM / AI engine processing time in seconds",
    ["model", "status"],
    buckets=(0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0, 1.5, 2.5, 5.0),
    registry=REGISTRY,
)

AI_TOKEN_USAGE_TOTAL = Counter(
    "ai_token_usage_total",
    "Total token consumption by AI inference",
    ["model", "token_type"],  # prompt or completion
    registry=REGISTRY,
)

# Business Action Metrics
BUSINESS_ACTIONS_TOTAL = Counter(
    "business_actions_total",
    "Total business actions executed (e.g. incident ticket creation)",
    ["action_type", "severity", "status"],
    registry=REGISTRY,
)

# Application Level Errors & Exception Tracking
APP_EXCEPTIONS_TOTAL = Counter(
    "app_exceptions_total",
    "Total unhandled or injected application exceptions",
    ["exception_type", "endpoint"],
    registry=REGISTRY,
)


def get_metrics_content() -> tuple[bytes, str]:
    """Generate latest Prometheus metrics formatted string."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
