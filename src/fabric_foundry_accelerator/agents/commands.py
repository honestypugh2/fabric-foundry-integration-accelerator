"""``ffia agents ask``: ask the sales agent (LOCAL by default; live Foundry is opt-in)."""

import argparse
import asyncio
import sys

from fabric_foundry_accelerator.agents.port import AgentQuestion
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.services.container import build_container


def _cmd_ask(args: argparse.Namespace) -> int:
    container = build_container(Settings())
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


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``agents`` subcommands."""
    agents = subparsers.add_parser("agents", help="ask agents (LOCAL by default; Foundry opt-in)")
    sub = agents.add_subparsers(dest="agents_command", required=True)
    ask = sub.add_parser("ask", help="ask the sales agent a question")
    ask.add_argument("question", nargs="+")
    ask.add_argument("--agent", default="sales-insights-agent")
    ask.add_argument("--json", action="store_true")
    ask.set_defaults(func=_cmd_ask)
