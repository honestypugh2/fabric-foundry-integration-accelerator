"""Agent provider that routes every question through the ``ProviderRouter`` (capability foundry_agent)."""

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentProvider, AgentQuestion
from fabric_foundry_accelerator.fallback.router import ProviderRouter
from fabric_foundry_accelerator.models.execution import ExecutionEnvelope, new_correlation_id


class RoutedAgentProvider:
    """Prefers the live Foundry agent when configured; falls back per environment policy."""

    def __init__(
        self, router: ProviderRouter, *, local: AgentProvider, live: AgentProvider | None
    ) -> None:
        """Create a routed provider."""
        self._router = router
        self._local = local
        self._live = live

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
        return await self._router.read(
            "foundry_agent",
            "ask",
            local=lambda: self._local.ask(question, correlation_id=cid),
            local_name=self._local.name,
            live=(lambda: live.ask(question, correlation_id=cid)) if live else None,
            live_name=live.name if live else None,
            correlation_id=cid,
        )
