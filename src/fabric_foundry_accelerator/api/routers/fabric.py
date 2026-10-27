"""HTTP adapters for fabric; domain behavior stays in services/providers."""

from typing import Annotated

from fastapi import APIRouter, Body

from fabric_foundry_accelerator.api.dependencies import ContainerDep, CorrelationDep
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.services.fabric_reads import FabricReadRequest, execute_read

router = APIRouter()


@router.post("/api/v1/fabric/read", tags=["fabric"])
async def fabric_read(
    body: Annotated[FabricReadRequest, Body()],
    container: ContainerDep,
    correlation_id: CorrelationDep,
) -> ExecutionEnvelope[object]:
    """Typed, read-only Fabric operations through the provider router."""
    return await execute_read(container.fabric, body, correlation_id=correlation_id)
