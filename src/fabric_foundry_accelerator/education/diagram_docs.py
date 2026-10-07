"""Generate the diagram sections of the architecture docs and the draw.io files from the views.

Each doc in ``docs/architecture`` keeps hand-written prose and one generated block between
markers. ``ffia diagrams render`` rewrites the blocks and the ``.drawio`` files; ``ffia diagrams
check`` fails when they are stale, so diagrams, docs and the app never drift apart.
"""

import argparse
import sys
from pathlib import Path

from fabric_foundry_accelerator.education.diagrams import DiagramView, render_mermaid
from fabric_foundry_accelerator.education.drawio import STATE_TEXT, render_drawio
from fabric_foundry_accelerator.education.guides import load_guides
from fabric_foundry_accelerator.education.lessons import (
    ArchitectureComponent,
    EducationLibrary,
    EducationReferences,
    load_education,
)
from fabric_foundry_accelerator.patterns.catalog import load_catalog
from fabric_foundry_accelerator.research.sources import (
    DEFAULT_REGISTRY_PATH,
    SourceRegistry,
    load_registry,
)

BEGIN = "<!-- BEGIN GENERATED DIAGRAM: run `ffia diagrams render`; do not edit by hand -->"
END = "<!-- END GENERATED DIAGRAM -->"
DOCS_ROOT = Path("docs/architecture")


class DiagramDocError(ValueError):
    """Raised when a doc is missing or lacks the generated-block markers."""


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _role(node_summary: str, component: ArchitectureComponent | None) -> str:
    if component is not None:
        return component.description.l200
    return node_summary


def _status(view: DiagramView, node_id: str) -> str:
    node = next(n for n in view.nodes if n.id == node_id)
    text = STATE_TEXT[node.state]
    return f"{text} (Phase {node.phase})" if node.state == "planned" else text


def render_block(view: DiagramView, library: EducationLibrary, registry: SourceRegistry) -> str:
    """Render the generated Markdown block for one view."""
    components = {c.id: c for c in library.architecture.components}
    sources = {s.id: s for s in registry.sources}
    lines = [
        BEGIN,
        "",
        f"> Generated from [`education/architecture/views/{view.id}.yaml`]"
        f"(../../education/architecture/views/{view.id}.yaml). Edit the YAML, then run "
        "`ffia diagrams render`.",
        "",
        f"- **draw.io:** [diagrams/{view.id}.drawio](diagrams/{view.id}.drawio). Open it in draw.io "
        "desktop, diagrams.net or the VS Code Draw.io Integration extension. Page 1 is the full "
        "architecture; the next pages build it up one step at a time.",
        f"- **Interactive:** run `make run`, then open `http://localhost:5173/architecture/{view.id}` "
        "to build it step by step, trace requests, switch Executive to L400 and see live runtime state.",
        "",
        "```mermaid",
        render_mermaid(view).rstrip(),
        "```",
        "",
        "Solid boxes are implemented here or documented by Microsoft; dashed boxes are planned, "
        "preview or optional.",
        "",
    ]
    for trace in view.traces:
        heading = "Workflow" if trace is view.traces[0] else f"Flow: {trace.title}"
        act = f" Offline demo act {trace.demo_act}." if trace.demo_act else ""
        lines += [f"### {heading}", "", f"*{trace.label}.* {trace.summary}{act}", ""]
        for number, hop in enumerate(trace.steps, start=1):
            note = f" {hop.note}" if hop.note else ""
            lines.append(f"{number}. {hop.say}{note}")
        lines.append("")
    lines += [
        "### Components",
        "",
        "| Component | Status | Role | In this repository |",
        "|---|---|---|---|",
    ]
    for node in view.nodes:
        component = components.get(node.component) if node.component else None
        where = f"`{node.repo_path}`" if node.repo_path else "-"
        lines.append(
            f"| {_cell(node.label)} | {_status(view, node.id)} | "
            f"{_cell(_role(node.summary, component))} | {where} |"
        )
    if view.aligned_to:
        lines += ["", "### Aligned to", ""]
        for source_id in view.aligned_to:
            source = sources[source_id]
            lines.append(f"- [{source.title}]({source.url}) ({source.status})")
    lines += ["", END]
    return "\n".join(lines)


def render_artifacts(
    library: EducationLibrary, registry: SourceRegistry, docs_root: Path = DOCS_ROOT
) -> dict[Path, str]:
    """Render every generated doc block and draw.io file.

    Raises:
        DiagramDocError: when a view's doc is missing or has no generated-block markers.
    """
    artifacts: dict[Path, str] = {}
    for view in library.views:
        artifacts[docs_root / "diagrams" / f"{view.id}.drawio"] = render_drawio(view)
        if view.doc is None:
            continue
        doc = docs_root / f"{view.doc}.md"
        if not doc.is_file():
            raise DiagramDocError(f"view {view.id}: {doc} does not exist")
        text = doc.read_text(encoding="utf-8")
        if BEGIN not in text or END not in text:
            raise DiagramDocError(f"{doc} has no generated-diagram markers")
        head, rest = text.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        artifacts[doc] = head + render_block(view, library, registry) + tail
    return artifacts


def _library(args: argparse.Namespace) -> tuple[EducationLibrary, SourceRegistry]:
    education_root = Path(args.education_root)
    catalog = load_catalog(education_root)
    registry = load_registry(Path(args.sources))
    refs = EducationReferences(
        pattern_ids=frozenset(p.id for p in catalog.patterns),
        source_ids=frozenset(s.id for s in registry.sources),
        guide_ids=frozenset(load_guides(Path(args.guides_root), catalog)),
    )
    return load_education(education_root, refs), registry


def _cmd_render(args: argparse.Namespace) -> int:
    library, registry = _library(args)
    artifacts = render_artifacts(library, registry, Path(args.docs_root))
    for path, text in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    sys.stdout.write(
        f"rendered {len(artifacts)} diagram artifacts (draw.io files and doc blocks)\n"
    )
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    library, registry = _library(args)
    try:
        artifacts = render_artifacts(library, registry, Path(args.docs_root))
    except DiagramDocError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    stale = [
        path
        for path, text in artifacts.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != text
    ]
    for path in stale:
        sys.stderr.write(f"{path} is stale; run `ffia diagrams render`\n")
    if not stale:
        sys.stdout.write(f"{len(artifacts)} diagram artifacts are up to date\n")
    return 1 if stale else 0


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:  # pyright: ignore[reportPrivateUsage]
    """Register ``diagrams`` subcommands."""
    diagrams = subparsers.add_parser("diagrams", help="architecture diagrams (draw.io and docs)")
    sub = diagrams.add_subparsers(dest="diagrams_command", required=True)
    for name, func, text in (
        ("render", _cmd_render, "write draw.io files and the generated doc blocks"),
        ("check", _cmd_check, "fail if draw.io files or doc blocks are stale"),
    ):
        command = sub.add_parser(name, help=text)
        command.add_argument("--education-root", default="education")
        command.add_argument("--guides-root", default="guides")
        command.add_argument("--sources", default=str(DEFAULT_REGISTRY_PATH))
        command.add_argument("--docs-root", default=str(DOCS_ROOT))
        command.set_defaults(func=func)
