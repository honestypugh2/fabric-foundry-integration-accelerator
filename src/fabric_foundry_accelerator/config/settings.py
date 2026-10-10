"""Typed runtime settings (``FFIA_`` variables, ``.env`` and optional ``.env.local`` overrides).

Real tenant, workspace or item identifiers never belong in committed files; both environment files are
git-ignored. Settings select configuration by *name* (environment, overlay); the configuration
files themselves hold only aliases.
"""

from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide settings."""

    model_config = SettingsConfigDict(
        env_prefix="FFIA_",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
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
    foundry_live: bool = False
    azure_tenant_id: SecretStr | None = Field(default=None, validation_alias="AZURE_TENANT_ID")
    azure_subscription_id: SecretStr | None = Field(
        default=None, validation_alias="AZURE_SUBSCRIPTION_ID"
    )
    azure_resource_group: SecretStr | None = Field(
        default=None, validation_alias="AZURE_RESOURCE_GROUP"
    )
    fabric_workspace_id: SecretStr | None = Field(
        default=None, validation_alias="FABRIC_WORKSPACE_ID"
    )
    fabric_workspace_alias: str = Field(
        default="demo-dev", validation_alias="FABRIC_WORKSPACE_ALIAS"
    )
    fabric_workspaces: SecretStr | None = Field(default=None, validation_alias="FABRIC_WORKSPACES")
    fabric_connection_name: SecretStr | None = Field(
        default=None, validation_alias="FABRIC_CONNECTION_NAME"
    )
    foundry_resource_name: SecretStr | None = Field(
        default=None, validation_alias="FOUNDRY_RESOURCE_NAME"
    )
    foundry_project_name: SecretStr | None = Field(
        default=None, validation_alias="FOUNDRY_PROJECT_NAME"
    )
    foundry_project_endpoint: SecretStr | None = Field(
        default=None, validation_alias="FOUNDRY_PROJECT_ENDPOINT"
    )
    foundry_model_deployment: SecretStr | None = Field(
        default=None, validation_alias="FOUNDRY_MODEL_DEPLOYMENT"
    )
    foundry_agent_names: SecretStr | None = Field(
        default=None, validation_alias="FOUNDRY_AGENT_NAMES"
    )
    # Opt-in Application Insights export; keep it in the git-ignored .env.local, never in the repo.
    applicationinsights_connection_string: SecretStr | None = None
    # Comma-separated preview flags to turn on for this process only (the overlay stays committed
    # with every preview off). Unknown names fail at startup.
    preview_features: Annotated[tuple[str, ...], NoDecode] = ()
    definitions_root: Path = Path("fabric/workspace")
    demos_root: Path = Path("demos")
    simulate_fabric_outage: bool = False
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    log_json: bool = False
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")

    @field_validator("preview_features", mode="before")
    @classmethod
    def _split_flags(cls, value: object) -> object:
        if isinstance(value, str):
            return tuple(flag.strip() for flag in value.split(",") if flag.strip())
        return value

    @field_validator("audit_path", "output_root", mode="before")
    @classmethod
    def _empty_means_unset(cls, value: object) -> object:
        # An empty environment variable means "not set", never the current directory.
        return None if value in ("", None) else value

    @property
    def lakehouse_root(self) -> Path:
        """Return where built Parquet layers live."""
        return self.output_root or self.data_root


class ApiSettings(Settings):
    """Interactive app defaults; CLI demos and tests retain explicit offline settings."""

    environment: str = Field(default="hybrid", pattern=r"^[a-z][a-z0-9-]*$")
    fabric_live: bool = True
    foundry_live: bool = True
