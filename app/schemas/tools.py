from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class CreateTicketToolInput(BaseModel):
    """
    Pydantic schema defining input arguments for the create_incident_ticket tool.
    Used for runtime validation and automatic JSON schema generation.
    """
    model_config = ConfigDict(extra="forbid")

    service: str = Field(
        description="Name of the affected production service or application unit"
    )
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Assessed severity level of the system issue or incident"
    )
    summary: str = Field(
        description="Concise one-sentence title describing the incident"
    )
    recommended_action: str = Field(
        description="Immediate mitigation or remediation step recommended for SRE team"
    )
