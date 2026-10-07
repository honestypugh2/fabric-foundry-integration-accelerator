"""Fabric provider port.

Domain services depend on this protocol only. Implementations:

* ``LocalFabricProvider`` (this phase): synthetic Parquet + DuckDB, labeled LOCAL.
* A live adapter (Phase 5): Fabric REST / Fabric MCP, labeled LIVE, read-only by default.

The port exposes no free-form SQL, no arbitrary file access and no write operations. Changes
to Fabric go through the approval flow, not through this read port.
"""

from collections.abc import Sequence
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.models.semantic import SemanticModel

JsonScalar = str | int | float | bool | None
ItemType = Literal["Lakehouse", "SemanticModel"]
MAX_PREVIEW_ROWS = 100


class WorkspaceInfo(BaseModel):
    """A workspace visible to the provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    display_name: str
    description: str


class ItemInfo(BaseModel):
    """An item in a workspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    display_name: str
    type: ItemType
    workspace_id: str
    description: str


class ColumnInfo(BaseModel):
    """A column name and type."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    data_type: str


class TableInfo(BaseModel):
    """A lakehouse table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    layer: str
    row_count: int
    columns: tuple[ColumnInfo, ...]


class TablePreview(BaseModel):
    """A bounded preview of table rows."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    table: str
    layer: str
    columns: tuple[ColumnInfo, ...]
    rows: tuple[dict[str, JsonScalar], ...]
    total_rows: int
    truncated: bool


class MeasureValue(BaseModel):
    """The value of one semantic-model measure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    display_name: str
    value: int | float | None
    format: str
    synthetic_demonstration: bool


class FabricProvider(Protocol):
    """Read-only Fabric capabilities used by domain services."""

    @property
    def name(self) -> str:
        """Return the provider name used in envelopes and audit records."""
        ...

    async def list_workspaces(
        self, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[WorkspaceInfo, ...]]:
        """List workspaces."""
        ...

    async def list_items(
        self, workspace_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[ItemInfo, ...]]:
        """List items in a workspace."""
        ...

    async def list_tables(
        self, lakehouse_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[TableInfo, ...]]:
        """List tables in a lakehouse."""
        ...

    async def read_table(
        self,
        lakehouse_id: str,
        table: str,
        *,
        limit: int = 20,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[TablePreview]:
        """Return a bounded preview of a table (at most ``MAX_PREVIEW_ROWS`` rows)."""
        ...

    async def get_semantic_model(
        self, semantic_model_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[SemanticModel]:
        """Return a semantic model definition."""
        ...

    async def evaluate_measures(
        self,
        semantic_model_id: str,
        measures: Sequence[str] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[tuple[MeasureValue, ...]]:
        """Evaluate declared measures (default: all) with no filter context."""
        ...
