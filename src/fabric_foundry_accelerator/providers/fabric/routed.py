"""Fabric provider that routes every read through the ``ProviderRouter``."""

from collections.abc import Sequence

from fabric_foundry_accelerator.fallback.router import ProviderRouter
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope, new_correlation_id
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.providers.fabric.port import (
    FabricProvider,
    ItemInfo,
    MeasureValue,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)


class RoutedFabricProvider:
    """``FabricProvider`` that prefers a live provider and falls back per policy."""

    def __init__(
        self, router: ProviderRouter, *, local: FabricProvider, live: FabricProvider | None
    ) -> None:
        """Create a routed provider."""
        self._router = router
        self._local = local
        self._live = live

    @property
    def name(self) -> str:
        """Return the provider name."""
        return "Provider Router (Fabric)"

    @property
    def live(self) -> FabricProvider | None:
        """Return the configured live provider, if any."""
        return self._live

    @property
    def local(self) -> FabricProvider:
        """Return the local provider."""
        return self._local

    async def list_workspaces(
        self, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[WorkspaceInfo, ...]]:
        """List workspaces."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "fabric_data",
            "list_workspaces",
            local=lambda: self._local.list_workspaces(correlation_id=cid),
            local_name=self._local.name,
            live=(lambda: live.list_workspaces(correlation_id=cid)) if live else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )

    async def list_items(
        self, workspace_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[ItemInfo, ...]]:
        """List items in a workspace."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "fabric_data",
            "list_items",
            local=lambda: self._local.list_items(workspace_id, correlation_id=cid),
            local_name=self._local.name,
            live=(lambda: live.list_items(workspace_id, correlation_id=cid)) if live else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )

    async def list_tables(
        self, lakehouse_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[TableInfo, ...]]:
        """List tables in a lakehouse."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "fabric_data",
            "list_tables",
            local=lambda: self._local.list_tables(lakehouse_id, correlation_id=cid),
            local_name=self._local.name,
            live=(lambda: live.list_tables(lakehouse_id, correlation_id=cid)) if live else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )

    async def read_table(
        self,
        lakehouse_id: str,
        table: str,
        *,
        limit: int = 20,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[TablePreview]:
        """Return a bounded table preview."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "fabric_data",
            "read_table",
            local=lambda: self._local.read_table(
                lakehouse_id, table, limit=limit, correlation_id=cid
            ),
            local_name=self._local.name,
            live=(lambda: live.read_table(lakehouse_id, table, limit=limit, correlation_id=cid))
            if live
            else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )

    async def get_semantic_model(
        self, semantic_model_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[SemanticModel]:
        """Return a semantic model definition."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "semantic_model",
            "get_semantic_model",
            local=lambda: self._local.get_semantic_model(semantic_model_id, correlation_id=cid),
            local_name=self._local.name,
            live=(lambda: live.get_semantic_model(semantic_model_id, correlation_id=cid))
            if live
            else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )

    async def evaluate_measures(
        self,
        semantic_model_id: str,
        measures: Sequence[str] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[tuple[MeasureValue, ...]]:
        """Evaluate declared measures."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        return await self._router.read(
            "semantic_model",
            "evaluate_measures",
            local=lambda: self._local.evaluate_measures(
                semantic_model_id, measures, correlation_id=cid
            ),
            local_name=self._local.name,
            live=(lambda: live.evaluate_measures(semantic_model_id, measures, correlation_id=cid))
            if live
            else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )
