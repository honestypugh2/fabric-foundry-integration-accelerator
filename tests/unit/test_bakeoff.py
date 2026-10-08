"""Bake-off graders: each task fails as prepared and passes with a reference solution.

The reference solutions are test fixtures that prove the graders work. They are not agent runs,
and no replay is ever generated from them.
"""

import json
import shutil
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from tests.conftest import CONFIG_ROOT, REPO_ROOT

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.audit.store import JsonlAuditStore
from fabric_foundry_accelerator.bakeoff.runs import (
    HarnessInfo,
    RunRecord,
    Safety,
    TranscriptEvent,
    check_runs,
    get_run,
    load_runs,
    scorecard,
)
from fabric_foundry_accelerator.bakeoff.tasks import (
    DESIGN_FILE,
    GradeReport,
    TaskSet,
    grade,
    load_tasks,
    prepare,
)
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.models.changes import ChangeRequest, FabricTarget
from fabric_foundry_accelerator.patterns.catalog import load_catalog
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError
from fabric_foundry_accelerator.services.container import Container

TASKS = load_tasks(CONFIG_ROOT)
PATTERN_IDS = {p.id for p in load_catalog(REPO_ROOT / "education").patterns}

REFERENCE_DESIGN: dict[str, Any] = {
    "source": "lab_results",
    "patterns": ["P10"],
    "layers": {
        "bronze": [{"name": "bronze_lab_results", "keys": ["lab_result_id"], "rules": []}],
        "silver": [
            {
                "name": "silver_lab_results",
                "keys": ["lab_result_id"],
                "rules": ["deduplicate on lab_result_id", "result_value is numeric"],
            }
        ],
        "gold": [{"name": "gold_lab_flags", "keys": ["patient_id", "test_code"], "rules": []}],
    },
}


def _grade(task: str, workspace: Path) -> GradeReport:
    return grade(TASKS, task, workspace, catalog_ids=PATTERN_IDS)


def _restore(tasks: TaskSet, workspace: Path, relative: str) -> None:
    path = tasks.repo_path(relative)
    shutil.copy(REPO_ROOT / path, workspace / path)


def test_task_set_is_well_formed() -> None:
    assert TASKS.ids() == [
        "design-medallion",
        "silver-transform",
        "gold-table",
        "fix-failing-transform",
        "change-plan",
    ]
    assert len({t.prompt_sha256 for t in TASKS.tasks}) == len(TASKS.tasks)
    for task in TASKS.tasks:
        assert "do not call any" in " ".join(task.prompt.lower().split())
        for path in task.allowed_changes:
            assert path.startswith("bakeoff/") or (REPO_ROOT / TASKS.repo_path(path)).is_file()
    with pytest.raises(UnknownResourceError):
        TASKS.task("nope")


@pytest.mark.parametrize(
    ("task", "reference"),
    [
        ("silver-transform", "silver/silver_vitals.sql"),
        ("gold-table", "gold_hc_lab/gold_financial.sql"),
        ("fix-failing-transform", "silver/silver_encounters.sql"),
    ],
)
def test_build_tasks_fail_as_prepared_and_pass_with_the_reference(
    tmp_path: Path, task: str, reference: str
) -> None:
    workspace = prepare(TASKS, task, repo_root=REPO_ROOT, dest=tmp_path / task)
    assert (
        (workspace / "BAKEOFF_TASK.md")
        .read_text(encoding="utf-8")
        .count(TASKS.task(task).prompt.strip())
    )
    before = _grade(task, workspace)
    assert not before.passed
    assert not next(c for c in before.checks if c.name == "build_matches_baseline").passed
    _restore(TASKS, workspace, reference)
    after = _grade(task, workspace)
    assert after.passed, after.checks
    assert after.changed_files == (TASKS.repo_path(reference),)


def test_design_task(tmp_path: Path) -> None:
    workspace = prepare(TASKS, "design-medallion", repo_root=REPO_ROOT, dest=tmp_path / "d")
    assert "not found" in _grade("design-medallion", workspace).checks[0].detail
    design = workspace / DESIGN_FILE
    design.parent.mkdir(parents=True, exist_ok=True)
    design.write_text(yaml.safe_dump(REFERENCE_DESIGN), encoding="utf-8")
    assert _grade("design-medallion", workspace).passed
    bad = {**REFERENCE_DESIGN, "patterns": ["P99"], "source": "other"}
    bad["layers"] = {**REFERENCE_DESIGN["layers"], "silver": [{"name": "s", "keys": ["id"]}]}
    design.write_text(yaml.safe_dump(bad), encoding="utf-8")
    detail = _grade("design-medallion", workspace).checks[0].detail
    assert "P99" in detail and "not lab_results" in detail and "data-quality rule" in detail
    assert "lab_result_id" in detail
    design.write_text("source: [unclosed", encoding="utf-8")
    assert "invalid design" in _grade("design-medallion", workspace).checks[0].detail
    (workspace / "README.md").write_text("edited", encoding="utf-8")
    scope = _grade("design-medallion", workspace).checks[1]
    assert not scope.passed and "README.md" in scope.detail


def test_change_plan_task(tmp_path: Path, make_container: Callable[..., Container]) -> None:
    workspace = prepare(TASKS, "change-plan", repo_root=REPO_ROOT, dest=tmp_path / "c")
    assert "no audit log" in _grade("change-plan", workspace).checks[0].detail
    audit_path = workspace / "data" / "runtime" / "audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text("\n", encoding="utf-8")
    assert "no change:plan" in _grade("change-plan", workspace).checks[0].detail
    container = make_container(audit=JsonlAuditStore(audit_path))
    container.changes.plan(
        ChangeRequest(
            operation="create_lakehouse",
            target=FabricTarget(
                workspace_alias="demo-dev",
                item_type="Lakehouse",
                item_name="lab_results_lakehouse",
                destination="LOCAL",
            ),
            reason="Bake-off reference plan.",
            requested_by="engineer-a",
        )
    )
    assert _grade("change-plan", workspace).passed
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"action": "change:execute"}) + "\n")
    assert "further than planning" in _grade("change-plan", workspace).checks[0].detail


def test_prepare_and_grade_errors(tmp_path: Path) -> None:
    (tmp_path / "busy").mkdir()
    (tmp_path / "busy" / "x").write_text("x", encoding="utf-8")
    with pytest.raises(InvalidRequestError, match="not empty"):
        prepare(TASKS, "change-plan", repo_root=REPO_ROOT, dest=tmp_path / "busy")
    with pytest.raises(InvalidRequestError, match="not prepared"):
        _grade("change-plan", tmp_path / "busy")
    workspace = prepare(TASKS, "change-plan", repo_root=REPO_ROOT, dest=tmp_path / "p")
    with pytest.raises(InvalidRequestError, match="prepared for"):
        _grade("design-medallion", workspace)
    broken = TASKS.model_copy(
        update={
            "tasks": tuple(
                t.model_copy(update={"setup": t.setup.model_copy(update={"find": "nope"})})
                if t.id == "fix-failing-transform"
                else t
                for t in TASKS.tasks
            )
        }
    )
    with pytest.raises(InvalidRequestError, match="exactly once"):
        prepare(broken, "fix-failing-transform", repo_root=REPO_ROOT, dest=tmp_path / "f")


def _record(run_id: str, report: GradeReport, *, model: str = "model-a") -> RunRecord:
    return RunRecord(
        schema_version=1,
        run_id=run_id,
        recorded_on=date(2026, 10, 8),
        label="LIVE",
        harness=HarnessInfo(name="Test harness", version="0.0.0"),
        model=model,
        task=report.task,
        prompt_sha256=TASKS.task(report.task).prompt_sha256,
        repo_commit="0" * 40,
        duration_seconds=12.5,
        grade=report,
        safety=Safety(approvals_requested=1, denied_tool_calls=0, unsafe_attempts=0),
        transcript=(TranscriptEvent(t=0, kind="prompt", summary="task prompt"),),
    )


def test_runs_scorecard_api_and_cli(
    tmp_path: Path,
    make_container: Callable[..., Container],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert scorecard(TASKS, []).label == "UNAVAILABLE"
    workspace = prepare(TASKS, "change-plan", repo_root=REPO_ROOT, dest=tmp_path / "w")
    report = _grade("change-plan", workspace)
    replays = tmp_path / "demos" / "bakeoff" / "replays"
    replays.mkdir(parents=True)
    for run in (_record("r1", report), _record("r2", report, model="model-b")):
        (replays / f"{run.run_id}.json").write_text(run.model_dump_json(), encoding="utf-8")
    runs = load_runs(replays)
    assert check_runs(TASKS, runs) == []
    card = scorecard(TASKS, runs)
    assert card.label == "LIVE" and [r.model for r in card.rows] == ["model-a", "model-b"]
    assert all(r.current_prompt and not r.passed for r in card.runs)
    assert get_run(replays, "r1").model == "model-a"
    with pytest.raises(UnknownResourceError):
        get_run(replays, "nope")
    bad = _record("r1", report).model_copy(update={"task": "nope"})
    assert {p.split(": ")[1] for p in check_runs(TASKS, [*runs, bad])} >= {
        "duplicate run_id",
        "unknown task 'nope'",
    }

    with TestClient(create_app(make_container(demos_root=tmp_path / "demos"))) as client:
        assert len(client.get("/api/v1/bakeoff/tasks").json()["tasks"]) == 5
        assert client.get("/api/v1/bakeoff/scorecard").json()["label"] == "LIVE"
        assert client.get("/api/v1/bakeoff/runs/r2").json()["model"] == "model-b"
        assert client.get("/api/v1/bakeoff/runs/nope").status_code == 404

    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("FFIA_AUDIT_PATH", "")
    monkeypatch.setenv("FFIA_DEMOS_ROOT", str(tmp_path / "no-replays"))
    assert main(["bakeoff", "tasks"]) == 0
    assert "fix-failing-transform" in capsys.readouterr().out
    assert main(["bakeoff", "check"]) == 0
    assert main(["bakeoff", "scorecard"]) == 0
    assert "[UNAVAILABLE]" in capsys.readouterr().out
    dest = tmp_path / "cli"
    assert main(["bakeoff", "prepare", "change-plan", "--dest", str(dest)]) == 0
    assert main(["bakeoff", "grade", "change-plan", "--workspace", str(dest)]) == 1
    assert "[FAIL] plan_not_executed" in capsys.readouterr().out
    assert main(["bakeoff", "grade", "change-plan", "--workspace", str(dest), "--json"]) == 1
    monkeypatch.setenv("FFIA_DEMOS_ROOT", str(tmp_path / "demos"))
    assert main(["bakeoff", "scorecard", "--json"]) == 0
    assert main(["bakeoff", "tasks", "--json"]) == 0
    (replays / "bad.json").write_text(_record("r1", report).model_dump_json(), encoding="utf-8")
    assert main(["bakeoff", "check"]) == 1
