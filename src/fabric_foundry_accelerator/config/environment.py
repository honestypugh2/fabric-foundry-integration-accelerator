"""Environment configuration: per-capability provider preference, fallback policy and limits."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import OperatingMode

Capability = Literal[
    "fabric_data", "semantic_model", "foundry_agent", "knowledge", "mcp", "evaluation", "audit"
]


class CapabilityPolicy(BaseModel):
    """How one capability is routed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    preferred: Literal["live", "local"]
    fallback: Literal["local", "none"]
    timeout_seconds: float = Field(default=5.0, gt=0, le=300)
    max_retries: int = Field(default=1, ge=0, le=3)
    backoff_seconds: float = Field(default=0.2, ge=0, le=5)


class CircuitBreakerPolicy(BaseModel):
    """Circuit breaker thresholds shared by live providers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    failure_threshold: int = Field(default=3, ge=1, le=20)
    reset_timeout_seconds: float = Field(default=60.0, gt=0, le=3600)


class EnvironmentConfiguration(BaseModel):
    """A named environment profile (``config/environments/<name>.yaml``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    mode: OperatingMode
    description: str
    capabilities: dict[Capability, CapabilityPolicy]
    circuit_breaker: CircuitBreakerPolicy = CircuitBreakerPolicy()

    def policy(self, capability: Capability) -> CapabilityPolicy:
        """Return the policy for a capability (local-only when not configured)."""
        return self.capabilities.get(
            capability, CapabilityPolicy(preferred="local", fallback="none")
        )


def load_environment(config_root: Path, name: str) -> EnvironmentConfiguration:
    """Load ``config/environments/<name>.yaml``."""
    path = config_root / "environments" / f"{name}.yaml"
    return EnvironmentConfiguration.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
