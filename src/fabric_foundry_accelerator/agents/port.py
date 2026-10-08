"""The agent provider port: ask a named agent a question and get a labeled, evidenced answer.

Adapters:

* ``LocalSalesAgent``: a deterministic, allow-listed agent over the synthetic manufacturing data,
  labeled LOCAL. It answers a fixed set of governed questions and says so for anything else.
* ``FoundryAgentProvider``: a Foundry Agent Service agent (for example one that uses the Fabric data
  agent tool), labeled LIVE or PREVIEW, opt-in.
"""

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import ExecutionEnvelope


class ToolCall(BaseModel):
    """One tool the agent used, as reported by the agent runtime."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    summary: str = ""


class AgentQuestion(BaseModel):
    """A question for a named agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: str = Field(default="sales-insights-agent", pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    question: str = Field(min_length=3, max_length=2000)


class AgentAnswer(BaseModel):
    """The agent's answer and how it was grounded."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: str
    question: str
    answer: str
    tool_calls: tuple[ToolCall, ...] = ()
    grounded: bool = Field(description="True when a governed data tool produced the numbers.")
    supported_questions: tuple[str, ...] = ()


class AgentProvider(Protocol):
    """Answers questions with a named agent."""

    @property
    def name(self) -> str:
        """Provider name."""
        ...

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        """Ask one question."""
        ...
