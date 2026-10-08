"""``ffia notebooks render | check``: Fabric Git-format reference notebooks from the medallion SQL."""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.models.semantic import load_semantic_model
from fabric_foundry_accelerator.synthetic.baseline import Baseline
from fabric_foundry_accelerator.synthetic.paths import semantic_model_path
from fabric_foundry_accelerator.synthetic.profiles import PROFILES
from fabric_foundry_accelerator.synthetic.spark import (
    NotebookDefinition,
    hc01_notebooks,
    stale_or_missing,
    write_notebooks,
)

HC01_PROFILE = "hc-lab-7file-v1"


def reference_notebooks(data_root: Path) -> list[NotebookDefinition]:
    """Build the HC-01 reference notebook definitions from committed data contracts."""
    profile = PROFILES[HC01_PROFILE]
    expected = Baseline.model_validate_json(
        (data_root / "expected" / f"{profile.id}.json").read_text(encoding="utf-8")
    )
    model = load_semantic_model(semantic_model_path(data_root, profile.id))
    return hc01_notebooks(profile, expected, model)


def _cmd_render(_: argparse.Namespace) -> int:
    settings = Settings()
    for path in write_notebooks(settings.definitions_root, reference_notebooks(settings.data_root)):
        sys.stdout.write(f"wrote {path}\n")
    return 0


def _cmd_check(_: argparse.Namespace) -> int:
    settings = Settings()
    stale = stale_or_missing(settings.definitions_root, reference_notebooks(settings.data_root))
    for path in stale:
        sys.stderr.write(f"{path} is stale; run `ffia notebooks render`\n")
    if not stale:
        sys.stdout.write("Reference notebooks: OK\n")
    return 1 if stale else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``notebooks`` subcommands."""
    notebooks = subparsers.add_parser("notebooks", help="Fabric reference notebooks (Git format)")
    sub = notebooks.add_subparsers(dest="notebooks_command", required=True)
    sub.add_parser("render", help="render the reference notebooks").set_defaults(func=_cmd_render)
    sub.add_parser("check", help="fail when rendered notebooks are stale").set_defaults(
        func=_cmd_check
    )
