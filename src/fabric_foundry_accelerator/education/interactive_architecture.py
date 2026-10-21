"""Offline architecture explorers rendered from the same contracts as the React studio."""

import json
from html import escape
from importlib.resources import files
from pathlib import Path

import yaml

from fabric_foundry_accelerator.education.diagrams import DiagramView, load_views
from fabric_foundry_accelerator.education.lessons import ArchitectureComponent, ArchitectureMap
from fabric_foundry_accelerator.education.svg import render_svg


def explorer_assets() -> str:
    """Inline the local explorer stylesheet and script without runtime dependencies."""
    assets = files("fabric_foundry_accelerator.education")
    css = assets.joinpath("architecture_explorer.css").read_text(encoding="utf-8")
    script = assets.joinpath("architecture_explorer.js").read_text(encoding="utf-8")
    return f"<style>{css}</style><script>{script}</script>"


def render_explorer(view: DiagramView, components: tuple[ArchitectureComponent, ...] = ()) -> str:
    """Render selectable vector nodes, connection drilldowns and every authored trace."""
    identifier = f"explorer-{view.id}"
    names = {node.id: node.label for node in view.nodes}
    data = (
        json.dumps(
            {
                "view": view.model_dump(mode="json"),
                "components": {item.id: item.model_dump(mode="json") for item in components},
            }
        )
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    traces = "".join(
        f'<option value="{trace.id}">{escape(trace.title)}</option>' for trace in view.traces
    )
    layers = "".join(
        f'<option value="{step.id}">{escape(step.label)}</option>' for step in view.steps
    )
    return (
        f'<section class="arch-explorer" data-explorer="{view.id}" id="{identifier}"'
        f' aria-labelledby="{identifier}-title"><h3 id="{identifier}-title">{escape(view.title)}</h3>'
        f"<p>{escape(view.summary)}</p>"
        "<p>Click a node or use Tab and Enter to inspect its role, responsibilities, connections"
        " and evidence. Traces explain the design; they do not execute a cloud operation.</p>"
        '<div class="arch-toolbar">'
        f'<label>Build layer <select data-layer><option value="">Full picture</option>{layers}</select></label>'
        f"<label>Request trace <select data-trace>{traces}</select></label>"
        '<button type="button" data-start>Start trace</button>'
        '<button type="button" data-back disabled>Previous hop</button>'
        '<button type="button" data-next disabled>Next hop</button>'
        '<button type="button" data-reset>Reset</button>'
        "<label>Learning depth <select data-level>"
        '<option value="executive">Executive</option><option value="l100" selected>L100</option>'
        '<option value="l200">L200</option><option value="l300">L300</option>'
        '<option value="l400">L400</option></select></label></div>'
        f'<p class="arch-cue" role="status" aria-live="polite">{escape(view.cue)}</p>'
        '<div class="arch-workspace"><div class="arch-scroll">'
        + render_svg(view, title_id=f"{identifier}-svg", interactive=True)
        + '</div><aside class="arch-inspector" aria-label="Node details">'
        "<p>Select a component to explore it.</p></aside></div>"
        "<details><summary>Trace steps and text alternative</summary>"
        + "".join(
            f"<h4>{escape(trace.title)} ({escape(trace.label)})</h4>"
            f"<p>{escape(trace.summary)}</p><ol>"
            + "".join(
                f'<li><button type="button" data-hop="{index}" data-path="{trace.id}">'
                f"{escape(names[hop.node])}"
                f"</button><p>{escape(hop.say)}</p><p>{escape(hop.note)}</p></li>"
                for index, hop in enumerate(trace.steps)
            )
            + "</ol>"
            for trace in view.traces
        )
        + "<h4>Components</h4><ul>"
        + "".join(
            f'<li><button type="button" data-inspect="{node.id}">{escape(node.label)}</button>'
            f" — {escape(node.summary or node.sublabel)} ({escape(node.state)})</li>"
            for node in view.nodes
        )
        + '</ul></details><script type="application/json" data-architecture>'
        + data
        + "</script><noscript><p>JavaScript is disabled. Read the component list and trace"
        " steps above; interactive inspection requires JavaScript.</p></noscript></section>"
    )


def render_library(root: Path, style: str) -> str:
    """Build a portable page with every canonical view and component description."""
    components = ArchitectureMap.model_validate(
        yaml.safe_load((root / "education/architecture/explorer.yaml").read_text(encoding="utf-8"))
    ).components
    explorers = "".join(
        render_explorer(view, components)
        for view in load_views(root / "education/architecture/views")
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Architecture explorer</title><style>{style}</style>{explorer_assets()}"
        '</head><body><main class="wrap"><h1>Explore every architecture</h1>'
        "<p>Inspect nodes, follow connections, choose a learning depth and trace each request. "
        f"These explanations do not run cloud tools.</p>{explorers}</main></body></html>"
    )
