"""Read models over the education library. Knowledge-check answers stay server-side until asked."""

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.education.guides import UseCaseGuide
from fabric_foundry_accelerator.education.lessons import (
    CapabilityStatus,
    Concept,
    EducationLibrary,
    EvidenceClaim,
    Lab,
    Level,
    LevelBody,
    TryIt,
)
from fabric_foundry_accelerator.education.workshop import LearningBrief, WorkshopContent
from fabric_foundry_accelerator.patterns.catalog import PatternCatalog
from fabric_foundry_accelerator.research.sources import SourceRegistry


class LessonSummary(BaseModel):
    """A lesson in a list."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    area: str
    title: str
    summary: str
    status: CapabilityStatus
    pattern_ids: tuple[str, ...]
    related_labs: tuple[str, ...]
    related_guides: tuple[str, ...]


class PublicCheck(BaseModel):
    """A knowledge check without its answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    level: Level
    question: str
    choices: tuple[str, ...]


class LessonView(LessonSummary):
    """A full lesson for the reader, with checks but no answers."""

    learning_objectives: tuple[str, ...]
    prerequisites: tuple[str, ...]
    concepts: tuple[Concept, ...]
    evidence: tuple[EvidenceClaim, ...]
    try_it: tuple[TryIt, ...]
    copilot_prompt: str
    claude_code_prompt: str
    production_notes: tuple[str, ...]
    sources: tuple[str, ...]
    levels: tuple[LevelBody, ...]
    checks: tuple[PublicCheck, ...]
    teaching: LearningBrief | None = None


class ReadingSource(BaseModel):
    """Resolved public reading; the source registry remains authoritative."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    url: str
    publisher: str


class PatternCoverage(BaseModel):
    """Coverage presence, not certification of an entire pattern."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pattern_id: str
    name: str
    lesson_ids: tuple[str, ...]
    lab_ids: tuple[str, ...]
    guide_ids: tuple[str, ...]
    diagram_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    default_demo_path: str


class WorkshopView(BaseModel):
    """Workshop journeys, verified references and honest breadth coverage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: Literal["LOCAL"] = "LOCAL"
    content: WorkshopContent
    sources: tuple[ReadingSource, ...]
    coverage: tuple[PatternCoverage, ...]


class CheckAnswer(BaseModel):
    """A learner's answer to one knowledge check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choice: int = Field(ge=0, le=9)


class CheckGrade(BaseModel):
    """Whether the answer was correct, with the explanation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    check_id: str
    correct: bool
    correct_choice: int
    explanation: str


class LabSummary(BaseModel):
    """A lab in a list."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    summary: str
    level: Level
    duration_minutes: int
    mode: Literal["OFFLINE", "HYBRID", "LIVE"]
    pattern_ids: tuple[str, ...]
    lessons: tuple[str, ...]


class EducationService:
    """Queries over a validated :class:`EducationLibrary`."""

    def __init__(
        self,
        library: EducationLibrary,
        *,
        catalog: PatternCatalog | None = None,
        guides: Mapping[str, UseCaseGuide] | None = None,
        registry: SourceRegistry | None = None,
    ) -> None:
        """Wrap a validated library."""
        self.library = library
        self.catalog = catalog
        self.guides = guides
        self.registry = registry

    def workshop(self) -> WorkshopView:
        """Return authored journeys and coverage without probing or changing any cloud service."""
        content = self.library.workshop
        if content is None or self.catalog is None or self.guides is None or self.registry is None:
            raise KeyError("Workshop content and coverage dependencies are not configured")
        cited = {source for brief in content.briefs for source in brief.research.sources}
        return WorkshopView(
            content=content,
            sources=tuple(
                ReadingSource(
                    id=source.id,
                    title=source.title,
                    url=str(source.url),
                    publisher=source.publisher,
                )
                for source in self.registry.sources
                if source.id in cited
            ),
            coverage=tuple(
                PatternCoverage(
                    pattern_id=pattern.id,
                    name=pattern.name,
                    lesson_ids=tuple(
                        lesson.id
                        for lesson in self.library.lessons
                        if pattern.id in lesson.pattern_ids
                    ),
                    lab_ids=tuple(
                        lab.id for lab in self.library.labs if pattern.id in lab.pattern_ids
                    ),
                    guide_ids=tuple(
                        guide.id for guide in self.guides.values() if pattern.id in guide.patterns
                    ),
                    diagram_ids=tuple(
                        view.id for view in self.library.views if pattern.id in view.pattern_ids
                    ),
                    evidence_ids=tuple(
                        entry.id for entry in content.evidence if pattern.id in entry.pattern_ids
                    ),
                    default_demo_path=pattern.default_demo_path,
                )
                for pattern in self.catalog.patterns
            ),
        )

    def lessons(
        self, *, area: str | None = None, pattern_id: str | None = None
    ) -> list[LessonSummary]:
        """Return lesson summaries, optionally filtered by area or pattern."""
        return [
            LessonSummary.model_validate(lesson.model_dump(include=set(LessonSummary.model_fields)))
            for lesson in self.library.lessons
            if (area is None or lesson.area == area)
            and (pattern_id is None or pattern_id in lesson.pattern_ids)
        ]

    def lesson(self, lesson_id: str) -> LessonView:
        """Return a lesson without check answers or raise ``KeyError``."""
        lesson = self.library.lesson(lesson_id)
        data = lesson.model_dump(include=set(LessonView.model_fields) - {"checks"})
        data["checks"] = [
            check.model_dump(include=set(PublicCheck.model_fields)) for check in lesson.checks
        ]
        data["teaching"] = (
            next(
                (
                    brief.model_dump()
                    for brief in self.library.workshop.briefs
                    if brief.lesson_id == lesson_id
                ),
                None,
            )
            if self.library.workshop
            else None
        )
        return LessonView.model_validate(data)

    def grade(self, lesson_id: str, check_id: str, answer: CheckAnswer) -> CheckGrade:
        """Grade one answer or raise ``KeyError`` for unknown lessons or checks."""
        check = self.library.lesson(lesson_id).check(check_id)
        return CheckGrade(
            check_id=check.id,
            correct=answer.choice == check.answer,
            correct_choice=check.answer,
            explanation=check.explanation,
        )

    def labs(self) -> list[LabSummary]:
        """Return lab summaries."""
        return [
            LabSummary.model_validate(lab.model_dump(include=set(LabSummary.model_fields)))
            for lab in self.library.labs
        ]

    def lab(self, lab_id: str) -> Lab:
        """Return a lab or raise ``KeyError``."""
        return self.library.lab(lab_id)
