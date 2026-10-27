"""HTTP adapters for runtime; domain behavior stays in services/providers."""

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.api.dependencies import ContainerDep
from fabric_foundry_accelerator.services.runtime import (
    ProviderStatus,
    RuntimeStatus,
    provider_statuses,
    runtime_status,
)

router = APIRouter()


class Health(BaseModel):
    """Liveness."""

    model_config = ConfigDict(frozen=True)

    status: str


class Readiness(BaseModel):
    """Readiness with the checks behind it."""

    model_config = ConfigDict(frozen=True)

    ready: bool
    checks: dict[str, bool]


class Capability(BaseModel):
    """A capability and how it is currently served."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    served_by: str


@router.get("/health", tags=["health"])
def health() -> Health:
    """Liveness probe."""
    return Health(status="ok")


@router.get("/ready", tags=["health"])
def ready(container: ContainerDep, response: Response) -> Readiness:
    """Readiness probe: local data built, guides and MCP manifest loaded."""
    checks = {
        "local_lakehouse_built": bool(runtime_status(container).built_profiles),
        "guides_loaded": bool(container.guides),
        "mcp_manifest_loaded": bool(container.tool_manifest.enabled()),
    }
    is_ready = all(checks.values())
    response.status_code = 200 if is_ready else 503
    return Readiness(ready=is_ready, checks=checks)


@router.get("/api/v1/runtime/status", tags=["runtime"])
def get_runtime_status(container: ContainerDep) -> RuntimeStatus:
    """Execution state for the status bar."""
    return runtime_status(container)


@router.get("/api/v1/runtime/providers", tags=["runtime"])
def get_providers(container: ContainerDep) -> list[ProviderStatus]:
    """Provider readiness per capability."""
    return list(provider_statuses(container))


@router.get("/api/v1/capabilities", tags=["runtime"])
def get_capabilities(container: ContainerDep) -> list[Capability]:
    """What the control plane can do and what serves each capability."""
    status = runtime_status(container)
    return [
        Capability(
            name="fabric_read",
            description="Typed, bounded reads of workspaces, items, tables and measures.",
            served_by=status.data_provider,
        ),
        Capability(
            name="change_plans",
            description="Plan, approve and execute changes under policy.",
            served_by="Change service (LOCAL simulated; LIVE unavailable)",
        ),
        Capability(
            name="recovery_drill",
            description="Open Mirroring snapshot and replay drill.",
            served_by="Local Open Mirroring Simulator (SIMULATED)",
        ),
        Capability(
            name="evaluation",
            description="Compare measures with expected baselines.",
            served_by="Baseline Evaluator (LOCAL)",
        ),
        Capability(name="mcp", description="Allow-listed MCP tools.", served_by=status.mcp),
        Capability(
            name="agents",
            description="Foundry agents and Agent Framework workflows.",
            served_by=status.agent_provider,
        ),
    ]
