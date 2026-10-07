"""Training fault injector: a stand-in for an unreachable live Fabric endpoint.

Used by the BREAK IT / RECOVER labs and the offline demo to show circuit breakers and fallback.
It never returns data and never contacts any service, so it cannot be mistaken for a real call.
"""

import asyncio
from collections.abc import Sequence
from typing import Literal, NoReturn

from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.providers.errors import ProviderUnavailableError
from fabric_foundry_accelerator.providers.fabric.port import (
    ItemInfo,
    MeasureValue,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)

OUTAGE_MESSAGE = "simulated outage injected for training: the live Fabric endpoint is unreachable"


class SimulatedOutageFabricProvider:
    """Fails every call, either immediately (``error``) or by hanging until timeout."""

    def __init__(self, *, failure: Literal["error", "timeout"] = "error") -> None:
        """Create the injector."""
        self._failure = failure
        self.calls = 0

    @property
    def name(self) -> str:
        """Return the provider name shown in route decisions."""
        return "Fabric REST API (simulated outage)"

    async def _fail(self) -> NoReturn:
        self.calls += 1
        if self._failure == "timeout":
            await asyncio.Event().wait()
        raise ProviderUnavailableError(OUTAGE_MESSAGE)

    async def list_workspaces(
        self, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[WorkspaceInfo, ...]]:
        """Fail."""
        await self._fail()

    async def list_items(
        self, workspace_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[ItemInfo, ...]]:
        """Fail."""
        await self._fail()

    async def list_tables(
        self, lakehouse_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[TableInfo, ...]]:
        """Fail."""
        await self._fail()

    async def read_table(
        self, lakehouse_id: str, table: str, *, limit: int = 20, correlation_id: str | None = None
    ) -> ExecutionEnvelope[TablePreview]:
        """Fail."""
        await self._fail()

    async def get_semantic_model(
        self, semantic_model_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[SemanticModel]:
        """Fail."""
        await self._fail()

    async def evaluate_measures(
        self,
        semantic_model_id: str,
        measures: Sequence[str] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[tuple[MeasureValue, ...]]:
        """Fail."""
        await self._fail()
