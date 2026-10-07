import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest
import uvicorn
from fastmcp import FastMCP
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.services import commands
from fabric_foundry_accelerator.services import demo as demo_module
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.demo import azure_cli_sign_in, demo_check, run_offline_demo
from fabric_foundry_accelerator.services.evaluation import compare


async def test_demo_check_reports_every_component(make_container: Callable[..., Container]) -> None:
    report = await demo_check(make_container(), azure_probe=False)
    components = [line.component for line in report.lines]
    assert components == [
        "Fabric Authentication",
        "Fabric API",
        "Fabric MCP",
        "Foundry",
        "Local Dataset",
        "Offline Provider",
        "API",
        "Frontend",
        "MCP Server",
    ]
    statuses = {line.component: line.status for line in report.lines}
    assert statuses["Local Dataset"] == "PASS" and statuses["Offline Provider"] == "READY"
    assert statuses["MCP Server"] == "READY" and statuses["Fabric API"] == "NOT AVAILABLE"
    assert report.recommended_mode.value == "OFFLINE"


async def test_offline_demo_passes_with_honest_labels(
    make_container: Callable[..., Container], tmp_path: Path
) -> None:
    report = await run_offline_demo(make_container(), work_dir=tmp_path)
    assert report.passed
    assert report.live_operations == 0 and report.cloud_operations == 0
    acts = {step.act: step for step in report.steps}
    assert sorted(acts) == list(range(1, 11))
    assert acts[6].label == "UNAVAILABLE" and not acts[6].required
    assert acts[5].label == "SIMULATED" and acts[8].label == "SIMULATED"
    assert all(step.passed for step in report.steps if step.required)


@pytest.mark.parametrize(
    ("which", "returncode", "expected"),
    [(None, 0, "NOT INSTALLED"), ("/usr/bin/az", 0, "PRESENT"), ("/usr/bin/az", 1, "ABSENT")],
)
def test_azure_cli_probe(
    monkeypatch: pytest.MonkeyPatch, which: str | None, returncode: int, expected: str
) -> None:
    def fake_which(_: str) -> str | None:
        return which

    def fake_run(*_: object, **__: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args=["az"], returncode=returncode)

    monkeypatch.setattr(demo_module.shutil, "which", fake_which)
    monkeypatch.setattr(demo_module.subprocess, "run", fake_run)
    assert azure_cli_sign_in() == expected


def test_azure_cli_probe_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*_: object, **__: object) -> None:
        raise subprocess.TimeoutExpired(cmd="az", timeout=30)

    def fake_which(_: str) -> str:
        return "/usr/bin/az"

    monkeypatch.setattr(demo_module.shutil, "which", fake_which)
    monkeypatch.setattr(demo_module.subprocess, "run", timeout)
    assert azure_cli_sign_in() == "ABSENT"


def test_compare_handles_missing_values() -> None:
    assert compare("m", None, None, 0.0).passed
    assert not compare("m", 1, None, 0.0).passed
    assert compare("m", 1.0, 1.0000001, 0.000001).passed


@pytest.fixture
def cli_settings(monkeypatch: pytest.MonkeyPatch, make_container: Callable[..., Container]) -> None:
    """Make CLI commands build containers from the test fixtures instead of the working directory."""

    def fake_build(settings: object = None) -> Container:
        return make_container()

    monkeypatch.setattr(commands, "build_container", fake_build)


@pytest.mark.usefixtures("cli_settings")
def test_cli_demo_check_text_and_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo", "check", "--no-azure-cli"]) == 0
    assert "Recommended Mode: OFFLINE" in capsys.readouterr().out
    assert main(["demo", "check", "--no-azure-cli", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["recommended_mode"] == "OFFLINE"


@pytest.mark.usefixtures("cli_settings")
def test_cli_demo_offline_text_and_json(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main(["demo", "offline", "--work-dir", str(tmp_path / "a")]) == 0
    out = capsys.readouterr().out
    assert "Release gate: PASSED" in out and "[SKIP] ACT  6 [UNAVAILABLE]" in out
    assert main(["demo", "offline", "--json", "--work-dir", str(tmp_path / "b")]) == 0
    assert json.loads(capsys.readouterr().out)["passed"] is True


def test_cli_schemas_export_and_check(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_ts = str(REPO_ROOT / "frontend" / "src" / "api" / "generated.ts")
    assert (
        main(["schemas", "check", "--dir", str(REPO_ROOT / "schemas"), "--typescript", repo_ts])
        == 0
    )
    target = [
        "--dir",
        str(tmp_path / "schemas"),
        "--typescript",
        str(tmp_path / "ts" / "generated.ts"),
    ]
    assert main(["schemas", "check", *target]) == 1
    assert main(["schemas", "export", *target]) == 0
    assert main(["schemas", "check", *target]) == 0
    assert (tmp_path / "schemas" / "openapi.json").is_file()
    assert "export interface LessonView" in (tmp_path / "ts" / "generated.ts").read_text(
        encoding="utf-8"
    )
    assert "up to date" in capsys.readouterr().out


def test_cli_serve_commands(
    monkeypatch: pytest.MonkeyPatch, make_container: Callable[..., Container]
) -> None:
    calls: list[tuple[object, ...]] = []

    def fake_build(settings: object = None) -> Container:
        return make_container()

    def fake_uvicorn(app: object, **kwargs: object) -> None:
        calls.append(("api", kwargs["host"], kwargs["port"]))

    def fake_mcp(self: FastMCP, **kwargs: object) -> None:
        calls.append(("mcp", kwargs["transport"]))

    monkeypatch.setattr(commands, "build_container", fake_build)
    monkeypatch.setattr(uvicorn, "run", fake_uvicorn)
    monkeypatch.setattr(FastMCP, "run", fake_mcp)
    assert main(["serve", "api", "--port", "8123"]) == 0
    assert main(["serve", "mcp"]) == 0
    assert calls == [("api", "127.0.0.1", 8123), ("mcp", "stdio")]
