"""Change-plan and approval models (PLAN -> VALIDATE -> APPROVE -> EXECUTE -> VERIFY -> AUDIT)."""

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import ExecutionLabel, new_correlation_id, utc_now

ItemType = Literal["Lakehouse", "Notebook", "SemanticModel", "Report"]
Destination = Literal["LOCAL", "LIVE"]


class FabricTarget(BaseModel):
    """What a change applies to. Workspaces are referenced by overlay alias, never by ID."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_alias: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    item_type: ItemType
    item_name: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9 _.-]*$")
    destination: Destination

    def destination_hash(self) -> str:
        """Return a stable hash binding approvals to this exact target and destination."""
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ChangeRequest(BaseModel):
    """A request to plan a change (from a person, an agent or an MCP tool)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: str = Field(pattern=r"^[a-z][a-z_]*$")
    target: FabricTarget
    reason: str = Field(min_length=5, max_length=500)
    requested_by: str = Field(min_length=1, max_length=80)


class ChangeStatus(StrEnum):
    """Lifecycle of a change."""

    PROPOSED = "PROPOSED"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class ProposedChange(BaseModel):
    """A validated change plan. Nothing has executed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change_id: str = Field(default_factory=new_correlation_id)
    correlation_id: str
    operation: str
    target: FabricTarget
    provider: str
    reason: str
    requested_by: str
    risk: Literal["low", "medium", "high"]
    reversible: bool
    expected_impact: str
    validation: tuple[str, ...]
    rollback: str
    approval_required: bool
    policy_allowed: bool
    policy_reasons: tuple[str, ...]
    precondition: CheckResult
    destination_hash: str
    status: ChangeStatus
    created_at: AwareDatetime = Field(default_factory=utc_now)


class ApprovalDecision(StrEnum):
    """A human decision."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRequest(BaseModel):
    """A human approval or rejection of a plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change_id: str
    approver: str = Field(min_length=1, max_length=80)
    decision: ApprovalDecision
    comment: str = Field(default="", max_length=500)


class Approval(BaseModel):
    """A recorded approval, bound to the target's destination hash and time-limited."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    approval_id: str = Field(default_factory=new_correlation_id)
    change_id: str
    approver: str
    decision: ApprovalDecision
    comment: str
    destination_hash: str
    created_at: AwareDatetime = Field(default_factory=utc_now)
    expires_at: AwareDatetime

    def is_expired(self, now: datetime) -> bool:
        """Return True once the approval window has passed."""
        return now >= self.expires_at


class ExecuteRequest(BaseModel):
    """A request to execute an approved plan."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change_id: str
    approval_id: str
    executed_by: str = Field(min_length=1, max_length=80)


class ExecutionResult(BaseModel):
    """What happened when an approved change was executed and verified."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change_id: str
    approval_id: str
    status: ChangeStatus
    execution_label: ExecutionLabel
    verification: CheckResult
    rollback: str
