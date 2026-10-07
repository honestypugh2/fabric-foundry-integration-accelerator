"""Typed Fabric read requests and their dispatch to the routed Fabric provider."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.providers.fabric.port import MAX_PREVIEW_ROWS, FabricProvider


class _Read(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ListWorkspaces(_Read):
    """List workspaces."""

    operation: Literal["list_workspaces"]


class ListItems(_Read):
    """List items in a workspace."""

    operation: Literal["list_items"]
    workspace_id: str


class ListTables(_Read):
    """List tables in a lakehouse."""

    operation: Literal["list_tables"]
    lakehouse_id: str


class ReadTable(_Read):
    """Preview a table (bounded)."""

    operation: Literal["read_table"]
    lakehouse_id: str
    table: str
    limit: int = Field(default=20, ge=1, le=MAX_PREVIEW_ROWS)


class GetSemanticModel(_Read):
    """Return a semantic model."""

    operation: Literal["get_semantic_model"]
    semantic_model_id: str


class EvaluateMeasures(_Read):
    """Evaluate declared measures."""

    operation: Literal["evaluate_measures"]
    semantic_model_id: str
    measures: list[str] | None = None


FabricReadRequest = Annotated[
    ListWorkspaces | ListItems | ListTables | ReadTable | GetSemanticModel | EvaluateMeasures,
    Field(discriminator="operation"),
]


async def execute_read(
    fabric: FabricProvider, request: FabricReadRequest, *, correlation_id: str
) -> ExecutionEnvelope[object]:
    """Dispatch a typed read to the provider. No free-form queries exist."""
    match request:
        case ListWorkspaces():
            result = await fabric.list_workspaces(correlation_id=correlation_id)
        case ListItems():
            result = await fabric.list_items(request.workspace_id, correlation_id=correlation_id)
        case ListTables():
            result = await fabric.list_tables(request.lakehouse_id, correlation_id=correlation_id)
        case ReadTable():
            result = await fabric.read_table(
                request.lakehouse_id,
                request.table,
                limit=request.limit,
                correlation_id=correlation_id,
            )
        case GetSemanticModel():
            result = await fabric.get_semantic_model(
                request.semantic_model_id, correlation_id=correlation_id
            )
        case EvaluateMeasures():
            result = await fabric.evaluate_measures(
                request.semantic_model_id, request.measures, correlation_id=correlation_id
            )
    return ExecutionEnvelope[object].model_validate(result.model_dump())
