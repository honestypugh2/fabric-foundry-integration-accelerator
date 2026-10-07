"""Architecture pattern catalog and rule-based recommendation."""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.research.sources import SourceRegistry

PatternStatus = Literal["GA", "PREVIEW", "MIXED"]

SELECTION_SIGNALS: dict[str, str] = {
    "conversational-structured-analytics": "Conversational questions over structured Fabric data",
    "multiple-governed-domains": "Several governed business domains with different owners",
    "shared-business-vocabulary": "A shared business vocabulary and entity model",
    "document-knowledge-retrieval": "Retrieval over documents stored in OneLake",
    "ai-in-data-engineering": "AI enrichment inside pipelines and notebooks",
    "enterprise-agent": "An application agent over governed enterprise context",
    "real-time-context": "Real-time operational signals",
    "business-system-write": "Writes to a business system or Fabric item",
    "governed-tool-access": "Sharing tools with many agents under governance",
    "medallion-foundation": "A medallion analytics foundation",
    "operational-replication-recovery": "Mirroring operational data and recovering it",
    "semantic-model-reporting": "Governed measures for reports and agents",
    "secure-production-deployment": "Production security and networking",
    "centralized-api-governance": "Central quotas, routing and tool registry",
    "evaluation-and-observability": "Evaluation and tracing as quality gates",
    "resilience-offline": "Fabric or Foundry may be unavailable",
    "multi-customer-reuse": "Reuse for another customer or industry",
    "developer-automation-cli": "Developer automation with Copilot or Claude Code",
    "reviewable-change-ci-cd": "Reviewable, repeatable changes through Git and CI",
    "backlog-automation": "Turning well-scoped issues into pull requests",
    "bulk-migration": "Bulk migration of legacy notebooks or pipelines",
    "automated-review": "Automated review in CI",
    "embedded-assistant": "An embedded assistant inside an internal product",
    "production-enterprise-ai": "Production enterprise AI end to end",
}


class ArchitecturePattern(BaseModel):
    """One catalog pattern (summary level)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^P\d{2}$")
    name: str
    summary: str
    status: PatternStatus
    preview_dependencies: tuple[str, ...]
    default_demo_path: Literal["LOCAL", "HYBRID", "DOCUMENTATION"]
    when_to_use: str
    when_not_to_use: str
    fabric_role: str
    foundry_role: str
    mcp_role: str
    authority: str
    offline_equivalent: str
    selection_signals: tuple[str, ...]
    sources: tuple[str, ...]

    @model_validator(mode="after")
    def _check(self) -> Self:
        unknown = set(self.selection_signals) - set(SELECTION_SIGNALS)
        if unknown:
            raise ValueError(f"{self.id}: unknown selection signals {sorted(unknown)}")
        if self.status == "PREVIEW" and not self.preview_dependencies:
            raise ValueError(f"{self.id}: PREVIEW patterns must list their preview dependencies")
        return self


class PatternCatalog(BaseModel):
    """``education/patterns/catalog.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    patterns: tuple[ArchitecturePattern, ...]

    def get(self, pattern_id: str) -> ArchitecturePattern:
        """Return a pattern by ID or raise ``KeyError``."""
        for pattern in self.patterns:
            if pattern.id == pattern_id:
                return pattern
        raise KeyError(pattern_id)

    def check_sources(self, registry: SourceRegistry) -> list[str]:
        """Return pattern source references missing from the source registry."""
        known = {s.id for s in registry.sources}
        return [f"{p.id}: {s}" for p in self.patterns for s in p.sources if s not in known]


class Recommendation(BaseModel):
    """A ranked pattern recommendation with its reasons."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pattern_id: str
    name: str
    score: int
    matched_needs: tuple[str, ...]
    status: PatternStatus
    preview_dependencies: tuple[str, ...]
    default_demo_path: str
    why: str


class UnknownNeedError(ValueError):
    """Raised when a recommendation request uses needs outside the vocabulary."""


def load_catalog(education_root: Path) -> PatternCatalog:
    """Load the pattern catalog."""
    raw = yaml.safe_load((education_root / "patterns" / "catalog.yaml").read_text(encoding="utf-8"))
    return PatternCatalog.model_validate(raw)


def recommend(
    catalog: PatternCatalog, needs: list[str], *, include_preview: bool = True
) -> list[Recommendation]:
    """Rank patterns by how many declared needs they address.

    Raises:
        UnknownNeedError: when a need is not in ``SELECTION_SIGNALS``.
    """
    unknown = sorted(set(needs) - set(SELECTION_SIGNALS))
    if unknown:
        raise UnknownNeedError(f"unknown needs {unknown}; valid needs: {sorted(SELECTION_SIGNALS)}")
    wanted = set(needs)
    results: list[Recommendation] = []
    for pattern in catalog.patterns:
        matched = tuple(s for s in pattern.selection_signals if s in wanted)
        if not matched or (pattern.status == "PREVIEW" and not include_preview):
            continue
        reasons = "; ".join(SELECTION_SIGNALS[s] for s in matched)
        caveat = (
            f" Requires preview: {', '.join(pattern.preview_dependencies)}."
            if pattern.preview_dependencies
            else ""
        )
        results.append(
            Recommendation(
                pattern_id=pattern.id,
                name=pattern.name,
                score=len(matched),
                matched_needs=matched,
                status=pattern.status,
                preview_dependencies=pattern.preview_dependencies,
                default_demo_path=pattern.default_demo_path,
                why=f"Addresses: {reasons}. Use when: {pattern.when_to_use}{caveat}",
            )
        )
    return sorted(results, key=lambda r: (-r.score, r.status == "PREVIEW", r.pattern_id))
