"""Circuit breaker: stop hammering a failing live provider during a demo or in production.

CLOSED -> (failure_threshold consecutive failures) -> OPEN -> (reset timeout) -> HALF_OPEN ->
success -> CLOSED, or failure -> OPEN.
"""

import time
from collections.abc import Callable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class BreakerState(StrEnum):
    """Circuit breaker state."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class BreakerStatus(BaseModel):
    """A point-in-time view of a breaker."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    state: BreakerState
    consecutive_failures: int
    failure_threshold: int
    last_failure_reason: str | None


class CircuitBreaker:
    """A small, deterministic circuit breaker with an injectable clock."""

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int,
        reset_timeout_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a closed breaker."""
        self.name = name
        self._threshold = failure_threshold
        self._reset_timeout = reset_timeout_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self._last_reason: str | None = None

    @property
    def state(self) -> BreakerState:
        """Return the current state (OPEN becomes HALF_OPEN once the reset timeout elapses)."""
        if self._opened_at is None:
            return BreakerState.CLOSED
        if self._clock() - self._opened_at >= self._reset_timeout:
            return BreakerState.HALF_OPEN
        return BreakerState.OPEN

    def allow(self) -> bool:
        """Return True when a call may be attempted."""
        return self.state is not BreakerState.OPEN

    def record_success(self) -> None:
        """Close the breaker."""
        self._failures = 0
        self._opened_at = None
        self._last_reason = None

    def record_failure(self, reason: str) -> None:
        """Count a failure; open the breaker at the threshold or on a failed half-open probe."""
        self._last_reason = reason
        if self.state is BreakerState.HALF_OPEN:
            self._opened_at = self._clock()
            return
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._clock()

    def status(self) -> BreakerStatus:
        """Return a snapshot of the breaker."""
        return BreakerStatus(
            name=self.name,
            state=self.state,
            consecutive_failures=self._failures,
            failure_threshold=self._threshold,
            last_failure_reason=self._last_reason,
        )
