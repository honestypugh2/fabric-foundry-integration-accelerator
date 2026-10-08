"""Monthly sales insights as a Microsoft Agent Framework workflow.

The workflow answers the question "could an agent monitor sales data and send each business team
monthly insights on its focus area?" with the governed shape:

``select teams`` → ``draft`` (one executor per team, fan-out, concurrent) → ``review gate``.

* The **agent proposes**: each draft comes from the routed agent provider (LOCAL offline, the live
  Foundry agent when opted in), so the numbers come from a governed data tool.
* **Deterministic logic validates**: the review gate checks grounding and that the team's baseline
  revenue and target attainment appear in the draft. A failed check holds the draft.
* **Humans approve delivery**: sending a brief to a team is a governed write and is never performed
  here. Every draft ends as ``READY FOR APPROVAL`` or ``HELD``.

Only ``agent-framework-core`` is used. ``agent-framework-foundry`` is not a dependency because it
requires a pre-release package and an older ``azure-ai-projects``; Foundry calls stay in
``FoundryAgentProvider`` behind the same provider port (ADR-0013).
"""

import importlib.metadata
from enum import StrEnum
from pathlib import Path
from typing import Never

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentProvider, AgentQuestion
from fabric_foundry_accelerator.evaluation.agent_eval import normalize
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope, new_correlation_id
from fabric_foundry_accelerator.providers.errors import (
    InvalidRequestError,
    ProviderUnavailableError,
)
from fabric_foundry_accelerator.synthetic.manufacturing import NOTICE, TEAMS, MfgBaseline

WORKFLOW_ID = "monthly-insights"
PROFILE = "mfg-sales-v1"
AGENT = "sales-insights-agent"
STEPS: tuple[str, ...] = (
    "select: choose the business teams for this run",
    "draft: one executor per team asks the agent for its brief (fan-out, concurrent)",
    "review: deterministic gate checks grounding and the team's baseline numbers",
    "deliver: not performed; sending briefs is a governed write that needs approval",
)
DELIVERY = (
    "Not sent. Delivering briefs to business teams (e-mail, Teams, a portal) is a governed write: "
    "PLAN, then human APPROVE, then EXECUTE through an authorized service, then AUDIT."
)
_TEAM_NAMES = {team_id: name for team_id, name, _, _ in TEAMS}


class BriefStatus(StrEnum):
    """Where a draft ends: ready for a human, or held by the gate."""

    READY = "READY FOR APPROVAL"
    HELD = "HELD"


class MonthlyInsightsRequest(BaseModel):
    """Which teams to brief; all teams by default."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    teams: tuple[str, ...] = Field(default=(), max_length=len(TEAMS))


class TeamBriefDraft(BaseModel):
    """One team's draft brief and the gate's verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    team_id: str
    team_name: str
    question: str
    answer: str
    label: str
    provider: str
    fallback_used: bool
    grounded: bool
    expected: tuple[str, ...]
    missing: tuple[str, ...]
    status: BriefStatus
    reason: str
    correlation_id: str


class MonthlyInsightsRun(BaseModel):
    """The result of one workflow run. Nothing was delivered."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str = Field(default_factory=new_correlation_id)
    workflow: str
    engine: str
    dataset_profile: str
    observation_month: str
    steps: tuple[str, ...]
    drafts: tuple[TeamBriefDraft, ...]
    ready: int
    held: int
    labels: tuple[str, ...]
    delivery: str
    synthetic_notice: str


def engine_name() -> str:
    """The orchestration engine and its installed version."""
    version = importlib.metadata.version("agent-framework-core")
    return f"Microsoft Agent Framework workflow (agent-framework-core {version})"


def load_baseline(data_root: Path) -> MfgBaseline:
    """The committed manufacturing baseline the review gate checks against.

    Raises:
        ProviderUnavailableError: the synthetic data has not been generated.
    """
    path = data_root / "expected" / f"{PROFILE}.json"
    if not path.is_file():
        raise ProviderUnavailableError(f"baseline {path} is missing; run `ffia data generate`")
    return MfgBaseline.model_validate_json(path.read_text(encoding="utf-8"))


def brief_question(team_id: str) -> str:
    """The question each drafter asks; matches the evaluated brief question."""
    return f"Write the monthly brief for the {_TEAM_NAMES[team_id]} team."


def expected_values(baseline: MfgBaseline, team_id: str) -> tuple[str, ...]:
    """Baseline numbers a correct brief must contain: revenue and target attainment."""
    brief = baseline.team_briefs[team_id]
    revenue, attainment = brief.get("revenue"), brief.get("target_attainment_pct")
    values: list[str] = []
    if isinstance(revenue, int | float):
        values.append(f"{revenue:.2f}")
    if isinstance(attainment, int | float):
        values.append(str(attainment))
    return tuple(values)


def review(
    team_id: str, envelope: ExecutionEnvelope[AgentAnswer], expected: tuple[str, ...]
) -> TeamBriefDraft:
    """The deterministic gate: grounded, and every expected value present."""
    answer = envelope.data
    missing = tuple(value for value in expected if value not in normalize(answer.answer))
    if not answer.grounded:
        status, reason = BriefStatus.HELD, "No governed data tool ran, so the numbers are unproven."
    elif missing:
        status, reason = BriefStatus.HELD, "The draft does not match the baseline."
    else:
        status, reason = BriefStatus.READY, "Grounded and matches the baseline."
    return TeamBriefDraft(
        team_id=team_id,
        team_name=_TEAM_NAMES[team_id],
        question=answer.question,
        answer=answer.answer,
        label=envelope.execution_label.value,
        provider=envelope.selected_provider,
        fallback_used=envelope.fallback_used,
        grounded=answer.grounded,
        expected=expected,
        missing=missing,
        status=status,
        reason=reason,
        correlation_id=envelope.correlation_id,
    )


class _Select(Executor):
    @handler
    async def select(
        self, request: MonthlyInsightsRequest, ctx: WorkflowContext[MonthlyInsightsRequest]
    ) -> None:
        await ctx.send_message(request)


class _Draft(Executor):
    """Drafts one team's brief. One instance per team, so drafts run concurrently."""

    def __init__(self, team_id: str, agent: AgentProvider, baseline: MfgBaseline) -> None:
        super().__init__(id=f"draft-{team_id.lower()}")
        self._team_id = team_id
        self._agent = agent
        self._expected = expected_values(baseline, team_id)

    @handler
    async def draft(
        self, request: MonthlyInsightsRequest, ctx: WorkflowContext[TeamBriefDraft]
    ) -> None:
        if request.teams and self._team_id not in request.teams:
            return
        envelope = await self._agent.ask(
            AgentQuestion(agent=AGENT, question=brief_question(self._team_id)),
            correlation_id=new_correlation_id(),
        )
        await ctx.send_message(review(self._team_id, envelope, self._expected))


class _Gate(Executor):
    @handler
    async def collect(
        self, draft: TeamBriefDraft, ctx: WorkflowContext[Never, TeamBriefDraft]
    ) -> None:
        await ctx.yield_output(draft)


async def run_monthly_insights(
    agent: AgentProvider, data_root: Path, request: MonthlyInsightsRequest
) -> MonthlyInsightsRun:
    """Run the workflow. Drafts only; nothing is delivered.

    Raises:
        InvalidRequestError: an unknown team id was requested.
        ProviderUnavailableError: the synthetic baseline is missing.
    """
    unknown = sorted(set(request.teams) - set(_TEAM_NAMES))
    if unknown:
        raise InvalidRequestError(f"unknown team(s): {', '.join(unknown)}")
    baseline = load_baseline(data_root)
    select, gate = _Select(id="select"), _Gate(id="review")
    drafters = [_Draft(team_id, agent, baseline) for team_id in _TEAM_NAMES]
    builder = WorkflowBuilder(start_executor=select, name=WORKFLOW_ID).add_fan_out_edges(
        select, drafters
    )
    for drafter in drafters:
        builder = builder.add_edge(drafter, gate)
    result = await builder.build().run(request)
    drafts = tuple(
        sorted(
            (output for output in result.get_outputs() if isinstance(output, TeamBriefDraft)),
            key=lambda draft: draft.team_id,
        )
    )
    ready = sum(draft.status is BriefStatus.READY for draft in drafts)
    return MonthlyInsightsRun(
        workflow=WORKFLOW_ID,
        engine=engine_name(),
        dataset_profile=PROFILE,
        observation_month=baseline.observation_month,
        steps=STEPS,
        drafts=drafts,
        ready=ready,
        held=len(drafts) - ready,
        labels=tuple(sorted({draft.label for draft in drafts})),
        delivery=DELIVERY,
        synthetic_notice=NOTICE,
    )
