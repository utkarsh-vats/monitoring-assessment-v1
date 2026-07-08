import json
import logging
from datetime import datetime, timezone
try:
    from typing import override
except ImportError:
    from typing_extensions import override
from app.context import get_request_id


class StructuredJsonFormatter(logging.Formatter):
    """
    Formats log entries as structured JSON enriched with the current correlation request_id.
    Standardized schema for ELK / Loki / Datadog aggregation.
    """
    @override
    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": get_request_id(),
            "message": record.getMessage()
        }

        # Extra structured attributes passed via extra={} dictionary
        if hasattr(record, "event"):
            log_payload["event"] = getattr(record, "event")
        if hasattr(record, "duration_ms"):
            log_payload["duration_ms"] = getattr(record, "duration_ms")
        if hasattr(record, "metadata"):
            log_payload["metadata"] = getattr(record, "metadata")
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Get or initialize a structured JSON logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
