"""Talk tracks render with valid references; the manufacturing data detects every injected issue."""

import json
from pathlib import Path

import pytest
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.education.diagrams import load_view
from fabric_foundry_accelerator.education.svg import render_svg, workflow
from fabric_foundry_accelerator.education.talktracks import TalkTrack, load_talk_tracks
from fabric_foundry_accelerator.synthetic.manufacturing import (
    INJECTED,
    MFG_PROFILES,
    MfgBaseline,
    build,
)

DEMOS = REPO_ROOT / "demos"
RAW = REPO_ROOT / "data" / "synthetic" / "raw" / "mfg-sales-v1"


def test_both_talk_tracks_load_and_answer_the_customer_questions() -> None:
    tracks = load_talk_tracks(DEMOS)
    assert set(tracks) == {"fabric-copilot-level-up", "foundry-fabric-agents-workshop"}
    guide2 = tracks["foundry-fabric-agents-workshop"]
    featured = [qa.q.lower() for qa in guide2.qa if qa.featured]
    for needle in (
        "foundry + fabric",
        "competitor",
        "monthly insights",
        "data-quality",
        "licensing",
    ):
        assert any(needle in q for q in featured), needle
    entries = {s.entry for p in guide2.parts for s in p.steps}
    assert {"foundry", "vscode", "fabric", "app", "terminal"} <= entries
    assert all(s.fallback for p in guide2.parts for s in p.steps if s.label == "LIVE")


def test_talk_track_validation_rejects_bad_timing_and_entries() -> None:
    data = json.loads(load_talk_tracks(DEMOS)["fabric-copilot-level-up"].model_dump_json())
    data["duration_minutes"] = 45
    with pytest.raises(ValueError, match="add up to 60"):
        TalkTrack.model_validate(data)
    data["duration_minutes"] = 60
    data["parts"][0]["steps"][0]["entry"] = "nowhere"
    with pytest.raises(ValueError, match="unknown entry"):
        TalkTrack.model_validate(data)


def test_svg_and_html_are_self_contained() -> None:
    view = load_view(REPO_ROOT / "education" / "architecture" / "views" / "mfg-01.yaml")
    svg = render_svg(view)
    assert svg.startswith("<svg") and "<script" not in svg and "Fabric data agent" in svg
    assert len(workflow(view)) == len(view.traces[0].steps)
    page = (DEMOS / "foundry-fabric-agents-workshop" / "index.html").read_text(encoding="utf-8")
    assert (
        "<script" not in page and "<svg" in page and "Can we see a demo of Foundry + Fabric" in page
    )
    assert (
        REPO_ROOT / "frontend" / "public" / "talktracks" / "foundry-fabric-agents-workshop.html"
    ).read_text(encoding="utf-8") == page


def test_talktracks_cli_is_current(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["talktracks", "check"]) == 0
    assert "4 talk-track files" in capsys.readouterr().out


def test_manufacturing_build_matches_injected_issues_and_baseline() -> None:
    result = build(RAW, MFG_PROFILES["mfg-sales-v1"])
    assert result.data_quality == INJECTED
    expected = MfgBaseline.model_validate_json(
        (REPO_ROOT / "data" / "synthetic" / "expected" / "mfg-sales-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert expected.data_quality == result.data_quality
    assert expected.team_briefs == result.team_briefs
    assert expected.clean_order_lines == result.clean_order_lines


def test_mfg_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    assert main(["mfg", "quality"]) == 0
    assert "duplicate_order_lines" in capsys.readouterr().out
    assert main(["mfg", "brief", "--team", "T-ENC", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["label"] == "LOCAL" and "T-ENC" in payload["briefs"]
    assert main(["mfg", "brief", "--team", "NOPE"]) == 2
    assert main(["mfg", "quality", "--json"]) == 0
    assert main(["mfg", "brief"]) == 0
