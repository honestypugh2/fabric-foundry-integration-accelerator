"""``ffia recovery`` subcommands."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.recovery.scenario import (
    DEFAULT_SCENARIO_PATH,
    load_scenario,
    run_recovery_drill,
)
from fabric_foundry_accelerator.synthetic.paths import DEFAULT_DATA_ROOT

DEFAULT_WORK_DIR = Path("data/synthetic/recovery/runs/latest")


def _cmd_run(args: argparse.Namespace) -> int:
    envelope = run_recovery_drill(
        load_scenario(Path(args.scenario)),
        data_root=Path(args.data_root),
        work_dir=Path(args.work_dir),
    )
    if args.json:
        sys.stdout.write(envelope.model_dump_json(indent=2) + "\n")
        return 0 if envelope.data.recovered else 1
    report = envelope.data
    lines = [
        f"{report.scenario} [{envelope.execution_label}; cloud operation performed: "
        f"{'YES' if envelope.cloud_operation_performed else 'NO'}]",
        envelope.simulation_notice or "",
        "",
    ]
    for step in report.steps:
        day = "" if step.day is None else f" (day {step.day})"
        lines.append(f"[{step.category}] {step.name}{day}: {step.summary}")
        lines.extend(
            f"    {'PASS' if c.passed else 'FAIL'} {c.name}: {c.detail}" for c in step.checks
        )
    lines += [
        "",
        f"Recovered from weekly snapshot: {'YES' if report.recovered else 'NO'}",
        "Recoverable without the weekly snapshot: "
        + ("YES" if report.counterfactual_recoverable else "NO"),
        f"Artifacts: {args.work_dir}",
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0 if report.recovered else 1


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``ffia recovery`` subcommands."""
    recovery = subparsers.add_parser(
        "recovery", help="Open Mirroring recovery drill (simulated locally)"
    )
    recovery_sub = recovery.add_subparsers(dest="recovery_command", required=True)
    run = recovery_sub.add_parser("run", help="run the snapshot + incremental + restore drill")
    run.add_argument("--scenario", default=str(DEFAULT_SCENARIO_PATH))
    run.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    run.add_argument("--work-dir", default=str(DEFAULT_WORK_DIR))
    run.add_argument(
        "--json", action="store_true", help="print the full SIMULATED envelope as JSON"
    )
    run.set_defaults(func=_cmd_run)
