"""Structured workshop journeys, instructional briefs and dated evidence."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.models.execution import ExecutionLabel


class ContentModel(BaseModel):
    """Strict immutable authored content."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class Foundation(ContentModel):
    """An underlying idea and its modern application, not a product lineage claim."""

    idea: str = Field(min_length=10)
    explanation: str = Field(min_length=30)
    application: str = Field(min_length=30)


class ResearchLens(ContentModel):
    """A falsifiable, reproducible exercise grounded in theory."""

    question: str = Field(min_length=20)
    foundations: tuple[Foundation, ...] = Field(min_length=2)
    evolution: tuple[str, ...] = Field(min_length=2)
    hypothesis: str = Field(min_length=30)
    experiment: str = Field(min_length=50)
    baseline: str = Field(min_length=20)
    metrics: tuple[str, ...] = Field(min_length=2)
    limitations: tuple[str, ...] = Field(min_length=2)
    sources: tuple[str, ...] = Field(min_length=1)


class LearningBrief(ContentModel):
    """The what/why/when/how contract, independent of the learner's depth."""

    lesson_id: str
    what: str = Field(min_length=30)
    why: str = Field(min_length=30)
    when: str = Field(min_length=30)
    when_not: str = Field(min_length=30)
    how: tuple[str, ...] = Field(min_length=2)
    expected_result: str = Field(min_length=30)
    failure_and_recovery: str = Field(min_length=30)
    diagram: str | None = None
    research: ResearchLens


class LearningJourney(ContentModel):
    """A deliberate sequence; durations are estimates, not observed task timings."""

    id: str
    title: str
    summary: str
    duration_minutes: int = Field(ge=5, le=480)
    lesson_ids: tuple[str, ...] = Field(min_length=1)


class CapabilityStage(ContentModel):
    """A before/after capability, its control and measurable evidence."""

    title: str
    task: str
    capability: str
    control: str
    evidence: str


class UseCaseStory(ContentModel):
    """Business-to-build framing, keyed by the existing use-case registry."""

    guide_id: str
    problem: str
    audience: str
    outcomes: tuple[str, ...] = Field(min_length=2)
    lesson_ids: tuple[str, ...] = Field(min_length=1)
    stages: tuple[CapabilityStage, ...] = Field(min_length=2)
    questions: tuple[str, ...] = ()
    production_gaps: tuple[str, ...] = Field(min_length=1)
    presenter_path: str = Field(pattern=r"^/talktracks/[a-z0-9-]+\.html$")


class EvidenceEntry(ContentModel):
    """Historical evidence with explicit scope; never a current health probe."""

    id: str
    category: Literal["DEPLOYMENT", "OPERATION", "INTERFACE"] = "OPERATION"
    title: str
    recorded_on: date
    label: ExecutionLabel
    provider: str
    server: str
    tool: str
    scope: str
    limitations: tuple[str, ...] = Field(min_length=1)
    pattern_ids: tuple[str, ...]
    screenshot: str | None = Field(default=None, pattern=r"^/workshop-evidence/[a-z0-9-]+\.png$")
    verification_record: str | None = Field(
        default=None, pattern=r"^(?:docs|infra)/(?:[a-z0-9-]+/)*[A-Za-z0-9-]+\.md$"
    )


class ExecutionPath(ContentModel):
    """Authored operating choices; commands are instructions, not automatic execution."""

    mode: Literal["OFFLINE", "HYBRID", "LIVE"]
    title: str
    description: str = Field(min_length=30)
    results: str = Field(min_length=30)
    fallback: str = Field(min_length=20)
    prerequisites: tuple[str, ...] = Field(min_length=1)
    commands: tuple[str, ...] = Field(min_length=1)
    safety: str = Field(min_length=30)


class WorkshopContent(ContentModel):
    """``education/workshop.yaml``; all instructional copy stays outside React."""

    version: Literal[1]
    title: str
    summary: str
    execution_summary: str = Field(min_length=30)
    execution_paths: tuple[ExecutionPath, ...] = Field(min_length=3, max_length=3)
    journeys: tuple[LearningJourney, ...] = Field(min_length=2)
    briefs: tuple[LearningBrief, ...] = Field(min_length=1)
    use_cases: tuple[UseCaseStory, ...] = Field(min_length=1)
    evidence: tuple[EvidenceEntry, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique(self) -> Self:
        if {path.mode for path in self.execution_paths} != {"OFFLINE", "HYBRID", "LIVE"}:
            raise ValueError("execution paths must include OFFLINE, HYBRID and LIVE exactly once")
        for label, ids in (
            ("journey", [item.id for item in self.journeys]),
            ("brief", [item.lesson_id for item in self.briefs]),
            ("use case", [item.guide_id for item in self.use_cases]),
            ("evidence", [item.id for item in self.evidence]),
        ):
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate workshop {label} ids")
        return self
