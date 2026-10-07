import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest
from tests.conftest import CONFIG_ROOT

from fabric_foundry_accelerator.audit.store import InMemoryAuditStore
from fabric_foundry_accelerator.config.environment import EnvironmentConfiguration, load_environment
from fabric_foundry_accelerator.fallback.circuit_breaker import BreakerState, CircuitBreaker
from fabric_foundry_accelerator.fallback.router import CapabilityUnavailableError, ProviderRouter
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.providers.errors import UnknownResourceError
from fabric_foundry_accelerator.providers.fabric.local import LocalFabricProvider
from fabric_foundry_accelerator.providers.fabric.outage import SimulatedOutageFabricProvider
from fabric_foundry_accelerator.providers.fabric.routed import RoutedFabricProvider
from fabric_foundry_accelerator.synthetic.pipeline import ValidationReport


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def no_sleep(_: float) -> None:
    return None


# ------------------------------------------------------------------ circuit breaker
def test_breaker_opens_half_opens_and_closes() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker("x", failure_threshold=2, reset_timeout_seconds=10, clock=clock)
    assert breaker.state is BreakerState.CLOSED and breaker.allow()
    breaker.record_failure("a")
    assert breaker.state is BreakerState.CLOSED
    breaker.record_failure("b")
    assert breaker.state is BreakerState.OPEN and not breaker.allow()
    clock.now = 10
    assert breaker.state is BreakerState.HALF_OPEN and breaker.allow()
    breaker.record_failure("probe failed")
    assert breaker.state is BreakerState.OPEN
    clock.now = 20
    breaker.record_success()
    status = breaker.status()
    assert (
        status.state is BreakerState.CLOSED
        and status.consecutive_failures == 0
        and status.last_failure_reason is None
    )


# ------------------------------------------------------------------ router
def _live_envelope(value: int) -> ExecutionEnvelope[int]:
    return ExecutionEnvelope[int](
        operating_mode=OperatingMode.HYBRID,
        execution_label=ExecutionLabel.LIVE,
        requested_provider="live",
        selected_provider="live",
        cloud_operation_performed=True,
        equivalent_fabric_service="Fabric REST",
        teaching_objective="t",
        data=value,
    )


def _local_envelope() -> ExecutionEnvelope[int]:
    return ExecutionEnvelope[int](
        operating_mode=OperatingMode.HYBRID,
        execution_label=ExecutionLabel.LOCAL,
        requested_provider="local",
        selected_provider="local",
        cloud_operation_performed=False,
        equivalent_fabric_service="Fabric REST",
        teaching_objective="t",
        simulation_notice="local",
        data=0,
    )


async def _local() -> ExecutionEnvelope[int]:
    return _local_envelope()


def _router(
    name: str = "hybrid", clock: FakeClock | None = None
) -> tuple[ProviderRouter, InMemoryAuditStore]:
    audit = InMemoryAuditStore()
    return ProviderRouter(
        load_environment(CONFIG_ROOT, name), audit=audit, clock=clock or FakeClock(), sleep=no_sleep
    ), audit


async def _read(
    router: ProviderRouter, live: Callable[[], Awaitable[ExecutionEnvelope[int]]] | None
) -> ExecutionEnvelope[int]:
    return await router.read(
        "fabric_data",
        "op",
        local=_local,
        local_name="local",
        live=live,
        live_name="live" if live else None,
        correlation_id="a" * 32,
    )


async def test_preferred_local_never_calls_live() -> None:
    router, audit = _router("offline")
    called = False

    async def live() -> ExecutionEnvelope[int]:
        nonlocal called
        called = True
        return _live_envelope(1)

    envelope = await _read(router, live)
    assert not called and envelope.execution_label is ExecutionLabel.LOCAL
    assert router.decisions()[-1].outcome == "LOCAL"
    assert audit.recent()[-1].action == "read:op"


async def test_live_success_is_used_and_audited() -> None:
    router, audit = _router()

    async def live() -> ExecutionEnvelope[int]:
        return _live_envelope(7)

    envelope = await _read(router, live)
    assert envelope.data == 7 and envelope.execution_label is ExecutionLabel.LIVE
    assert router.decisions()[-1].outcome == "LIVE"
    assert audit.recent()[-1].cloud_operation_performed is True


async def test_live_recovers_after_a_retry() -> None:
    router, _ = _router()
    attempts = 0

    async def flaky() -> ExecutionEnvelope[int]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionError("transient")
        return _live_envelope(1)

    envelope = await _read(router, flaky)
    assert envelope.execution_label is ExecutionLabel.LIVE
    assert router.decisions()[-1].attempts == 2


async def test_live_failure_falls_back_with_reason_and_opens_breaker() -> None:
    router, _ = _router()
    outage = SimulatedOutageFabricProvider()

    async def live() -> ExecutionEnvelope[int]:
        await outage.list_workspaces()
        raise AssertionError("unreachable")

    results = [await _read(router, live) for _ in range(4)]
    assert all(r.fallback_used and r.operating_mode is OperatingMode.HYBRID for r in results)
    assert all(
        r.execution_label is ExecutionLabel.LOCAL and r.requested_provider == "live"
        for r in results
    )
    assert "simulated outage" in (results[0].fallback_reason or "")
    assert "circuit breaker OPEN" in (results[-1].fallback_reason or "")
    assert (
        outage.calls == 3 * 2
    )  # three failed reads with one retry each; the fourth is short-circuited
    assert router.breaker("fabric_data").state is BreakerState.OPEN
    assert router.decisions()[-1].outcome == "FALLBACK"


async def test_client_errors_propagate_without_fallback_or_breaker_change() -> None:
    router, _ = _router()

    async def live() -> ExecutionEnvelope[int]:
        raise UnknownResourceError("no such table")

    with pytest.raises(UnknownResourceError):
        await _read(router, live)
    assert router.breaker("fabric_data").status().consecutive_failures == 0


async def test_timeout_is_reported() -> None:
    environment = load_environment(CONFIG_ROOT, "hybrid").model_dump()
    environment["capabilities"]["fabric_data"]["timeout_seconds"] = 0.01
    environment["capabilities"]["fabric_data"]["max_retries"] = 0
    router = ProviderRouter(
        EnvironmentConfiguration.model_validate(environment),
        audit=InMemoryAuditStore(),
        sleep=no_sleep,
    )
    hanging = SimulatedOutageFabricProvider(failure="timeout")

    async def live() -> ExecutionEnvelope[int]:
        await hanging.list_workspaces()
        raise AssertionError("unreachable")

    envelope = await _read(router, live)
    assert "timed out after 0.01s" in (envelope.fallback_reason or "")


async def test_no_fallback_means_unavailable() -> None:
    router, audit = _router("live")
    with pytest.raises(CapabilityUnavailableError) as error:
        await _read(router, None)
    assert error.value.decision.outcome == "UNAVAILABLE"
    assert "not configured" in (error.value.decision.failure_reason or "")
    assert audit.recent()[-1].execution_label is ExecutionLabel.UNAVAILABLE


async def test_live_preferred_but_not_configured_falls_back_in_hybrid() -> None:
    router, _ = _router()
    envelope = await _read(router, None)
    assert envelope.fallback_used and "not configured" in (envelope.fallback_reason or "")


async def test_routed_provider_covers_every_operation(
    built: tuple[Path, dict[str, ValidationReport]], data_root: Path
) -> None:
    router, _ = _router()
    local = LocalFabricProvider(data_root, output_root=built[0], mode=OperatingMode.HYBRID)
    routed = RoutedFabricProvider(router, local=local, live=SimulatedOutageFabricProvider())
    lakehouse, model = "local-lh-hc-lab-7file-v1", "local-sm-hc-lab-7file-v1"
    results = await asyncio.gather(
        routed.list_workspaces(),
        routed.list_items("local-ws-synthetic"),
        routed.list_tables(lakehouse),
        routed.read_table(lakehouse, "dim_payer", limit=2),
        routed.get_semantic_model(model),
        routed.evaluate_measures(model, ["claim_count"]),
    )
    assert all(r.fallback_used for r in results)
    assert (
        routed.name == "Provider Router (Fabric)"
        and routed.local is local
        and routed.live is not None
    )
    plain = RoutedFabricProvider(router, local=local, live=None)
    assert (await plain.read_table(lakehouse, "dim_payer", limit=1)).fallback_used
