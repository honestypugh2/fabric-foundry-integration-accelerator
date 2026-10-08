"""Use-Case Guides: sanitized, synthetic-data walkthroughs derived from real engagements.

A guide is configuration plus a guided journey on top of the core accelerator. Guides never
fork core code and never contain customer identity; their provenance records only that they
were derived from a customer engagement and sanitized.
"""

from datetime import date
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.patterns.catalog import PatternCatalog
from fabric_foundry_accelerator.synthetic.manufacturing import MFG_PROFILES
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

Harness = Literal[
    "copilot-vscode", "copilot-cli", "copilot-app", "copilot-cloud-agent", "claude-code"
]
Maturity = Literal["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
ToolStatus = Literal["GA", "PREVIEW", "OSS", "UNKNOWN/NEEDS VALIDATION"]


class ToolRequirement(BaseModel):
    """A tool, server, extension or service the guide needs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    purpose: str
    version: str | None = None
    status: ToolStatus
    install: str
    required: bool = True


class ToolPath(BaseModel):
    """The provider, server and tool a step must use. Substitution is not allowed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str
    server: str | None = None
    tools: tuple[str, ...] = ()
    substitution_allowed: bool = False


class Rehearsal(BaseModel):
    """The governed change a write step can rehearse against the simulated workspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: str = Field(pattern=r"^[a-z][a-z_]*$")
    item_type: Literal["Lakehouse", "Notebook", "SemanticModel", "Report"]
    item_name: str = Field(min_length=1, max_length=120)
    note: str = ""


class GuideStep(BaseModel):
    """One step with prompts, checkpoint and the evidence that proves it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^\d{2}-[a-z0-9-]+$")
    title: str
    objective: str
    copilot_prompt: str
    claude_code_prompt: str
    tool_path: ToolPath
    writes: bool
    approval_required: bool
    checkpoint: str
    evidence_required: tuple[str, ...] = Field(min_length=1)
    not_evidence: tuple[str, ...] = ()
    offline_equivalent: str
    offline_command: str | None = None
    failure_modes: tuple[str, ...] = ()
    requires_windows: bool = False
    rehearsal: Rehearsal | None = None
    diagram_focus: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _writes_need_approval(self) -> Self:
        if self.writes and not self.approval_required:
            raise ValueError(f"step {self.id}: steps that write must require approval")
        if self.rehearsal is not None and not self.writes:
            raise ValueError(f"step {self.id}: only write steps can rehearse a change")
        return self


class GuideProvenance(BaseModel):
    """Sanitized provenance. Never names, titles, authors, identifiers or URLs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    derived_from: Literal["customer engagement guide (sanitized)", "original"]
    sanitized_on: date
    denylist_ref: str


class UseCaseGuide(BaseModel):
    """A Use-Case Guide (``guides/<id>/guide.yaml``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z]+-\d{2}-[a-z0-9-]+$")
    title: str
    industry: str
    scenario: str
    summary: str
    version: str
    status: Literal["draft", "validated-offline", "validated-live"]
    provenance: GuideProvenance
    patterns: tuple[str, ...]
    maturity_levels: tuple[Maturity, ...]
    harnesses: tuple[Harness, ...]
    operating_rules: tuple[str, ...]
    tools: tuple[ToolRequirement, ...]
    tenant_settings: tuple[str, ...] = ()
    os_constraints: tuple[str, ...] = ()
    dataset_profile: str
    expected_baseline: str
    diagram: str | None = None
    steps: tuple[GuideStep, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.dataset_profile not in PROFILES and self.dataset_profile not in MFG_PROFILES:
            raise ValueError(f"unknown dataset_profile {self.dataset_profile!r}")
        ids = [s.id for s in self.steps]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate step ids")
        return self

    def step(self, step_id: str) -> GuideStep:
        """Return a step by ID or raise ``KeyError``."""
        for candidate in self.steps:
            if candidate.id == step_id:
                return candidate
        raise KeyError(step_id)


def load_guide(path: Path) -> UseCaseGuide:
    """Load one guide manifest."""
    return UseCaseGuide.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_guides(
    guides_root: Path, catalog: PatternCatalog | None = None
) -> dict[str, UseCaseGuide]:
    """Load every guide under ``guides/`` (folders starting with ``_`` are templates).

    Raises:
        ValueError: when a guide references an unknown pattern or its folder name differs from its id.
    """
    guides: dict[str, UseCaseGuide] = {}
    for manifest in sorted(guides_root.glob("*/guide.yaml")):
        if manifest.parent.name.startswith("_"):
            continue
        guide = load_guide(manifest)
        if guide.id != manifest.parent.name:
            raise ValueError(
                f"guide id {guide.id!r} must match its folder {manifest.parent.name!r}"
            )
        if catalog is not None:
            known = {p.id for p in catalog.patterns}
            unknown = sorted(set(guide.patterns) - known)
            if unknown:
                raise ValueError(f"guide {guide.id} references unknown patterns {unknown}")
        guides[guide.id] = guide
    return guides
