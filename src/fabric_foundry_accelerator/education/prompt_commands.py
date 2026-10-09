"""Render portable prompt packs from the existing structured lessons and guides."""

import argparse
import sys
from pathlib import Path
from typing import Literal

import yaml

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.education.lessons import LessonMeta
from fabric_foundry_accelerator.patterns.catalog import load_catalog

Harness = Literal["github-copilot", "claude-code"]


def _header(title: str, harness: Harness) -> list[str]:
    status = (
        "DOCUMENTED ONLY: no Claude Code runs were recorded. Claude models inside Copilot "
        "are not Claude Code."
        if harness == "claude-code"
        else "Recorded bake-off results describe Copilot CLI only, not every Copilot surface."
    )
    return [
        f"# {title}",
        "",
        "<!-- Generated from education and guide YAML; run ffia prompts render. -->",
        "",
        status,
        "",
        "Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data "
        "only. State the provider, server and tool before cloud calls. Default to read-only; "
        "a prompt is not approval for a write. Label execution and fallback honestly.",
        "",
    ]


def rendered(settings: Settings) -> dict[Path, str]:
    """Build packs from authored lesson prompts or catalog-grounded planning prompts."""
    catalog = load_catalog(settings.education_root)
    lessons: dict[str, LessonMeta] = {}
    for path in sorted((settings.education_root / "patterns").glob("*/lesson.yaml")):
        lesson = LessonMeta.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        for pattern_id in lesson.pattern_ids:
            if pattern_id in lessons:
                raise ValueError(f"duplicate pattern prompt source: {pattern_id}")
            lessons[pattern_id] = lesson
    guides = load_guides(settings.guides_root, catalog)
    outputs: dict[Path, str] = {}
    for harness in ("github-copilot", "claude-code"):
        key = "copilot_prompt" if harness == "github-copilot" else "claude_code_prompt"
        lines = _header("Architecture pattern prompts", harness)
        for pattern in catalog.patterns:
            lesson = lessons.get(pattern.id)
            if lesson is None:
                source = "Source: [catalog](../../education/patterns/catalog.yaml)."
                prompt = (
                    f"Read the catalog entry for {pattern.id}: {pattern.name}. "
                    f"Explain this scenario: {pattern.summary} "
                    f"Trace Fabric's role ({pattern.fabric_role}), Foundry's role "
                    f"({pattern.foundry_role}), and MCP's role ({pattern.mcp_role}). "
                    f"Identify the authority boundary: {pattern.authority} "
                    f"Plan the offline demonstration: {pattern.offline_equivalent} "
                    "Name any preview dependencies and propose the smallest validation "
                    "check. Do not edit files, call cloud tools, or claim an operation ran."
                )
            else:
                source = f"Source: [lesson](../../education/patterns/{lesson.id}/lesson.yaml)."
                prompt = getattr(lesson, key).strip()
            lines += [
                f"## {pattern.id}: {pattern.name}",
                "",
                f"Status: {pattern.status}. Offline equivalent: {pattern.offline_equivalent}",
                "",
                source,
                "",
                "```text",
                prompt,
                "```",
                "",
            ]
        root = Path("prompts") / harness
        outputs[root / "patterns.md"] = "\n".join(lines)
        for guide in guides.values():
            lines = _header(guide.title, harness)
            lines += [
                f"Source: [guide](../../guides/{guide.id}/guide.yaml).",
                "",
                f"Dataset: `{guide.dataset_profile}`. Guide status: {guide.status}.",
                "",
            ]
            for step in guide.steps:
                tool = step.tool_path
                lines += [
                    f"## {step.id}: {step.title}",
                    "",
                    f"Provider: {tool.provider}; server: {tool.server or 'not applicable'}; "
                    f"tools: {', '.join(tool.tools) or 'none'}.",
                    "",
                    f"Skills: {', '.join(step.skills) or 'none required'}. "
                    f"Human approval required: {'yes' if step.approval_required else 'no'}.",
                    "",
                    "```text",
                    getattr(step, key).strip(),
                    "```",
                    "",
                    f"Checkpoint: {step.checkpoint}",
                    "",
                    f"Offline equivalent: {step.offline_equivalent}",
                    "",
                ]
                if tool.fallback:
                    fallback = tool.fallback
                    lines += [
                        (
                            f"Fallback: {fallback.label}, {fallback.server}, "
                            f"{', '.join(fallback.tools)}. {fallback.note}"
                        ).rstrip(),
                        "",
                    ]
            outputs[root / f"{guide.id}.md"] = "\n".join(lines)
    return outputs


def _cmd_render(_: argparse.Namespace) -> int:
    for path, content in rendered(Settings()).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        sys.stdout.write(f"wrote {path}\n")
    return 0


def _cmd_check(_: argparse.Namespace) -> int:
    errors = [
        f"{path} is stale; run `ffia prompts render`"
        for path, content in rendered(Settings()).items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    for error in errors:
        sys.stderr.write(f"prompts: {error}\n")
    if not errors:
        sys.stdout.write("prompt packs are current; Claude Code is documented-only\n")
    return 1 if errors else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``ffia prompts render|check``."""
    parser = subparsers.add_parser("prompts", help="portable pattern and guide prompt packs")
    sub = parser.add_subparsers(dest="prompts_command", required=True)
    sub.add_parser("render", help="render existing structured prompts").set_defaults(
        func=_cmd_render
    )
    sub.add_parser("check", help="check generated prompt packs").set_defaults(func=_cmd_check)
