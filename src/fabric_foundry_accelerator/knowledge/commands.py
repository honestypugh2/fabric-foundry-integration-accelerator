"""``ffia knowledge search``: cited passages from the synthetic knowledge base (PREVIEW flag)."""

import argparse
import sys

from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.knowledge.local import (
    PREVIEW_FLAG,
    KnowledgeQuery,
    search_knowledge,
)
from fabric_foundry_accelerator.services.container import build_container


def _cmd_search(args: argparse.Namespace) -> int:
    settings = Settings()
    container = build_container(settings)
    envelope = search_knowledge(
        KnowledgeQuery(question=" ".join(args.question), top=args.top),
        data_root=settings.data_root,
        enabled=PREVIEW_FLAG in container.overlay.enabled_previews(),
        mode=container.environment.mode,
    )
    if args.json:
        sys.stdout.write(envelope.model_dump_json(indent=2) + "\n")
        return 0
    result = envelope.data
    sys.stdout.write(f"[{envelope.execution_label.value}] {envelope.selected_provider}\n")
    if envelope.simulation_notice:
        sys.stdout.write(f"{envelope.simulation_notice}\n")
    for index, passage in enumerate(result.passages, start=1):
        c = passage.citation
        sys.stdout.write(f"\n[{index}] {c.title} > {c.section} ({c.path})\n    {passage.text}\n")
    sys.stdout.write(f"\n{result.note}\n")
    return 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``knowledge`` subcommands."""
    knowledge = subparsers.add_parser(
        "knowledge", help="Foundry IQ knowledge analog (PREVIEW flag; SIMULATED offline)"
    )
    sub = knowledge.add_subparsers(dest="knowledge_command", required=True)
    search = sub.add_parser("search", help="retrieve cited passages for a question")
    search.add_argument("question", nargs="+")
    search.add_argument("--top", type=int, default=3, choices=range(1, 6))
    search.add_argument("--json", action="store_true")
    search.set_defaults(func=_cmd_search)
