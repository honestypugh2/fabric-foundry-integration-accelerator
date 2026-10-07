"""Execution labels and the envelope every provider result travels in.

The envelope makes execution state explicit and *validated*: a LOCAL, SIMULATED or
MOCKED result can never claim that a cloud operation was performed, and a LIVE result
must claim one. This is the code-level guarantee behind the rule "never present
simulation as a real Fabric, Azure, Foundry, Power BI or MCP operation".
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class OperatingMode(StrEnum):
    """How the system as a whole is running."""

    LIVE = "LIVE"
    HYBRID = "HYBRID"
    OFFLINE = "OFFLINE"


class ExecutionLabel(StrEnum):
    """How a single result was produced."""

    LIVE = "LIVE"
    HYBRID = "HYBRID"
    LOCAL = "LOCAL"
    SIMULATED = "SIMULATED"
    MOCKED = "MOCKED"
    PREVIEW = "PREVIEW"
    UNAVAILABLE = "UNAVAILABLE"


NON_CLOUD_LABELS = frozenset(
    {ExecutionLabel.LOCAL, ExecutionLabel.SIMULATED, ExecutionLabel.MOCKED}
)


class EvidenceCategory(StrEnum):
    """How strongly a statement is supported. Used to keep teaching claims honest."""

    SIMULATED_LOCALLY = "SIMULATED LOCALLY"
    DOCUMENTED_FABRIC_BEHAVIOR = "DOCUMENTED FABRIC BEHAVIOR"
    REQUIRES_TENANT_VALIDATION = "REQUIRES TENANT VALIDATION"
    ASSUMPTION = "ASSUMPTION"
    PRODUCTION_RECOMMENDATION = "PRODUCTION RECOMMENDATION"
    PREVIEW_LIMITATION = "PREVIEW LIMITATION"


class Evidence(BaseModel):
    """A single piece of evidence attached to a result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: EvidenceCategory
    statement: str
    reference: str | None = None


def new_correlation_id() -> str:
    """Return a new correlation ID (32 hex characters, no dashes)."""
    return uuid4().hex


def utc_now() -> datetime:
    """Return the current UTC-aware timestamp."""
    return datetime.now(UTC)


class ExecutionEnvelope[T](BaseModel):
    """A provider result plus the execution facts needed to interpret it honestly."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operating_mode: OperatingMode
    execution_label: ExecutionLabel
    requested_provider: str
    selected_provider: str
    cloud_operation_performed: bool
    equivalent_fabric_service: str
    teaching_objective: str
    data: T
    correlation_id: str = Field(default_factory=new_correlation_id, pattern=r"^[0-9a-f]{32}$")
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    fallback_used: bool = False
    fallback_reason: str | None = None
    simulation_notice: str | None = None
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def _enforce_honest_labels(self) -> Self:
        if self.execution_label in NON_CLOUD_LABELS:
            if self.cloud_operation_performed:
                raise ValueError(
                    f"{self.execution_label} results cannot claim a cloud operation was performed"
                )
            if not self.simulation_notice:
                raise ValueError(f"{self.execution_label} results require a simulation_notice")
        if self.execution_label is ExecutionLabel.LIVE and not self.cloud_operation_performed:
            raise ValueError("LIVE results must report cloud_operation_performed=True")
        if (
            self.execution_label is ExecutionLabel.LIVE
            and self.operating_mode is OperatingMode.OFFLINE
        ):
            raise ValueError("LIVE results cannot be produced in OFFLINE mode")
        if self.fallback_used and not self.fallback_reason:
            raise ValueError("fallback_used requires a fallback_reason")
        return self
