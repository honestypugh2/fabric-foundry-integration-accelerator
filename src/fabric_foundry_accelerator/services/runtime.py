"""Runtime status: what the UI status bar, the API and the MCP server report about execution state."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.fallback.circuit_breaker import BreakerStatus
from fabric_foundry_accelerator.fallback.router import RouteDecision
from fabric_foundry_accelerator.models.execution import OperatingMode
from fabric_foundry_accelerator.providers.fabric.live import NOT_CONFIGURED_NOTE
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.synthetic.medallion import lakehouse_tables
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

ProviderKind = Literal["LIVE", "LOCAL", "FAULT-INJECTION", "NOT AVAILABLE"]


class ProviderStatus(BaseModel):
    """One provider and its readiness."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability: str
    name: str
    kind: ProviderKind
    configured: bool
    ready: bool
    note: str


class RuntimeStatus(BaseModel):
    """Execution state shown everywhere (never implies a live connection that does not exist)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operating_mode: OperatingMode
    environment: str
    overlay: str
    data_provider: str
    agent_provider: str
    mcp: str
    identity: str
    write_mode: str
    preview_features: tuple[str, ...]
    providers: tuple[ProviderStatus, ...]
    breakers: tuple[BreakerStatus, ...]
    recent_route_decisions: tuple[RouteDecision, ...]
    built_profiles: tuple[str, ...]


def provider_statuses(container: Container) -> tuple[ProviderStatus, ...]:
    """Return provider readiness for every capability."""
    live = container.fabric.live
    built = [p for p in sorted(PROFILES) if lakehouse_tables(container.settings.lakehouse_root, p)]
    statuses = [
        ProviderStatus(
            capability="fabric_data",
            name=container.local_fabric.name,
            kind="LOCAL",
            configured=True,
            ready=bool(built),
            note=f"Synthetic lakehouses built: {', '.join(built) or 'none'}",
        )
    ]
    if live is not None:
        injected = "simulated outage" in live.name
        statuses.append(
            ProviderStatus(
                capability="fabric_data",
                name=live.name,
                kind="FAULT-INJECTION" if injected else "LIVE",
                configured=True,
                ready=not injected and container.router.breaker("fabric_data").allow(),
                note="Training fault injector: every call fails."
                if injected
                else "Live Fabric provider configured; health is not probed here. Inspect route evidence.",
            )
        )
    else:
        statuses.append(
            ProviderStatus(
                capability="fabric_data",
                name="Fabric REST (application provider)",
                kind="NOT AVAILABLE",
                configured=False,
                ready=False,
                note=NOT_CONFIGURED_NOTE,
            )
        )
    statuses.append(
        ProviderStatus(
            capability="foundry_agent",
            name=container.agents.local.name,
            kind="LOCAL",
            configured=True,
            ready=True,
            note="Deterministic, allow-listed questions over synthetic manufacturing data.",
        )
    )
    live_agent = container.agents.live
    statuses.append(
        ProviderStatus(
            capability="foundry_agent",
            name=live_agent.name if live_agent else "Foundry Agent Service",
            kind="LIVE" if live_agent else "NOT AVAILABLE",
            configured=live_agent is not None,
            ready=live_agent is not None,
            note="Existing Foundry agent configured; health is not probed here. Inspect route evidence."
            if live_agent
            else "Opt in with FFIA_FOUNDRY_LIVE=1, a hybrid or live environment and a `foundry:` binding; "
            "check with `ffia foundry readiness`.",
        )
    )
    return tuple(statuses)


def runtime_status(container: Container) -> RuntimeStatus:
    """Return the current runtime status."""
    settings = container.settings
    writer = container.changes.live_writer
    live_writes = (
        f"LIVE writes after approval by the {writer.name} (create_lakehouse, create_notebook only)"
        if writer is not None and settings.allow_live_mutation
        else "LIVE writes enabled by flag but no live writer is configured"
        if settings.allow_live_mutation
        else "LIVE writes disabled"
    )
    return RuntimeStatus(
        operating_mode=container.mode,
        environment=container.environment.name,
        overlay=container.overlay.alias,
        data_provider=(
            "Local Fabric Educational Provider (LOCAL)"
            if container.fabric.live is None
            else f"Router: {container.fabric.live.name} with LOCAL fallback per policy"
        ),
        agent_provider=(
            f"{container.agents.local.name} (LOCAL)"
            if container.agents.live is None
            else f"Router: {container.agents.live.name} with LOCAL fallback per policy"
        ),
        mcp=f"Local server ready: {len(container.tool_manifest.enabled())} allow-listed tools",
        identity=(
            "Azure CLI user, delegated, pinned to the bound tenant (configured, not probed here)"
            if container.bindings is not None
            and (container.settings.fabric_live or container.settings.foundry_live)
            else "Local process (no cloud identity in use)"
        ),
        write_mode=f"Approval required; LOCAL executions are SIMULATED; {live_writes}",
        preview_features=tuple(container.overlay.enabled_previews()),
        providers=provider_statuses(container),
        breakers=tuple(b.status() for b in container.router.breakers()),
        recent_route_decisions=tuple(container.router.decisions()[-20:]),
        built_profiles=tuple(
            p for p in sorted(PROFILES) if lakehouse_tables(settings.lakehouse_root, p)
        ),
    )
