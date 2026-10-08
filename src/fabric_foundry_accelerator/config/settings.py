"""Typed runtime settings (environment variables prefixed ``FFIA_`` plus optional ``.env.local``).

Real tenant, workspace or item identifiers never belong in committed files; ``.env.local`` is
git-ignored. Settings select configuration by *name* (environment, overlay); the configuration
files themselves hold only aliases.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide settings."""

    model_config = SettingsConfigDict(
        env_prefix="FFIA_", env_file=".env.local", env_file_encoding="utf-8", extra="ignore"
    )

    environment: str = Field(default="offline", pattern=r"^[a-z][a-z0-9-]*$")
    overlay: str = Field(default="example-healthcare", pattern=r"^[a-z][a-z0-9-]*$")
    config_root: Path = Path("config")
    data_root: Path = Path("data/synthetic")
    output_root: Path | None = None
    guides_root: Path = Path("guides")
    education_root: Path = Path("education")
    sources_path: Path = Path("docs/research/sources.yaml")
    frontend_root: Path = Path("frontend")
    audit_path: Path | None = Path("data/runtime/audit.jsonl")
    runtime_root: Path = Path("data/runtime")
    auto_build_data: bool = True
    demo_check_azure_cli: bool = True
    allow_live_mutation: bool = False
    fabric_live: bool = False
    definitions_root: Path = Path("fabric/workspace")
    simulate_fabric_outage: bool = False
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    log_json: bool = False
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")

    @field_validator("audit_path", "output_root", mode="before")
    @classmethod
    def _empty_means_unset(cls, value: object) -> object:
        # An empty environment variable means "not set", never the current directory.
        return None if value in ("", None) else value

    @property
    def lakehouse_root(self) -> Path:
        """Return where built Parquet layers live."""
        return self.output_root or self.data_root
