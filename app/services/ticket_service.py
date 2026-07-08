import uuid
from typing import Any
from app.observability.logger import get_logger
from app.observability.metrics import BUSINESS_ACTIONS_TOTAL

logger = get_logger("app.services.ticket_service")


def create_incident_ticket(
    service: str,
    severity: str,
    summary: str,
    recommended_action: str
) -> dict[str, Any]:
    """
    Executes the business action: Creates a simulated SRE/DevOps incident ticket.
    Emits structured logs and increments business metrics.
    """
    ticket_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    status = "CREATED"

    logger.info(
        f"Executing business action: create_incident_ticket [{ticket_id}] for service={service}",
        extra={
            "event": "business_action_executed",
            "metadata": {
                "action_type": "CREATE_INCIDENT_TICKET",
                "ticket_id": ticket_id,
                "service": service,
                "severity": severity,
                "status": status
            }
        }
    )

    # Increment Prometheus business action counter
    BUSINESS_ACTIONS_TOTAL.labels(
        action_type="CREATE_INCIDENT_TICKET",
        severity=severity.upper(),
        status=status
    ).inc()

    return {
        "action_type": "CREATE_INCIDENT_TICKET",
        "ticket_id": ticket_id,
        "service": service,
        "severity": severity.upper(),
        "summary": summary,
        "recommended_action": recommended_action,
        "status": status
    }
