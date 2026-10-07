"""Read models over the education library. Knowledge-check answers stay server-side until asked."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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

    def __init__(self, library: EducationLibrary) -> None:
        """Wrap a validated library."""
        self.library = library

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
