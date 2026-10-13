"""Cross-registry authoring checks, separate from runtime or live certification."""

from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ValidationError

from fabric_foundry_accelerator.education.guides import GuideStep, UseCaseGuide
from fabric_foundry_accelerator.education.lessons import EducationLibrary, guide_diagram_errors
from fabric_foundry_accelerator.mcp.profiles import load_profiles
from fabric_foundry_accelerator.policies.engine import (
    WritePolicy,
    load_tool_manifest,
    load_write_policy,
)
from fabric_foundry_accelerator.skills.vendor import load_lock


class BaselineReference(BaseModel):
    """Identity shared by committed dataset baselines; measurements are profile-specific."""

    profile: str


def _file(root: Path, relative: str) -> bool:
    path = (root / relative).resolve()
    return path.is_relative_to(root.resolve()) and path.is_file()


def _asset_errors(guide: UseCaseGuide, repo_root: Path, guides_root: Path) -> list[str]:
    errors = [
        f"guide {guide.id}: missing {name}"
        for name in ("README.md", "AGENTS.md", "CLAUDE.md")
        if not (guides_root / guide.id / name).is_file()
    ]
    if not _file(repo_root, guide.expected_baseline):
        errors.append(f"guide {guide.id}: missing or unsafe baseline {guide.expected_baseline}")
    else:
        try:
            baseline = BaselineReference.model_validate_json(
                (repo_root / guide.expected_baseline).read_text(encoding="utf-8")
            )
        except ValidationError as error:
            errors.append(f"guide {guide.id}: invalid baseline: {error}")
        else:
            if baseline.profile != guide.dataset_profile:
                errors.append(f"guide {guide.id}: baseline profile differs from dataset_profile")
    if guide.diagram is None:
        errors.append(f"guide {guide.id}: missing architecture view")
    else:
        for suffix in ("png", "drawio"):
            if not _file(repo_root, f"docs/architecture/diagrams/{guide.diagram}.{suffix}"):
                errors.append(
                    f"guide {guide.id}: missing draw.io {suffix.upper()} for {guide.diagram}"
                )
    return errors


def _step_errors(
    guide_id: str,
    step: GuideStep,
    *,
    allowed_tools: Mapping[str, set[str]],
    skills: set[str],
    policy: WritePolicy,
) -> list[str]:
    where = f"guide {guide_id} step {step.id}"
    errors = [f"{where}: unknown skill {skill}" for skill in set(step.skills) - skills]
    tool_path = step.tool_path
    if tool_path.server:
        allowed = allowed_tools.get(tool_path.server, set())
        if tool_path.server not in allowed_tools:
            errors.append(f"{where}: unknown or unconfigured server {tool_path.server}")
        elif allowed:
            errors += [
                f"{where}: tool {tool} is not allow-listed"
                for tool in set(tool_path.tools) - allowed
            ]
    if tool_path.fallback:
        errors += [
            f"{where}: unknown fallback tool {tool}"
            for tool in set(tool_path.fallback.tools) - allowed_tools["ffia-local"]
        ]
    if step.rehearsal:
        definition = policy.operation(step.rehearsal.operation)
        if definition is None or step.rehearsal.item_type not in definition.item_types:
            errors.append(f"{where}: rehearsal operation/item type is not in write policy")
    return errors


def authoring_warnings(
    guides: Mapping[str, UseCaseGuide],
    config_root: Path,
) -> list[str]:
    """Disclose extension-managed servers whose tool contracts cannot be checked offline."""
    profiles = load_profiles(config_root)
    return [
        f"guide {guide.id} step {step.id}: {step.tool_path.server} has no pinned tool catalog; "
        "documented operation names require connected validation"
        for guide in guides.values()
        for step in guide.steps
        if step.tool_path.server in profiles.servers
        and not profiles.servers[step.tool_path.server].catalog
        and step.tool_path.server != "ffia-local"
    ]


def authoring_errors(
    library: EducationLibrary,
    guides: Mapping[str, UseCaseGuide],
    *,
    repo_root: Path,
    guides_root: Path,
    config_root: Path,
) -> list[str]:
    """Return blocking errors for published guides and their shared authoring assets."""
    errors = guide_diagram_errors(library, guides)
    profiles = load_profiles(config_root)
    allowed_tools: dict[str, set[str]] = {}
    for profile in profiles.profiles.values():
        for server, usage in profile.servers.items():
            allowed_tools.setdefault(server, set()).update(usage.tools)
    allowed_tools["ffia-local"] = set(load_tool_manifest(config_root).enabled())
    skills = {item.name for item in load_lock(config_root).skills} | {
        path.parent.name for path in (repo_root / ".claude" / "skills").glob("*/SKILL.md")
    }
    policy = load_write_policy(config_root)
    for guide in guides.values():
        errors += _asset_errors(guide, repo_root, guides_root)
        for step in guide.steps:
            errors += _step_errors(
                guide.id,
                step,
                allowed_tools=allowed_tools,
                skills=skills,
                policy=policy,
            )
    if library.workshop is None:
        errors.append("authoring: missing workshop stories")
    else:
        for story in library.workshop.use_cases:
            name = story.presenter_path.removeprefix("/talktracks/")
            if not _file(repo_root, f"frontend/public/talktracks/{name}"):
                errors.append(f"guide {story.guide_id}: missing presenter handout {name}")
            track_id = name.removesuffix(".html")
            if not _file(repo_root, f"demos/{track_id}/talk-track.yaml"):
                errors.append(f"guide {story.guide_id}: missing structured presenter source")
    return errors
