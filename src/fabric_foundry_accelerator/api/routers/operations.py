"""HTTP adapters for operations; domain behavior stays in services/providers."""

import asyncio

from fastapi import APIRouter

from fabric_foundry_accelerator.api.dependencies import ContainerDep, CorrelationDep
from fabric_foundry_accelerator.audit.store import AuditRecord
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope
from fabric_foundry_accelerator.recovery.scenario import (
    DEFAULT_SCENARIO_PATH,
    load_scenario,
    run_recovery_drill,
)
from fabric_foundry_accelerator.services.demo import (
    DemoCheckReport,
    OfflineDemoReport,
    demo_check,
    run_offline_demo,
)
from fabric_foundry_accelerator.services.evaluation import EvaluationRequest
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

router = APIRouter()


@router.post("/api/v1/recovery/drill", tags=["recovery"])
async def recovery_drill(
    container: ContainerDep, correlation_id: CorrelationDep
) -> ExecutionEnvelope[object]:
    """Run the Open Mirroring snapshot + incremental + restore drill (SIMULATED)."""
    data_root = container.settings.data_root
    scenario = load_scenario(data_root / "recovery" / DEFAULT_SCENARIO_PATH.name)
    work_dir = data_root / "recovery" / "runs" / f"api-{correlation_id}"
    envelope = await asyncio.to_thread(
        run_recovery_drill, scenario, data_root=data_root, work_dir=work_dir
    )
    return ExecutionEnvelope[object].model_validate(
        envelope.model_copy(update={"correlation_id": correlation_id}).model_dump()
    )


@router.post("/api/v1/evaluations/run", tags=["evaluation"])
async def run_evaluation(
    body: EvaluationRequest, container: ContainerDep, correlation_id: CorrelationDep
) -> ExecutionEnvelope[object]:
    """Compare observed (or local) measure values with the expected baseline."""
    envelope = await container.evaluation.run(body, correlation_id=correlation_id)
    return ExecutionEnvelope[object].model_validate(envelope.model_dump())


@router.get("/api/v1/audit/{correlation_id}", tags=["audit"])
def get_audit(correlation_id: str, container: ContainerDep) -> list[AuditRecord]:
    """Redacted audit records for a correlation ID."""
    return container.audit.for_correlation(correlation_id)


@router.get("/api/v1/demo/status", tags=["demo"])
async def demo_status(container: ContainerDep) -> DemoCheckReport:
    """Readiness of every demo component and the recommended mode."""
    return await demo_check(container, azure_probe=container.settings.demo_check_azure_cli)


@router.get("/api/v1/profiles", tags=["data"])
def list_profiles() -> list[str]:
    """Dataset profiles."""
    return sorted(PROFILES)


@router.post("/api/v1/demo/run", tags=["demo"])
async def run_demo(container: ContainerDep, correlation_id: CorrelationDep) -> OfflineDemoReport:
    """Run the ten-act offline demo against this process's services (labeled results only)."""
    work_dir = container.settings.runtime_root / "demo" / correlation_id
    return await run_offline_demo(container, work_dir=work_dir)
