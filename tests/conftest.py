"""Shared fixtures: build every dataset profile once per test session into a temp directory."""

from collections.abc import Callable
from pathlib import Path

import pytest

from fabric_foundry_accelerator.audit.store import InMemoryAuditStore
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.services.container import Container, build_container
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


CONFIG_ROOT = REPO_ROOT / "config"


@pytest.fixture
def make_settings(built: tuple[Path, dict[str, ValidationReport]]) -> Callable[..., Settings]:
    """Factory for settings pointing at the repository content and the session-built lakehouse."""

    def factory(**overrides: object) -> Settings:
        values: dict[str, object] = {
            "config_root": CONFIG_ROOT,
            "data_root": DATA_ROOT,
            "output_root": built[0],
            "guides_root": REPO_ROOT / "guides",
            "education_root": REPO_ROOT / "education",
            "frontend_root": REPO_ROOT / "frontend",
            "audit_path": None,
            "demo_check_azure_cli": False,
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)  # pyright: ignore[reportCallIssue]

    return factory


@pytest.fixture
def make_container(make_settings: Callable[..., Settings]) -> Callable[..., Container]:
    """Factory for containers with an in-memory audit store."""

    def factory(*, audit: InMemoryAuditStore | None = None, **overrides: object) -> Container:
        return build_container(make_settings(**overrides), audit=audit or InMemoryAuditStore())

    return factory
