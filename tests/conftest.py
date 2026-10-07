"""Shared fixtures: build every dataset profile once per test session into a temp directory."""

from pathlib import Path

import pytest

from fabric_foundry_accelerator.synthetic.paths import DEFAULT_DATA_ROOT
from fabric_foundry_accelerator.synthetic.pipeline import ValidationReport, build_and_validate
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / DEFAULT_DATA_ROOT


@pytest.fixture(scope="session")
def data_root() -> Path:
    return DATA_ROOT


@pytest.fixture(scope="session")
def built(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, ValidationReport]]:
    """Build all profiles from committed raw CSVs; return (output_root, reports)."""
    output_root = tmp_path_factory.mktemp("lakehouse")
    reports = {
        profile_id: build_and_validate(profile, data_root=DATA_ROOT, output_root=output_root)
        for profile_id, profile in PROFILES.items()
    }
    return output_root, reports
