"""``ffia mcp profiles | render | check``: MCP client configuration from one source."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.mcp.profiles import (
    CLIENT_FILES,
    CLIENTS,
    McpClient,
    check_profiles,
    load_profiles,
    render_text,
)


def _cmd_profiles(_: argparse.Namespace) -> int:
    profiles = load_profiles(Settings().config_root)
    for name, profile in profiles.profiles.items():
        flags = [profile.execution_label.value, "writes" if profile.writes else "read-only"]
        if profile.default:
            flags.append("default")
        if profile.approval == "per-call":
            flags.append("per-call approval")
        sys.stdout.write(f"{name:<26} {profile.title}  [{', '.join(flags)}]\n")
        for server, usage in profile.servers.items():
            tools = f"{len(usage.tools)} allow-listed tools" if usage.tools else "all server tools"
            sys.stdout.write(f"    - {server}: {tools}\n")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    client: McpClient = args.client
    text = render_text(load_profiles(Settings().config_root), args.profile, client)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        sys.stderr.write(f"wrote {args.output} ({CLIENT_FILES[client]})\n")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_check(_: argparse.Namespace) -> int:
    settings = Settings()
    errors = check_profiles(settings.config_root, settings.config_root.parent)
    for error in errors:
        sys.stderr.write(f"mcp: {error}\n")
    if not errors:
        sys.stdout.write("MCP profiles: OK\n")
    return 1 if errors else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``mcp`` subcommands."""
    mcp = subparsers.add_parser("mcp", help="MCP client profiles (render and check)")
    sub = mcp.add_subparsers(dest="mcp_command", required=True)
    sub.add_parser("profiles", help="list profiles").set_defaults(func=_cmd_profiles)
    render = sub.add_parser("render", help="render a profile for an MCP client")
    render.add_argument("profile")
    render.add_argument("--client", choices=CLIENTS, default="vscode")
    render.add_argument("--output", help="write to this file instead of stdout")
    render.set_defaults(func=_cmd_render)
    sub.add_parser("check", help="validate pins, allow-lists and safety rules").set_defaults(
        func=_cmd_check
    )
