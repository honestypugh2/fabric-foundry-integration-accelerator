"""Live Foundry Agent Service adapter (opt-in).

Calls an existing agent through the Foundry project's Responses API with the Foundry SDK. The SDK is
imported lazily, so offline runs never load it. Tool calls reported by the runtime are returned as
evidence; when a preview tool (such as the Fabric data agent tool) was used, the result is labeled
PREVIEW. Identity is the signed-in Azure CLI user for one pinned tenant.

The Fabric data agent keeps one conversation per user and accepts one active run at a time, so
this provider serializes live calls. A call that the router abandons after its timeout keeps the
lock until the SDK call really returns, and a "run is active" rejection is retried a bounded
number of times before the router's fallback policy applies.
"""

import asyncio
import threading
import time
from collections.abc import Callable, Sequence
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
BUSY_RETRY_DELAYS: tuple[float, ...] = (5.0, 15.0, 30.0)


def is_busy_thread_error(error: Exception) -> bool:
    """True when the service rejected a call because another run is active on the thread."""
    text = str(error)
    return "while a run" in text and "is active" in text


class ResponsesClient(Protocol):
    """Runs one question against a named agent; returns the text and the output item types."""

    def ask(self, agent: str, question: str) -> tuple[str, list[str]]:
        """Return (answer text, output item types in order)."""
        ...


class SdkResponsesClient:
    """``ResponsesClient`` backed by azure-ai-projects (lazy import)."""

    def __init__(
        self,
        endpoint: str,
        tenant_id: str,
        *,
        tool_choice: str = "auto",
        request_timeout: float | None = None,
    ) -> None:
        """Bind to one project endpoint and tenant.

        ``request_timeout`` ends the HTTP call itself, so a call the router has abandoned does not
        keep the provider's lock; set it just under the router's timeout.
        """
        self._endpoint = endpoint
        self._tenant_id = tenant_id
        self._tool_choice = tool_choice
        self._request_timeout = request_timeout

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
        response = client.responses.create(
            input=question, tool_choice=self._tool_choice, timeout=self._request_timeout
        )
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

    def __init__(
        self,
        client: ResponsesClient,
        *,
        mode: OperatingMode,
        busy_retry_delays: Sequence[float] = BUSY_RETRY_DELAYS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create the provider. ``mode`` must be HYBRID or LIVE."""
        if mode is OperatingMode.OFFLINE:
            raise ValueError("the live Foundry agent provider cannot run in OFFLINE mode")
        self._client = client
        self._mode = mode
        self._delays = tuple(busy_retry_delays)
        self._sleep = sleep
        self._lock = threading.Lock()

    def _call(self, agent: str, question: str) -> tuple[str, list[str]]:
        # Runs in a worker thread; holds the lock until the SDK call returns.
        with self._lock:
            for delay in (*self._delays, None):
                try:
                    return self._client.ask(agent, question)
                except Exception as error:  # the SDK raises many HTTP error types; re-raised
                    if delay is None or not is_busy_thread_error(error):
                        raise
                    self._sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover

    @property
    def name(self) -> str:
        """Provider name."""
        return PROVIDER_NAME

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        """Ask the live agent (a blocking SDK call, run in a worker thread)."""
        text, types = await asyncio.to_thread(self._call, question.agent, question.question)
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
