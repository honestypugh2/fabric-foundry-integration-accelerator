"""Typed registry of authoritative sources used to justify architecture decisions.

The registry lives in ``docs/research/sources.yaml`` and is rendered to
``docs/research/source-validation.md``. CI fails when the rendered file is stale.
"""

from collections import defaultdict
from datetime import date
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

DEFAULT_REGISTRY_PATH = Path("docs/research/sources.yaml")
DEFAULT_RENDERED_PATH = Path("docs/research/source-validation.md")


class SourceStatus(StrEnum):
    """Lifecycle status of the capability a source describes."""

    GA = "GA"
    PREVIEW = "PREVIEW"
    DEPRECATED = "DEPRECATED"
    UNKNOWN = "UNKNOWN/NEEDS VALIDATION"
    GUIDANCE = "GUIDANCE"
    OSS = "OSS"


class SourceRecord(BaseModel):
    """One authoritative source with the fields required by the source-validation policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=3)
    url: HttpUrl
    publisher: str
    retrieved_date: date
    last_updated_date: date | None = None
    technology: str
    associated_patterns: list[str] = Field(default_factory=list[str])
    status: SourceStatus
    key_architecture_statement: str
    implementation_relevance: str
    security_implications: str
    limitations: str
    fallback: str
    deprecation_or_replacement: str | None = None

    @field_validator("url")
    @classmethod
    def _require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("source URLs must use https")
        return value


class SourceRegistry(BaseModel):
    """The full registry file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = Field(ge=1)
    sources: list[SourceRecord]

    @field_validator("sources")
    @classmethod
    def _unique_ids(cls, value: list[SourceRecord]) -> list[SourceRecord]:
        seen: set[str] = set()
        for record in value:
            if record.id in seen:
                raise ValueError(f"duplicate source id: {record.id}")
            seen.add(record.id)
        return value


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> SourceRegistry:
    """Load and validate the source registry."""
    return SourceRegistry.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip() or "—"


_FIELDS: tuple[tuple[str, str], ...] = (
    ("URL", "url"),
    ("Publisher", "publisher"),
    ("Retrieved", "retrieved_date"),
    ("Last updated", "last_updated_date"),
    ("Status", "status"),
    ("Associated patterns", "associated_patterns"),
    ("Key architecture statement", "key_architecture_statement"),
    ("Implementation relevance", "implementation_relevance"),
    ("Security implications", "security_implications"),
    ("Limitations", "limitations"),
    ("Fallback", "fallback"),
    ("Deprecation / replacement", "deprecation_or_replacement"),
)


def render_markdown(registry: SourceRegistry) -> str:
    """Render the registry as deterministic Markdown grouped by technology."""
    by_tech: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in registry.sources:
        by_tech[record.technology].append(record)

    lines = [
        "# Source validation",
        "",
        "<!-- GENERATED FILE: edit docs/research/sources.yaml, then run "
        "`uv run ffia sources render`. -->",
        "",
        "Official product documentation overrides older samples. Community content never",
        "overrides authoritative product documentation. Status values: GA, PREVIEW,",
        "DEPRECATED, UNKNOWN/NEEDS VALIDATION, GUIDANCE (architecture guidance), OSS",
        "(official open-source project without a product lifecycle label).",
        "",
        "## Summary",
        "",
        "| Technology | Source | Status | Retrieved |",
        "|---|---|---|---|",
    ]
    for tech in sorted(by_tech):
        for record in sorted(by_tech[tech], key=lambda r: r.id):
            lines.append(
                f"| {_cell(tech)} | [{_cell(record.title)}](#{record.id}) | "
                f"{record.status.value} | {record.retrieved_date.isoformat()} |"
            )
    for tech in sorted(by_tech):
        lines += ["", f"## {tech}"]
        for record in sorted(by_tech[tech], key=lambda r: r.id):
            lines += ["", f'<a id="{record.id}"></a>', "", f"### {record.title}", ""]
            lines += ["| Field | Value |", "|---|---|"]
            for label, attr in _FIELDS:
                value: object = getattr(record, attr)
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                elif isinstance(value, SourceStatus):
                    value = value.value
                lines.append(f"| {label} | {_cell(value)} |")
    lines.append("")
    return "\n".join(lines)
