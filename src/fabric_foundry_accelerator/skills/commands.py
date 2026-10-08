"""``ffia skills install | status | check``: pinned, curated Fabric Skills."""

import argparse
import sys

import httpx

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.skills.vendor import SkillsError, check, install, load_lock, status


def _cmd_install(_: argparse.Namespace) -> int:
    settings = Settings()
    lock = load_lock(settings.config_root)
    sys.stdout.write(
        f"Downloading {lock.source}@{lock.tag} (public archive; no tenant call) and verifying SHA-256...\n"
    )
    try:
        with httpx.Client() as client:
            written = install(lock, settings.config_root.parent, client)
    except (SkillsError, httpx.HTTPError) as error:
        sys.stderr.write(f"skills: {error}\n")
        return 1
    sys.stdout.write(
        f"installed {len(lock.skills)} skills ({len(written)} files) under {lock.install_root}/\n"
    )
    for skill in lock.skills:
        sys.stdout.write(f"  - {skill.name}: {skill.why}\n")
    sys.stdout.write("The bundle's .mcp.json was NOT installed; use `ffia mcp render <profile>`.\n")
    return 0


def _cmd_status(_: argparse.Namespace) -> int:
    settings = Settings()
    lock = load_lock(settings.config_root)
    states = status(lock, settings.config_root.parent)
    for name, state in states.items():
        sys.stdout.write(f"{name:<28} {state}\n")
    return 0 if all(s.startswith("installed") for s in states.values()) else 1


def _cmd_check(_: argparse.Namespace) -> int:
    settings = Settings()
    errors = check(load_lock(settings.config_root), settings.config_root.parent)
    for error in errors:
        sys.stderr.write(f"skills: {error}\n")
    if not errors:
        sys.stdout.write("Skills lock and approval rules: OK\n")
    return 1 if errors else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``skills`` subcommands."""
    skills = subparsers.add_parser("skills", help="pinned, curated Fabric Skills")
    sub = skills.add_subparsers(dest="skills_command", required=True)
    sub.add_parser("install", help="download, verify and install the pinned skills").set_defaults(
        func=_cmd_install
    )
    sub.add_parser("status", help="show installed skills and pins").set_defaults(func=_cmd_status)
    sub.add_parser("check", help="offline: lock, .gitignore and approval rules").set_defaults(
        func=_cmd_check
    )
