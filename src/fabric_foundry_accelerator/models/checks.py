"""Pass/fail check results shared by data validation and recovery simulation."""

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.models.execution import EvidenceCategory


class CheckResult(BaseModel):
    """The outcome of one deterministic validation check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    passed: bool
    detail: str
    category: EvidenceCategory = EvidenceCategory.SIMULATED_LOCALLY


def failed(checks: list[CheckResult] | tuple[CheckResult, ...]) -> list[CheckResult]:
    """Return only the failed checks."""
    return [c for c in checks if not c.passed]
