"""Tracing: agent spans carry evidence fields and never the question text; export is opt-in."""

from collections.abc import Callable

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic import SecretStr

from fabric_foundry_accelerator.agents.port import AgentQuestion
from fabric_foundry_accelerator.agents.routed import RoutedAgentProvider
from fabric_foundry_accelerator.observability import tracing
from fabric_foundry_accelerator.services.container import Container


async def test_agent_span_records_evidence_but_not_the_question(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    routed = RoutedAgentProvider(
        container.router,
        local=container.agents.local,
        live=None,
        tracer=provider.get_tracer("test"),
    )
    question = "How many duplicate order lines are there?"
    envelope = await routed.ask(AgentQuestion(question=question), correlation_id="c" * 32)
    [span] = exporter.get_finished_spans()
    attrs = dict(span.attributes or {})
    assert span.name == "ffia.agent.ask"
    assert attrs["ffia.correlation_id"] == "c" * 32 == envelope.correlation_id
    assert attrs["ffia.execution_label"] == "LOCAL" and attrs["ffia.fallback_used"] is False
    assert attrs["ffia.tools"] == ("local_sales_query",) and attrs["ffia.grounded"] is True
    assert attrs["ffia.question_length"] == len(question)
    assert all(question not in str(value) for value in attrs.values())


def test_configure_tracing_is_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "no exporter" in tracing.configure_tracing(None)
    assert "no exporter" in tracing.configure_tracing(SecretStr(""))
    calls: list[dict[str, object]] = []

    import azure.monitor.opentelemetry as monitor  # noqa: PLC0415

    def fake(**kwargs: object) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(monitor, "configure_azure_monitor", fake)
    status = tracing.configure_tracing(
        SecretStr("InstrumentationKey=00000000-0000-0000-0000-000000000000")
    )
    assert "Application Insights" in status
    assert calls == [
        {
            "connection_string": "InstrumentationKey=00000000-0000-0000-0000-000000000000",
            "enable_live_metrics": False,
        }
    ]
