"""``ffia agents ask|eval|workflow``: the sales agent (LOCAL by default; live Foundry is opt-in)."""

import argparse
import asyncio
import sys

from fabric_foundry_accelerator.agents.port import AgentQuestion
from fabric_foundry_accelerator.agents.workflows import (
    MonthlyInsightsRequest,
    live_safe_concurrency,
    run_monthly_insights,
)
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.evaluation.agent_eval import load_suite, run_suite
from fabric_foundry_accelerator.observability.tracing import configure_tracing
from fabric_foundry_accelerator.services.container import build_container


def _cmd_ask(args: argparse.Namespace) -> int:
    settings = Settings()
    configure_tracing(settings.applicationinsights_connection_string)
    container = build_container(settings)
    question = AgentQuestion(agent=args.agent, question=" ".join(args.question))
    envelope = asyncio.run(container.agents.ask(question))
    if args.json:
        sys.stdout.write(envelope.model_dump_json(indent=2) + "\n")
        return 0
    answer = envelope.data
    sys.stdout.write(
        f"[{envelope.execution_label.value}] {envelope.selected_provider}\n\n{answer.answer}\n"
    )
    if answer.tool_calls:
        sys.stdout.write("\nTools used: " + ", ".join(c.name for c in answer.tool_calls) + "\n")
    if not answer.grounded and answer.supported_questions:
        sys.stdout.write(
            "\nSupported offline questions:\n"
            + "".join(f"  - {q}\n" for q in answer.supported_questions)
        )
    if envelope.fallback_used:
        sys.stdout.write(f"\nFallback: {envelope.fallback_reason}\n")
    return 0


def _cmd_eval(args: argparse.Namespace) -> int:
    settings = Settings()
    configure_tracing(settings.applicationinsights_connection_string)
    container = build_container(settings)
    suite = load_suite(settings.config_root, args.suite)
    report = asyncio.run(run_suite(container.agents, suite))
    if args.json:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
        return 0 if report.gate_passed else 1
    sys.stdout.write(
        f"Agent evaluation: {suite.id} via {report.provider} [{', '.join(report.labels)}]\n"
    )
    for case in report.cases:
        mark = "PASS" if case.passed else "FAIL"
        detail = (
            f"missing {', '.join(case.missing)}" if case.missing else f"grounded={case.grounded}"
        )
        sys.stdout.write(f"  [{mark}] {case.id}: {detail}\n")
    sys.stdout.write(f"\n{report.passed}/{report.compared} passed; gate {report.status}\n")
    return 0 if report.gate_passed else 1


def _cmd_workflow(args: argparse.Namespace) -> int:
    settings = Settings()
    configure_tracing(settings.applicationinsights_connection_string)
    container = build_container(settings)
    run = asyncio.run(
        run_monthly_insights(
            container.agents,
            settings.data_root,
            MonthlyInsightsRequest(teams=tuple(args.team)),
            max_concurrency=live_safe_concurrency(container.agents),
        )
    )
    if args.json:
        sys.stdout.write(run.model_dump_json(indent=2) + "\n")
        return 0
    sys.stdout.write(
        f"Workflow {run.workflow} ({run.engine}) [{', '.join(run.labels)}], "
        f"month {run.observation_month}\n"
    )
    for draft in run.drafts:
        sys.stdout.write(f"\n[{draft.status.value}] {draft.team_name}: {draft.reason}\n")
        sys.stdout.write(f"  {draft.answer}\n")
    sys.stdout.write(
        f"\n{run.ready} ready for approval, {run.held} held.\n{run.delivery}\n{run.synthetic_notice}\n"
    )
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``agents`` subcommands."""
    agents = subparsers.add_parser("agents", help="ask agents (LOCAL by default; Foundry opt-in)")
    sub = agents.add_subparsers(dest="agents_command", required=True)
    ask = sub.add_parser("ask", help="ask the sales agent a question")
    ask.add_argument("question", nargs="+")
    ask.add_argument("--agent", default="sales-insights-agent")
    ask.add_argument("--json", action="store_true")
    ask.set_defaults(func=_cmd_ask)
    evaluate = sub.add_parser("eval", help="evaluate the agent against the governed baseline")
    evaluate.add_argument("--suite", default="sales-insights-agent")
    evaluate.add_argument("--json", action="store_true")
    evaluate.set_defaults(func=_cmd_eval)
    workflow = sub.add_parser(
        "workflow",
        help="run the monthly-insights Agent Framework workflow (drafts only; nothing is sent)",
    )
    workflow.add_argument(
        "--team", action="append", default=[], help="team id (repeatable; default: all)"
    )
    workflow.add_argument("--json", action="store_true")
    workflow.set_defaults(func=_cmd_workflow)
