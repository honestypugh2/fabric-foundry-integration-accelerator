"""Deterministic agent evaluation: does the agent answer governed questions with the right numbers?

Each case checks two things that matter for business answers:

* **Grounding:** a governed data tool produced the numbers (or, for out-of-scope questions, it did
  not pretend to).
* **Correctness:** every expected value from the baseline appears in the answer, ignoring "$" and
  thousands separators.

The same suite runs against the LOCAL agent offline and the live Foundry agent (opt-in), so the
result labels say which one was evaluated.
"""

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.agents.port import AgentProvider, AgentQuestion
from fabric_foundry_accelerator.models.execution import new_correlation_id
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError

SUITES_DIR = Path("evaluations")


class AgentEvalCase(BaseModel):
    """One question with its expected values."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    question: str
    # Each entry must appear in the answer. A list entry means "any of these equivalent forms".
    expect_contains: tuple[str | tuple[str, ...], ...] = ()
    expect_grounded: bool


class AgentEvalSuite(BaseModel):
    """``config/evaluations/<id>.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    agent: str
    profile: str
    min_pass_rate: float = Field(ge=0, le=1)
    cases: tuple[AgentEvalCase, ...] = Field(min_length=1)


class AgentCaseResult(BaseModel):
    """The outcome of one case."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    question: str
    passed: bool
    grounded: bool
    missing: tuple[str, ...]
    label: str
    answer_excerpt: str
    tools: tuple[str, ...]
    provider: str
    fallback_used: bool


class AgentEvalReport(BaseModel):
    """All cases, the pass rate and the gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluation_id: str = Field(default_factory=new_correlation_id)
    suite: str
    provider: str
    labels: tuple[str, ...]
    fallback_cases: int
    compared: int
    passed: int
    pass_rate: float
    gate_passed: bool
    status: Literal["PASSED", "FAILED"]
    cases: tuple[AgentCaseResult, ...]


class AgentProfile(BaseModel):
    """What the UI needs to ask an agent: who answers and which questions are evaluated."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent: str
    suite: str
    dataset_profile: str
    local_provider: str
    live_provider: str | None
    suggested_questions: tuple[str, ...]


def agent_profile(
    suite: AgentEvalSuite, *, local_provider: str, live_provider: str | None
) -> AgentProfile:
    """Describe an agent from its evaluation suite, so suggestions are the evaluated questions."""
    return AgentProfile(
        agent=suite.agent,
        suite=suite.id,
        dataset_profile=suite.profile,
        local_provider=local_provider,
        live_provider=live_provider,
        suggested_questions=tuple(case.question for case in suite.cases),
    )


def load_suite(config_root: Path, suite_id: str) -> AgentEvalSuite:
    """Load an evaluation suite by id.

    Raises:
        InvalidRequestError: the id is not a plain slug.
        UnknownResourceError: no such suite.
    """
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", suite_id) or len(suite_id) > 64:
        raise InvalidRequestError(f"invalid evaluation suite id {suite_id!r}")
    path = config_root / SUITES_DIR / f"{suite_id}.yaml"
    if not path.is_file():
        raise UnknownResourceError(f"unknown evaluation suite {suite_id!r}")
    return AgentEvalSuite.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def attainment_forms(pct: float) -> tuple[str, ...]:
    """Equivalent ways to state target attainment: "143.1% of target" or "43.1% above target"."""
    distance = round(abs(pct - 100), 1)
    return (str(pct), str(distance)) if distance else (str(pct),)


def missing_values(answer: str, expected: tuple[str | tuple[str, ...], ...]) -> tuple[str, ...]:
    """Expected entries absent from ``answer``; alternatives are reported joined by " or "."""
    text = normalize(answer)
    missing: list[str] = []
    for entry in expected:
        forms = (entry,) if isinstance(entry, str) else entry
        if not any(normalize(form) in text for form in forms):
            missing.append(" or ".join(forms))
    return tuple(missing)


def normalize(text: str) -> str:
    """Drop currency symbols, thousands separators and Markdown emphasis before matching."""
    return re.sub(r"(?<=\d),(?=\d{3})", "", text.replace("$", "").replace("*", ""))


async def run_suite(agent: AgentProvider, suite: AgentEvalSuite) -> AgentEvalReport:
    """Ask every case sequentially (live agent calls are slow and metered) and score the answers."""
    results: list[AgentCaseResult] = []
    labels: list[str] = []
    providers: list[str] = []
    for case in suite.cases:
        envelope = await agent.ask(AgentQuestion(agent=suite.agent, question=case.question))
        providers.append(envelope.selected_provider)
        missing = missing_values(envelope.data.answer, case.expect_contains)
        grounded = envelope.data.grounded
        label = envelope.execution_label.value + (" (fallback)" if envelope.fallback_used else "")
        labels.append(label)
        results.append(
            AgentCaseResult(
                id=case.id,
                question=case.question,
                # A fallback answer did not come from the requested agent, so it cannot pass.
                passed=not missing
                and grounded == case.expect_grounded
                and not envelope.fallback_used,
                grounded=grounded,
                missing=missing,
                label=label,
                answer_excerpt=envelope.data.answer[:300],
                tools=tuple(c.name for c in envelope.data.tool_calls),
                provider=envelope.selected_provider,
                fallback_used=envelope.fallback_used,
            )
        )
    passed = sum(r.passed for r in results)
    rate = passed / len(results)
    gate = rate >= suite.min_pass_rate
    return AgentEvalReport(
        suite=suite.id,
        provider=" + ".join(dict.fromkeys(providers)),
        labels=tuple(sorted(set(labels))),
        fallback_cases=sum(r.fallback_used for r in results),
        compared=len(results),
        passed=passed,
        pass_rate=round(rate, 4),
        gate_passed=gate,
        status="PASSED" if gate else "FAILED",
        cases=tuple(results),
    )
