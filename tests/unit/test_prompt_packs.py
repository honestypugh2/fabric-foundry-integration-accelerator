"""Portable packs reuse authored prompts and catalog context without inventing run evidence."""

import argparse
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.education.lessons import LessonMeta
from fabric_foundry_accelerator.education.prompt_commands import register, rendered
from fabric_foundry_accelerator.patterns.catalog import load_catalog


def test_packs_cover_every_pattern_and_guide(make_settings: Callable[..., Settings]) -> None:
    settings = make_settings()
    outputs = rendered(settings)
    assert all(
        line == line.rstrip() for content in outputs.values() for line in content.splitlines()
    )
    catalog = load_catalog(settings.education_root)
    guides = load_guides(settings.guides_root, catalog)
    assert len(outputs) == 2 * (1 + len(guides))
    for harness, key in (
        ("github-copilot", "copilot_prompt"),
        ("claude-code", "claude_code_prompt"),
    ):
        root = Path("prompts") / harness
        patterns = outputs[root / "patterns.md"]
        for pattern in catalog.patterns:
            assert f"## {pattern.id}: {pattern.name}" in patterns
        for path in (settings.education_root / "patterns").glob("*/lesson.yaml"):
            lesson = LessonMeta.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            if lesson.pattern_ids:
                assert getattr(lesson, key).strip() in patterns
        assert "Do not edit files, call cloud tools, or claim an operation ran." in patterns
        for guide in guides.values():
            pack = outputs[root / f"{guide.id}.md"]
            for step in guide.steps:
                assert getattr(step, key).strip() in pack
                assert step.checkpoint in pack
        if harness == "claude-code":
            assert all(
                "DOCUMENTED ONLY" in content
                for path, content in outputs.items()
                if path.parent == root
            )


def test_check_detects_drift_and_render_repairs_it(
    tmp_path: Path,
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = make_settings()
    monkeypatch.setattr(
        "fabric_foundry_accelerator.education.prompt_commands.Settings", lambda: settings
    )
    monkeypatch.chdir(tmp_path)
    parser = argparse.ArgumentParser()
    register(parser.add_subparsers(required=True))

    def run(command: str) -> int:
        args = parser.parse_args(["prompts", command])
        return int(args.func(args))

    assert run("check") == 1
    assert "stale" in capsys.readouterr().err
    assert run("render") == 0
    assert run("check") == 0
    path = tmp_path / "prompts" / "claude-code" / "patterns.md"
    path.write_text("stale", encoding="utf-8")
    assert run("check") == 1


def test_duplicate_lesson_sources_are_rejected(
    tmp_path: Path, make_settings: Callable[..., Settings]
) -> None:
    settings = make_settings()
    patterns = tmp_path / "patterns"
    patterns.mkdir()
    shutil.copyfile(
        settings.education_root / "patterns" / "catalog.yaml", patterns / "catalog.yaml"
    )
    for name in ("first", "second"):
        target = patterns / name
        target.mkdir()
        shutil.copyfile(
            settings.education_root / "patterns" / "p06-enterprise-agent" / "lesson.yaml",
            target / "lesson.yaml",
        )
    with pytest.raises(ValueError, match="duplicate pattern prompt source: P06"):
        rendered(settings.model_copy(update={"education_root": tmp_path}))
