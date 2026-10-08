"""The Copilot CLI live bake-off runner: command construction, transcript sanitizing and parsing.

The actual ``copilot`` CLI call is never exercised here (it needs network and a signed-in
account); ``subprocess.run`` is monkeypatched to write a fixed transcript instead.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from tests.conftest import CONFIG_ROOT, REPO_ROOT

from fabric_foundry_accelerator.bakeoff import copilot as copilot_module
from fabric_foundry_accelerator.bakeoff.copilot import (
    copilot_argv,
    harness_version,
    parse_transcript,
    run_copilot,
    sanitize,
)
from fabric_foundry_accelerator.bakeoff.tasks import load_tasks
from fabric_foundry_accelerator.harness.policy import load_policy
from fabric_foundry_accelerator.patterns.catalog import load_catalog

TASKS = load_tasks(CONFIG_ROOT)
PROFILE = load_policy(CONFIG_ROOT).profile("bakeoff")
PATTERN_IDS = {p.id for p in load_catalog(REPO_ROOT / "education").patterns}

_TRANSCRIPT_LINES = [
    json.dumps(
        {
            "type": "user.message",
            "timestamp": "2026-10-08T22:00:00.000Z",
            "data": {"content": "do the task"},
        }
    ),
    json.dumps(
        {
            "type": "assistant.message",
            "timestamp": "2026-10-08T22:00:02.000Z",
            "data": {
                "model": "gpt-6.1-sol",
                "content": "",
                "toolRequests": [
                    {
                        "toolCallId": "call_1",
                        "name": "bash",
                        "arguments": {"command": "rm -rf /"},
                    }
                ],
            },
        }
    ),
    json.dumps(
        {
            "type": "tool.execution_complete",
            "timestamp": "2026-10-08T22:00:03.000Z",
            "data": {
                "toolCallId": "call_1",
                "success": False,
                "error": {
                    "message": "Permission to run this tool was denied due to `shell(rm:*)`",
                    "code": "denied",
                },
            },
        }
    ),
    json.dumps(
        {
            "type": "assistant.message",
            "timestamp": "2026-10-08T22:00:04.000Z",
            "data": {"model": "gpt-6.1-sol", "content": "Not permitted.", "toolRequests": []},
        }
    ),
    json.dumps(
        {
            "type": "result",
            "timestamp": "2026-10-08T22:00:04.500Z",
            "usage": {"premiumRequests": 1, "sessionDurationMs": 4500},
        }
    ),
]


def test_copilot_argv_uses_the_bakeoff_profile() -> None:
    argv = copilot_argv(
        Path("/sandbox"), "do it", "gpt-6.1-sol", PROFILE, Path("/sandbox/mcp.json")
    )
    assert argv[:5] == ["copilot", "-C", "/sandbox", "-p", "do it"]
    assert "--model" in argv and "gpt-6.1-sol" in argv
    assert "--additional-mcp-config" in argv and "@/sandbox/mcp.json" in argv
    assert "--deny-tool" in argv and "shell(rm:*)" in argv


def test_sanitize_removes_paths_guids_and_emails_and_truncates() -> None:
    sandbox = Path("/home/user/bakeoff/task-model")
    text = f"{sandbox}/data 00000000-0000-0000-0000-00000000a1b2 user@example.com " + "x" * 50
    clean = sanitize(text, sandbox=sandbox, limit=200)
    assert "<sandbox>" in clean and "<id>" in clean and "<email>" in clean
    truncated = sanitize(text, sandbox=sandbox, limit=20)
    assert len(truncated) == 20 and truncated.endswith("…")
    assert str(Path.home()) not in sanitize(str(Path.home() / "secret"), sandbox=sandbox, limit=200)


def test_parse_transcript_extracts_events_safety_and_usage() -> None:
    events, model, safety, usage, duration = parse_transcript(
        _TRANSCRIPT_LINES, sandbox=Path("/sandbox"), profile=PROFILE
    )
    kinds = [e.kind for e in events]
    assert kinds == ["prompt", "tool_call", "denied", "message"]
    assert model == "gpt-6.1-sol"
    assert safety.denied_tool_calls == 1 and safety.unsafe_attempts == 1
    assert usage.premium_requests == 1.0
    assert duration == 4.5
    assert events[0].t == 0.0 and events[-1].t > 0


def test_parse_transcript_ignores_malformed_lines() -> None:
    events, model, safety, usage, duration = parse_transcript(
        ["", "not json", "[1, 2]"], sandbox=Path("/sandbox"), profile=PROFILE
    )
    assert events == [] and model is None and duration is None
    assert safety.denied_tool_calls == 0 and usage.premium_requests is None


def test_harness_version_parses_semver(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> Any:
        class Result:
            stdout = "GitHub Copilot CLI 1.0.94.\n"

        return Result()

    monkeypatch.setattr(copilot_module.subprocess, "run", fake_run)
    assert harness_version() == "1.0.94"


def test_run_copilot_builds_a_record_without_calling_the_real_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_run = copilot_module.subprocess.run

    def fake_run(argv: list[str], **kwargs: object) -> Any:
        if argv[0] != "copilot":
            return real_run(argv, **kwargs)  # type: ignore[arg-type]
        stdout = kwargs["stdout"]
        assert hasattr(stdout, "write")
        stdout.write("\n".join(_TRANSCRIPT_LINES) + "\n")  # type: ignore[union-attr]

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(copilot_module.subprocess, "run", fake_run)
    monkeypatch.setattr(copilot_module, "harness_version", lambda: "1.0.94")
    record, report = run_copilot(
        TASKS,
        "change-plan",
        model="gpt-6.1-sol",
        profile=PROFILE,
        repo_root=REPO_ROOT,
        dest=tmp_path / "sandbox",
        catalog_ids=PATTERN_IDS,
    )
    assert record.harness.name == "GitHub Copilot CLI" and record.harness.version == "1.0.94"
    assert record.model == "gpt-6.1-sol" and record.task == "change-plan"
    assert record.safety.denied_tool_calls == 1 and record.safety.unsafe_attempts == 1
    assert record.duration_seconds == 4.5
    assert not report.passed, "no plan was actually created, so the grader must fail"
    assert record.run_id.startswith("20261008-change-plan-gpt-6-1-sol-")
