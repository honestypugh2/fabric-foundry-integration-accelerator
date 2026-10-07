"""``ffia data`` subcommands: generate, build/validate and export synthetic data."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.models.checks import failed
from fabric_foundry_accelerator.synthetic.medallion import DataValidationError
from fabric_foundry_accelerator.synthetic.paths import DEFAULT_DATA_ROOT
from fabric_foundry_accelerator.synthetic.pipeline import (
    build_and_validate,
    check_profile,
    export_raw,
    generate_profile,
)
from fabric_foundry_accelerator.synthetic.profiles import PROFILES, DatasetProfile, get_profile

ALL = "all"


def _out(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _err(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _selected(profile: str) -> list[DatasetProfile]:
    return list(PROFILES.values()) if profile == ALL else [get_profile(profile)]


def _cmd_generate(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    problems = 0
    for profile in _selected(args.profile):
        if args.check:
            differences = check_profile(profile, root)
            for difference in differences:
                _err(f"{profile.id}: {difference}")
            problems += len(differences)
            _out(
                f"{profile.id}: "
                + ("matches generator" if not differences else "DIFFERS from generator")
            )
        else:
            manifest = generate_profile(profile, root)
            rows = ", ".join(f"{f.name} {f.rows}" for f in manifest.files)
            _out(f"{profile.id}: wrote {rows}")
    return 1 if problems else 0


def _cmd_build(args: argparse.Namespace) -> int:
    root = Path(args.data_root)
    output = Path(args.output_root) if args.output_root else root
    status = 0
    for profile in _selected(args.profile):
        try:
            report = build_and_validate(
                profile, data_root=root, output_root=output, update_baseline=args.update_baseline
            )
        except DataValidationError as error:
            _err(f"{profile.id}: BUILD FAILED: {error}")
            status = 1
            continue
        tables = sum(len(t) for t in report.build.row_counts.values())
        layers = ", ".join(f"{layer} {len(t)}" for layer, t in report.build.row_counts.items())
        bad = failed(list(report.checks))
        for check in bad:
            _err(f"{profile.id}: FAIL {check.name}: {check.detail}")
        for difference in report.baseline_differences:
            _err(f"{profile.id}: BASELINE {difference}")
        if args.verbose:
            for check in report.checks:
                _out(f"  {'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")
        verdict = (
            "baseline written"
            if args.update_baseline
            else ("baseline matched" if not report.baseline_differences else "baseline DIFFERS")
        )
        _out(
            f"{profile.id}: {tables} tables ({layers}); "
            f"{len(report.checks) - len(bad)}/{len(report.checks)} checks passed; {verdict} "
            "[LOCAL, no cloud operation]"
        )
        status = status or (0 if report.passed else 1)
    return status


def _cmd_export(args: argparse.Namespace) -> int:
    profile = get_profile(args.profile)
    copied = export_raw(profile, Path(args.data_root), Path(args.dest))
    _out(
        f"copied {len(copied)} files to {args.dest} with SHA256SUMS "
        "(verify with `sha256sum -c SHA256SUMS`)"
    )
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``ffia data`` subcommands."""
    data = subparsers.add_parser("data", help="synthetic data: generate, build, validate, export")
    data_sub = data.add_subparsers(dest="data_command", required=True)
    choices = [*sorted(PROFILES), ALL]

    generate = data_sub.add_parser(
        "generate", help="generate raw CSVs (or --check committed files)"
    )
    generate.add_argument("--profile", choices=choices, default=ALL)
    generate.add_argument(
        "--check", action="store_true", help="verify committed files match the generator"
    )
    generate.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    generate.set_defaults(func=_cmd_generate)

    build = data_sub.add_parser(
        "build", help="build Bronze/Silver/Gold Parquet and validate the baseline"
    )
    build.add_argument("--profile", choices=choices, default=ALL)
    build.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    build.add_argument(
        "--output-root", default=None, help="where layer Parquet goes (default: data root)"
    )
    build.add_argument("--update-baseline", action="store_true", help="write expected baselines")
    build.add_argument("--verbose", action="store_true", help="print every check")
    build.set_defaults(func=_cmd_build)

    export = data_sub.add_parser(
        "export", help="copy a profile's raw CSVs plus SHA256SUMS to a folder"
    )
    export.add_argument("--profile", choices=sorted(PROFILES), required=True)
    export.add_argument("--dest", required=True)
    export.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    export.set_defaults(func=_cmd_export)
