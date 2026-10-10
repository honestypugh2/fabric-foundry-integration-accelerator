"""Instructional completeness, reference integrity and honest coverage."""

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.education.lessons import EducationReferences, load_education
from fabric_foundry_accelerator.education.workshop import WorkshopContent
from fabric_foundry_accelerator.research.sources import load_registry
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.education import EducationService


def test_workshop_covers_every_lesson_and_resolves_readings(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    view = container.education.workshop()
    lesson_ids = {lesson.id for lesson in container.education.library.lessons}
    assert {brief.lesson_id for brief in view.content.briefs} == lesson_ids
    assert len(view.content.journeys) == 4
    assert view.label == "LOCAL"
    cited = {source for brief in view.content.briefs for source in brief.research.sources}
    assert {source.id for source in view.sources} == cited
    for lesson_id in lesson_ids:
        lesson = container.education.lesson(lesson_id)
        assert lesson.teaching is not None
        assert len(lesson.teaching.research.foundations) >= 2
        assert all("answer" not in check.model_dump() for check in lesson.checks)


def test_coverage_matches_registries_without_claiming_certification(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    view = container.education.workshop()
    assert {item.pattern_id for item in view.coverage} == {
        pattern.id for pattern in container.catalog.patterns
    }
    assert all(item.lesson_ids for item in view.coverage)
    p25 = next(item for item in view.coverage if item.pattern_id == "P25")
    assert "spec-driven-delivery" in p25.lesson_ids
    assert not p25.evidence_ids and p25.default_demo_path == "DOCUMENTATION"
    assert {story.guide_id for story in view.content.use_cases} == set(container.guides)
    assert any(not item.lab_ids for item in view.coverage)
    assert all(entry.limitations for entry in view.content.evidence)


def test_unconfigured_workshop_is_explicit(make_container: Callable[..., Container]) -> None:
    with pytest.raises(KeyError, match="not configured"):
        EducationService(make_container().education.library).workshop()


def test_execution_choices_and_existing_resource_evidence(
    make_container: Callable[..., Container],
) -> None:
    content = make_container().education.workshop().content
    assert {path.mode for path in content.execution_paths} == {"OFFLINE", "HYBRID", "LIVE"}
    assert "ffia serve api --offline" in content.execution_paths[0].commands
    deployments = [entry for entry in content.evidence if entry.category == "DEPLOYMENT"]
    assert {entry.id for entry in deployments} == {
        "fabric-environment",
        "foundry-environment",
        "azure-observability",
    }
    assert all(entry.label == "LIVE" and entry.verification_record for entry in deployments)
    for entry in content.evidence:
        if entry.verification_record:
            assert (REPO_ROOT / entry.verification_record).is_file()
    assert (
        next(
            entry for entry in content.evidence if entry.id == "synthetic-telemetry-ingestion"
        ).label
        == "LIVE"
    )


def test_execution_choices_cannot_omit_offline(make_container: Callable[..., Container]) -> None:
    data = make_container().education.workshop().content.model_dump()
    data["execution_paths"][0]["mode"] = "LIVE"
    with pytest.raises(ValidationError, match="OFFLINE, HYBRID and LIVE"):
        WorkshopContent.model_validate(data)


def test_evidence_record_rejects_private_or_traversal_paths(
    make_container: Callable[..., Container],
) -> None:
    data = make_container().education.workshop().content.model_dump()
    data["evidence"][0]["verification_record"] = "../../.env"
    with pytest.raises(ValidationError, match="verification_record"):
        WorkshopContent.model_validate(data)


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "lesson",
        "source",
        "diagram",
        "journey",
        "guide",
        "missing-story",
        "story-lesson",
        "pattern",
    ],
)
def test_workshop_reference_errors(
    tmp_path: Path, make_container: Callable[..., Container], kind: str
) -> None:
    container = make_container()
    root = tmp_path / "education"
    shutil.copytree(REPO_ROOT / "education", root)
    path = root / "workshop.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if kind == "missing":
        data["briefs"].pop()
    elif kind == "lesson":
        data["briefs"][0]["lesson_id"] = "unknown"
    elif kind == "source":
        data["briefs"][0]["research"]["sources"] = ["unknown"]
    elif kind == "diagram":
        data["briefs"][0]["diagram"] = "unknown"
    elif kind == "journey":
        data["journeys"][0]["lesson_ids"] = ["unknown"]
    elif kind == "guide":
        data["use_cases"][0]["guide_id"] = "unknown"
    elif kind == "missing-story":
        data["use_cases"].pop()
    elif kind == "story-lesson":
        data["use_cases"][0]["lesson_ids"] = ["unknown"]
    else:
        data["evidence"][0]["pattern_ids"] = ["P99"]
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    refs = EducationReferences(
        pattern_ids=frozenset(pattern.id for pattern in container.catalog.patterns),
        source_ids=frozenset(
            source.id for source in load_registry(REPO_ROOT / "docs/research/sources.yaml").sources
        ),
        guide_ids=frozenset(container.guides),
    )
    with pytest.raises(
        ValueError, match=r"missing instructional brief|missing use-case story|unknown"
    ):
        load_education(root, refs)


@pytest.mark.parametrize("field", ["journeys", "briefs", "use_cases", "evidence"])
def test_duplicate_workshop_ids_are_rejected(
    make_container: Callable[..., Container], field: str
) -> None:
    data = make_container().education.workshop().content.model_dump()
    data[field] = [*data[field], data[field][0]]
    with pytest.raises(ValidationError, match="duplicate workshop"):
        WorkshopContent.model_validate(data)
