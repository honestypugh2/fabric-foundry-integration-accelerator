import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.education.lessons import (
    LAB_SEQUENCE,
    LEVELS,
    ArchitectureMap,
    Completeness,
    EducationLibrary,
    EducationReferences,
    KnowledgeCheck,
    Lab,
    load_education,
    load_lab,
    load_lesson,
)
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.education import CheckAnswer, EducationService

EDUCATION = REPO_ROOT / "education"
EXEMPLAR = EDUCATION / "patterns" / "p08-human-in-the-loop"


@pytest.fixture(scope="module")
def library() -> EducationLibrary:
    from fabric_foundry_accelerator.education.guides import load_guides  # noqa: PLC0415
    from fabric_foundry_accelerator.patterns.catalog import load_catalog  # noqa: PLC0415
    from fabric_foundry_accelerator.research.sources import load_registry  # noqa: PLC0415

    catalog = load_catalog(EDUCATION)
    refs = EducationReferences(
        pattern_ids=frozenset(p.id for p in catalog.patterns),
        source_ids=frozenset(
            s.id for s in load_registry(REPO_ROOT / "docs" / "research" / "sources.yaml").sources
        ),
        guide_ids=frozenset(load_guides(REPO_ROOT / "guides", catalog)),
    )
    return load_education(EDUCATION, refs)


def _refs(**overrides: frozenset[str]) -> EducationReferences:
    values = {
        "pattern_ids": frozenset({"P08", "P09"}),
        "source_ids": frozenset(
            {"foundry-agent-service", "agent-framework", "fabric-rest-identity"}
        ),
        "guide_ids": frozenset({"hc-01-fabric-mcp-powerbi-medallion-lab"}),
    }
    values.update(overrides)
    return EducationReferences(**values)


def _steps() -> list[dict[str, str]]:
    return [
        {"stage": stage, "title": stage.title(), "instructions": f"Do `{stage}`."}
        for stage in LAB_SEQUENCE
    ]


def _lab(lab_id: str = "lab-governed-change", **overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": lab_id,
        "title": "Lab",
        "summary": "A lab.",
        "level": "l300",
        "duration_minutes": 20,
        "mode": "OFFLINE",
        "pattern_ids": ["P08"],
        "lessons": ["p08-human-in-the-loop"],
        "steps": _steps(),
    }
    data.update(overrides)
    return data


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@pytest.fixture
def content(tmp_path: Path) -> Path:
    """A minimal valid education tree: the exemplar lesson, one lab, a map and the gate."""
    root = tmp_path / "education"
    shutil.copytree(EXEMPLAR, root / "patterns" / "p08-human-in-the-loop")
    _write_yaml(root / "labs" / "lab-governed-change" / "lab.yaml", _lab())
    _write_yaml(
        root / "architecture" / "explorer.yaml",
        {
            "version": 1,
            "layers": [
                {"id": "authority", "name": "Authority", "question": "Who?", "summary": "S"}
            ],
            "components": [
                {
                    "id": "policy",
                    "name": "Policy",
                    "layer": "authority",
                    "status": "LOCAL",
                    "description": dict.fromkeys(LEVELS, "text"),
                    "owns": ["Rules"],
                    "pattern_ids": ["P08"],
                    "offline_equivalent": "Itself.",
                }
            ],
        },
    )
    questions: list[dict[str, object]] = [
        {"id": f"Q{i:02d}", "question": f"Question {i}?", "planned_phase": 8} for i in range(1, 31)
    ]
    questions[0] = {
        "id": "Q01",
        "question": "Who approves?",
        "answered_by": ["p08-human-in-the-loop"],
    }
    _write_yaml(root / "completeness.yaml", {"version": 1, "questions": questions})
    return root


# ------------------------------------------------------------------ repository content
def test_repository_content_is_complete(library: EducationLibrary) -> None:
    assert len(library.lessons) >= 14
    assert all(tuple(body.level for body in lesson.levels) == LEVELS for lesson in library.lessons)
    assert all({c.level for c in lesson.checks} == set(LEVELS) for lesson in library.lessons)
    anchors = {
        p for lesson in library.lessons if lesson.area == "patterns" for p in lesson.pattern_ids
    }
    assert {"P06", "P08", "P09", "P10", "P11", "P16", "P17"} <= anchors
    assert len(library.labs) >= 5
    assert all(tuple(step.stage for step in lab.steps) == LAB_SEQUENCE for lab in library.labs)
    report = library.completeness_report()
    assert report.total == 30 and report.answered == 30
    assert all(item.answered for item in report.items)


def test_repository_content_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    args = [
        "education",
        "check",
        "--education-root",
        str(EDUCATION),
        "--guides-root",
        str(REPO_ROOT / "guides"),
        "--sources",
        str(REPO_ROOT / "docs" / "research" / "sources.yaml"),
    ]
    assert main(args) == 0
    assert "completeness gate:" in capsys.readouterr().out
    assert main([*args, "--min-coverage", "1.0"]) == 0
    capsys.readouterr()
    shutil.copytree(EDUCATION, tmp_path / "education")
    gate = tmp_path / "education" / "completeness.yaml"
    data = yaml.safe_load(gate.read_text(encoding="utf-8"))
    data["questions"][24].pop("answered_by")
    data["questions"][24]["planned_phase"] = 8
    _write_yaml(gate, data)
    incomplete_args = [
        "education",
        "check",
        "--education-root",
        str(tmp_path / "education"),
        "--guides-root",
        str(REPO_ROOT / "guides"),
        "--sources",
        str(REPO_ROOT / "docs" / "research" / "sources.yaml"),
        "--min-coverage",
        "1.0",
    ]
    assert main(incomplete_args) == 1
    assert "below the required" in capsys.readouterr().err


# ------------------------------------------------------------------ loader rules
def test_minimal_tree_loads_and_reports_coverage(content: Path) -> None:
    library = load_education(content, _refs())
    assert [lesson.id for lesson in library.lessons] == ["p08-human-in-the-loop"]
    report = library.completeness_report()
    assert (report.answered, report.total, report.coverage) == (1, 30, 0.0333)
    assert library.lab("lab-governed-change").steps[4].stage == "BREAK IT"
    with pytest.raises(KeyError, match="unknown lab"):
        library.lab("missing")
    with pytest.raises(KeyError, match="unknown lesson"):
        library.lesson("missing")


@pytest.mark.parametrize(
    ("refs", "message"),
    [
        (_refs(pattern_ids=frozenset()), "unknown pattern P08"),
        (_refs(source_ids=frozenset({"agent-framework"})), "unknown source"),
        (_refs(guide_ids=frozenset()), "unknown guide"),
    ],
)
def test_cross_references_are_validated(
    content: Path, refs: EducationReferences, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        load_education(content, refs)


def test_unknown_lab_lesson_and_prerequisite_references(content: Path) -> None:
    _write_yaml(content / "labs" / "lab-governed-change" / "lab.yaml", _lab(lessons=["nope"]))
    with pytest.raises(ValueError, match="unknown lesson nope"):
        load_education(content, _refs())
    _write_yaml(content / "labs" / "lab-governed-change" / "lab.yaml", _lab())
    lesson_file = content / "patterns" / "p08-human-in-the-loop" / "lesson.yaml"
    meta = yaml.safe_load(lesson_file.read_text(encoding="utf-8"))
    _write_yaml(
        lesson_file, {**meta, "prerequisites": ["missing-lesson"], "related_labs": ["missing-lab"]}
    )
    with pytest.raises(ValueError, match="unknown prerequisite lesson missing-lesson") as error:
        load_education(content, _refs())
    assert "unknown lab missing-lab" in str(error.value)


def test_completeness_references_existing_lessons(content: Path) -> None:
    data = yaml.safe_load((content / "completeness.yaml").read_text(encoding="utf-8"))
    data["questions"][1] = {"id": "Q02", "question": "?", "answered_by": ["ghost"]}
    _write_yaml(content / "completeness.yaml", data)
    with pytest.raises(ValueError, match="completeness Q02: unknown lesson ghost"):
        load_education(content, _refs())


def test_architecture_references_are_validated(content: Path) -> None:
    path = content / "architecture" / "explorer.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["components"][0]["sources"] = ["nope"]
    _write_yaml(path, data)
    with pytest.raises(ValueError, match="architecture policy: unknown source nope"):
        load_education(content, _refs())
    data["components"][0]["sources"] = []
    data["components"][0]["pattern_ids"] = ["P99"]
    _write_yaml(path, data)
    with pytest.raises(ValueError, match="architecture policy: unknown pattern P99"):
        load_education(content, _refs())


def test_lesson_folder_and_files_are_enforced(content: Path) -> None:
    folder = content / "patterns" / "p08-human-in-the-loop"
    (folder / "l400.md").unlink()
    with pytest.raises(ValueError, match=r"missing l400\.md"):
        load_lesson(folder)
    moved = content / "mcp" / "p08-human-in-the-loop"
    shutil.copytree(EXEMPLAR, moved)
    with pytest.raises(ValueError, match="must live in education/patterns"):
        load_lesson(moved)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ("## Too short", "too short"),
        ("## Heading\n\n" + "Words. " * 60 + "\n\n<script>alert(1)</script>", "raw HTML"),
    ],
)
def test_level_bodies_must_teach_without_html(tmp_path: Path, body: str, message: str) -> None:
    folder = tmp_path / "patterns" / "p08-human-in-the-loop"
    shutil.copytree(EXEMPLAR, folder)
    (folder / "l200.md").write_text(body, encoding="utf-8")
    with pytest.raises(ValidationError, match=message):
        load_lesson(folder)


def test_html_inside_code_is_allowed(tmp_path: Path) -> None:
    folder = tmp_path / "patterns" / "p08-human-in-the-loop"
    shutil.copytree(EXEMPLAR, folder)
    body = (
        "## Code\n\n"
        + "Text. " * 50
        + "\n\n```bash\ncurl localhost/<id>\n```\n\nUse `<change_id>`."
    )
    (folder / "l300.md").write_text(body, encoding="utf-8")
    assert load_lesson(folder).levels[3].markdown == body


def test_every_level_needs_a_check(tmp_path: Path) -> None:
    folder = tmp_path / "patterns" / "p08-human-in-the-loop"
    shutil.copytree(EXEMPLAR, folder)
    checks = yaml.safe_load((folder / "checks.yaml").read_text(encoding="utf-8"))
    _write_yaml(
        folder / "checks.yaml", {"checks": [c for c in checks["checks"] if c["level"] != "l400"]}
    )
    with pytest.raises(ValidationError, match="no knowledge check"):
        load_lesson(folder)
    _write_yaml(folder / "checks.yaml", {"checks": [*checks["checks"], checks["checks"][0]]})
    with pytest.raises(ValidationError, match="duplicate check ids"):
        load_lesson(folder)


def test_knowledge_check_rules() -> None:
    base = {"id": "q", "level": "l100", "question": "?", "choices": ["a", "b"], "explanation": "e"}
    with pytest.raises(ValidationError, match="out of range"):
        KnowledgeCheck.model_validate({**base, "answer": 2})
    with pytest.raises(ValidationError, match="unique"):
        KnowledgeCheck.model_validate({**base, "choices": ["a", "a"], "answer": 0})


def test_lab_rules(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="stages must follow"):
        Lab.model_validate(_lab(steps=list(reversed(_steps()))))
    html_steps = _steps()
    html_steps[0]["instructions"] = "<b>bold</b>"
    with pytest.raises(ValidationError, match="raw HTML"):
        Lab.model_validate(_lab(steps=html_steps))
    _write_yaml(tmp_path / "labs" / "lab-other" / "lab.yaml", _lab("lab-governed-change"))
    with pytest.raises(ValueError, match="must live in education/labs/lab-governed-change"):
        load_lab(tmp_path / "labs" / "lab-other" / "lab.yaml")


def test_architecture_and_completeness_rules() -> None:
    layer = {"id": "a", "name": "A", "question": "?", "summary": "s"}
    component = {
        "id": "c",
        "name": "C",
        "layer": "a",
        "status": "GA",
        "description": dict.fromkeys(LEVELS, "t"),
        "owns": ["x"],
        "offline_equivalent": "o",
    }
    flow = {"id": "f", "source": "c", "target": "c", "label": "l", "kind": "access"}
    ArchitectureMap.model_validate(
        {"version": 1, "layers": [layer], "components": [component], "flows": [flow]}
    )
    with pytest.raises(ValidationError, match="unknown layer"):
        ArchitectureMap.model_validate(
            {"version": 1, "layers": [layer], "components": [{**component, "layer": "z"}]}
        )
    with pytest.raises(ValidationError, match="unknown components"):
        ArchitectureMap.model_validate(
            {
                "version": 1,
                "layers": [layer],
                "components": [component],
                "flows": [{**flow, "target": "z"}],
            }
        )
    with pytest.raises(ValidationError, match="duplicate component ids"):
        ArchitectureMap.model_validate(
            {"version": 1, "layers": [layer], "components": [component, component]}
        )
    questions = [{"id": f"Q{i:02d}", "question": "?", "planned_phase": 9} for i in range(1, 31)]
    questions[0] = {"id": "Q01", "question": "?"}
    with pytest.raises(ValidationError, match="need a planned_phase"):
        Completeness.model_validate({"version": 1, "questions": questions})


# ------------------------------------------------------------------ service
def test_education_service_hides_answers_and_grades(library: EducationLibrary) -> None:
    service = EducationService(library)
    assert {s.id for s in service.lessons(pattern_id="P08")} >= {"p08-human-in-the-loop"}
    assert all(s.area == "patterns" for s in service.lessons(area="patterns"))
    view = service.lesson("p08-human-in-the-loop")
    assert "answer" not in view.checks[0].model_dump()
    check = library.lesson("p08-human-in-the-loop").checks[0]
    right = service.grade(view.id, check.id, CheckAnswer(choice=check.answer))
    wrong = service.grade(
        view.id, check.id, CheckAnswer(choice=(check.answer + 1) % len(check.choices))
    )
    assert right.correct and not wrong.correct and wrong.correct_choice == check.answer
    with pytest.raises(KeyError, match="has no check"):
        service.grade(view.id, "missing", CheckAnswer(choice=0))
    assert [lab.id for lab in service.labs()] == [lab.id for lab in library.labs]
    assert service.lab(library.labs[0].id).steps


def test_container_loads_education(make_container: Callable[..., Container]) -> None:
    container = make_container()
    assert container.education.library.lessons
