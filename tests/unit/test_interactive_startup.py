from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.config.bindings import BindingsError
from fabric_foundry_accelerator.config.settings import ApiSettings, Settings
from fabric_foundry_accelerator.services.container import build_container


def test_interactive_defaults_and_offline_library_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ENVIRONMENT", "FABRIC_LIVE", "FOUNDRY_LIVE", "ALLOW_LIVE_MUTATION"):
        monkeypatch.delenv(f"FFIA_{name}", raising=False)
    interactive = ApiSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert interactive.environment == "hybrid"
    assert interactive.fabric_live and interactive.foundry_live
    assert not interactive.allow_live_mutation
    offline = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert offline.environment == "offline"
    assert not offline.fabric_live and not offline.foundry_live


def test_interactive_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FFIA_ENVIRONMENT", "live")
    monkeypatch.setenv("FFIA_FABRIC_LIVE", "0")
    settings = ApiSettings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert settings.environment == "live" and not settings.fabric_live


def test_root_environment_file_is_used_with_explicit_override_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("ENVIRONMENT", "FABRIC_LIVE", "FOUNDRY_LIVE"):
        monkeypatch.delenv(f"FFIA_{name}", raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", (".env", ".env.local"))
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "FFIA_ENVIRONMENT=hybrid\nFFIA_FABRIC_LIVE=1\nFFIA_FOUNDRY_LIVE=1\n", encoding="utf-8"
    )
    settings = Settings()
    assert settings.environment == "hybrid" and settings.fabric_live and settings.foundry_live
    (tmp_path / ".env.local").write_text("FFIA_FOUNDRY_LIVE=0\n", encoding="utf-8")
    assert not Settings().foundry_live
    monkeypatch.setenv("FFIA_FOUNDRY_LIVE", "1")
    assert Settings().foundry_live


def test_unbound_hybrid_serves_both_guides_and_explicit_read_fallback(
    make_settings: Callable[..., Settings],
) -> None:
    container = build_container(
        make_settings(environment="hybrid", fabric_live=True, foundry_live=True)
    )
    assert container.fabric.live is None and container.agents.live is None
    with TestClient(create_app(container)) as client:
        status = client.get("/api/v1/runtime/status").json()
        assert status["operating_mode"] == "HYBRID"
        assert "LIVE writes disabled" in status["write_mode"]
        guides = client.get("/api/v1/guides").json()
        assert len(guides) == 2
        for guide in guides:
            assert client.get(f"/api/v1/guides/{guide['id']}").status_code == 200
        result = client.post("/api/v1/fabric/read", json={"operation": "list_workspaces"}).json()
        assert result["execution_label"] == "LOCAL"
        assert result["fallback_used"] is True
        assert "not configured" in result["fallback_reason"]


def test_missing_bindings_never_enable_live_writes(
    make_settings: Callable[..., Settings],
) -> None:
    with pytest.raises(BindingsError):
        build_container(
            make_settings(
                environment="hybrid",
                fabric_live=True,
                foundry_live=True,
                allow_live_mutation=True,
            )
        )
