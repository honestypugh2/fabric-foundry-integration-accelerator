"""Runtime overlay for architecture views: what each bound node is doing right now.

The frontend colors diagram nodes from this report; it never infers state on its own. Nodes that
belong to later phases report NOT CONFIGURED, so a diagram never implies a live connection that
does not exist.
"""

from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.education.diagrams import DiagramView, RuntimeBinding
from fabric_foundry_accelerator.fallback.circuit_breaker import BreakerState
from fabric_foundry_accelerator.models.execution import OperatingMode, utc_now
from fabric_foundry_accelerator.providers.fabric.live import NOT_CONFIGURED_NOTE
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.runtime import RuntimeStatus, runtime_status

NodeStatus = Literal["ACTIVE", "READY", "DEGRADED", "UNAVAILABLE", "NOT CONFIGURED"]


class NodeRuntime(BaseModel):
    """The live state of one diagram node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    node: str
    binding: RuntimeBinding
    status: NodeStatus
    label: str
    detail: str


class ViewRuntime(BaseModel):
    """The runtime overlay for one view."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    view_id: str
    operating_mode: OperatingMode
    observed_at: str
    nodes: tuple[NodeRuntime, ...]


def _fabric_live(container: Container, status: RuntimeStatus) -> tuple[NodeStatus, str, str]:
    live = container.fabric.live
    if live is None:
        return (
            "NOT CONFIGURED",
            "UNAVAILABLE",
            NOT_CONFIGURED_NOTE,
        )
    breaker = next((b for b in status.breakers if b.name == "fabric_data"), None)
    if "simulated outage" in live.name:
        state = breaker.state.value if breaker else "CLOSED"
        return "DEGRADED", "FAULT-INJECTION", f"Training outage injected; breaker {state}."
    if breaker is not None and breaker.state is not BreakerState.CLOSED:
        return (
            "DEGRADED",
            "LIVE",
            f"Breaker {breaker.state.value}: reads use the approved fallback.",
        )
    return "READY", "LIVE", f"{live.name}: configured (calls are made on demand, not probed here)."


Overlay = tuple[NodeStatus, str, str]


def _api(_: Container, status: RuntimeStatus) -> Overlay:
    return "ACTIVE", "LOCAL", f"Serving this request in {status.operating_mode} mode."


def _mcp(_: Container, status: RuntimeStatus) -> Overlay:
    return "READY", "LOCAL", f"{status.mcp}; each harness starts it over stdio."


def _fabric_local(container: Container, status: RuntimeStatus) -> Overlay:
    if not status.built_profiles:
        return "UNAVAILABLE", "LOCAL", "No synthetic lakehouse is built. Run make data."
    role = "Primary" if container.fabric.live is None else "Approved fallback"
    return "ACTIVE", "LOCAL", f"{role} provider; profiles: {', '.join(status.built_profiles)}."


def _foundry(container: Container, __: RuntimeStatus) -> Overlay:
    live = container.agents.live
    if live is None:
        return (
            "NOT CONFIGURED",
            "UNAVAILABLE",
            "Live Foundry is opt-in (FFIA_FOUNDRY_LIVE=1); the LOCAL sales agent answers offline instead.",
        )
    return "READY", "LIVE", f"{live.name}: configured (called on demand, not probed here)."


def _router(container: Container, status: RuntimeStatus) -> Overlay:
    breakers = (
        ", ".join(f"{b.name} {b.state.value}" for b in status.breakers) or "no breaker tripped"
    )
    return "ACTIVE", "LOCAL", f"{container.environment.name} policy; {breakers}."


def _changes(container: Container, status: RuntimeStatus) -> Overlay:
    plans = len(container.changes.plans())
    return "ACTIVE", "SIMULATED", f"{plans} plans in this process. {status.write_mode}."


def _audit(container: Container, _: RuntimeStatus) -> Overlay:
    return "ACTIVE", "LOCAL", f"{len(container.audit.recent(500))} recent records."


def _education(container: Container, _: RuntimeStatus) -> Overlay:
    library = container.education.library
    return (
        "ACTIVE",
        "LOCAL",
        f"{len(library.lessons)} lessons, {len(library.views)} architecture views.",
    )


def _evaluation(_: Container, __: RuntimeStatus) -> Overlay:
    return "READY", "LOCAL", "Compares measures with the expected baselines."


_BINDINGS: dict[RuntimeBinding, Callable[[Container, RuntimeStatus], Overlay]] = {
    "api": _api,
    "mcp": _mcp,
    "fabric-local": _fabric_local,
    "fabric-live": _fabric_live,
    "foundry": _foundry,
    "router": _router,
    "changes": _changes,
    "audit": _audit,
    "education": _education,
    "evaluation": _evaluation,
}


def view_runtime(container: Container, view: DiagramView) -> ViewRuntime:
    """Return the live state of every runtime-bound node in a view."""
    status = runtime_status(container)
    nodes: list[NodeRuntime] = []
    for node in view.nodes:
        if node.runtime is None:
            continue
        state, label, detail = _BINDINGS[node.runtime](container, status)
        nodes.append(
            NodeRuntime(
                node=node.id, binding=node.runtime, status=state, label=label, detail=detail
            )
        )
    return ViewRuntime(
        view_id=view.id,
        operating_mode=status.operating_mode,
        observed_at=utc_now().isoformat(),
        nodes=tuple(nodes),
    )
