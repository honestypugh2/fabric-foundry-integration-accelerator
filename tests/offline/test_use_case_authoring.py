"""A third real guide and an isolated fourth guide prove the shared authoring path offline."""

import json
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.education.authoring import authoring_errors
from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.services.container import Container
from tests.conftest import REPO_ROOT

GUIDE = "dq-01-synthetic-quality-investigation"


def test_real_registered_guide_api_and_governance(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    guide = container.guides[GUIDE]
    with TestClient(create_app(container)) as client:
        assert GUIDE in {item["id"] for item in client.get("/api/v1/guides").json()}
        assert client.get(f"/api/v1/guides/{GUIDE}").json()["dataset_profile"] == "mfg-sales-v1"
        for step in guide.steps:
            response = client.get(f"/api/v1/guides/{GUIDE}/steps/{step.id}")
            assert response.status_code == 200 and response.json()["id"] == step.id
        assert client.get(f"/api/v1/guides/{GUIDE}/steps/99-missing").status_code == 404
        workshop = client.get("/api/v1/education/workshop").json()
        story = next(item for item in workshop["content"]["use_cases"] if item["guide_id"] == GUIDE)
        assert all(
            client.get(f"/api/v1/education/lessons/{lesson}").status_code == 200
            for lesson in story["lesson_ids"]
        )
        rehearsal = guide.step("05-rehearse-notebook-proposal").rehearsal
        assert rehearsal is not None
        response = client.post(
            "/api/v1/plans",
            json={
                "operation": rehearsal.operation,
                "target": {
                    "workspace_alias": "demo-dev",
                    "item_type": rehearsal.item_type,
                    "item_name": rehearsal.item_name,
                    "destination": "LOCAL",
                },
                "reason": "DQ-01 notebook creation rehearsal; no correction runs",
                "requested_by": "engineer-a",
            },
        )
        assert response.status_code == 200
        plan = response.json()
        assert (
            client.post(
                "/api/v1/approvals",
                json={
                    "change_id": plan["change_id"],
                    "approver": "engineer-a",
                    "decision": "APPROVED",
                },
            ).status_code
            == 409
        )
        approval = client.post(
            "/api/v1/approvals",
            json={"change_id": plan["change_id"], "approver": "approver-b", "decision": "APPROVED"},
        )
        assert approval.status_code == 200
        request = {
            "change_id": plan["change_id"],
            "approval_id": approval.json()["approval_id"],
            "executed_by": "scoped-writer",
        }
        execution = client.post("/api/v1/fabric/change", json=request)
        assert execution.status_code == 200
        payload = execution.json()
        assert payload["execution_label"] == "SIMULATED"
        assert payload["cloud_operation_performed"] is False
        assert payload["data"]["verification"]["passed"] is True
        assert client.post("/api/v1/fabric/change", json=request).status_code == 409
        records = client.get(f"/api/v1/audit/{plan['correlation_id']}").json()
        assert any(record["action"] == "change:execute" and record["success"] for record in records)
        assert any(not record["success"] for record in records)


def test_quality_baseline_detects_scratch_mismatch_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["mfg", "quality", "--check", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "LOCAL" and payload["baseline_passed"] is True
    assert len(payload["data_quality"]) == 9
    root = tmp_path / "synthetic"
    shutil.copytree(REPO_ROOT / "data/synthetic/raw/mfg-sales-v1", root / "raw/mfg-sales-v1")
    (root / "expected").mkdir()
    baseline_path = REPO_ROOT / "data/synthetic/expected/mfg-sales-v1.json"
    original = baseline_path.read_bytes()
    data = json.loads(original)
    data["data_quality"]["duplicate_order_lines"] += 1
    (root / "expected/mfg-sales-v1.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("FFIA_DATA_ROOT", str(root))
    assert main(["mfg", "quality", "--check", "--json"]) == 1
    failed = json.loads(capsys.readouterr().out)
    assert failed["baseline_passed"] is False
    assert failed["failures"] == ["duplicate_order_lines: expected 13, observed 12"]
    assert main(["mfg", "quality", "--check"]) == 1
    assert "quality baseline:" in capsys.readouterr().err
    assert baseline_path.read_bytes() == original
    monkeypatch.setenv("FFIA_DATA_ROOT", str(REPO_ROOT / "data/synthetic"))
    assert main(["mfg", "quality", "--check"]) == 0
    assert "Independent quality baseline: PASSED" in capsys.readouterr().out


@pytest.mark.parametrize("defect", ["missing", "invalid", "profile"])
def test_quality_reports_invalid_baseline_explicitly(
    defect: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    shutil.copytree(REPO_ROOT / "data/synthetic/raw/mfg-sales-v1", tmp_path / "raw/mfg-sales-v1")
    (tmp_path / "expected").mkdir()
    if defect != "missing":
        data = json.loads((REPO_ROOT / "data/synthetic/expected/mfg-sales-v1.json").read_text())
        data["profile"] = "wrong-profile"
        (tmp_path / "expected/mfg-sales-v1.json").write_text(
            "invalid-json" if defect == "invalid" else json.dumps(data),
            encoding="utf-8",
        )
    monkeypatch.setenv("FFIA_DATA_ROOT", str(tmp_path))
    result = main(["mfg", "quality", "--check", "--json"])
    output = capsys.readouterr()
    if defect == "profile":
        assert result == 1 and json.loads(output.out)["baseline_passed"] is False
    else:
        assert result == 2 and "unavailable or invalid" in output.err and not output.out


@pytest.fixture
def authoring_tree(tmp_path: Path) -> Path:
    """Copy only authoring inputs and public assets; no private bindings or runtime data."""
    for folder in ("guides", "education", "demos", "config", ".claude/skills"):
        shutil.copytree(
            REPO_ROOT / folder,
            tmp_path / folder,
            ignore=shutil.ignore_patterns("*.local.yaml", "*.local.json", "__pycache__"),
        )
    for folder in (
        "data/synthetic/expected",
        "docs/architecture/diagrams",
        "frontend/public/talktracks",
    ):
        shutil.copytree(REPO_ROOT / folder, tmp_path / folder)
    return tmp_path


def test_template_adds_fourth_guide_without_core_changes(
    authoring_tree: Path,
    make_container: Callable[..., Container],
    capsys: pytest.CaptureFixture[str],
) -> None:
    new_id = "demo-04-template-proof"
    folder = authoring_tree / "guides" / new_id
    shutil.copytree(authoring_tree / "guides/_template", folder)
    manifest = yaml.safe_load((folder / "guide.yaml").read_text(encoding="utf-8"))
    manifest["id"] = new_id
    manifest["title"] = "Synthetic template proof"
    (folder / "guide.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    workshop_path = authoring_tree / "education/workshop.yaml"
    workshop = yaml.safe_load(workshop_path.read_text(encoding="utf-8"))
    story = dict(workshop["use_cases"][-1])
    story["guide_id"] = new_id
    workshop["use_cases"].append(story)
    workshop_path.write_text(yaml.safe_dump(workshop), encoding="utf-8")
    args = [
        "education",
        "check",
        "--repo-root",
        str(authoring_tree),
        "--guides-root",
        str(authoring_tree / "guides"),
        "--education-root",
        str(authoring_tree / "education"),
        "--config-root",
        str(authoring_tree / "config"),
        "--sources",
        str(REPO_ROOT / "docs/research/sources.yaml"),
        "--min-coverage",
        "1.0",
    ]
    assert main(args) == 0, capsys.readouterr().err
    container = make_container(
        guides_root=authoring_tree / "guides",
        education_root=authoring_tree / "education",
    )
    with TestClient(create_app(container)) as client:
        assert client.get(f"/api/v1/guides/{new_id}").status_code == 200
        assert new_id in {guide["id"] for guide in client.get("/api/v1/guides").json()}
    (folder / "AGENTS.md").unlink()
    assert main(args) == 1
    assert "missing AGENTS.md" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("defect", "message"),
    [
        ("instructions", "missing CLAUDE.md"),
        ("baseline", "baseline profile differs"),
        ("invalid-baseline", "invalid baseline"),
        ("unsafe-baseline", "missing or unsafe baseline"),
        ("png", "missing draw.io PNG"),
        ("drawio", "missing draw.io DRAWIO"),
        ("view", "missing architecture view"),
        ("presenter", "missing presenter handout"),
        ("presenter-source", "missing structured presenter source"),
        ("skill", "unknown skill"),
        ("tool", "not allow-listed"),
        ("server", "unknown or unconfigured server"),
        ("fallback", "unknown fallback tool"),
        ("rehearsal", "not in write policy"),
    ],
)
def test_authoring_rejects_broken_assets_and_references(
    defect: str,
    message: str,
    authoring_tree: Path,
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    path = authoring_tree / "guides" / GUIDE / "guide.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    removals = {
        "instructions": f"guides/{GUIDE}/CLAUDE.md",
        "png": "docs/architecture/diagrams/mfg-01.png",
        "drawio": "docs/architecture/diagrams/mfg-01.drawio",
        "presenter": "frontend/public/talktracks/foundry-fabric-agents-workshop.html",
        "presenter-source": "demos/foundry-fabric-agents-workshop/talk-track.yaml",
    }
    if defect in removals:
        (authoring_tree / removals[defect]).unlink()
    elif defect in {"baseline", "invalid-baseline"}:
        baseline = authoring_tree / manifest["expected_baseline"]
        baseline.write_text(
            '{"profile": "wrong-profile"}' if defect == "baseline" else "not-json",
            encoding="utf-8",
        )
    elif defect == "unsafe-baseline":
        manifest["expected_baseline"] = "../outside.json"
    elif defect == "view":
        manifest["diagram"] = None
        for step in manifest["steps"]:
            step["diagram_focus"] = []
    elif defect == "skill":
        manifest["steps"][0]["skills"] = ["unknown-skill"]
    elif defect in {"tool", "server", "fallback"}:
        tool_path = manifest["steps"][3]["tool_path"]
        if defect == "tool":
            tool_path["tools"] = ["unknown-tool"]
        elif defect == "server":
            tool_path["server"] = "unknown-server"
        else:
            tool_path["fallback"]["tools"] = ["unknown-tool"]
    else:
        manifest["steps"][4]["rehearsal"]["operation"] = "unknown_operation"
    path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    errors = authoring_errors(
        container.education.library,
        load_guides(authoring_tree / "guides", container.catalog),
        repo_root=authoring_tree,
        guides_root=authoring_tree / "guides",
        config_root=authoring_tree / "config",
    )
    assert any(message in error for error in errors), errors
