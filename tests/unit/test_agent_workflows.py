"""The monthly-insights Agent Framework workflow: drafts per team, a deterministic gate, no delivery."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.conftest import DATA_ROOT, REPO_ROOT

from fabric_foundry_accelerator.agents.local import LocalSalesAgent
from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion, ToolCall
from fabric_foundry_accelerator.agents.workflows import (
    BriefStatus,
    MonthlyInsightsRequest,
    expected_values,
    load_baseline,
    run_monthly_insights,
)
from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.providers.errors import (
    InvalidRequestError,
    ProviderUnavailableError,
)
from fabric_foundry_accelerator.services.container import Container


class ScriptedAgent:
    """Answers every brief question with ``reply``; records peak concurrency."""

    def __init__(self, reply: Callable[[str], str], *, grounded: bool = True) -> None:
        self._reply = reply
        self._grounded = grounded
        self.in_flight = 0
        self.peak = 0

    @property
    def name(self) -> str:
        return "Scripted agent"

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        await asyncio.sleep(0.05)
        self.in_flight -= 1
        return ExecutionEnvelope[AgentAnswer](
            operating_mode=OperatingMode.OFFLINE,
            execution_label=ExecutionLabel.MOCKED,
            requested_provider=self.name,
            selected_provider=self.name,
            cloud_operation_performed=False,
            equivalent_fabric_service="test",
            teaching_objective="test",
            simulation_notice="MOCKED agent for tests.",
            data=AgentAnswer(
                agent=question.agent,
                question=question.question,
                answer=self._reply(question.question),
                tool_calls=(ToolCall(name="t"),) if self._grounded else (),
                grounded=self._grounded,
            ),
        )


def test_local_workflow_drafts_every_team_and_sends_nothing() -> None:
    run = asyncio.run(
        run_monthly_insights(LocalSalesAgent(DATA_ROOT), DATA_ROOT, MonthlyInsightsRequest())
    )
    assert [d.team_id for d in run.drafts] == ["T-ENC", "T-HWFAB", "T-KEY", "T-STRMET"]
    assert (run.ready, run.held) == (4, 0)
    assert run.labels == ("LOCAL",)
    assert "agent-framework-core" in run.engine
    assert run.delivery.startswith("Not sent.") and run.max_concurrency == 4
    assert all(d.status is BriefStatus.READY and not d.missing for d in run.drafts)
    enclosures = run.drafts[0]
    assert enclosures.expected == ("88207.09", "143.1 or 43.1")
    assert run.observation_month == "2026-09-01"


def test_team_filter_and_concurrent_drafting() -> None:
    baseline = load_baseline(DATA_ROOT)

    names = {team: str(brief["team_name"]) for team, brief in baseline.team_briefs.items()}

    def correct(question: str) -> str:
        team = next(t for t, name in names.items() if name in question)
        values = expected_values(baseline, team)
        return " and ".join(v if isinstance(v, str) else v[-1] for v in values)

    agent = ScriptedAgent(correct)
    run = asyncio.run(run_monthly_insights(agent, DATA_ROOT, MonthlyInsightsRequest()))
    assert run.ready == 4
    assert agent.peak > 1, "drafters should run concurrently (fan-out)"
    serial = ScriptedAgent(correct)
    asyncio.run(
        run_monthly_insights(serial, DATA_ROOT, MonthlyInsightsRequest(), max_concurrency=1)
    )
    assert serial.peak == 1, "a live agent gets one draft at a time"
    single = asyncio.run(
        run_monthly_insights(agent, DATA_ROOT, MonthlyInsightsRequest(teams=("T-KEY",)))
    )
    assert [d.team_id for d in single.drafts] == ["T-KEY"]


def test_gate_holds_ungrounded_and_wrong_numbers() -> None:
    ungrounded = asyncio.run(
        run_monthly_insights(
            ScriptedAgent(lambda _: "Revenue looks great!", grounded=False),
            DATA_ROOT,
            MonthlyInsightsRequest(teams=("T-ENC",)),
        )
    )
    held = ungrounded.drafts[0]
    assert held.status is BriefStatus.HELD and "No governed data tool" in held.reason
    wrong = asyncio.run(
        run_monthly_insights(
            ScriptedAgent(lambda _: "Revenue was $88,207.09, 120.0% of target."),
            DATA_ROOT,
            MonthlyInsightsRequest(teams=("T-ENC",)),
        )
    )
    draft = wrong.drafts[0]
    assert draft.status is BriefStatus.HELD
    assert draft.missing == ("143.1 or 43.1",)
    assert (wrong.ready, wrong.held) == (0, 1)


def test_errors(tmp_path: Path) -> None:
    with pytest.raises(InvalidRequestError, match="T-NOPE"):
        asyncio.run(
            run_monthly_insights(
                LocalSalesAgent(DATA_ROOT), DATA_ROOT, MonthlyInsightsRequest(teams=("T-NOPE",))
            )
        )
    with pytest.raises(ProviderUnavailableError, match="ffia data generate"):
        load_baseline(tmp_path)


def test_api_and_cli(
    make_container: Callable[..., Container],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with TestClient(create_app(make_container())) as client:
        path = "/api/v1/agents/workflows/monthly-insights"
        body = client.post(path, json={}).json()
        assert body["ready"] == 4 and body["labels"] == ["LOCAL"]
        assert client.post(path, json={"teams": ["T-NOPE"]}).status_code == 422
        assert client.post(path, json={"teams": ["T-ENC"], "extra": 1}).status_code == 422
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("FFIA_AUDIT_PATH", "")
    assert main(["agents", "workflow", "--team", "T-ENC"]) == 0
    out = capsys.readouterr().out
    assert "[READY FOR APPROVAL] Enclosures" in out and "1 ready for approval, 0 held." in out
    assert main(["agents", "workflow", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ready"] == 4
