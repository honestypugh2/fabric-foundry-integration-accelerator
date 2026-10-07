"""Policy models and the deterministic policy engine for writes and tools.

Models propose. Deterministic logic validates. Policy constrains. Humans approve.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Risk = Literal["low", "medium", "high"]
Destination = Literal["LOCAL", "LIVE"]


class WriteOperation(BaseModel):
    """A write operation the policy knows about."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z_]*$")
    item_types: tuple[str, ...]
    risk: Risk
    reversible: bool
    expected_impact: str
    validation: tuple[str, ...]
    rollback: str


class DestinationRule(BaseModel):
    """Whether a write destination may be executed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool
    note: str


class WritePolicy(BaseModel):
    """``config/policies/writes.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    approval_ttl_minutes: int = Field(ge=1, le=1440)
    separation_of_duties: bool
    operations: tuple[WriteOperation, ...]
    destinations: dict[Destination, DestinationRule]

    def operation(self, name: str) -> WriteOperation | None:
        """Return an operation by name."""
        return next((o for o in self.operations if o.name == name), None)


class ToolManifestEntry(BaseModel):
    """Governance metadata for one MCP tool."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(pattern=r"^[a-z][a-z_]*$")
    description: str
    owner: str
    version: str
    classification: str
    identity: str
    allowed_operations: tuple[Literal["read", "propose"], ...]
    read_only: bool
    rate_limit_per_minute: int = Field(ge=1)
    timeout_seconds: float = Field(gt=0, le=300)
    audit: bool
    enabled: bool
    failure_policy: str
    revocation: str


class ToolServer(BaseModel):
    """Server-level manifest metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str
    identity: str


class ToolManifest(BaseModel):
    """``config/policies/tools.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    server: ToolServer
    tools: tuple[ToolManifestEntry, ...]

    def enabled(self) -> dict[str, ToolManifestEntry]:
        """Return enabled tools keyed by name."""
        return {t.name: t for t in self.tools if t.enabled}


class PolicyDecision(BaseModel):
    """The outcome of evaluating a proposed write."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    allowed: bool
    approval_required: bool
    risk: Risk
    reasons: tuple[str, ...]


def load_write_policy(config_root: Path) -> WritePolicy:
    """Load the write policy."""
    raw = yaml.safe_load((config_root / "policies" / "writes.yaml").read_text(encoding="utf-8"))
    return WritePolicy.model_validate(raw)


def load_tool_manifest(config_root: Path) -> ToolManifest:
    """Load the MCP tool manifest."""
    raw = yaml.safe_load((config_root / "policies" / "tools.yaml").read_text(encoding="utf-8"))
    return ToolManifest.model_validate(raw)


def evaluate_write(
    policy: WritePolicy,
    *,
    operation: str,
    item_type: str,
    destination: Destination,
    workspace_alias: str,
    allowed_writes: tuple[str, ...],
    workspace_aliases: tuple[str, ...],
    allow_live_mutation: bool,
) -> PolicyDecision:
    """Evaluate a proposed write deterministically. Approval is always required for writes."""
    reasons: list[str] = []
    definition = policy.operation(operation)
    if definition is None:
        return PolicyDecision(
            allowed=False,
            approval_required=True,
            risk="high",
            reasons=(f"Unknown operation {operation!r}.",),
        )
    if operation not in allowed_writes:
        reasons.append(f"Operation {operation!r} is not in the overlay's allowed_writes.")
    if item_type not in definition.item_types:
        reasons.append(f"Operation {operation!r} does not apply to item type {item_type!r}.")
    if workspace_alias not in workspace_aliases:
        reasons.append(f"Workspace alias {workspace_alias!r} is not declared in the overlay.")
    rule = policy.destinations[destination]
    if not rule.allowed:
        reasons.append(f"{destination} destination is not allowed: {rule.note}")
    if destination == "LIVE" and not allow_live_mutation:
        reasons.append("Live mutation is disabled (FFIA_ALLOW_LIVE_MUTATION is not set).")
    return PolicyDecision(
        allowed=not reasons,
        approval_required=True,
        risk=definition.risk,
        reasons=tuple(reasons) or ("Policy checks passed; human approval is still required.",),
    )
