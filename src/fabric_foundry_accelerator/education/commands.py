"""``ffia education check``: validate lessons, labs, the architecture map and the completeness gate."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.education.lessons import (
    EducationReferences,
    guide_diagram_errors,
    load_education,
)
from fabric_foundry_accelerator.patterns.catalog import load_catalog
from fabric_foundry_accelerator.research.sources import DEFAULT_REGISTRY_PATH, load_registry


def _cmd_check(args: argparse.Namespace) -> int:
    education_root = Path(args.education_root)
    catalog = load_catalog(education_root)
    refs = EducationReferences(
        pattern_ids=frozenset(p.id for p in catalog.patterns),
        source_ids=frozenset(s.id for s in load_registry(Path(args.sources)).sources),
        guide_ids=frozenset(load_guides(Path(args.guides_root), catalog)),
    )
    try:
        library = load_education(education_root, refs)
    except ValueError as error:
        sys.stderr.write(f"education content is invalid:\n{error}\n")
        return 1
    diagram_errors = guide_diagram_errors(library, load_guides(Path(args.guides_root), catalog))
    if diagram_errors:
        sys.stderr.write("guide diagrams are invalid:\n- " + "\n- ".join(diagram_errors) + "\n")
        return 1
    report = library.completeness_report()
    checks = sum(len(lesson.checks) for lesson in library.lessons)
    sys.stdout.write(
        f"{len(library.lessons)} lessons x 5 levels, {checks} knowledge checks, "
        f"{len(library.labs)} labs, {len(library.architecture.components)} architecture components\n"
        f"completeness gate: {report.answered}/{report.total} questions answered "
        f"({report.coverage:.0%})\n"
    )
    for item in report.items:
        if not item.answered:
            sys.stdout.write(
                f"  - {item.id} planned for Phase {item.planned_phase}: {item.question}\n"
            )
    if report.coverage < args.min_coverage:
        sys.stderr.write(
            f"coverage {report.coverage:.0%} is below the required {args.min_coverage:.0%}\n"
        )
        return 1
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``education`` subcommands."""
    education = subparsers.add_parser("education", help="structured learning content")
    sub = education.add_subparsers(dest="education_command", required=True)
    check = sub.add_parser(
        "check", help="validate lessons, labs, architecture map and completeness gate"
    )
    check.add_argument("--education-root", default="education")
    check.add_argument("--guides-root", default="guides")
    check.add_argument("--sources", default=str(DEFAULT_REGISTRY_PATH))
    check.add_argument("--min-coverage", type=float, default=0.0)
    check.set_defaults(func=_cmd_check)
