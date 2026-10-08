"""Live Foundry Agent Service adapter (opt-in).

Calls an existing agent through the Foundry project's Responses API with the Foundry SDK. The SDK is
imported lazily, so offline runs never load it. Tool calls reported by the runtime are returned as
evidence; when a preview tool (such as the Fabric data agent tool) was used, the result is labeled
PREVIEW. Identity is the signed-in Azure CLI user for one pinned tenant.
"""

import asyncio
from typing import Any, Protocol, cast

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion, ToolCall
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)

PROVIDER_NAME = "Foundry Agent Service (live)"
_DATA_TOOLS = ("fabric", "azure_ai_search", "sharepoint", "file_search", "mcp")


class ResponsesClient(Protocol):
    """Runs one question against a named agent; returns the text and the output item types."""

    def ask(self, agent: str, question: str) -> tuple[str, list[str]]:
        """Return (answer text, output item types in order)."""
        ...


class SdkResponsesClient:
    """``ResponsesClient`` backed by azure-ai-projects (lazy import)."""

    def __init__(self, endpoint: str, tenant_id: str, *, tool_choice: str = "required") -> None:
        """Bind to one project endpoint and tenant."""
        self._endpoint = endpoint
        self._tenant_id = tenant_id
        self._tool_choice = tool_choice

    def ask(
        self, agent: str, question: str
    ) -> tuple[str, list[str]]:  # pragma: no cover - live only
        """Call the agent through the Responses API."""
        from azure.ai.projects import AIProjectClient  # noqa: PLC0415 - live path only
        from azure.identity import AzureCliCredential  # noqa: PLC0415 - live path only

        project = AIProjectClient(
            endpoint=self._endpoint, credential=AzureCliCredential(tenant_id=self._tenant_id)
        )
        client = cast("Any", project.get_openai_client(agent_name=agent))
        response = client.responses.create(input=question, tool_choice=self._tool_choice)
        types = [str(getattr(item, "type", "")) for item in response.output]
        return str(response.output_text), types


def _tool_calls(types: list[str]) -> tuple[ToolCall, ...]:
    calls: list[ToolCall] = []
    for kind in types:
        if kind in ("message", "reasoning") or kind.endswith("_output"):
            continue
        calls.append(ToolCall(name=kind, summary="reported by Foundry Agent Service"))
    return tuple(calls)


class FoundryAgentProvider:
    """``AgentProvider`` backed by a Foundry project; labeled LIVE or PREVIEW."""

    def __init__(self, client: ResponsesClient, *, mode: OperatingMode) -> None:
        """Create the provider. ``mode`` must be HYBRID or LIVE."""
        if mode is OperatingMode.OFFLINE:
            raise ValueError("the live Foundry agent provider cannot run in OFFLINE mode")
        self._client = client
        self._mode = mode

    @property
    def name(self) -> str:
        """Provider name."""
        return PROVIDER_NAME

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        """Ask the live agent (a blocking SDK call, run in a worker thread)."""
        text, types = await asyncio.to_thread(self._client.ask, question.agent, question.question)
        calls = _tool_calls(types)
        preview = any("preview" in c.name for c in calls)
        grounded = any(any(tool in c.name for tool in _DATA_TOOLS) for c in calls)
        return ExecutionEnvelope[AgentAnswer](
            operating_mode=self._mode,
            execution_label=ExecutionLabel.PREVIEW if preview else ExecutionLabel.LIVE,
            requested_provider=PROVIDER_NAME,
            selected_provider=PROVIDER_NAME,
            cloud_operation_performed=True,
            equivalent_fabric_service="Foundry Agent Service: Responses API",
            teaching_objective="A Foundry agent answers from governed Fabric data under the user's identity.",
            correlation_id=correlation_id or new_correlation_id(),
            data=AgentAnswer(
                agent=question.agent,
                question=question.question,
                answer=text,
                tool_calls=calls,
                grounded=grounded,
            ),
        )
