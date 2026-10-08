"""Agent provider that routes every question through the ``ProviderRouter`` (capability foundry_agent)."""

from opentelemetry.trace import Tracer

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentProvider, AgentQuestion
from fabric_foundry_accelerator.fallback.router import ProviderRouter
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope, new_correlation_id
from fabric_foundry_accelerator.observability.tracing import get_tracer, record_envelope


class RoutedAgentProvider:
    """Prefers the live Foundry agent when configured; falls back per environment policy."""

    def __init__(
        self,
        router: ProviderRouter,
        *,
        local: AgentProvider,
        live: AgentProvider | None,
        tracer: Tracer | None = None,
    ) -> None:
        """Create a routed provider; ``tracer`` defaults to the package tracer."""
        self._router = router
        self._local = local
        self._live = live
        self._tracer = tracer or get_tracer()

    @property
    def name(self) -> str:
        """Provider name."""
        return "Provider Router (agents)"

    @property
    def live(self) -> AgentProvider | None:
        """The live provider, if configured."""
        return self._live

    @property
    def local(self) -> AgentProvider:
        """The local provider."""
        return self._local

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        """Ask through the router."""
        cid = correlation_id or new_correlation_id()
        live = self._live
        with self._tracer.start_as_current_span("ffia.agent.ask") as span:
            span.set_attribute("ffia.agent", question.agent)
            span.set_attribute("ffia.question_length", len(question.question))
            envelope = await self._router.read(
                "foundry_agent",
                "ask",
                local=lambda: self._local.ask(question, correlation_id=cid),
                local_name=self._local.name,
                live=(lambda: live.ask(question, correlation_id=cid)) if live else None,
                live_name=live.name if live else None,
                correlation_id=cid,
            )
            record_envelope(
                span,
                correlation_id=cid,
                provider=envelope.selected_provider,
                label=envelope.execution_label.value,
                fallback_used=envelope.fallback_used,
                tools=[c.name for c in envelope.data.tool_calls],
                grounded=envelope.data.grounded,
            )
            return envelope
