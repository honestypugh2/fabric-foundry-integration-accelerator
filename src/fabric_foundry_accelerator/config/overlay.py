"""Customer overlay: configuration-driven customization with no source-code forks.

Overlays are fictional or sanitized. They hold *aliases* only; real identifiers live in
git-ignored ``*.local.yaml`` files and are never committed.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.synthetic.profiles import PROFILES

_ALIAS = r"^[a-z][a-z0-9-]*$"


class ApprovalRule(BaseModel):
    """Approval requirement for a write operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: str
    approvers: int = Field(default=1, ge=1, le=3)
    reason: str


class EvaluationThresholds(BaseModel):
    """Thresholds the evaluation gate applies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    measure_absolute_tolerance: float = Field(default=0.000001, ge=0)
    minimum_pass_rate: float = Field(default=1.0, ge=0, le=1)


class RecoveryObjectives(BaseModel):
    """Recovery objectives used by the recovery lab (synthetic assumptions)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rpo_hours: int = Field(ge=0)
    rto_hours: int = Field(ge=0)
    snapshot_interval_days: int = Field(ge=1)
    change_file_retention_days: int = Field(ge=1)


class CustomerOverlay(BaseModel):
    """A customer or industry overlay (``config/customers/<alias>.yaml``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    alias: str = Field(pattern=_ALIAS)
    industry: str
    scenario: str
    description: str
    synthetic: Literal[True]
    data_domains: tuple[str, ...]
    fabric_workspace_aliases: dict[str, str]
    foundry_project_aliases: dict[str, str]
    allowed_reads: tuple[str, ...]
    allowed_writes: tuple[str, ...]
    required_approvals: tuple[ApprovalRule, ...]
    feature_flags: dict[str, bool]
    preview_feature_flags: dict[str, bool]
    learning_modules: tuple[str, ...]
    demo_sequence: tuple[str, ...]
    synthetic_dataset: str
    guides: tuple[str, ...] = ()
    evaluation_thresholds: EvaluationThresholds = EvaluationThresholds()
    compliance_notes: tuple[str, ...]
    retention_assumptions: tuple[str, ...]
    recovery_objectives: RecoveryObjectives

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.synthetic_dataset not in PROFILES:
            raise ValueError(f"unknown synthetic_dataset {self.synthetic_dataset!r}")
        for alias in (*self.fabric_workspace_aliases, *self.foundry_project_aliases):
            if not alias.replace("-", "").isalnum() or alias != alias.lower():
                raise ValueError(f"aliases must be lowercase words joined by hyphens: {alias!r}")
        unapproved = {r.operation for r in self.required_approvals} - set(self.allowed_writes)
        if unapproved:
            raise ValueError(
                f"approval rules for operations that are not allowed: {sorted(unapproved)}"
            )
        return self

    def approval_rule(self, operation: str) -> ApprovalRule | None:
        """Return the approval rule for an operation, if any."""
        return next((r for r in self.required_approvals if r.operation == operation), None)

    def with_previews(self, names: tuple[str, ...]) -> CustomerOverlay:
        """Return a copy with the named preview flags turned on.

        Raises:
            ValueError: a name is not a preview flag of this overlay.
        """
        unknown = sorted(set(names) - set(self.preview_feature_flags))
        if unknown:
            raise ValueError(
                f"unknown preview feature(s) {unknown}; known: {sorted(self.preview_feature_flags)}"
            )
        flags = {**self.preview_feature_flags, **dict.fromkeys(names, True)}
        return self.model_copy(update={"preview_feature_flags": flags})

    def enabled_previews(self) -> list[str]:
        """Return the names of enabled preview features."""
        return sorted(name for name, enabled in self.preview_feature_flags.items() if enabled)


def load_overlay(config_root: Path, alias: str) -> CustomerOverlay:
    """Load ``config/customers/<alias>.yaml``."""
    path = config_root / "customers" / f"{alias}.yaml"
    return CustomerOverlay.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
