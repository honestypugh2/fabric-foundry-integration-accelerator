"""Live tenant bindings: the only place real identifiers live, in a git-ignored local file.

``config/customers/<overlay>.local.yaml`` maps the overlay's workspace aliases to real Fabric
workspace IDs and pins the tenant. It is ignored by Git (``*.local.yaml``) and never committed.
Without it, live reads and writes refuse to run: a write must target an exact, pinned workspace.
"""

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class TenantBindings(BaseModel):
    """``<overlay>.local.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = Field(pattern=GUID_PATTERN)
    workspaces: dict[str, WorkspaceBinding] = Field(default_factory=dict[str, WorkspaceBinding])

    def workspace_id(self, alias: str) -> str | None:
        """Return the workspace ID for an alias, if bound."""
        binding = self.workspaces.get(alias)
        return binding.workspace_id if binding else None


class BindingsError(ValueError):
    """Raised when bindings are missing or do not cover a request."""


def bindings_path(config_root: Path, overlay: str) -> Path:
    """Return the git-ignored bindings path for an overlay."""
    return config_root / "customers" / f"{overlay}.local.yaml"


def load_bindings(config_root: Path, overlay: str) -> TenantBindings | None:
    """Load bindings, or return None when the local file does not exist."""
    path = bindings_path(config_root, overlay)
    if not path.is_file():
        return None
    return TenantBindings.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
