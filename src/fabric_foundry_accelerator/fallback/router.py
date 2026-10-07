"""Provider router: probe live, bound retries, trip breakers, apply the approved fallback policy.

Reads may fall back to an approved LOCAL equivalent; the returned envelope then carries
``fallback_used=True``, the reason, and ``operating_mode=HYBRID``. Request errors (unknown
resource, invalid input) are never retried and never trigger fallback. Writes are not routed
here: an approved LIVE write is never redirected to LOCAL (see ``services.changes``).
"""

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from tenacity import (
    AsyncRetrying,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from fabric_foundry_accelerator.audit.store import (
    AuditRecord,
    AuditStore,
    audit_from_envelope,
    elapsed_ms,
)
from fabric_foundry_accelerator.config.environment import Capability, EnvironmentConfiguration
from fabric_foundry_accelerator.fallback.circuit_breaker import BreakerState, CircuitBreaker
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    utc_now,
)
from fabric_foundry_accelerator.observability.redaction import redact_text
from fabric_foundry_accelerator.providers.errors import CLIENT_ERRORS, ProviderError

Outcome = Literal["LIVE", "LOCAL", "FALLBACK", "UNAVAILABLE"]


class RouteDecision(BaseModel):
    """Why a request went where it went."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability: str
    operation: str
    correlation_id: str
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    requested_provider: str
    selected_provider: str
    operating_mode: OperatingMode
    outcome: Outcome
    attempts: int
    failure_reason: str | None = None
    fallback_reason: str | None = None
    breaker_state: BreakerState | None = None


class CapabilityUnavailableError(ProviderError):
    """Raised when neither the live provider nor an approved fallback can serve a read."""

    def __init__(self, decision: RouteDecision) -> None:
        """Create the error with the route decision attached."""
        super().__init__(
            f"{decision.capability} unavailable: {decision.failure_reason or 'no provider'}"
        )
        self.decision = decision


class ProviderRouter:
    """Routes reads per capability using the environment's policy."""

    def __init__(
        self,
        environment: EnvironmentConfiguration,
        *,
        audit: AuditStore,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        history: int = 200,
    ) -> None:
        """Create a router."""
        self._environment = environment
        self._audit = audit
        self._clock = clock
        self._sleep = sleep
        self._breakers: dict[str, CircuitBreaker] = {}
        self._decisions: deque[RouteDecision] = deque(maxlen=history)

    @property
    def environment(self) -> EnvironmentConfiguration:
        """Return the active environment configuration."""
        return self._environment

    def breaker(self, capability: Capability) -> CircuitBreaker:
        """Return (creating if needed) the breaker for a capability."""
        if capability not in self._breakers:
            policy = self._environment.circuit_breaker
            self._breakers[capability] = CircuitBreaker(
                capability,
                failure_threshold=policy.failure_threshold,
                reset_timeout_seconds=policy.reset_timeout_seconds,
                clock=self._clock,
            )
        return self._breakers[capability]

    def breakers(self) -> list[CircuitBreaker]:
        """Return all created breakers."""
        return list(self._breakers.values())

    def decisions(self) -> list[RouteDecision]:
        """Return recent route decisions, oldest first."""
        return list(self._decisions)

    async def read[T](
        self,
        capability: Capability,
        operation: str,
        *,
        local: Callable[[], Awaitable[ExecutionEnvelope[T]]],
        local_name: str,
        live: Callable[[], Awaitable[ExecutionEnvelope[T]]] | None,
        live_name: str | None,
        correlation_id: str,
        actor: str = "system",
    ) -> ExecutionEnvelope[T]:
        """Serve a read through the live provider or the approved fallback."""
        policy = self._environment.policy(capability)
        started = utc_now()
        if policy.preferred == "local":
            envelope = await local()
            self._remember(
                RouteDecision(
                    capability=capability,
                    operation=operation,
                    correlation_id=correlation_id,
                    requested_provider=local_name,
                    selected_provider=local_name,
                    operating_mode=envelope.operating_mode,
                    outcome="LOCAL",
                    attempts=0,
                )
            )
            self._audit_envelope(envelope, actor, operation, capability, started)
            return envelope

        requested = live_name or "live provider (not configured)"
        failure, attempts = "live provider is not configured", 0
        if live is not None:
            breaker = self.breaker(capability)
            if not breaker.allow():
                last = breaker.status().last_failure_reason
                failure = f"circuit breaker OPEN after repeated failures ({last})"
            else:
                retrying = self._retrying(policy.max_retries, policy.backoff_seconds)
                try:
                    envelope, attempts = await self._call_live(
                        live, retrying, policy.timeout_seconds
                    )
                except CLIENT_ERRORS:
                    raise
                except Exception as error:  # noqa: BLE001 - controlled translation boundary: any live failure becomes a recorded route decision
                    attempts = policy.max_retries + 1
                    failure = _describe(error, policy.timeout_seconds)
                    breaker.record_failure(failure)
                else:
                    breaker.record_success()
                    self._remember(
                        RouteDecision(
                            capability=capability,
                            operation=operation,
                            correlation_id=correlation_id,
                            requested_provider=requested,
                            selected_provider=requested,
                            operating_mode=envelope.operating_mode,
                            outcome="LIVE",
                            attempts=attempts,
                            breaker_state=breaker.state,
                        )
                    )
                    self._audit_envelope(envelope, actor, operation, capability, started)
                    return envelope

        state = self._breakers[capability].state if capability in self._breakers else None
        if policy.fallback == "none":
            decision = self._remember(
                RouteDecision(
                    capability=capability,
                    operation=operation,
                    correlation_id=correlation_id,
                    requested_provider=requested,
                    selected_provider="none",
                    operating_mode=self._environment.mode,
                    outcome="UNAVAILABLE",
                    attempts=attempts,
                    failure_reason=failure,
                    breaker_state=state,
                )
            )
            self._audit.record(_unavailable_record(decision, actor))
            raise CapabilityUnavailableError(decision)

        reason = f"Live provider unavailable ({failure}); served by the approved LOCAL fallback."
        local_envelope = await local()
        envelope = local_envelope.model_copy(
            update={
                "fallback_used": True,
                "fallback_reason": reason,
                "requested_provider": requested,
                "operating_mode": OperatingMode.HYBRID,
            }
        )
        self._remember(
            RouteDecision(
                capability=capability,
                operation=operation,
                correlation_id=correlation_id,
                requested_provider=requested,
                selected_provider=local_name,
                operating_mode=OperatingMode.HYBRID,
                outcome="FALLBACK",
                attempts=attempts,
                failure_reason=failure,
                fallback_reason=reason,
                breaker_state=state,
            )
        )
        self._audit_envelope(envelope, actor, operation, capability, started)
        return envelope

    def _retrying(self, retries: int, backoff: float) -> AsyncRetrying:
        # Built before the live call so configuration errors are never mistaken for outages.
        return AsyncRetrying(
            stop=stop_after_attempt(retries + 1),
            wait=wait_exponential_jitter(
                multiplier=max(backoff, 0.001), max=max(backoff * 8, 0.001), jitter=backoff
            ),
            retry=retry_if_not_exception_type(CLIENT_ERRORS),
            reraise=True,
            sleep=self._sleep,
        )

    async def _call_live[T](
        self,
        live: Callable[[], Awaitable[ExecutionEnvelope[T]]],
        retrying: AsyncRetrying,
        timeout: float,
    ) -> tuple[ExecutionEnvelope[T], int]:
        attempts = 0
        async for attempt in retrying:
            with attempt:
                attempts += 1
                async with asyncio.timeout(timeout):
                    return await live(), attempts
        raise AssertionError("unreachable")  # pragma: no cover - tenacity always returns or raises

    def _remember(self, decision: RouteDecision) -> RouteDecision:
        self._decisions.append(decision)
        return decision

    def _audit_envelope[T](
        self,
        envelope: ExecutionEnvelope[T],
        actor: str,
        operation: str,
        capability: str,
        started: datetime,
    ) -> None:
        record = audit_from_envelope(
            envelope,
            actor=actor,
            action=f"read:{operation}",
            capability=capability,
            duration_ms=elapsed_ms(started),
        )
        self._audit.record(record)


def _describe(error: BaseException, timeout: float) -> str:
    if isinstance(error, TimeoutError):
        return f"timed out after {timeout:g}s"
    return f"{type(error).__name__}: {redact_text(str(error))}"


def _unavailable_record(decision: RouteDecision, actor: str) -> AuditRecord:
    return AuditRecord(
        correlation_id=decision.correlation_id,
        actor=actor,
        action=f"read:{decision.operation}",
        capability=decision.capability,
        requested_provider=decision.requested_provider,
        selected_provider=decision.selected_provider,
        operating_mode=decision.operating_mode,
        execution_label=ExecutionLabel.UNAVAILABLE,
        cloud_operation_performed=False,
        success=False,
        details={"failure_reason": decision.failure_reason, "attempts": decision.attempts},
    )
