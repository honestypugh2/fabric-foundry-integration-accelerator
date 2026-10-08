"""Run a bake-off task live in GitHub Copilot CLI and record it as a sanitized replay.

``run_copilot`` prepares the sandbox, starts ``copilot -p`` there with the strict ``bakeoff``
permission profile (identical for every model), the sandbox's own ``ffia-local`` MCP server and
``PYTHONPATH`` pointing at the sandbox, so the agent's own checks run the sandbox code. It then
grades the sandbox and turns the JSONL transcript into a :class:`RunRecord`.

Recording is opt-in (``--record``). Transcripts are sanitized (sandbox and home paths, GUIDs,
e-mail addresses removed; long text truncated) and are still scanned by ``ffia privacy scan``.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from fabric_foundry_accelerator.bakeoff.runs import (
    EventKind,
    HarnessInfo,
    RunRecord,
    Safety,
    TranscriptEvent,
    Usage,
)
from fabric_foundry_accelerator.bakeoff.tasks import GradeReport, TaskSet, grade, prepare
from fabric_foundry_accelerator.harness.policy import (
    HarnessProfile,
    evaluate_command,
    render_copilot_cli,
)

HARNESS_NAME = "GitHub Copilot CLI"
TRANSCRIPT = Path(".bakeoff") / "transcript.jsonl"
_GUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_LIMITS = {"prompt": 1500, "message": 1500, "tool_call": 400, "tool_result": 400, "denied": 400}


def _mcp_config(sandbox: Path) -> dict[str, object]:
    # The sandbox's own ffia-local server, run with this environment's Python and dependencies.
    code = (
        "import os, sys; "
        f"os.chdir({str(sandbox)!r}); sys.path.insert(0, {str(sandbox / 'src')!r}); "
        "from fabric_foundry_accelerator.cli import main; sys.exit(main(['serve', 'mcp']))"
    )
    return {
        "mcpServers": {
            "ffia-local": {
                "type": "local",
                "command": sys.executable,
                "args": ["-c", code],
                "tools": ["*"],
            }
        }
    }


def copilot_argv(
    sandbox: Path, prompt: str, model: str, profile: HarnessProfile, mcp_file: Path
) -> list[str]:
    """The exact ``copilot`` command line for one run."""
    return [
        "copilot",
        "-C",
        str(sandbox),
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--no-auto-update",
        "--disable-builtin-mcps",
        "--additional-mcp-config",
        f"@{mcp_file}",
        *render_copilot_cli(profile),
    ]


def harness_version() -> str:
    """``copilot --version`` (for example ``1.0.94``)."""
    result = subprocess.run(
        ["copilot", "--version"],  # noqa: S607 - copilot on PATH
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    match = re.search(r"\d+\.\d+\.\d+", result.stdout)
    return match.group(0) if match else "unknown"


def sanitize(text: str, *, sandbox: Path, limit: int) -> str:
    """Remove local paths, GUIDs and e-mail addresses; truncate."""
    clean = text.replace(str(sandbox), "<sandbox>").replace(str(Path.home()), "~")
    clean = _EMAIL.sub("<email>", _GUID.sub("<id>", clean))
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def _timestamp(value: object) -> float:
    if not isinstance(value, str):
        return 0.0
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def _dict(value: object) -> dict[str, object]:
    return dict(cast("dict[str, object]", value)) if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return list(cast("list[object]", value)) if isinstance(value, list) else []


def _deny_prefixes(profile: HarnessProfile) -> tuple[str, ...]:
    return profile.shell.deny


def _unsafe(command: str, profile: HarnessProfile) -> bool:
    words = command.strip().split()
    attempted = any(words[: len(p.split())] == p.split() for p in _deny_prefixes(profile))
    return attempted or evaluate_command(command).denied


class _Parsed:
    def __init__(self) -> None:
        self.events: list[TranscriptEvent] = []
        self.model: str | None = None
        self.denied = 0
        self.unsafe = 0
        self.premium: float | None = None
        self.duration: float | None = None


def _handle(
    kind: str,
    data: dict[str, object],
    t: float,
    parsed: _Parsed,
    sandbox: Path,
    profile: HarnessProfile,
) -> None:
    def add(event_kind: EventKind, summary: str, name: str | None = None) -> None:
        parsed.events.append(
            TranscriptEvent(
                t=round(t, 1),
                kind=event_kind,
                name=name,
                summary=sanitize(summary, sandbox=sandbox, limit=_LIMITS.get(event_kind, 400)),
            )
        )

    if kind == "user.message":
        add("prompt", str(data.get("content", "")))
    elif kind == "assistant.message":
        parsed.model = str(data.get("model") or parsed.model or "")
        content = str(data.get("content") or "")
        if content:
            add("message", content)
        for request in map(_dict, _list(data.get("toolRequests"))):
            arguments = _dict(request.get("arguments"))
            name = str(request.get("name", ""))
            command = arguments.get("command")
            if isinstance(command, str):
                parsed.unsafe += _unsafe(command, profile)
                add("tool_call", command, name)
            else:
                add("tool_call", json.dumps(arguments)[:400], name)
    elif kind == "tool.execution_complete":
        error = _dict(data.get("error"))
        if error.get("code") == "denied":
            parsed.denied += 1
            add("denied", str(error.get("message", "denied")))
        else:
            result = _dict(data.get("result"))
            status = "ok" if data.get("success") else "failed"
            add("tool_result", f"{status}: {result.get('content', error.get('message', ''))}")


def parse_transcript(
    lines: list[str], *, sandbox: Path, profile: HarnessProfile
) -> tuple[list[TranscriptEvent], str | None, Safety, Usage, float | None]:
    """Turn Copilot CLI ``--output-format json`` lines into sanitized events and counts."""
    parsed = _Parsed()
    start: float | None = None
    for line in lines:
        if not line.strip():
            continue
        try:
            record = _dict(json.loads(line))
        except json.JSONDecodeError:
            continue
        kind = str(record.get("type", ""))
        if kind == "result":
            usage = _dict(record.get("usage"))
            premium = usage.get("premiumRequests")
            duration = usage.get("sessionDurationMs")
            parsed.premium = float(premium) if isinstance(premium, int | float) else None
            parsed.duration = float(duration) / 1000 if isinstance(duration, int | float) else None
            continue
        stamp = _timestamp(record.get("timestamp"))
        start = stamp if start is None and stamp else start
        _handle(
            kind,
            _dict(record.get("data")),
            max(0.0, stamp - (start or stamp)),
            parsed,
            sandbox,
            profile,
        )
    safety = Safety(
        approvals_requested=0, denied_tool_calls=parsed.denied, unsafe_attempts=parsed.unsafe
    )
    return (
        parsed.events,
        parsed.model,
        safety,
        Usage(premium_requests=parsed.premium),
        parsed.duration,
    )


def run_copilot(
    tasks: TaskSet,
    task_id: str,
    *,
    model: str,
    profile: HarnessProfile,
    repo_root: Path,
    dest: Path,
    catalog_ids: set[str],
    timeout: float = 1200,
) -> tuple[RunRecord, GradeReport]:
    """Prepare, run Copilot CLI non-interactively, grade, and build the run record."""
    task = tasks.task(task_id)
    sandbox = prepare(tasks, task_id, repo_root=repo_root, dest=dest).resolve()
    mcp_file = sandbox / ".bakeoff" / "mcp.json"
    mcp_file.write_text(json.dumps(_mcp_config(sandbox)), encoding="utf-8")
    venv_bin = str(Path(sys.executable).parent)
    env = {
        **os.environ,
        "PATH": f"{venv_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "PYTHONPATH": str(sandbox / "src"),
        "COPILOT_AUTO_UPDATE": "false",
    }
    env.pop("FFIA_AUDIT_PATH", None)
    started = time.monotonic()
    with (sandbox / TRANSCRIPT).open("w", encoding="utf-8") as out:
        subprocess.run(  # noqa: S603 - fixed argv, no shell
            copilot_argv(sandbox, task.prompt, model, profile, mcp_file),
            stdout=out,
            stderr=subprocess.DEVNULL,
            env=env,
            cwd=sandbox,
            check=False,
            timeout=timeout,
        )
    elapsed = time.monotonic() - started
    report = grade(tasks, task_id, sandbox, catalog_ids=catalog_ids)
    lines = (sandbox / TRANSCRIPT).read_text(encoding="utf-8").splitlines()
    events, seen_model, safety, usage, duration = parse_transcript(
        lines, sandbox=sandbox, profile=profile
    )
    if not events:
        events = [
            TranscriptEvent(
                t=0, kind="prompt", summary=sanitize(task.prompt, sandbox=sandbox, limit=1500)
            )
        ]
    today = datetime.now(UTC).date()
    slug = re.sub(r"[^a-z0-9]+", "-", (seen_model or model).lower()).strip("-")
    record = RunRecord(
        schema_version=1,
        run_id=f"{today:%Y%m%d}-{task.id}-{slug}-{int(time.time()) % 100000}",
        recorded_on=today,
        label="LIVE",
        harness=HarnessInfo(name=HARNESS_NAME, version=harness_version()),
        model=seen_model or model,
        task=task.id,
        prompt_sha256=task.prompt_sha256,
        repo_commit=report.commit,
        duration_seconds=round(duration if duration is not None else elapsed, 1),
        grade=report,
        safety=safety,
        usage=usage,
        transcript=tuple(events),
        notes="Non-interactive run (copilot -p); permissions decided by the bakeoff profile, so no approval prompts.",
    )
    return record, report
