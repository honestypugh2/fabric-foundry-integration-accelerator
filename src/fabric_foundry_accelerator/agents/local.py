"""A deterministic, allow-listed sales agent over the synthetic manufacturing data (LOCAL).

It is the offline equivalent of a Foundry agent that uses the Fabric data agent tool: every number
comes from SQL over the local ``gold_sales`` table, never from a model. Questions outside the
allow-list get an honest "not answerable offline" reply with the supported questions.
"""

import re
from datetime import date
from pathlib import Path

from fabric_foundry_accelerator.agents.port import AgentAnswer, AgentQuestion, ToolCall
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.synthetic.manufacturing import (
    MFG_PROFILES,
    PRODUCT_LINES,
    TEAMS,
    build,
    line_revenue,
    open_sales,
)

PROVIDER_NAME = "Local sales agent (deterministic, synthetic)"
PROFILE = "mfg-sales-v1"
SUPPORTED: tuple[str, ...] = (
    "Which product line grew fastest last month?",
    "What was total booked revenue last month?",
    "How many duplicate order lines are there?",
    "What data-quality issues are there?",
    "Write the monthly brief for the Enclosures team.",
)
_LINE_NAMES = {code: name for code, name, _, _ in PRODUCT_LINES}
_TOOL = ToolCall(name="local_sales_query", summary="SQL over the local gold_sales table (DuckDB)")


def _previous(month: date) -> date:
    return date(month.year - (month.month == 1), (month.month - 2) % 12 + 1, 1)


class LocalSalesAgent:
    """``AgentProvider`` over local synthetic data; labeled LOCAL."""

    def __init__(self, data_root: Path, *, mode: OperatingMode = OperatingMode.OFFLINE) -> None:
        """Create the agent over ``data_root/raw/mfg-sales-v1``."""
        self._raw = data_root / "raw" / PROFILE
        self._profile = MFG_PROFILES[PROFILE]
        self._mode = mode

    @property
    def name(self) -> str:
        """Provider name."""
        return PROVIDER_NAME

    def _fastest_line(self) -> str:
        month = self._profile.observation_month
        con, _ = open_sales(self._raw, self._profile)
        with con:
            now, before = line_revenue(con, month), line_revenue(con, _previous(month))
        growth = {
            line: (now.get(line, 0.0) - before[line]) / before[line]
            for line in before
            if before[line]
        }
        best = max(growth, key=lambda line: growth[line])
        return (
            f"**{_LINE_NAMES[best]} ({best}) grew fastest**: booked revenue up "
            f"{100 * growth[best]:.2f}% in {month:%B %Y} versus {_previous(month):%B %Y} "
            f"(${before[best]:,.2f} → ${now[best]:,.2f})."
        )

    def _total(self) -> str:
        result = build(self._raw, self._profile)
        return (
            f"Total booked revenue for {self._profile.observation_month:%B %Y} was "
            f"**${result.observation_month_revenue:,.2f}**, excluding cancelled lines and lines with "
            "data-quality flags."
        )

    def _duplicates(self) -> str:
        _, quality = self._open_quality()
        return (
            f"There are **{quality['duplicate_order_lines']}** duplicate order lines (same order_id and "
            "line_number). A data steward should review them before they are removed in Silver."
        )

    def _open_quality(self) -> tuple[None, dict[str, int]]:
        con, quality = open_sales(self._raw, self._profile)
        con.close()
        return None, quality

    def _quality(self) -> str:
        _, quality = self._open_quality()
        lines = [f"- {name.replace('_', ' ')}: {count}" for name, count in quality.items()]
        return "Data-quality findings (detection only; fixes need approval):\n" + "\n".join(lines)

    def _brief(self, team_id: str) -> str:
        result = build(self._raw, self._profile)
        b = result.team_briefs[team_id]
        return (
            f"**{b['team_name']}**, {self._profile.observation_month:%B %Y}: booked revenue "
            f"${b['revenue']:,.2f} ({b['mom_change_pct']:+}% vs last month, {b['yoy_change_pct']:+}% vs "
            f"last year), {b['target_attainment_pct']}% of target, gross margin {b['gross_margin_pct']}%. "
            f"Top growing product: {b['top_growing_product']}. Synthetic demonstration data."
        )

    def _route(self, text: str) -> str | None:
        q = text.lower()
        team = next(
            (t[0] for t in TEAMS if t[1].lower().split(" &")[0] in q or t[0].lower() in q),
            None,
        )
        if "brief" in q and team:
            return self._brief(team)
        if re.search(r"(fastest|grew|growth)", q) and "line" in q:
            return self._fastest_line()
        if "duplicate" in q:
            return self._duplicates()
        if re.search(r"data[- ]quality|issues", q):
            return self._quality()
        if "revenue" in q and "total" in q:
            return self._total()
        return None

    async def ask(
        self, question: AgentQuestion, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[AgentAnswer]:
        """Answer an allow-listed question from local data."""
        answer = self._route(question.question)
        grounded = answer is not None
        data = AgentAnswer(
            agent=question.agent,
            question=question.question,
            answer=answer
            or "This offline agent answers only allow-listed questions over synthetic data. Try one of the "
            "supported questions, or switch to the live Foundry agent.",
            tool_calls=(_TOOL,) if grounded else (),
            grounded=grounded,
            supported_questions=SUPPORTED,
        )
        return ExecutionEnvelope[AgentAnswer](
            operating_mode=self._mode,
            execution_label=ExecutionLabel.LOCAL,
            requested_provider=PROVIDER_NAME,
            selected_provider=PROVIDER_NAME,
            cloud_operation_performed=False,
            equivalent_fabric_service="Foundry agent with the Fabric data agent tool (offline analog)",
            teaching_objective="Numbers come from a governed data tool, never from the model.",
            simulation_notice="LOCAL deterministic agent over synthetic data. No Foundry or Fabric call was made.",
            correlation_id=correlation_id or new_correlation_id(),
            data=data,
        )
