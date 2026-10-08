"""HTTP routes. Thin by design: validate, call a service, return its result."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion
from fabric_foundry_accelerator.audit.store import AuditRecord
from fabric_foundry_accelerator.education.diagrams import DiagramView
from fabric_foundry_accelerator.education.drawio import render_drawio
from fabric_foundry_accelerator.education.guides import GuideStep, UseCaseGuide
from fabric_foundry_accelerator.education.layout import ViewLayout, compute_layout
from fabric_foundry_accelerator.education.lessons import ArchitectureMap, CompletenessReport, Lab
from fabric_foundry_accelerator.evaluation.agent_eval import AgentEvalReport, load_suite, run_suite
from fabric_foundry_accelerator.models.changes import (
    Approval,
    ApprovalRequest,
    ChangeRequest,
    ExecuteRequest,
    ProposedChange,
)
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope, new_correlation_id
from fabric_foundry_accelerator.patterns.catalog import (
    SELECTION_SIGNALS,
    ArchitecturePattern,
    Recommendation,
    recommend,
)
from fabric_foundry_accelerator.recovery.scenario import (
    DEFAULT_SCENARIO_PATH,
    load_scenario,
    run_recovery_drill,
)
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.demo import (
    DemoCheckReport,
    OfflineDemoReport,
    demo_check,
    run_offline_demo,
)
from fabric_foundry_accelerator.services.diagram_runtime import ViewRuntime, view_runtime
from fabric_foundry_accelerator.services.education import (
    CheckAnswer,
    CheckGrade,
    LabSummary,
    LessonSummary,
    LessonView,
)
from fabric_foundry_accelerator.services.evaluation import EvaluationRequest
from fabric_foundry_accelerator.services.fabric_reads import FabricReadRequest, execute_read
from fabric_foundry_accelerator.services.runtime import (
    ProviderStatus,
    RuntimeStatus,
    provider_statuses,
    runtime_status,
)
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

router = APIRouter()


def get_container(request: Request) -> Container:
    """Return the process container."""
    container: Container = request.app.state.container
    return container


def get_correlation_id(request: Request) -> str:
    """Return the request correlation ID set by middleware."""
    value: str = getattr(request.state, "correlation_id", new_correlation_id())
    return value


ContainerDep = Annotated[Container, Depends(get_container)]
CorrelationDep = Annotated[str, Depends(get_correlation_id)]


class Health(BaseModel):
    """Liveness."""

    model_config = ConfigDict(frozen=True)

    status: str


class Readiness(BaseModel):
    """Readiness with the checks behind it."""

    model_config = ConfigDict(frozen=True)

    ready: bool
    checks: dict[str, bool]


class RecommendRequest(BaseModel):
    """Needs from the selection vocabulary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    needs: list[str] = Field(min_length=1)
    include_preview: bool = True


class Capability(BaseModel):
    """A capability and how it is currently served."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    served_by: str


# ------------------------------------------------------------------ health
@router.get("/health", tags=["health"])
def health() -> Health:
    """Liveness probe."""
    return Health(status="ok")


@router.get("/ready", tags=["health"])
def ready(container: ContainerDep, response: Response) -> Readiness:
    """Readiness probe: local data built, guides and MCP manifest loaded."""
    checks = {
        "local_lakehouse_built": bool(runtime_status(container).built_profiles),
        "guides_loaded": bool(container.guides),
        "mcp_manifest_loaded": bool(container.tool_manifest.enabled()),
    }
    is_ready = all(checks.values())
    response.status_code = 200 if is_ready else 503
    return Readiness(ready=is_ready, checks=checks)


# ------------------------------------------------------------------ runtime
@router.get("/api/v1/runtime/status", tags=["runtime"])
def get_runtime_status(container: ContainerDep) -> RuntimeStatus:
    """Execution state for the status bar."""
    return runtime_status(container)


@router.get("/api/v1/runtime/providers", tags=["runtime"])
def get_providers(container: ContainerDep) -> list[ProviderStatus]:
    """Provider readiness per capability."""
    return list(provider_statuses(container))


@router.get("/api/v1/capabilities", tags=["runtime"])
def get_capabilities(container: ContainerDep) -> list[Capability]:
    """What the control plane can do and what serves each capability."""
    status = runtime_status(container)
    return [
        Capability(
            name="fabric_read",
            description="Typed, bounded reads of workspaces, items, tables and measures.",
            served_by=status.data_provider,
        ),
        Capability(
            name="change_plans",
            description="Plan, approve and execute changes under policy.",
            served_by="Change service (LOCAL simulated; LIVE unavailable)",
        ),
        Capability(
            name="recovery_drill",
            description="Open Mirroring snapshot and replay drill.",
            served_by="Local Open Mirroring Simulator (SIMULATED)",
        ),
        Capability(
            name="evaluation",
            description="Compare measures with expected baselines.",
            served_by="Baseline Evaluator (LOCAL)",
        ),
        Capability(name="mcp", description="Allow-listed MCP tools.", served_by=status.mcp),
        Capability(
            name="agents",
            description="Foundry agents and Agent Framework workflows.",
            served_by=status.agent_provider,
        ),
    ]


# ------------------------------------------------------------------ patterns and guides
@router.get("/api/v1/patterns", tags=["patterns"])
def list_patterns(container: ContainerDep) -> list[ArchitecturePattern]:
    """All architecture patterns."""
    return list(container.catalog.patterns)


class SelectionSignal(BaseModel):
    """One need from the pattern-selection vocabulary."""

    model_config = ConfigDict(frozen=True)

    id: str
    description: str


@router.get("/api/v1/patterns/signals", tags=["patterns"])
def list_selection_signals() -> list[SelectionSignal]:
    """The needs vocabulary accepted by the pattern recommender."""
    return [SelectionSignal(id=key, description=text) for key, text in SELECTION_SIGNALS.items()]


@router.get("/api/v1/patterns/{pattern_id}", tags=["patterns"])
def get_pattern(pattern_id: str, container: ContainerDep) -> ArchitecturePattern:
    """One architecture pattern."""
    return container.catalog.get(pattern_id)


@router.post("/api/v1/patterns/recommend", tags=["patterns"])
def recommend_patterns(body: RecommendRequest, container: ContainerDep) -> list[Recommendation]:
    """Rank patterns for declared needs."""
    return recommend(container.catalog, body.needs, include_preview=body.include_preview)


@router.get("/api/v1/guides", tags=["guides"])
def list_guides(container: ContainerDep) -> list[UseCaseGuide]:
    """All Use-Case Guides."""
    return list(container.guides.values())


@router.get("/api/v1/guides/{guide_id}", tags=["guides"])
def get_guide(guide_id: str, container: ContainerDep) -> UseCaseGuide:
    """One Use-Case Guide."""
    return container.guides[guide_id]


@router.get("/api/v1/guides/{guide_id}/steps/{step_id}", tags=["guides"])
def get_guide_step(guide_id: str, step_id: str, container: ContainerDep) -> GuideStep:
    """One guide step."""
    return container.guides[guide_id].step(step_id)


# ------------------------------------------------------------------ fabric reads and changes
@router.post("/api/v1/fabric/read", tags=["fabric"])
async def fabric_read(
    body: Annotated[FabricReadRequest, Body()],
    container: ContainerDep,
    correlation_id: CorrelationDep,
) -> ExecutionEnvelope[object]:
    """Typed, read-only Fabric operations through the provider router."""
    return await execute_read(container.fabric, body, correlation_id=correlation_id)


# ------------------------------------------------------------------ agents
@router.post("/api/v1/agents/ask", tags=["agents"])
async def ask_agent(
    body: Annotated[AgentQuestion, Body()],
    container: ContainerDep,
    correlation_id: CorrelationDep,
) -> ExecutionEnvelope[AgentAnswer]:
    """Ask a named agent through the provider router (LOCAL by default; live Foundry is opt-in)."""
    return await container.agents.ask(body, correlation_id=correlation_id)


@router.post("/api/v1/agents/evaluate", tags=["agents"])
async def evaluate_agent(
    container: ContainerDep, suite: str = "sales-insights-agent"
) -> AgentEvalReport:
    """Run an agent evaluation suite (sequential; live agents are slow and metered)."""
    return await run_suite(container.agents, load_suite(container.settings.config_root, suite))


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


# ------------------------------------------------------------------ recovery, evaluation, audit, demo
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


# ------------------------------------------------------------------ education
@router.get("/api/v1/education/lessons", tags=["education"])
def list_lessons(
    container: ContainerDep, area: str | None = None, pattern_id: str | None = None
) -> list[LessonSummary]:
    """Lesson summaries, optionally filtered by area or pattern."""
    return container.education.lessons(area=area, pattern_id=pattern_id)


@router.get("/api/v1/education/lessons/{lesson_id}", tags=["education"])
def get_lesson(lesson_id: str, container: ContainerDep) -> LessonView:
    """One lesson with all five levels and its knowledge checks (answers withheld)."""
    return container.education.lesson(lesson_id)


@router.post("/api/v1/education/lessons/{lesson_id}/checks/{check_id}", tags=["education"])
def answer_check(
    lesson_id: str, check_id: str, body: CheckAnswer, container: ContainerDep
) -> CheckGrade:
    """Grade one knowledge-check answer."""
    return container.education.grade(lesson_id, check_id, body)


@router.get("/api/v1/education/labs", tags=["education"])
def list_labs(container: ContainerDep) -> list[LabSummary]:
    """Lab summaries."""
    return container.education.labs()


@router.get("/api/v1/education/labs/{lab_id}", tags=["education"])
def get_lab(lab_id: str, container: ContainerDep) -> Lab:
    """One lab with its eleven stages."""
    return container.education.lab(lab_id)


@router.get("/api/v1/education/architecture", tags=["education"])
def get_architecture(container: ContainerDep) -> ArchitectureMap:
    """The architecture explorer map."""
    return container.education.library.architecture


@router.get("/api/v1/education/completeness", tags=["education"])
def get_completeness(container: ContainerDep) -> CompletenessReport:
    """Coverage of the 30-question architecture completeness gate."""
    return container.education.library.completeness_report()


class ViewSummary(BaseModel):
    """An architecture view in a list."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    kind: str
    summary: str
    doc: str | None
    pattern_ids: tuple[str, ...]


@router.get("/api/v1/education/views", tags=["education"])
def list_views(container: ContainerDep) -> list[ViewSummary]:
    """Architecture views (interactive diagrams)."""
    return [
        ViewSummary(
            id=v.id,
            title=v.title,
            kind=v.kind,
            summary=v.summary,
            doc=v.doc,
            pattern_ids=v.pattern_ids,
        )
        for v in container.education.library.views
    ]


class RenderedView(BaseModel):
    """A view with the shared layout used by both the app and the draw.io files."""

    model_config = ConfigDict(frozen=True)

    view: DiagramView
    layout: ViewLayout


@router.get("/api/v1/education/views/{view_id}", tags=["education"])
def get_view(view_id: str, container: ContainerDep) -> RenderedView:
    """One architecture view and its layout: nodes, edges, zones, bands, build steps and traces."""
    view = container.education.library.view(view_id)
    return RenderedView(view=view, layout=compute_layout(view))


@router.get("/api/v1/education/views/{view_id}/drawio", tags=["education"])
def get_view_drawio(view_id: str, container: ContainerDep) -> Response:
    """The view as a draw.io file (same content as docs/architecture/diagrams)."""
    view = container.education.library.view(view_id)
    return Response(
        content=render_drawio(view),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{view.id}.drawio"'},
    )


@router.get("/api/v1/education/views/{view_id}/runtime", tags=["education"])
def get_view_runtime(view_id: str, container: ContainerDep) -> ViewRuntime:
    """The live state of every runtime-bound node in a view."""
    return view_runtime(container, container.education.library.view(view_id))
