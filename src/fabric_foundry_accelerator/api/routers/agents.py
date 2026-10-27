"""HTTP adapters for agents; domain behavior stays in services/providers."""

from typing import Annotated

from fastapi import APIRouter, Body

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion
from fabric_foundry_accelerator.agents.workflows import (
    MonthlyInsightsRequest,
    MonthlyInsightsRun,
    live_safe_concurrency,
    run_monthly_insights,
)
from fabric_foundry_accelerator.api.dependencies import ContainerDep, CorrelationDep
from fabric_foundry_accelerator.evaluation.agent_eval import (
    AgentEvalReport,
    AgentProfile,
    agent_profile,
    load_suite,
    run_suite,
)
from fabric_foundry_accelerator.knowledge.local import (
    PREVIEW_FLAG,
    KnowledgeQuery,
    KnowledgeResult,
    search_knowledge,
)
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope

router = APIRouter()


@router.get("/api/v1/agents/{agent}", tags=["agents"])
def get_agent(agent: str, container: ContainerDep) -> AgentProfile:
    """Who answers for an agent and the questions its evaluation suite covers."""
    live = container.agents.live
    return agent_profile(
        load_suite(container.settings.config_root, agent),
        local_provider=container.agents.local.name,
        live_provider=None if live is None else live.name,
    )


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


@router.post("/api/v1/agents/workflows/monthly-insights", tags=["agents"])
async def run_monthly_insights_workflow(
    body: Annotated[MonthlyInsightsRequest, Body()], container: ContainerDep
) -> MonthlyInsightsRun:
    """Draft each team's monthly brief through an Agent Framework workflow. Nothing is sent."""
    return await run_monthly_insights(
        container.agents,
        container.settings.data_root,
        body,
        max_concurrency=live_safe_concurrency(container.agents),
    )


@router.post("/api/v1/knowledge/search", tags=["knowledge"])
def search_knowledge_base(
    body: Annotated[KnowledgeQuery, Body()],
    container: ContainerDep,
    correlation_id: CorrelationDep,
) -> ExecutionEnvelope[KnowledgeResult]:
    """Cited passages from the synthetic knowledge base (Foundry IQ analog, PREVIEW flag)."""
    return search_knowledge(
        body,
        data_root=container.settings.data_root,
        enabled=PREVIEW_FLAG in container.overlay.enabled_previews(),
        mode=container.environment.mode,
        correlation_id=correlation_id,
    )
