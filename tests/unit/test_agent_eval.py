"""Agent evaluation: the suite matches the baseline; the evaluator catches wrong or ungrounded answers."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from tests.conftest import CONFIG_ROOT, DATA_ROOT, REPO_ROOT

from fabric_foundry_accelerator.agents.local import LocalSalesAgent
from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion, ToolCall
from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.evaluation.agent_eval import load_suite, normalize, run_suite
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.synthetic.manufacturing import MfgBaseline

SUITE = load_suite(CONFIG_ROOT, "sales-insights-agent")


def test_suite_expectations_come_from_the_baseline() -> None:
    baseline = MfgBaseline.model_validate_json(
        (REPO_ROOT / "data" / "synthetic" / "expected" / "mfg-sales-v1.json").read_text(
            encoding="utf-8"
        )
    )
    cases = {c.id: c for c in SUITE.cases}
    assert f"{baseline.observation_month_revenue:.2f}" in cases["total-revenue"].expect_contains
    assert (
        str(baseline.data_quality["duplicate_order_lines"]) in cases["duplicates"].expect_contains
    )
    enc = baseline.team_briefs["T-ENC"]
    assert f"{enc['revenue']:.2f}" in cases["enclosures-brief"].expect_contains
    assert str(enc["target_attainment_pct"]) in cases["enclosures-brief"].expect_contains
    assert any(not c.expect_grounded for c in SUITE.cases)


def test_normalize_ignores_currency_separators_and_emphasis() -> None:
    assert normalize("**$509,726.22** and 12,000") == "509726.22 and 12000"


async def test_local_agent_passes_the_gate() -> None:
    report = await run_suite(LocalSalesAgent(DATA_ROOT), SUITE)
    assert report.gate_passed and report.pass_rate == 1.0 and report.labels == ("LOCAL",)
    assert report.cases[0].tools == ("local_sales_query",)


class Scripted:
    """Answers every question with fixed text; optionally claims a data tool."""

    def __init__(self, text: str, *, grounded: bool) -> None:
        self.text, self.grounded = text, grounded

    @property
    def name(self) -> str:
        return "scripted"

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        return ExecutionEnvelope[AgentAnswer](
            operating_mode=OperatingMode.OFFLINE,
            execution_label=ExecutionLabel.MOCKED,
            requested_provider="scripted",
            selected_provider="scripted",
            cloud_operation_performed=False,
            equivalent_fabric_service="test",
            teaching_objective="test",
            simulation_notice="Scripted test agent.",
            data=AgentAnswer(
                agent=question.agent,
                question=question.question,
                answer=self.text,
                tool_calls=(ToolCall(name="fabric_dataagent_preview_call"),)
                if self.grounded
                else (),
                grounded=self.grounded,
            ),
        )


@pytest.mark.parametrize(
    ("agent", "failing"),
    [
        (
            Scripted("Enclosures grew 55.78%.", grounded=False),
            {"fastest-line", "total-revenue", "duplicates", "enclosures-brief"},
        ),
        (
            Scripted("Enclosures grew 12%.", grounded=True),
            {"fastest-line", "total-revenue", "enclosures-brief", "out-of-scope"},
        ),
    ],
)
async def test_wrong_or_ungrounded_answers_fail_the_gate(
    agent: Scripted, failing: set[str]
) -> None:
    report = await run_suite(agent, SUITE)
    assert not report.gate_passed and report.status == "FAILED"
    assert {c.id for c in report.cases if not c.passed} == failing


def test_suite_lookup_errors() -> None:
    with pytest.raises(InvalidRequestError):
        load_suite(CONFIG_ROOT, "../etc/passwd")
    with pytest.raises(UnknownResourceError):
        load_suite(CONFIG_ROOT, "nope")


def test_api_and_cli(
    make_container: Callable[..., Container],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with TestClient(create_app(make_container())) as client:
        body = client.post("/api/v1/agents/evaluate").json()
        assert body["gate_passed"] is True and body["passed"] == 5
        assert client.post("/api/v1/agents/evaluate", params={"suite": "nope"}).status_code == 404
        assert client.post("/api/v1/agents/evaluate", params={"suite": "Bad Id"}).status_code == 422
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("FFIA_AUDIT_PATH", "")
    assert main(["agents", "eval"]) == 0
    assert "5/5 passed; gate PASSED" in capsys.readouterr().out
    assert main(["agents", "eval", "--json"]) == 0
    assert '"gate_passed": true' in capsys.readouterr().out
