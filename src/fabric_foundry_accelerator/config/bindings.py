"""Live tenant bindings from ignored environment variables or legacy local YAML.

``config/customers/<overlay>.local.yaml`` maps the overlay's workspace aliases to real Fabric
workspace IDs and pins the tenant. Named Azure, Fabric and Foundry values in ``.env`` override it.
Neither source is committed. Live writes must target an exact, pinned workspace.
"""

import json
import re
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from fabric_foundry_accelerator.config.settings import Settings

GUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


class WorkspaceBinding(BaseModel):
    """A workspace alias bound to a real workspace, with optional item bindings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str = Field(pattern=GUID_PATTERN)
    semantic_models: dict[str, str] = Field(default_factory=dict[str, str])

    @model_validator(mode="after")
    def _ids(self) -> Self:
        import re  # noqa: PLC0415

        bad = [k for k, v in self.semantic_models.items() if not re.match(GUID_PATTERN, v)]
        if bad:
            raise ValueError(f"semantic model ids must be GUIDs: {bad}")
        return self


class FoundryBinding(BaseModel):
    """A Microsoft Foundry resource and project in the presenter's demo subscription."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subscription_id: str = Field(pattern=GUID_PATTERN)
    resource_group: str = Field(min_length=1, max_length=90)
    account: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{1,62}$")
    project: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9-]{1,62}$")
    model_deployments: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    fabric_connection: str | None = None

    @property
    def endpoint(self) -> str:
        """Return the canonical endpoint for the bound resource and project."""
        return f"https://{self.account}.services.ai.azure.com/api/projects/{self.project}"


class TenantBindings(BaseModel):
    """``<overlay>.local.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = Field(pattern=GUID_PATTERN)
    workspaces: dict[str, WorkspaceBinding] = Field(default_factory=dict[str, WorkspaceBinding])
    foundry: FoundryBinding | None = None

    def workspace_id(self, alias: str) -> str | None:
        """Return the workspace ID for an alias, if bound."""
        binding = self.workspaces.get(alias)
        return binding.workspace_id if binding else None


class BindingsError(ValueError):
    """Raised when bindings are missing or do not cover a request."""


def bindings_path(config_root: Path, overlay: str) -> Path:
    """Return the git-ignored bindings path for an overlay."""
    return config_root / "customers" / f"{overlay}.local.yaml"


def load_bindings(
    config_root: Path, overlay: str, *, settings: Settings | None = None
) -> TenantBindings | None:
    """Load private bindings; supplied settings override them with environment values."""
    path = bindings_path(config_root, overlay)
    base = (
        TenantBindings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        if path.is_file()
        else None
    )
    if settings is None:
        return base
    data: dict[str, object] = base.model_dump() if base else {}
    if settings.azure_tenant_id is not None:
        data["tenant_id"] = settings.azure_tenant_id.get_secret_value()
    workspaces = dict(base.workspaces) if base else {}
    try:
        if settings.fabric_workspaces is not None:
            workspaces = TypeAdapter(dict[str, WorkspaceBinding]).validate_json(
                settings.fabric_workspaces.get_secret_value()
            )
        if settings.fabric_workspace_id is not None:
            workspace_id = settings.fabric_workspace_id.get_secret_value()
            previous = workspaces.get(settings.fabric_workspace_alias)
            workspaces[settings.fabric_workspace_alias] = WorkspaceBinding(
                workspace_id=workspace_id,
                semantic_models=previous.semantic_models
                if previous and previous.workspace_id == workspace_id
                else {},
            )
        data["workspaces"] = workspaces
        foundry: dict[str, object] = base.foundry.model_dump() if base and base.foundry else {}
        overrides = {
            "subscription_id": settings.azure_subscription_id,
            "resource_group": settings.azure_resource_group,
            "account": settings.foundry_resource_name,
            "project": settings.foundry_project_name,
            "fabric_connection": settings.fabric_connection_name,
        }
        if foundry or any(
            value is not None for key, value in overrides.items() if key != "subscription_id"
        ):
            foundry.update(
                {
                    key: value.get_secret_value()
                    for key, value in overrides.items()
                    if value is not None
                }
            )
            if settings.foundry_model_deployment is not None:
                foundry["model_deployments"] = (
                    settings.foundry_model_deployment.get_secret_value(),
                )
            if settings.foundry_agent_names is not None:
                foundry["agents"] = TypeAdapter(tuple[str, ...]).validate_json(
                    settings.foundry_agent_names.get_secret_value()
                )
            data["foundry"] = foundry
        if not data.get("tenant_id"):
            if workspaces or foundry or settings.foundry_project_endpoint is not None:
                raise BindingsError("Environment cloud bindings require AZURE_TENANT_ID")
            return None
        resolved = TenantBindings.model_validate(data)
    except ValidationError:
        raise BindingsError(
            "Invalid environment cloud bindings; check variable names and formats."
        ) from None
    if settings.foundry_project_endpoint is not None and (
        resolved.foundry is None
        or settings.foundry_project_endpoint.get_secret_value() != resolved.foundry.endpoint
    ):
        raise BindingsError(
            "FOUNDRY_PROJECT_ENDPOINT must match the configured Foundry resource and project"
        )
    return resolved


def export_environment(bindings: TenantBindings, path: Path = Path(".env")) -> tuple[str, ...]:
    """Populate an ignored environment file from existing bindings without printing values."""
    if path.is_symlink():
        raise BindingsError("Refusing to overwrite a symlinked environment file")
    if bindings.foundry is None:
        raise BindingsError("A Foundry binding is required to populate the environment")
    foundry = bindings.foundry
    primary = bindings.workspaces.get("demo-dev")
    if primary is None or not foundry.model_deployments or not foundry.fabric_connection:
        raise BindingsError(
            "Dev workspace, model deployment and Fabric connection bindings are required"
        )
    values = {
        "FFIA_ENVIRONMENT": "hybrid",
        "FFIA_FABRIC_LIVE": "1",
        "FFIA_FOUNDRY_LIVE": "1",
        "FFIA_ALLOW_LIVE_MUTATION": "0",
        "AZURE_TENANT_ID": bindings.tenant_id,
        "AZURE_SUBSCRIPTION_ID": foundry.subscription_id,
        "AZURE_RESOURCE_GROUP": foundry.resource_group,
        "FABRIC_WORKSPACE_ALIAS": "demo-dev",
        "FABRIC_WORKSPACE_ID": primary.workspace_id,
        "FABRIC_WORKSPACES": json.dumps(
            {key: value.model_dump() for key, value in bindings.workspaces.items()}
        ),
        "FABRIC_CONNECTION_NAME": foundry.fabric_connection,
        "FOUNDRY_RESOURCE_NAME": foundry.account,
        "FOUNDRY_PROJECT_NAME": foundry.project,
        "FOUNDRY_PROJECT_ENDPOINT": foundry.endpoint,
        "FOUNDRY_MODEL_DEPLOYMENT": foundry.model_deployments[0],
        "FOUNDRY_AGENT_NAMES": json.dumps(foundry.agents),
    }
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    retained: list[str] = []
    for line in lines:
        match = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        if match is None or match[1] not in values:
            retained.append(line)
    text = "\n".join(retained).rstrip() + "\n\n"
    text += "\n".join(f"{key}={json.dumps(value)}" for key, value in values.items()) + "\n"
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(text, encoding="utf-8")
    return tuple(values)
