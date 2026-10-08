"""Recorded bake-off runs (replays) and the scorecard built from them.

A run record is a real, recorded harness run: the harness and model, the exact prompt hash, the
deterministic grade, safety counts taken from the transcript, usage where the harness shows it,
and a sanitized transcript. Replays live in ``demos/bakeoff/replays/*.json`` and are scanned by
``ffia privacy scan`` like every committed file. There are no synthetic or invented runs: with no
recordings the scorecard is UNAVAILABLE.
"""

import statistics
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.bakeoff.tasks import GradeReport, TaskSet
from fabric_foundry_accelerator.providers.errors import UnknownResourceError

REPLAYS_DIR = Path("bakeoff") / "replays"
EventKind = Literal[
    "prompt", "message", "tool_call", "tool_result", "approval_requested", "denied", "command"
]


class TranscriptEvent(BaseModel):
    """One sanitized step of a recorded run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    t: float = Field(ge=0, description="seconds since the run started")
    kind: EventKind
    name: str | None = None
    summary: str = Field(max_length=2000)


class HarnessInfo(BaseModel):
    """The agent harness that ran the task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    version: str


class Safety(BaseModel):
    """Counts taken from the transcript."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    approvals_requested: int = Field(ge=0)
    denied_tool_calls: int = Field(ge=0)
    unsafe_attempts: int = Field(ge=0)


class Usage(BaseModel):
    """What the harness reported; ``None`` when it did not show it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    premium_requests: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class RunRecord(BaseModel):
    """One recorded run of one task in one harness with one model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1]
    run_id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=96)
    recorded_on: date
    label: Literal["LIVE"]
    harness: HarnessInfo
    model: str
    task: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    repo_commit: str = Field(pattern=r"^[0-9a-f]{7,40}$")
    duration_seconds: float = Field(ge=0)
    grade: GradeReport
    safety: Safety
    usage: Usage = Usage()
    transcript: tuple[TranscriptEvent, ...] = Field(min_length=1)
    notes: str = ""


class RunSummary(BaseModel):
    """One row of the run list."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    recorded_on: date
    harness: str
    model: str
    task: str
    passed: bool
    checks_passed: int
    checks: int
    duration_seconds: float
    approvals_requested: int
    denied_tool_calls: int
    unsafe_attempts: int
    premium_requests: float | None
    current_prompt: bool


class ScorecardRow(BaseModel):
    """Aggregates for one harness and model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    harness: str
    model: str
    runs: int
    tasks_passed: int
    median_duration_seconds: float
    approvals_requested: int
    denied_tool_calls: int
    unsafe_attempts: int
    premium_requests: float | None


class Scorecard(BaseModel):
    """Every recorded run and the per-harness, per-model aggregates."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: Literal["LIVE", "UNAVAILABLE"]
    note: str
    task_ids: tuple[str, ...]
    rows: tuple[ScorecardRow, ...]
    runs: tuple[RunSummary, ...]


def load_runs(replays_dir: Path) -> list[RunRecord]:
    """Load and validate every replay, newest first."""
    if not replays_dir.is_dir():
        return []
    runs = [
        RunRecord.model_validate_json(path.read_text(encoding="utf-8"))
        for path in sorted(replays_dir.glob("*.json"))
    ]
    return sorted(runs, key=lambda r: (r.recorded_on, r.run_id), reverse=True)


def check_runs(tasks: TaskSet, runs: list[RunRecord]) -> list[str]:
    """Problems that make a replay unusable: unknown task, duplicate ID or grade mismatch."""
    problems: list[str] = []
    seen: set[str] = set()
    known = set(tasks.ids())
    for run in runs:
        if run.run_id in seen:
            problems.append(f"{run.run_id}: duplicate run_id")
        seen.add(run.run_id)
        if run.task not in known:
            problems.append(f"{run.run_id}: unknown task {run.task!r}")
        if run.grade.task != run.task:
            problems.append(f"{run.run_id}: grade is for {run.grade.task!r}")
        if run.grade.passed != all(c.passed for c in run.grade.checks):
            problems.append(f"{run.run_id}: grade.passed does not match its checks")
    return problems


def get_run(replays_dir: Path, run_id: str) -> RunRecord:
    """Return one replay.

    Raises:
        UnknownResourceError: no such run.
    """
    for run in load_runs(replays_dir):
        if run.run_id == run_id:
            return run
    raise UnknownResourceError(f"unknown bake-off run {run_id!r}")


def _summary(run: RunRecord, tasks: TaskSet) -> RunSummary:
    current = run.task in tasks.ids() and tasks.task(run.task).prompt_sha256 == run.prompt_sha256
    return RunSummary(
        run_id=run.run_id,
        recorded_on=run.recorded_on,
        harness=f"{run.harness.name} {run.harness.version}",
        model=run.model,
        task=run.task,
        passed=run.grade.passed,
        checks_passed=sum(c.passed for c in run.grade.checks),
        checks=len(run.grade.checks),
        duration_seconds=run.duration_seconds,
        approvals_requested=run.safety.approvals_requested,
        denied_tool_calls=run.safety.denied_tool_calls,
        unsafe_attempts=run.safety.unsafe_attempts,
        premium_requests=run.usage.premium_requests,
        current_prompt=current,
    )


def scorecard(tasks: TaskSet, runs: list[RunRecord]) -> Scorecard:
    """Aggregate recorded runs by harness and model; UNAVAILABLE when nothing was recorded."""
    summaries = [_summary(run, tasks) for run in runs]
    groups: dict[tuple[str, str], list[RunSummary]] = {}
    for summary in summaries:
        groups.setdefault((summary.harness, summary.model), []).append(summary)
    rows: list[ScorecardRow] = []
    for (harness, model), items in sorted(groups.items()):
        premium = [i.premium_requests for i in items if i.premium_requests is not None]
        rows.append(
            ScorecardRow(
                harness=harness,
                model=model,
                runs=len(items),
                tasks_passed=sum(i.passed for i in items),
                median_duration_seconds=round(
                    statistics.median(i.duration_seconds for i in items), 1
                ),
                approvals_requested=sum(i.approvals_requested for i in items),
                denied_tool_calls=sum(i.denied_tool_calls for i in items),
                unsafe_attempts=sum(i.unsafe_attempts for i in items),
                premium_requests=round(sum(premium), 2) if premium else None,
            )
        )
    if not runs:
        note = (
            "No recorded runs yet. Run a task with `ffia bakeoff prepare`, your harness and "
            "`ffia bakeoff grade`, then record it. Nothing here is simulated."
        )
    else:
        note = (
            "Dated observations of recorded runs on this repository's synthetic tasks; they "
            "depend on the model, prompt and task and are not product claims."
        )
    return Scorecard(
        label="LIVE" if runs else "UNAVAILABLE",
        note=note,
        task_ids=tuple(tasks.ids()),
        rows=tuple(rows),
        runs=tuple(summaries),
    )
