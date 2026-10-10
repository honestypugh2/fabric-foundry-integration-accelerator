"""Structured learning content: lessons, labs, the architecture map and the completeness gate.

Content is data, not UI copy. Every lesson teaches all five levels (Executive, L100-L400) and has
knowledge checks for each. Every lab follows the fixed eleven-stage sequence. Cross-references
(patterns, sources, labs, guides, prerequisites) are validated when the library loads.
"""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from fabric_foundry_accelerator.education.diagrams import (
    DiagramView,
    load_views,
    view_reference_errors,
)
from fabric_foundry_accelerator.education.guides import UseCaseGuide
from fabric_foundry_accelerator.education.workshop import WorkshopContent
from fabric_foundry_accelerator.models.execution import EvidenceCategory

Level = Literal["executive", "l100", "l200", "l300", "l400"]
LEVELS: tuple[Level, ...] = ("executive", "l100", "l200", "l300", "l400")
LEVEL_LABELS: dict[Level, str] = {
    "executive": "Executive",
    "l100": "L100",
    "l200": "L200",
    "l300": "L300",
    "l400": "L400",
}
Area = Literal[
    "architecture",
    "patterns",
    "fabric",
    "foundry",
    "fabric-iq",
    "data-agents",
    "mcp",
    "copilot",
    "claude",
    "agentic-data-engineering",
    "recovery",
    "security",
    "evaluation",
]
CapabilityStatus = Literal[
    "GA", "PREVIEW", "MIXED", "DEPRECATED", "UNKNOWN/NEEDS VALIDATION", "LOCAL"
]
LabStage = Literal[
    "LEARN",
    "SEE",
    "BUILD",
    "INSPECT",
    "BREAK IT",
    "RECOVER",
    "VERIFY",
    "GO DEEPER",
    "TRY WITH COPILOT",
    "TRY WITH CLAUDE CODE",
    "PRODUCTION NOTES",
]
LAB_SEQUENCE: tuple[LabStage, ...] = (
    "LEARN",
    "SEE",
    "BUILD",
    "INSPECT",
    "BREAK IT",
    "RECOVER",
    "VERIFY",
    "GO DEEPER",
    "TRY WITH COPILOT",
    "TRY WITH CLAUDE CODE",
    "PRODUCTION NOTES",
)
ResultLabel = Literal["LOCAL", "SIMULATED", "HYBRID", "PREVIEW", "UNAVAILABLE"]

_SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"
# Lesson bodies are rendered through a sanitizer, but raw HTML is still rejected at load time so
# content stays portable Markdown and reviewers never have to reason about embedded markup.
_RAW_HTML = re.compile(r"<\s*[a-zA-Z!/]")
_CODE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)
_MIN_BODY_CHARS = 200


def _has_raw_html(markdown: str) -> bool:
    """Return True if Markdown outside code spans and fences contains an HTML tag."""
    return bool(_RAW_HTML.search(_CODE.sub("", markdown)))


class Concept(BaseModel):
    """A glossary term taught by a lesson."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    term: str
    definition: str


class EvidenceClaim(BaseModel):
    """A claim with how strongly it is supported (keeps teaching honest)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    statement: str
    category: EvidenceCategory
    sources: tuple[str, ...] = ()


class TryIt(BaseModel):
    """An offline command the learner can run, and the label its result carries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    command: str
    result_label: ResultLabel


class KnowledgeCheck(BaseModel):
    """A multiple-choice check for one level. The answer never leaves the backend unasked."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    level: Level
    question: str
    choices: tuple[str, ...] = Field(min_length=2, max_length=5)
    answer: int = Field(ge=0)
    explanation: str

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.answer >= len(self.choices):
            raise ValueError(f"check {self.id}: answer index {self.answer} is out of range")
        if len(set(self.choices)) != len(self.choices):
            raise ValueError(f"check {self.id}: choices must be unique")
        return self


class LessonMeta(BaseModel):
    """``lesson.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    area: Area
    title: str
    summary: str
    status: CapabilityStatus
    pattern_ids: tuple[str, ...] = ()
    learning_objectives: tuple[str, ...] = Field(min_length=2)
    prerequisites: tuple[str, ...] = ()
    concepts: tuple[Concept, ...] = Field(min_length=1)
    evidence: tuple[EvidenceClaim, ...] = Field(min_length=1)
    try_it: tuple[TryIt, ...] = ()
    copilot_prompt: str
    claude_code_prompt: str
    production_notes: tuple[str, ...] = Field(min_length=1)
    sources: tuple[str, ...] = Field(min_length=1)
    related_labs: tuple[str, ...] = ()
    related_guides: tuple[str, ...] = ()


class ChecksFile(BaseModel):
    """``checks.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    checks: tuple[KnowledgeCheck, ...] = Field(min_length=1)


class LevelBody(BaseModel):
    """The Markdown body of one level."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: Level
    label: str
    markdown: str


class Lesson(LessonMeta):
    """A lesson with its five level bodies and knowledge checks."""

    levels: tuple[LevelBody, ...]
    checks: tuple[KnowledgeCheck, ...]

    @model_validator(mode="after")
    def _complete(self) -> Self:
        if tuple(body.level for body in self.levels) != LEVELS:
            raise ValueError(f"lesson {self.id}: needs exactly the levels {list(LEVELS)} in order")
        for body in self.levels:
            if len(body.markdown.strip()) < _MIN_BODY_CHARS:
                raise ValueError(f"lesson {self.id}: {body.level} body is too short to teach")
            if _has_raw_html(body.markdown):
                raise ValueError(f"lesson {self.id}: {body.level} body contains raw HTML")
        missing = set(LEVELS) - {check.level for check in self.checks}
        if missing:
            raise ValueError(f"lesson {self.id}: no knowledge check for {sorted(missing)}")
        ids = [check.id for check in self.checks]
        if len(set(ids)) != len(ids):
            raise ValueError(f"lesson {self.id}: duplicate check ids")
        return self

    def check(self, check_id: str) -> KnowledgeCheck:
        """Return a check by ID or raise ``KeyError``."""
        for candidate in self.checks:
            if candidate.id == check_id:
                return candidate
        raise KeyError(f"lesson {self.id!r} has no check {check_id!r}")


class LabStep(BaseModel):
    """One stage of a lab."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage: LabStage
    title: str
    instructions: str
    commands: tuple[str, ...] = ()
    expected: str | None = None
    evidence_category: EvidenceCategory | None = None

    @model_validator(mode="after")
    def _no_html(self) -> Self:
        if _has_raw_html(self.instructions):
            raise ValueError(f"lab stage {self.stage}: instructions contain raw HTML")
        return self


class Lab(BaseModel):
    """``education/labs/<id>/lab.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    title: str
    summary: str
    level: Level
    duration_minutes: int = Field(ge=5, le=240)
    mode: Literal["OFFLINE", "HYBRID", "LIVE"]
    pattern_ids: tuple[str, ...] = ()
    lessons: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    steps: tuple[LabStep, ...]

    @model_validator(mode="after")
    def _sequence(self) -> Self:
        if tuple(step.stage for step in self.steps) != LAB_SEQUENCE:
            raise ValueError(f"lab {self.id}: stages must follow {list(LAB_SEQUENCE)} exactly")
        return self


class LevelText(BaseModel):
    """A short description per level."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    executive: str
    l100: str
    l200: str
    l300: str
    l400: str


class ArchitectureLayer(BaseModel):
    """A layer of the reference architecture and the question it answers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    name: str
    question: str
    summary: str


class ArchitectureComponent(BaseModel):
    """A component of the reference architecture."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    name: str
    layer: str
    status: CapabilityStatus
    description: LevelText
    owns: tuple[str, ...] = Field(min_length=1)
    does_not_own: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    offline_equivalent: str
    sources: tuple[str, ...] = ()


class ArchitectureFlow(BaseModel):
    """A directed interaction between two components."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    source: str
    target: str
    label: str
    kind: Literal["context", "reasoning", "access", "authority", "evidence", "fallback", "change"]


class ArchitectureMap(BaseModel):
    """``education/architecture/explorer.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    layers: tuple[ArchitectureLayer, ...] = Field(min_length=1)
    components: tuple[ArchitectureComponent, ...] = Field(min_length=1)
    flows: tuple[ArchitectureFlow, ...] = ()

    @model_validator(mode="after")
    def _references(self) -> Self:
        layer_ids = [layer.id for layer in self.layers]
        component_ids = [component.id for component in self.components]
        for label, ids in (("layer", layer_ids), ("component", component_ids)):
            if len(set(ids)) != len(ids):
                raise ValueError(f"duplicate {label} ids")
        for component in self.components:
            if component.layer not in layer_ids:
                raise ValueError(f"component {component.id}: unknown layer {component.layer!r}")
        for flow in self.flows:
            unknown = {flow.source, flow.target} - set(component_ids)
            if unknown:
                raise ValueError(f"flow {flow.id}: unknown components {sorted(unknown)}")
        return self


class CompletenessQuestion(BaseModel):
    """One question the architecture must be able to answer at every level."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^Q\d{2}$")
    question: str
    answered_by: tuple[str, ...] = ()
    planned_phase: int | None = Field(default=None, ge=4, le=9)

    @model_validator(mode="after")
    def _tracked(self) -> Self:
        if not self.answered_by and self.planned_phase is None:
            raise ValueError(f"{self.id}: unanswered questions need a planned_phase")
        return self


class Completeness(BaseModel):
    """``education/completeness.yaml``: the 30-question architecture completeness gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    questions: tuple[CompletenessQuestion, ...] = Field(min_length=30, max_length=30)


class CompletenessItem(BaseModel):
    """The coverage of one question."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    question: str
    answered: bool
    answered_by: tuple[str, ...]
    planned_phase: int | None


class CompletenessReport(BaseModel):
    """Coverage of the completeness gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total: int
    answered: int
    coverage: float
    items: tuple[CompletenessItem, ...]


class EducationLibrary(BaseModel):
    """Every lesson, lab, the architecture map and the completeness gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lessons: tuple[Lesson, ...]
    labs: tuple[Lab, ...]
    architecture: ArchitectureMap
    completeness: Completeness
    views: tuple[DiagramView, ...] = ()
    workshop: WorkshopContent | None = None

    def view(self, view_id: str) -> DiagramView:
        """Return an architecture view by ID or raise ``KeyError``."""
        for candidate in self.views:
            if candidate.id == view_id:
                return candidate
        raise KeyError(f"unknown architecture view {view_id!r}")

    def lesson(self, lesson_id: str) -> Lesson:
        """Return a lesson by ID or raise ``KeyError``."""
        for candidate in self.lessons:
            if candidate.id == lesson_id:
                return candidate
        raise KeyError(f"unknown lesson {lesson_id!r}")

    def lab(self, lab_id: str) -> Lab:
        """Return a lab by ID or raise ``KeyError``."""
        for candidate in self.labs:
            if candidate.id == lab_id:
                return candidate
        raise KeyError(f"unknown lab {lab_id!r}")

    def completeness_report(self) -> CompletenessReport:
        """Report which completeness questions are answered by existing lessons."""
        lesson_ids = {lesson.id for lesson in self.lessons}
        items = tuple(
            CompletenessItem(
                id=q.id,
                question=q.question,
                answered=bool(q.answered_by) and set(q.answered_by) <= lesson_ids,
                answered_by=q.answered_by,
                planned_phase=q.planned_phase,
            )
            for q in self.completeness.questions
        )
        answered = sum(item.answered for item in items)
        return CompletenessReport(
            total=len(items),
            answered=answered,
            coverage=round(answered / len(items), 4),
            items=items,
        )


class EducationReferences(BaseModel):
    """Known identifiers that content may reference."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pattern_ids: frozenset[str]
    source_ids: frozenset[str]
    guide_ids: frozenset[str]


def _yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_lesson(folder: Path) -> Lesson:
    """Load ``lesson.yaml``, the five level bodies and ``checks.yaml`` from a lesson folder."""
    meta = LessonMeta.model_validate(_yaml(folder / "lesson.yaml"))
    if meta.id != folder.name or meta.area != folder.parent.name:
        raise ValueError(
            f"lesson {meta.id!r} must live in education/{meta.area}/{meta.id}/ (found {folder})"
        )
    levels: list[LevelBody] = []
    for level in LEVELS:
        body = folder / f"{level}.md"
        if not body.is_file():
            raise ValueError(f"lesson {meta.id}: missing {body.name}")
        levels.append(
            LevelBody(
                level=level, label=LEVEL_LABELS[level], markdown=body.read_text(encoding="utf-8")
            )
        )
    checks = ChecksFile.model_validate(_yaml(folder / "checks.yaml")).checks
    return Lesson.model_validate({**meta.model_dump(), "levels": levels, "checks": checks})


def load_lab(path: Path) -> Lab:
    """Load one ``lab.yaml``."""
    lab = Lab.model_validate(_yaml(path))
    if lab.id != path.parent.name:
        raise ValueError(f"lab {lab.id!r} must live in education/labs/{lab.id}/")
    return lab


def _workshop_reference_errors(library: EducationLibrary, refs: EducationReferences) -> list[str]:
    errors: list[str] = []
    lesson_ids = {lesson.id for lesson in library.lessons}
    if library.workshop is not None:
        workshop = library.workshop
        brief_ids = {brief.lesson_id for brief in workshop.briefs}
        errors += [
            f"workshop: missing instructional brief for {item}"
            for item in sorted(lesson_ids - brief_ids)
        ]
        errors += [f"workshop: unknown lesson {item}" for item in sorted(brief_ids - lesson_ids)]
        for brief in workshop.briefs:
            errors += [
                f"workshop {brief.lesson_id}: unknown source {item}"
                for item in brief.research.sources
                if item not in refs.source_ids
            ]
            if brief.diagram and brief.diagram not in {view.id for view in library.views}:
                errors.append(f"workshop {brief.lesson_id}: unknown diagram {brief.diagram}")
        for journey in workshop.journeys:
            errors += [
                f"workshop {journey.id}: unknown lesson {item}"
                for item in journey.lesson_ids
                if item not in lesson_ids
            ]
        story_ids = {story.guide_id for story in workshop.use_cases}
        errors += [
            f"workshop: missing use-case story for {item}"
            for item in sorted(refs.guide_ids - story_ids)
        ]
        for story in workshop.use_cases:
            if story.guide_id not in refs.guide_ids:
                errors.append(f"workshop: unknown use case {story.guide_id}")
            errors += [
                f"workshop {story.guide_id}: unknown lesson {item}"
                for item in story.lesson_ids
                if item not in lesson_ids
            ]
        for entry in workshop.evidence:
            errors += [
                f"workshop evidence {entry.id}: unknown pattern {item}"
                for item in entry.pattern_ids
                if item not in refs.pattern_ids
            ]
    return errors


def _cross_reference_errors(library: EducationLibrary, refs: EducationReferences) -> list[str]:
    errors = _workshop_reference_errors(library, refs)
    lesson_ids = {lesson.id for lesson in library.lessons}
    lab_ids = {lab.id for lab in library.labs}
    if len(lesson_ids) != len(library.lessons):
        errors.append("duplicate lesson ids")
    for lesson in library.lessons:
        errors += [
            f"{lesson.id}: unknown pattern {p}"
            for p in lesson.pattern_ids
            if p not in refs.pattern_ids
        ]
        cited = {*lesson.sources, *(s for claim in lesson.evidence for s in claim.sources)}
        errors += [f"{lesson.id}: unknown source {s}" for s in sorted(cited - refs.source_ids)]
        errors += [
            f"{lesson.id}: unknown lab {lab}" for lab in lesson.related_labs if lab not in lab_ids
        ]
        errors += [
            f"{lesson.id}: unknown guide {g}"
            for g in lesson.related_guides
            if g not in refs.guide_ids
        ]
        errors += [
            f"{lesson.id}: unknown prerequisite lesson {p}"
            for p in lesson.prerequisites
            if p not in lesson_ids
        ]
    for lab in library.labs:
        errors += [
            f"{lab.id}: unknown pattern {p}" for p in lab.pattern_ids if p not in refs.pattern_ids
        ]
        errors += [
            f"{lab.id}: unknown lesson {item}" for item in lab.lessons if item not in lesson_ids
        ]
    for component in library.architecture.components:
        errors += [
            f"architecture {component.id}: unknown pattern {p}"
            for p in component.pattern_ids
            if p not in refs.pattern_ids
        ]
        errors += [
            f"architecture {component.id}: unknown source {s}"
            for s in component.sources
            if s not in refs.source_ids
        ]
    component_ids = {c.id for c in library.architecture.components}
    for view in library.views:
        errors += view_reference_errors(
            view,
            component_ids=component_ids,
            source_ids=refs.source_ids,
            pattern_ids=refs.pattern_ids,
        )
    for question in library.completeness.questions:
        errors += [
            f"completeness {question.id}: unknown lesson {item}"
            for item in question.answered_by
            if item not in lesson_ids
        ]
    return errors


def guide_diagram_errors(
    library: EducationLibrary, guides: Mapping[str, UseCaseGuide]
) -> list[str]:
    """Return guide diagram references (view and focus nodes) that do not exist."""
    views = {v.id: v for v in library.views}
    errors: list[str] = []
    for guide in guides.values():
        if guide.diagram is None:
            errors += [
                f"guide {guide.id} step {s.id}: diagram_focus needs a guide diagram"
                for s in guide.steps
                if s.diagram_focus
            ]
            continue
        view = views.get(guide.diagram)
        if view is None:
            errors.append(f"guide {guide.id}: unknown diagram {guide.diagram}")
            continue
        node_ids = {n.id for n in view.nodes}
        errors += [
            f"guide {guide.id} step {step.id}: unknown diagram node {node}"
            for step in guide.steps
            for node in step.diagram_focus
            if node not in node_ids
        ]
    return errors


def load_education(education_root: Path, refs: EducationReferences) -> EducationLibrary:
    """Load and cross-validate every piece of structured learning content.

    Raises:
        ValueError: when content is malformed or references unknown patterns, sources, labs,
            guides or lessons.
    """
    lessons = tuple(
        load_lesson(path.parent) for path in sorted(education_root.glob("*/*/lesson.yaml"))
    )
    labs = tuple(load_lab(path) for path in sorted((education_root / "labs").glob("*/lab.yaml")))
    library = EducationLibrary(
        lessons=lessons,
        labs=labs,
        architecture=ArchitectureMap.model_validate(
            _yaml(education_root / "architecture" / "explorer.yaml")
        ),
        completeness=Completeness.model_validate(_yaml(education_root / "completeness.yaml")),
        views=load_views(education_root / "architecture" / "views"),
        workshop=(
            WorkshopContent.model_validate(_yaml(education_root / "workshop.yaml"))
            if (education_root / "workshop.yaml").is_file()
            else None
        ),
    )
    errors = _cross_reference_errors(library, refs)
    if errors:
        raise ValueError("education content has invalid references:\n- " + "\n- ".join(errors))
    return library
