from fastapi import FastAPI
from fastapi.responses import Response

from app.config import settings
from app.context import get_request_id
from app.middleware.correlation import CorrelationIdMiddleware
from app.observability.logger import get_logger
from app.observability.metrics import get_metrics_content
from app.schemas.ask import AskRequest, AskResponse
from app.services.ai_engine import process_ask_request

logger = get_logger("app.main")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Observable AI Backend Service with Prometheus, Grafana, Structured JSON Logs, and Correlation IDs"
)

app.add_middleware(CorrelationIdMiddleware)


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(payload: AskRequest):
    """
    Primary AI endpoint: Accepts natural language query, performs AI tool-calling triage,
    and returns structured diagnosis + business action ticket.
    """
    logger.info(
        f"Received /ask request for question: {payload.question[:60]}...",
        extra={"event": "ask_request_received", "metadata": {"question": payload.question}}
    )
    result = await process_ask_request(payload.question, payload.context)

    return AskResponse(
        request_id=get_request_id(),
        status="success",
        data=result
    )


@app.get("/health")
async def health_check():
    """Liveness and readiness probe for Kubernetes / Docker Compose."""
    return {
        "status": "HEALTHY",
        "service": settings.app_name,
        "version": settings.version,
        "request_id": get_request_id()
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus scrape endpoint returning custom application metrics."""
    data, content_type = get_metrics_content()
    return Response(content=data, media_type=content_type)
