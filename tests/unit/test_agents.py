"""Agent provider port: local deterministic agent, live Foundry adapter (fake client), routing."""

import asyncio
import json
import shutil
import time
from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from tests.conftest import CONFIG_ROOT, DATA_ROOT, REPO_ROOT

from fabric_foundry_accelerator.agents.foundry import FoundryAgentProvider, SdkResponsesClient
from fabric_foundry_accelerator.agents.local import SUPPORTED, LocalSalesAgent
from fabric_foundry_accelerator.agents.port import AgentQuestion
from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.config.bindings import BindingsError, bindings_path
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.services.container import Container, build_container

Q = AgentQuestion


@pytest.mark.parametrize(
    ("question", "fragment"),
    [
        (
            "Which product line grew fastest last month?",
            "Enclosures (ENC) grew fastest**: booked revenue up 55.78%",
        ),
        ("Which product line grew fastest last month?", "$56,623.73 → $88,207.09"),
        ("What was total booked revenue last month?", "$509,726.22"),
        ("How many duplicate order lines are there?", "**12**"),
        ("What data-quality issues are there?", "duplicate order lines: 12"),
        ("Write the monthly brief for the Enclosures team.", "Enclosures**, September 2026"),
        ("Write the monthly brief for T-KEY", "Key Accounts"),
    ],
)
async def test_local_agent_answers_governed_questions(question: str, fragment: str) -> None:
    envelope = await LocalSalesAgent(DATA_ROOT).ask(Q(question=question), correlation_id="a" * 32)
    assert (
        envelope.execution_label is ExecutionLabel.LOCAL and not envelope.cloud_operation_performed
    )
    assert envelope.correlation_id == "a" * 32
    assert envelope.data.grounded and envelope.data.tool_calls[0].name == "local_sales_query"
    assert fragment in envelope.data.answer


async def test_local_agent_refuses_outside_the_allow_list() -> None:
    envelope = await LocalSalesAgent(DATA_ROOT).ask(Q(question="Tell me a joke"))
    assert not envelope.data.grounded and envelope.data.tool_calls == ()
    assert envelope.data.supported_questions == SUPPORTED
    assert "only allow-listed questions" in envelope.data.answer


class FakeClient:
    def __init__(
        self, types: list[str], text: str = "Enclosures grew fastest.", delay: float = 0.0
    ) -> None:
        self.types, self.text, self.delay = types, text, delay
        self.calls: list[tuple[str, str]] = []

    def ask(self, agent: str, question: str) -> tuple[str, list[str]]:
        self.calls.append((agent, question))
        if self.delay:
            time.sleep(self.delay)
        return self.text, self.types


async def test_foundry_provider_labels_preview_tools_and_grounding() -> None:
    client = FakeClient(
        [
            "fabric_dataagent_preview_call",
            "fabric_dataagent_preview_call_output",
            "reasoning",
            "message",
        ]
    )
    envelope = await FoundryAgentProvider(client, mode=OperatingMode.HYBRID).ask(
        Q(question="Which line grew?")
    )
    assert envelope.execution_label is ExecutionLabel.PREVIEW and envelope.cloud_operation_performed
    assert [c.name for c in envelope.data.tool_calls] == ["fabric_dataagent_preview_call"]
    assert envelope.data.grounded and client.calls == [("sales-insights-agent", "Which line grew?")]

    plain = await FoundryAgentProvider(FakeClient(["message"]), mode=OperatingMode.LIVE).ask(
        Q(question="hello?")
    )
    assert plain.execution_label is ExecutionLabel.LIVE and not plain.data.grounded


class BusyClient(FakeClient):
    """Rejects the first ``busy`` calls like the Fabric data agent does while a run is active."""

    def __init__(
        self, busy: int, error: str = "Can't add messages to thread t while a run r is active."
    ) -> None:
        super().__init__(["fabric_dataagent_preview_call"])
        self.busy, self.error = busy, error

    def ask(self, agent: str, question: str) -> tuple[str, list[str]]:
        if self.busy:
            self.busy -= 1
            self.calls.append((agent, question))
            raise RuntimeError(self.error)
        return super().ask(agent, question)


async def test_foundry_provider_retries_a_busy_thread_then_gives_up() -> None:
    waits: list[float] = []
    provider = FoundryAgentProvider(
        BusyClient(busy=2),
        mode=OperatingMode.HYBRID,
        busy_retry_delays=(1, 2, 3),
        sleep=waits.append,
    )
    envelope = await provider.ask(Q(question="Total revenue?"))
    assert envelope.execution_label is ExecutionLabel.PREVIEW and waits == [1, 2]
    stuck = FoundryAgentProvider(
        BusyClient(busy=9), mode=OperatingMode.HYBRID, busy_retry_delays=(1, 2), sleep=waits.append
    )
    with pytest.raises(RuntimeError, match="is active"):
        await stuck.ask(Q(question="Total revenue?"))
    other = BusyClient(busy=1, error="401 Unauthorized")
    with pytest.raises(RuntimeError, match="401"):
        await FoundryAgentProvider(other, mode=OperatingMode.HYBRID, sleep=waits.append).ask(
            Q(question="Total revenue?")
        )
    assert len(other.calls) == 1, "only a busy thread is retried"


async def test_foundry_provider_serializes_live_calls() -> None:
    client = FakeClient(["fabric_dataagent_preview_call"], delay=0.05)
    provider = FoundryAgentProvider(client, mode=OperatingMode.HYBRID)
    start = time.perf_counter()
    await asyncio.gather(*(provider.ask(Q(question=f"question {i}")) for i in range(3)))
    assert time.perf_counter() - start >= 0.15 and len(client.calls) == 3


def test_foundry_provider_refuses_offline_and_sdk_client_is_lazy() -> None:
    with pytest.raises(ValueError, match="OFFLINE"):
        FoundryAgentProvider(FakeClient([]), mode=OperatingMode.OFFLINE)
    SdkResponsesClient(
        "https://example.invalid/api/projects/p", "00000000-0000-0000-0000-000000000001"
    )


def _config_with_foundry(tmp_path: Path) -> Path:
    root = tmp_path / "config"
    shutil.copytree(CONFIG_ROOT, root, ignore=shutil.ignore_patterns("*.local.yaml"))
    bindings = {
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "foundry": {
            "subscription_id": "00000000-0000-0000-0000-000000000002",
            "resource_group": "rg",
            "account": "foundry-demo",
            "project": "agents",
        },
    }
    bindings_path(root, "example-healthcare").write_text(yaml.safe_dump(bindings), encoding="utf-8")
    return root


def test_container_live_agent_requires_opt_in_mode_and_binding(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> None:
    assert build_container(make_settings()).agents.live is None
    with pytest.raises(BindingsError, match="FFIA_ENVIRONMENT"):
        build_container(make_settings(foundry_live=True))
    with pytest.raises(BindingsError, match="foundry:"):
        build_container(make_settings(foundry_live=True, environment="live"))
    container = build_container(
        make_settings(
            foundry_live=True, environment="hybrid", config_root=_config_with_foundry(tmp_path)
        ),
        agent_client=FakeClient(["fabric_dataagent_preview_call"]),
    )
    assert (
        container.agents.live is not None
        and container.agents.live.name == "Foundry Agent Service (live)"
    )


async def test_routed_agent_uses_live_then_falls_back(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> None:
    root = _config_with_foundry(tmp_path)
    live = build_container(
        make_settings(foundry_live=True, environment="hybrid", config_root=root),
        agent_client=FakeClient(["fabric_dataagent_preview_call"]),
    )
    envelope = await live.agents.ask(Q(question="Which line grew?"))
    assert envelope.execution_label is ExecutionLabel.PREVIEW and not envelope.fallback_used

    class Broken(FakeClient):
        def ask(self, agent: str, question: str) -> tuple[str, list[str]]:
            raise ConnectionError("Fabric capacity paused")

    fallback = build_container(
        make_settings(foundry_live=True, environment="hybrid", config_root=root),
        agent_client=Broken([]),
    )
    envelope = await fallback.agents.ask(Q(question="Which product line grew fastest last month?"))
    assert envelope.fallback_used and envelope.execution_label is ExecutionLabel.LOCAL
    assert "Enclosures" in envelope.data.answer and "LOCAL fallback" in (
        envelope.fallback_reason or ""
    )


def test_api_and_runtime_status(make_container: Callable[..., Container]) -> None:
    with TestClient(create_app(make_container())) as client:
        response = client.post(
            "/api/v1/agents/ask", json={"question": "How many duplicate order lines are there?"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["execution_label"] == "LOCAL" and "**12**" in body["data"]["answer"]
        assert client.post("/api/v1/agents/ask", json={"question": "x"}).status_code == 422
        status = client.get("/api/v1/runtime/status").json()
        assert status["agent_provider"].startswith("Local sales agent")
        providers = client.get("/api/v1/runtime/providers").json()
        kinds = {p["kind"] for p in providers if p["capability"] == "foundry_agent"}
        assert kinds == {"LOCAL", "NOT AVAILABLE"}


def test_agents_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(_config_with_foundry(tmp_path)))
    monkeypatch.setenv("FFIA_AUDIT_PATH", "")
    assert (
        main(["agents", "ask", "Which", "product", "line", "grew", "fastest", "last", "month?"])
        == 0
    )
    out = capsys.readouterr().out
    assert "[LOCAL]" in out and "Tools used: local_sales_query" in out
    assert main(["agents", "ask", "Tell me a joke"]) == 0
    assert "Supported offline questions" in capsys.readouterr().out
    assert main(["agents", "ask", "--json", "How many duplicate order lines are there?"]) == 0
    assert json.loads(capsys.readouterr().out)["data"]["grounded"] is True
