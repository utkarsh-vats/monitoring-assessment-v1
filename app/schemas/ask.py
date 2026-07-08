from typing import Any
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Natural language DevOps/SRE question or alert snippet"
    )
    context: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Optional metadata context (environment, service name, cluster)"
    )


class AskResponse(BaseModel):
    request_id: str = Field(..., description="End-to-end request correlation ID")
    status: str = Field(default="success", description="Outcome status")
    data: dict[str, Any] = Field(..., description="Payload containing AI diagnosis and business action")
