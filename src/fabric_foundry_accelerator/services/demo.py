"""Demo continuity: ``demo-check`` (readiness) and ``demo-offline`` (scripted release-gate demo)."""

import asyncio
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Literal

from fastmcp import Client
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.config.environment import load_environment
from fabric_foundry_accelerator.fallback.router import ProviderRouter
from fabric_foundry_accelerator.mcp.server import build_mcp_server
from fabric_foundry_accelerator.models.changes import (
    ApprovalDecision,
    ApprovalRequest,
    ChangeRequest,
    ChangeStatus,
    ExecuteRequest,
    FabricTarget,
)
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.patterns.catalog import recommend
from fabric_foundry_accelerator.providers.fabric.live import NOT_CONFIGURED_NOTE
from fabric_foundry_accelerator.providers.fabric.outage import SimulatedOutageFabricProvider
from fabric_foundry_accelerator.providers.fabric.routed import RoutedFabricProvider
from fabric_foundry_accelerator.recovery.scenario import (
    DEFAULT_SCENARIO_PATH,
    load_scenario,
    run_recovery_drill,
)
from fabric_foundry_accelerator.services.changes import (
    ApprovalError,
    ChangeService,
    LiveWriteUnavailableError,
)
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.evaluation import EvaluationRequest
from fabric_foundry_accelerator.services.runtime import provider_statuses, runtime_status
from fabric_foundry_accelerator.synthetic.medallion import lakehouse_tables
from fabric_foundry_accelerator.synthetic.pipeline import check_profile
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

AzureCliState = Literal["PRESENT", "ABSENT", "NOT INSTALLED"]


class CheckLine(BaseModel):
    """One readiness line."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component: str
    status: str
    detail: str


class DemoCheckReport(BaseModel):
    """Readiness of every demo component and the recommended mode."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lines: tuple[CheckLine, ...]
    recommended_mode: OperatingMode
    reason: str


def azure_cli_sign_in() -> AzureCliState:
    """Check the Azure CLI's LOCAL credential cache (no network call, no identifiers printed)."""
    executable = shutil.which("az")
    if executable is None:
        return "NOT INSTALLED"
    try:
        # Fixed arguments, no shell; reads the local profile cache only.
        completed = subprocess.run(  # noqa: S603 - fixed arguments, no shell
            [executable, "account", "show", "-o", "none"],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "ABSENT"
    return "PRESENT" if completed.returncode == 0 else "ABSENT"


async def demo_check(container: Container, *, azure_probe: bool = True) -> DemoCheckReport:
    """Probe each component and recommend LIVE, HYBRID or OFFLINE."""
    from fabric_foundry_accelerator.api.app import (  # noqa: PLC0415 - avoids an import cycle with routes
        create_app,
    )

    settings = container.settings
    az = await asyncio.to_thread(azure_cli_sign_in) if azure_probe else "NOT INSTALLED"
    live = next(
        (
            p
            for p in provider_statuses(container)
            if p.capability == "fabric_data" and p.kind != "LOCAL"
        ),
        None,
    )
    data_ok = all(not check_profile(p, settings.data_root) for p in PROFILES.values())
    built = [p for p in sorted(PROFILES) if lakehouse_tables(settings.lakehouse_root, p)]
    paths = create_app(container).openapi().get("paths", {})
    async with Client(build_mcp_server(container)) as client:
        tools = await client.list_tools()
    frontend = settings.frontend_root
    frontend_state = (
        "BUILT"
        if (frontend / "dist" / "index.html").is_file()
        else "INSTALLED"
        if (frontend / "node_modules").is_dir()
        else "NOT INSTALLED"
    )
    lines = (
        CheckLine(
            component="Fabric Authentication",
            status={"PRESENT": "PASS", "ABSENT": "FAIL", "NOT INSTALLED": "NOT CONFIGURED"}[az],
            detail=f"Azure CLI credential cache {az.lower()} (local check only; not proof of Fabric access)",
        ),
        CheckLine(
            component="Fabric API",
            status="NOT CONFIGURED" if live is None else live.kind,
            detail=live.note if live else NOT_CONFIGURED_NOTE,
        ),
        CheckLine(
            component="Fabric MCP",
            status="NOT CONFIGURED",
            detail="Configure the Fabric MCP servers per guide (e.g. HC-01 step 01); not probed here.",
        ),
        CheckLine(
            component="Foundry",
            status="NOT CONFIGURED",
            detail="Foundry providers are added in Phase 6.",
        ),
        CheckLine(
            component="Local Dataset",
            status="PASS" if data_ok else "FAIL",
            detail="Committed synthetic CSVs match the generator."
            if data_ok
            else "Run `ffia data generate --check`.",
        ),
        CheckLine(
            component="Offline Provider",
            status="READY" if len(built) == len(PROFILES) else "NOT READY",
            detail=f"Built profiles: {', '.join(built) or 'none'}",
        ),
        CheckLine(
            component="API",
            status="READY" if paths else "NOT READY",
            detail=f"{len(paths)} API paths (in-process check)",
        ),
        CheckLine(
            component="Frontend",
            status=frontend_state,
            detail="Run `make setup-frontend` then `make run-frontend`.",
        ),
        CheckLine(
            component="MCP Server",
            status="READY" if tools else "NOT READY",
            detail=f"{len(tools)} allow-listed tools (in-process MCP call)",
        ),
    )
    live_ready = live is not None and live.ready
    mode = OperatingMode.HYBRID if live_ready else OperatingMode.OFFLINE
    reason = (
        "A live Fabric provider is healthy; reads use it with LOCAL fallback."
        if live_ready
        else (
            "No live provider is configured and healthy; OFFLINE runs everything locally with honest labels."
        )
    )
    return DemoCheckReport(lines=lines, recommended_mode=mode, reason=reason)


# ---------------------------------------------------------------------------- offline demo
class DemoStep(BaseModel):
    """One act of the scripted demo."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    act: int
    title: str
    required: bool
    passed: bool
    label: str
    summary: str
    evidence: tuple[str, ...] = ()


class OfflineDemoReport(BaseModel):
    """Outcome of the offline demo (a release gate)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    passed: bool
    operating_mode: OperatingMode
    steps: tuple[DemoStep, ...]
    label_counts: dict[str, int]
    live_operations: int
    cloud_operations: int


class _Tracker:
    def __init__(self) -> None:
        self.envelopes: list[ExecutionEnvelope[object]] = []

    def add[T](self, envelope: ExecutionEnvelope[T]) -> ExecutionEnvelope[T]:
        self.envelopes.append(ExecutionEnvelope[object].model_validate(envelope.model_dump()))
        return envelope


async def run_offline_demo(container: Container, *, work_dir: Path) -> OfflineDemoReport:
    """Run the ten-act demo without any cloud access."""
    tracker = _Tracker()
    steps: list[DemoStep] = []
    hc = "hc-lab-7file-v1"

    status = runtime_status(container)
    steps.append(
        DemoStep(
            act=1,
            title="Why: Fabric is context, Foundry is reasoning, MCP is access, identity is authority",
            required=True,
            passed=True,
            label="LOCAL",
            summary=f"Mode {status.operating_mode}; data provider: {status.data_provider}.",
            evidence=(
                f"write mode: {status.write_mode}",
                f"preview features enabled: {list(status.preview_features) or 'none'}",
            ),
        )
    )

    tables = tracker.add(await container.fabric.list_tables(f"local-lh-{hc}"))
    evaluation = tracker.add(await container.evaluation.run(EvaluationRequest(profile=hc)))
    layers = Counter(t.layer for t in tables.data)
    steps.append(
        DemoStep(
            act=2,
            title="Data: raw to bronze, silver, gold and semantics",
            required=True,
            passed=evaluation.data.gate_passed and len(tables.data) == 24,
            label=tables.execution_label.value,
            summary=(
                f"{len(tables.data)} tables ({dict(layers)}); "
                f"{evaluation.data.passed}/{evaluation.data.compared} measures match the baseline."
            ),
            evidence=(
                tables.simulation_notice or "",
                f"evaluation gate passed: {evaluation.data.gate_passed}",
            ),
        )
    )

    async with Client(build_mcp_server(container)) as client:
        result = await client.call_tool("inspect_medallion_architecture", {"profile": hc})
    payload = result.structured_content or {}
    mcp_ok = (
        payload.get("execution_label") == "LOCAL"
        and payload.get("cloud_operation_performed") is False
    )
    steps.append(
        DemoStep(
            act=3,
            title="MCP: a real protocol call to the LOCAL educational server",
            required=True,
            passed=mcp_ok,
            label=str(payload.get("execution_label")),
            summary="Called inspect_medallion_architecture over MCP. No Fabric MCP server was called.",
            evidence=("MCP standardizes access; it did not authorize anything.",),
        )
    )

    ranked = recommend(
        container.catalog,
        ["conversational-structured-analytics", "business-system-write", "resilience-offline"],
    )
    steps.append(
        DemoStep(
            act=4,
            title="Architecture patterns",
            required=True,
            passed=bool(ranked),
            label="LOCAL",
            summary="Top patterns: " + ", ".join(f"{r.pattern_id} {r.name}" for r in ranked[:3]),
            evidence=tuple(r.why for r in ranked[:3]),
        )
    )

    steps.append(await _agentic_change_act(container, tracker))
    steps.append(
        DemoStep(
            act=6,
            title="Foundry: an agent consuming governed context",
            required=False,
            passed=False,
            label="UNAVAILABLE",
            summary="Foundry and Agent Framework providers arrive in Phase 6. Nothing was simulated as Foundry here.",
        )
    )
    steps.append(await _failure_act(container, tracker))

    scenario = load_scenario(container.settings.data_root / "recovery" / DEFAULT_SCENARIO_PATH.name)
    drill = tracker.add(
        await asyncio.to_thread(
            run_recovery_drill,
            scenario,
            data_root=container.settings.data_root,
            work_dir=work_dir / "recovery",
        )
    )
    steps.append(
        DemoStep(
            act=8,
            title="Recovery: snapshot, incrementals, failure, restore, replay",
            required=True,
            passed=drill.data.recovered and not drill.data.counterfactual_recoverable,
            label=drill.execution_label.value,
            summary=(
                f"Recovered from the weekly snapshot: {drill.data.recovered}; "
                f"recoverable without it: {drill.data.counterfactual_recoverable}."
            ),
            evidence=(drill.simulation_notice or "",),
        )
    )

    steps.append(
        DemoStep(
            act=9,
            title="Education: patterns and Use-Case Guides",
            required=True,
            passed=len(container.catalog.patterns) >= 24 and bool(container.guides),
            label="LOCAL",
            summary=(
                f"{len(container.catalog.patterns)} patterns and {len(container.guides)} guide(s) loaded; "
                "level content arrives in Phase 4."
            ),
        )
    )

    labels = Counter(e.execution_label.value for e in tracker.envelopes)
    live_ops = labels.get("LIVE", 0)
    cloud_ops = sum(e.cloud_operation_performed for e in tracker.envelopes)
    steps.append(
        DemoStep(
            act=10,
            title="Proof: what ran LIVE and what was simulated",
            required=True,
            passed=live_ops == 0 and cloud_ops == 0,
            label="LOCAL",
            summary=(
                f"Envelopes by label: {dict(labels)}. LIVE operations: {live_ops}. "
                f"Cloud operations performed: {cloud_ops}."
            ),
            evidence=(
                "Every result above carries its label, provider, correlation ID and simulation notice.",
            ),
        )
    )

    return OfflineDemoReport(
        passed=all(s.passed for s in steps if s.required),
        operating_mode=container.mode,
        steps=tuple(steps),
        label_counts=dict(labels),
        live_operations=live_ops,
        cloud_operations=cloud_ops,
    )


async def _agentic_change_act(container: Container, tracker: _Tracker) -> DemoStep:
    suffix = new_correlation_id()[:6]
    target = FabricTarget(
        workspace_alias="demo-dev",
        item_type="Lakehouse",
        item_name=f"demo_lakehouse_{suffix}",
        destination="LOCAL",
    )
    plan = container.changes.plan(
        ChangeRequest(
            operation="create_lakehouse",
            target=target,
            reason="Offline demo: governed change",
            requested_by="demo-engineer",
        )
    )
    try:
        container.changes.approve(
            ApprovalRequest(
                change_id=plan.change_id,
                approver="demo-engineer",
                decision=ApprovalDecision.APPROVED,
            )
        )
        self_approval_refused = False
    except ApprovalError:
        self_approval_refused = True
    approval = container.changes.approve(
        ApprovalRequest(
            change_id=plan.change_id,
            approver="demo-approver",
            decision=ApprovalDecision.APPROVED,
            comment="Reviewed plan",
        )
    )
    executed = tracker.add(
        await container.changes.execute(
            ExecuteRequest(
                change_id=plan.change_id,
                approval_id=approval.approval_id,
                executed_by="scoped-writer",
            )
        )
    )
    duplicate = container.changes.plan(
        ChangeRequest(
            operation="create_lakehouse",
            target=target,
            reason="Offline demo: duplicate attempt",
            requested_by="demo-engineer",
        )
    )

    live_service = ChangeService(
        policy=container.write_policy,
        overlay=container.overlay,
        audit=container.audit,
        mode=container.mode,
        allow_live_mutation=True,
    )
    live_target = target.model_copy(update={"destination": "LIVE"})
    live_plan = live_service.plan(
        ChangeRequest(
            operation="create_lakehouse",
            target=live_target,
            reason="Offline demo: LIVE write attempt",
            requested_by="demo-engineer",
        )
    )
    live_approval = live_service.approve(
        ApprovalRequest(
            change_id=live_plan.change_id,
            approver="demo-approver",
            decision=ApprovalDecision.APPROVED,
        )
    )
    try:
        await live_service.execute(
            ExecuteRequest(
                change_id=live_plan.change_id,
                approval_id=live_approval.approval_id,
                executed_by="scoped-writer",
            )
        )
        live_refused = False
    except LiveWriteUnavailableError:
        live_refused = True
    not_redirected = not live_service.workspace.items()
    passed = (
        self_approval_refused
        and executed.data.status is ChangeStatus.VERIFIED
        and duplicate.status is ChangeStatus.BLOCKED
        and live_refused
        and not_redirected
    )
    return DemoStep(
        act=5,
        title="Agentic change: plan, validate, approve, execute, verify, audit",
        required=True,
        passed=passed,
        label=executed.execution_label.value,
        summary=(
            "LOCAL plan approved by a second person, executed in the simulated workspace and verified; "
            "the duplicate was blocked; the approved LIVE change was refused and NOT redirected to LOCAL."
        ),
        evidence=(
            f"self-approval refused: {self_approval_refused}",
            f"verification: {executed.data.verification.detail}",
            f"duplicate plan status: {duplicate.status}",
            f"LIVE write refused without redirect: {live_refused and not_redirected}",
        ),
    )


async def _failure_act(container: Container, tracker: _Tracker) -> DemoStep:
    hybrid = load_environment(container.settings.config_root, "hybrid")
    router = ProviderRouter(hybrid, audit=container.audit)
    outage = SimulatedOutageFabricProvider()
    routed = RoutedFabricProvider(router, local=container.local_fabric, live=outage)
    lakehouse = "local-lh-hc-lab-7file-v1"
    results = [
        tracker.add(await routed.list_tables(lakehouse))
        for _ in range(hybrid.circuit_breaker.failure_threshold + 1)
    ]
    last = router.decisions()[-1]
    breaker = router.breaker("fabric_data").status()
    passed = (
        all(r.fallback_used and r.operating_mode is OperatingMode.HYBRID for r in results)
        and breaker.state.value == "OPEN"
        and outage.calls
        == hybrid.circuit_breaker.failure_threshold * (hybrid.policy("fabric_data").max_retries + 1)
    )
    return DemoStep(
        act=7,
        title="Failure: simulated Fabric outage, circuit breaker and approved fallback",
        required=True,
        passed=passed,
        label=results[-1].execution_label.value,
        summary=(
            f"{len(results)} reads fell back to LOCAL data in HYBRID mode (fallback_used, with a reason); "
            f"breaker {breaker.state} after {breaker.consecutive_failures} failures; "
            "the last read skipped the live call."
        ),
        evidence=(
            results[-1].fallback_reason or "",
            f"last route decision: {last.outcome} ({last.failure_reason})",
        ),
    )
