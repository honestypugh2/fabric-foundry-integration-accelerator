"""Foundry IQ knowledge analog: preview-flagged, SIMULATED offline, cited, never presented as Foundry."""

from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.conftest import CONFIG_ROOT, DATA_ROOT, REPO_ROOT

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.config.overlay import load_overlay
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.knowledge.local import (
    PREVIEW_FLAG,
    KnowledgeQuery,
    load_sections,
    retrieve,
    search_knowledge,
)
from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.providers.errors import ProviderUnavailableError
from fabric_foundry_accelerator.services.container import Container

KB = DATA_ROOT / "knowledge" / "mfg-sales-v1"


def _top(question: str) -> tuple[str, str]:
    passages = retrieve(load_sections(KB), question, 1)
    return passages[0].citation.document, passages[0].citation.section


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Can agents fix data quality issues in the source?",
            ("data-quality-runbook", "Correction"),
        ),
        ("Can we scrape a competitor's website?", ("external-data-policy", "Allowed sources")),
        ("Are briefs sent automatically?", ("monthly-brief-policy", "Approval before sending")),
        (
            "What counts as booked revenue?",
            ("revenue-recognition", "What counts as booked revenue"),
        ),
    ],
)
def test_retrieval_cites_the_right_section(question: str, expected: tuple[str, str]) -> None:
    assert _top(question) == expected


def test_documents_are_synthetic_and_sectioned() -> None:
    sections = load_sections(KB)
    assert len(sections) >= 10
    for path in KB.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "synthetic: true" in text and "SYNTHETIC DOCUMENT" in text
    assert all("SYNTHETIC DOCUMENT" not in text for _, text in sections)


def test_no_match_and_stopword_only_questions() -> None:
    assert retrieve(load_sections(KB), "banana", 3) == ()
    assert retrieve(load_sections(KB), "what is the", 3) == ()
    with pytest.raises(ProviderUnavailableError):
        load_sections(KB / "missing")


def test_flag_off_is_unavailable_and_flag_on_is_simulated() -> None:
    query = KnowledgeQuery(question="What counts as booked revenue?", top=2)
    off = search_knowledge(query, data_root=DATA_ROOT, enabled=False, mode=OperatingMode.OFFLINE)
    assert off.execution_label is ExecutionLabel.UNAVAILABLE
    assert off.data.passages == () and PREVIEW_FLAG in off.data.note
    on = search_knowledge(
        query,
        data_root=DATA_ROOT,
        enabled=True,
        mode=OperatingMode.OFFLINE,
        correlation_id="c" * 32,
    )
    assert on.execution_label is ExecutionLabel.SIMULATED
    assert on.cloud_operation_performed is False and on.correlation_id == "c" * 32
    assert "No Foundry, Azure AI Search or OneLake call was made" in (on.simulation_notice or "")
    assert len(on.data.passages) == 2
    empty = search_knowledge(
        KnowledgeQuery(question="banana bread"),
        data_root=DATA_ROOT,
        enabled=True,
        mode=OperatingMode.OFFLINE,
    )
    assert "does not cover" in empty.data.note
    with pytest.raises(ValidationError):
        KnowledgeQuery(question="ok", top=9)


def test_preview_setting_enables_flag_and_rejects_unknown_names(
    make_container: Callable[..., Container], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FFIA_PREVIEW_FEATURES", f" {PREVIEW_FLAG} , ")
    assert Settings().preview_features == (PREVIEW_FLAG,)
    container = make_container(preview_features=(PREVIEW_FLAG,))
    assert container.overlay.enabled_previews() == [PREVIEW_FLAG]
    overlay = load_overlay(CONFIG_ROOT, "example-healthcare")
    assert overlay.preview_feature_flags[PREVIEW_FLAG] is False
    with pytest.raises(ValueError, match="unknown preview feature"):
        overlay.with_previews(("nope",))


def test_api_and_cli(
    make_container: Callable[..., Container],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    path = "/api/v1/knowledge/search"
    with TestClient(create_app(make_container())) as client:
        body = client.post(path, json={"question": "Are briefs sent automatically?"}).json()
        assert body["execution_label"] == "UNAVAILABLE"
        assert client.post(path, json={"question": "x"}).status_code == 422
    with TestClient(create_app(make_container(preview_features=(PREVIEW_FLAG,)))) as client:
        body = client.post(path, json={"question": "Are briefs sent automatically?"}).json()
        assert body["execution_label"] == "SIMULATED"
        assert body["data"]["passages"][0]["citation"]["section"] == "Approval before sending"
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("FFIA_AUDIT_PATH", "")
    monkeypatch.setenv("FFIA_RUNTIME_ROOT", str(tmp_path))
    assert main(["knowledge", "search", "booked", "revenue"]) == 0
    assert "[UNAVAILABLE]" in capsys.readouterr().out
    monkeypatch.setenv("FFIA_PREVIEW_FEATURES", PREVIEW_FLAG)
    assert main(["knowledge", "search", "booked", "revenue", "--top", "1"]) == 0
    out = capsys.readouterr().out
    assert "[SIMULATED]" in out and "Booked revenue definition > What counts" in out
    assert main(["knowledge", "search", "booked", "revenue", "--json"]) == 0
    assert '"execution_label": "SIMULATED"' in capsys.readouterr().out
