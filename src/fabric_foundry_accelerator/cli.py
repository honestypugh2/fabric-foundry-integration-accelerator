"""Command-line interface: ``ffia``.

Subcommands are deliberately small, offline-safe utilities. Cloud-touching
commands are added in later phases behind explicit flags.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from fabric_foundry_accelerator import __version__
from fabric_foundry_accelerator.education import commands as education_commands
from fabric_foundry_accelerator.observability.logging import configure_logging
from fabric_foundry_accelerator.privacy.leak_scan import (
    DEFAULT_DENYLIST_PATH,
    LOCAL_DENYLIST_PATH,
    Denylist,
    add_terms_to_file,
    list_repository_files,
    scan_paths,
)
from fabric_foundry_accelerator.recovery import commands as recovery_commands
from fabric_foundry_accelerator.research.sources import (
    DEFAULT_REGISTRY_PATH,
    DEFAULT_RENDERED_PATH,
    load_registry,
    render_markdown,
)
from fabric_foundry_accelerator.services import commands as runtime_commands
from fabric_foundry_accelerator.synthetic import commands as data_commands


def _out(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _err(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _cmd_version(_: argparse.Namespace) -> int:
    _out(__version__)
    return 0


def _cmd_privacy_scan(args: argparse.Namespace) -> int:
    root = Path(args.root)
    denylist_path = root / Path(args.denylist)
    denylist = Denylist.load(denylist_path, local_terms_path=root / LOCAL_DENYLIST_PATH)
    paths = [Path(p) for p in args.paths] if args.paths else list_repository_files(root)
    findings = scan_paths(paths, root=root, denylist=denylist, exclude=[denylist_path])
    for finding in findings:
        _err(finding.render())
    _out(
        f"leak-scan: {len(paths)} file(s), {len(denylist)} denylisted term hash(es), "
        f"{len(findings)} finding(s)"
    )
    return 1 if findings else 0


def _cmd_privacy_add_terms(args: argparse.Namespace) -> int:
    terms = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    added = add_terms_to_file(Path(args.denylist), terms)
    _out(f"added {added} new term hash(es); plaintext was not written")
    return 0


def _cmd_sources_render(args: argparse.Namespace) -> int:
    rendered = render_markdown(load_registry(Path(args.registry)))
    Path(args.output).write_text(rendered, encoding="utf-8")
    _out(f"rendered {args.output}")
    return 0


def _cmd_sources_check(args: argparse.Namespace) -> int:
    rendered = render_markdown(load_registry(Path(args.registry)))
    output = Path(args.output)
    current = output.read_text(encoding="utf-8") if output.is_file() else ""
    if current != rendered:
        _err(f"{output} is stale; run `uv run ffia sources render`")
        return 1
    _out(f"{output} is up to date")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(prog="ffia", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="print the package version").set_defaults(func=_cmd_version)

    privacy = sub.add_parser("privacy", help="privacy and leakage guardrails")
    privacy_sub = privacy.add_subparsers(dest="privacy_command", required=True)
    scan = privacy_sub.add_parser("scan", help="scan files for customer/secret/GUID/email leaks")
    scan.add_argument("paths", nargs="*", help="files to scan (default: repository files)")
    scan.add_argument("--root", default=".", help="repository root")
    scan.add_argument("--denylist", default=str(DEFAULT_DENYLIST_PATH))
    scan.set_defaults(func=_cmd_privacy_scan)
    add = privacy_sub.add_parser("add-terms", help="hash terms from stdin into the denylist")
    add.add_argument("--denylist", default=str(DEFAULT_DENYLIST_PATH))
    add.set_defaults(func=_cmd_privacy_add_terms)

    sources = sub.add_parser("sources", help="authoritative source registry")
    sources_sub = sources.add_subparsers(dest="sources_command", required=True)
    for name, func, help_text in (
        ("render", _cmd_sources_render, "render source-validation.md"),
        ("check", _cmd_sources_check, "fail if source-validation.md is stale"),
    ):
        cmd = sources_sub.add_parser(name, help=help_text)
        cmd.add_argument("--registry", default=str(DEFAULT_REGISTRY_PATH))
        cmd.add_argument("--output", default=str(DEFAULT_RENDERED_PATH))
        cmd.set_defaults(func=func)

    data_commands.register(sub)
    recovery_commands.register(sub)
    runtime_commands.register(sub)
    education_commands.register(sub)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    # Logs always go to stderr so stdout stays clean for command output and MCP stdio.
    configure_logging()
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
