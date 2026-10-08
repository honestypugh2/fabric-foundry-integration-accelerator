"""``ffia bakeoff tasks|prepare|grade|check|scorecard``: same tasks, every harness, honest scores."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.bakeoff.copilot import HARNESS_NAME, run_copilot
from fabric_foundry_accelerator.bakeoff.runs import (
    REPLAYS_DIR,
    check_runs,
    load_runs,
    scorecard,
)
from fabric_foundry_accelerator.bakeoff.tasks import grade, load_tasks, prepare
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.harness.policy import load_policy
from fabric_foundry_accelerator.patterns.catalog import load_catalog


def _cmd_tasks(args: argparse.Namespace) -> int:
    tasks = load_tasks(Settings().config_root)
    if args.json:
        sys.stdout.write(tasks.model_dump_json(indent=2) + "\n")
        return 0
    for task in tasks.tasks:
        sys.stdout.write(
            f"{task.id}: {task.title}\n  {task.summary}\n  checks: {', '.join(task.checks)}\n"
        )
    return 0


def _cmd_prepare(args: argparse.Namespace) -> int:
    settings = Settings()
    tasks = load_tasks(settings.config_root)
    dest = prepare(tasks, args.task, repo_root=Path(args.repo_root), dest=Path(args.dest))
    task = tasks.task(args.task)
    sys.stdout.write(
        f"Prepared {task.id} in {dest} (committed repository plus the task's setup).\n"
        f"Open that folder in your harness and give it exactly the prompt in {dest}/BAKEOFF_TASK.md.\n"
        f"Then: ffia bakeoff grade {task.id} --workspace {dest}\n"
    )
    return 0


def _cmd_grade(args: argparse.Namespace) -> int:
    settings = Settings()
    tasks = load_tasks(settings.config_root)
    ids = {p.id for p in load_catalog(settings.education_root).patterns}
    report = grade(tasks, args.task, Path(args.workspace), catalog_ids=ids)
    if args.json:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
        return 0 if report.passed else 1
    for check in report.checks:
        sys.stdout.write(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}\n")
    sys.stdout.write(f"Changed files: {', '.join(report.changed_files) or 'none'}\n")
    sys.stdout.write(f"{report.task}: {'PASSED' if report.passed else 'FAILED'} [LOCAL grader]\n")
    return 0 if report.passed else 1


def _cmd_run(args: argparse.Namespace) -> int:
    settings = Settings()
    tasks = load_tasks(settings.config_root)
    ids = {p.id for p in load_catalog(settings.education_root).patterns}
    profile = load_policy(settings.config_root).profile("bakeoff")
    sys.stdout.write(
        f"[LIVE] {HARNESS_NAME} --model {args.model}: {args.task} in {args.dest} "
        "(bakeoff permission profile; this uses premium requests)\n"
    )
    record, report = run_copilot(
        tasks,
        args.task,
        model=args.model,
        profile=profile,
        repo_root=Path(args.repo_root),
        dest=Path(args.dest),
        catalog_ids=ids,
        timeout=args.timeout,
    )
    for check in report.checks:
        sys.stdout.write(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}\n")
    safety = record.safety
    sys.stdout.write(
        f"{record.task} / {record.model}: {'PASSED' if report.passed else 'FAILED'} in "
        f"{record.duration_seconds}s; denied {safety.denied_tool_calls}, unsafe attempts "
        f"{safety.unsafe_attempts}, premium requests {record.usage.premium_requests}\n"
    )
    if args.record:
        target = settings.demos_root / REPLAYS_DIR / f"{record.run_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(record.model_dump_json(indent=1) + "\n", encoding="utf-8")
        sys.stdout.write(f"recorded {target} (run `ffia privacy scan` before committing)\n")
    return 0 if report.passed else 1


def _cmd_check(_: argparse.Namespace) -> int:
    settings = Settings()
    tasks = load_tasks(settings.config_root)
    runs = load_runs(settings.demos_root / REPLAYS_DIR)
    problems = check_runs(tasks, runs)
    for problem in problems:
        sys.stderr.write(f"bakeoff: {problem}\n")
    if problems:
        return 1
    sys.stdout.write(f"bakeoff: {len(tasks.tasks)} tasks, {len(runs)} recorded run(s) valid\n")
    return 0


def _cmd_scorecard(args: argparse.Namespace) -> int:
    settings = Settings()
    tasks = load_tasks(settings.config_root)
    card = scorecard(tasks, load_runs(settings.demos_root / REPLAYS_DIR))
    if args.json:
        sys.stdout.write(card.model_dump_json(indent=2) + "\n")
        return 0
    sys.stdout.write(f"[{card.label}] {card.note}\n")
    for row in card.rows:
        sys.stdout.write(
            f"  {row.harness} / {row.model}: {row.tasks_passed}/{row.runs} passed, "
            f"median {row.median_duration_seconds}s, approvals {row.approvals_requested}, "
            f"denied {row.denied_tool_calls}, unsafe attempts {row.unsafe_attempts}\n"
        )
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``bakeoff`` subcommands."""
    bakeoff = subparsers.add_parser("bakeoff", help="same tasks for every harness and model")
    sub = bakeoff.add_subparsers(dest="bakeoff_command", required=True)
    tasks = sub.add_parser("tasks", help="list the tasks and their checks")
    tasks.add_argument("--json", action="store_true")
    tasks.set_defaults(func=_cmd_tasks)
    prep = sub.add_parser("prepare", help="create a sandbox for one task from the committed repo")
    prep.add_argument("task")
    prep.add_argument("--dest", required=True)
    prep.add_argument("--repo-root", default=".")
    prep.set_defaults(func=_cmd_prepare)
    grader = sub.add_parser("grade", help="grade a sandbox with deterministic checks")
    grader.add_argument("task")
    grader.add_argument("--workspace", required=True)
    grader.add_argument("--json", action="store_true")
    grader.set_defaults(func=_cmd_grade)
    run = sub.add_parser(
        "run", help="LIVE: run a task in GitHub Copilot CLI (premium requests), grade it"
    )
    run.add_argument("task")
    run.add_argument("--model", required=True)
    run.add_argument("--dest", required=True)
    run.add_argument("--repo-root", default=".")
    run.add_argument("--timeout", type=float, default=1200)
    run.add_argument("--record", action="store_true", help="save a sanitized replay")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check", help="validate the task set and every recorded replay")
    check.set_defaults(func=_cmd_check)
    card = sub.add_parser("scorecard", help="aggregate recorded runs by harness and model")
    card.add_argument("--json", action="store_true")
    card.set_defaults(func=_cmd_scorecard)
