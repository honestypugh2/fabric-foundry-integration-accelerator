"""``ffia harness render|check|guard``: one permission policy for every agent harness."""

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.harness.policy import (
    VSCODE_KEY,
    check,
    guard_hook_output,
    load_policy,
    render_claude,
    render_copilot_cli,
    render_vscode,
)


def _render_text(args: argparse.Namespace) -> str:
    profile = load_policy(Settings().config_root).profile(args.profile)
    if args.client == "copilot-cli":
        argv = render_copilot_cli(profile)
        if args.output:
            return json.dumps(argv, indent=2) + "\n"
        return " ".join(f"'{a}'" if "(" in a else a for a in argv) + "\n"
    if args.client == "vscode":
        rules = render_vscode(profile)
        path = Path(args.output) if args.output else None
        if path is None:
            return json.dumps(rules, indent=2) + "\n"
        settings: object = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        merged: dict[str, object] = (
            dict(cast("dict[str, object]", settings)) if isinstance(settings, dict) else {}
        )
        merged[VSCODE_KEY] = rules
        return json.dumps(merged, indent=2) + "\n"
    return json.dumps(render_claude(profile), indent=2) + "\n"


def _cmd_render(args: argparse.Namespace) -> int:
    text = _render_text(args)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text, encoding="utf-8")
        sys.stdout.write(f"wrote {args.output}\n")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_check(_: argparse.Namespace) -> int:
    settings = Settings()
    errors = check(load_policy(settings.config_root), Path())
    for error in errors:
        sys.stderr.write(f"harness: {error}\n")
    if errors:
        return 1
    sys.stdout.write("harness: Claude Code and VS Code settings match config/harness/policy.yaml\n")
    return 0


def _cmd_guard(_: argparse.Namespace) -> int:
    # Claude Code PreToolUse hook: read the tool call on stdin; print a decision only to deny.
    output = guard_hook_output(sys.stdin.read())
    if output:
        sys.stdout.write(output + "\n")
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``harness`` subcommands."""
    harness = subparsers.add_parser("harness", help="agent harness permissions as code")
    sub = harness.add_subparsers(dest="harness_command", required=True)
    rend = sub.add_parser("render", help="render a profile for a client")
    rend.add_argument("profile")
    rend.add_argument("--client", choices=["claude", "copilot-cli", "vscode"], default="claude")
    rend.add_argument("--output")
    rend.set_defaults(func=_cmd_render)
    chk = sub.add_parser("check", help="committed settings equal the repo profile render")
    chk.set_defaults(func=_cmd_check)
    grd = sub.add_parser("guard", help="Claude Code PreToolUse hook (reads the tool call on stdin)")
    grd.set_defaults(func=_cmd_guard)
