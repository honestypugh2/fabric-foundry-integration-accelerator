"""Live, read-only Fabric provider over the Fabric REST API and Power BI ``executeQueries``.

What it can read live: workspaces, items (lakehouses and semantic models), lakehouse tables, and
semantic-model measures through DAX. Fabric REST has no row-preview or model-definition read, so
those raise a clear client error instead of being faked or silently served from local data.
Every result is labeled LIVE (PREVIEW for preview APIs) with ``cloud_operation_performed=True``.
"""

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from fabric_foundry_accelerator.config.bindings import TenantBindings
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.models.semantic import SemanticModel, load_semantic_model
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError
from fabric_foundry_accelerator.providers.fabric.port import (
    ItemInfo,
    MeasureValue,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient
from fabric_foundry_accelerator.synthetic.paths import semantic_model_path

PROVIDER_NAME = "Fabric REST API (live)"
NOT_CONFIGURED_NOTE = (
    "No live Fabric provider configured. Opt in with FFIA_FABRIC_LIVE=1, a hybrid or live "
    "environment and the local bindings file; check the tenant with `ffia fabric readiness`."
)
ITEM_TYPES = ("Lakehouse", "SemanticModel")
MEASURE_CONCURRENCY = 4


def _layer(table: str) -> str:
    for prefix, layer in (
        ("bronze_", "bronze"),
        ("silver_", "silver"),
        ("gold_", "gold"),
        ("dim_", "gold"),
        ("fact_", "gold"),
    ):
        if table.startswith(prefix):
            return layer
    return "unclassified"


class LiveFabricProvider:
    """``FabricProvider`` backed by the live tenant, scoped to the bound tenant and workspaces."""

    def __init__(
        self,
        client: FabricRestClient,
        bindings: TenantBindings,
        *,
        data_root: Path,
        mode: OperatingMode,
    ) -> None:
        """Create a live provider. ``mode`` must be HYBRID or LIVE."""
        if mode is OperatingMode.OFFLINE:
            raise ValueError("the live Fabric provider cannot run in OFFLINE mode")
        self._client = client
        self._bindings = bindings
        self._data_root = data_root
        self._mode = mode
        self._item_workspace: dict[str, str] = {}

    @property
    def name(self) -> str:
        """Return the provider name."""
        return PROVIDER_NAME

    def _envelope[T](
        self,
        data: T,
        *,
        service: str,
        objective: str,
        correlation_id: str | None,
        label: ExecutionLabel = ExecutionLabel.LIVE,
    ) -> ExecutionEnvelope[T]:
        return ExecutionEnvelope[T](
            operating_mode=self._mode,
            execution_label=label,
            requested_provider=PROVIDER_NAME,
            selected_provider=PROVIDER_NAME,
            cloud_operation_performed=True,
            equivalent_fabric_service=service,
            teaching_objective=objective,
            data=data,
            correlation_id=correlation_id or new_correlation_id(),
        )

    async def list_workspaces(
        self, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[WorkspaceInfo, ...]]:
        """List workspaces the signed-in user can access."""
        rows = await self._client.get_all("/workspaces")
        data = tuple(
            WorkspaceInfo(
                id=str(r["id"]),
                display_name=str(r.get("displayName", "")),
                description=str(r.get("description", "")),
            )
            for r in rows
        )
        return self._envelope(
            data,
            service="Fabric REST: List Workspaces",
            objective="What the user can see.",
            correlation_id=correlation_id,
        )

    async def list_items(
        self, workspace_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[ItemInfo, ...]]:
        """List lakehouses and semantic models in a workspace."""
        rows = await self._client.get_all(f"/workspaces/{workspace_id}/items")
        items: list[ItemInfo] = []
        for row in rows:
            kind = str(row.get("type", ""))
            if kind not in ITEM_TYPES:
                continue
            item = ItemInfo(
                id=str(row["id"]),
                display_name=str(row.get("displayName", "")),
                type=cast("Any", kind),
                workspace_id=workspace_id,
                description=str(row.get("description", "")),
            )
            self._item_workspace[item.id] = workspace_id
            items.append(item)
        return self._envelope(
            tuple(items),
            service="Fabric REST: List Items",
            objective="Find governed items.",
            correlation_id=correlation_id,
        )

    async def _workspace_for(self, item_id: str) -> str:
        cached = self._item_workspace.get(item_id)
        if cached:
            return cached
        for binding in self._bindings.workspaces.values():
            rows = await self._client.get_all(f"/workspaces/{binding.workspace_id}/items")
            for row in rows:
                self._item_workspace[str(row["id"])] = binding.workspace_id
            if item_id in self._item_workspace:
                return self._item_workspace[item_id]
        raise UnknownResourceError(f"item {item_id!r} is not in any bound workspace")

    async def list_tables(
        self, lakehouse_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[TableInfo, ...]]:
        """List lakehouse tables (row counts and columns are not part of this API).

        The List Tables API is documented as preview and does not support schema-enabled
        lakehouses (the Fabric MCP ``onelake_list-tables`` tool covers those), so results are
        labeled PREVIEW even though the call is live.
        """
        workspace_id = await self._workspace_for(lakehouse_id)
        rows = await self._client.get_all(
            f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/tables", key="data"
        )
        data = tuple(
            TableInfo(name=str(r["name"]), layer=_layer(str(r["name"])), row_count=None, columns=())
            for r in rows
        )
        return self._envelope(
            data,
            service="Fabric REST: Lakehouse List Tables (preview API)",
            objective="See which Delta tables exist.",
            correlation_id=correlation_id,
            label=ExecutionLabel.PREVIEW,
        )

    async def read_table(
        self, lakehouse_id: str, table: str, *, limit: int = 20, correlation_id: str | None = None
    ) -> ExecutionEnvelope[TablePreview]:
        """Row previews are not available through Fabric REST."""
        raise InvalidRequestError(
            "Row previews are not available through the Fabric REST API. Query the lakehouse SQL "
            "analytics endpoint (for example through the Data Warehouse MCP server, preview) or "
            "preview the synthetic data offline."
        )

    async def get_semantic_model(
        self, semantic_model_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[SemanticModel]:
        """Model definitions are not read by this provider."""
        raise InvalidRequestError(
            "Reading semantic model definitions is not part of this read-only provider. Use the "
            "Power BI Modeling MCP server or Fabric IQ MCP, or compare against the committed contract."
        )

    def _contract_for(self, semantic_model_id: str) -> tuple[str, SemanticModel]:
        for binding in self._bindings.workspaces.values():
            for profile, model_id in binding.semantic_models.items():
                if model_id.lower() == semantic_model_id.lower():
                    return binding.workspace_id, load_semantic_model(
                        semantic_model_path(self._data_root, profile)
                    )
        raise UnknownResourceError(
            f"semantic model {semantic_model_id!r} is not bound to a dataset profile in the local bindings file"
        )

    async def evaluate_measures(
        self,
        semantic_model_id: str,
        measures: Sequence[str] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[tuple[MeasureValue, ...]]:
        """Evaluate the model's measures by display name with DAX (no filter context)."""
        workspace_id, contract = self._contract_for(semantic_model_id)
        wanted = [m for m in contract.measures if measures is None or m.name in measures]
        unknown = set(measures or ()) - {m.name for m in contract.measures}
        if unknown:
            raise UnknownResourceError(f"unknown measures: {sorted(unknown)}")
        gate = asyncio.Semaphore(MEASURE_CONCURRENCY)

        async def one(display: str) -> float | int | None:
            escaped = display.replace("]", "]]")
            async with gate:
                try:
                    rows = await self._client.execute_dax(
                        workspace_id, semantic_model_id, f'EVALUATE ROW("v", [{escaped}])'
                    )
                except InvalidRequestError:
                    return None  # the measure is missing or invalid in the live model
            value = next(iter(rows[0].values()), None) if rows else None
            return (
                value if isinstance(value, (int, float)) and not isinstance(value, bool) else None
            )

        values = await asyncio.gather(*(one(m.display_name) for m in wanted))
        data = tuple(
            MeasureValue(
                name=m.name,
                display_name=m.display_name,
                value=v,
                format=m.format,
                synthetic_demonstration=m.synthetic_demonstration,
            )
            for m, v in zip(wanted, values, strict=True)
        )
        return self._envelope(
            data,
            service="Power BI REST: Datasets - Execute Queries (DAX)",
            objective="Reconcile the live model's measures with the governed baseline.",
            correlation_id=correlation_id,
        )
