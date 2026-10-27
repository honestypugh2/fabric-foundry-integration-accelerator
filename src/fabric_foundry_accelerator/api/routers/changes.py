"""HTTP adapters for changes; domain behavior stays in services/providers."""

from fastapi import APIRouter

from fabric_foundry_accelerator.api.dependencies import ContainerDep, CorrelationDep
from fabric_foundry_accelerator.models.changes import (
    Approval,
    ApprovalRequest,
    ChangeRequest,
    ExecuteRequest,
    ProposedChange,
)
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope

router = APIRouter()


@router.post("/api/v1/plans", tags=["changes"])
def create_plan(
    body: ChangeRequest, container: ContainerDep, correlation_id: CorrelationDep
) -> ProposedChange:
    """Plan and validate a change. Nothing executes."""
    return container.changes.plan(body, correlation_id=correlation_id)


@router.get("/api/v1/plans", tags=["changes"])
def list_plans(container: ContainerDep) -> list[ProposedChange]:
    """All plans in this process."""
    return container.changes.plans()


@router.get("/api/v1/plans/{change_id}", tags=["changes"])
def get_plan(change_id: str, container: ContainerDep) -> ProposedChange:
    """One plan."""
    return container.changes.get_plan(change_id)


@router.post("/api/v1/approvals", tags=["changes"])
def approve(body: ApprovalRequest, container: ContainerDep) -> Approval:
    """Record a human approval or rejection."""
    return container.changes.approve(body)


@router.post("/api/v1/fabric/change", tags=["changes"])
async def execute_change(
    body: ExecuteRequest, container: ContainerDep
) -> ExecutionEnvelope[object]:
    """Execute an approved change. LIVE changes are never redirected to LOCAL."""
    result = await container.changes.execute(body)
    return ExecutionEnvelope[object].model_validate(result.model_dump())
