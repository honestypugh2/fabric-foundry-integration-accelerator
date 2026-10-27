"""Contract checks for portable vector architecture explorers."""

import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path

import pytest

from fabric_foundry_accelerator.education.diagrams import DiagramView, load_views
from fabric_foundry_accelerator.education.interactive_architecture import (
    explorer_assets,
    render_explorer,
    render_library,
)

ROOT = Path(__file__).resolve().parents[2]
VIEWS = load_views(ROOT / "education/architecture/views")


class ExplorerInspection(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[str] = []
        self.edges: list[str] = []
        self.ids: list[str] = []
        self.remote_assets: list[str] = []
        self.payload = ""
        self.in_payload = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if identifier := values.get("id"):
            self.ids.append(identifier)
        if node := values.get("data-node"):
            self.nodes.append(node)
            assert values["role"] == "button" and values["tabindex"] == "0"
        if edge := values.get("data-edge"):
            self.edges.append(edge)
        if tag in {"img", "iframe"} or values.get("src"):
            self.remote_assets.append(tag)
        if tag == "script" and "data-architecture" in values:
            self.in_payload = True

    def handle_data(self, data: str) -> None:
        if self.in_payload:
            self.payload += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.in_payload = False


@pytest.mark.parametrize("view", VIEWS, ids=[view.id for view in VIEWS])
def test_every_view_has_selectable_nodes_and_exact_authored_traces(view: DiagramView) -> None:
    html = render_explorer(view)
    parser = ExplorerInspection()
    parser.feed(html)
    assert parser.nodes == [node.id for node in view.nodes]
    assert parser.edges == [edge.id for edge in view.edges]
    assert len(parser.ids) == len(set(parser.ids))
    assert not parser.remote_assets
    assert json.loads(parser.payload)["view"] == view.model_dump(mode="json")
    assert view.traces
    for trace in view.traces:
        assert f'data-path="{trace.id}"' in html
        for step in trace.steps:
            assert escape(step.say) in html
    for control in (
        "data-layer",
        "data-start",
        "data-back",
        "data-next",
        "data-reset",
        "data-level",
    ):
        assert control in html


def test_library_has_unique_identifiers_and_no_external_runtime() -> None:
    html = render_library(ROOT, "")
    parser = ExplorerInspection()
    parser.feed(html)
    assert len(parser.ids) == len(set(parser.ids))
    assert not parser.remote_assets
    assert html.count('data-explorer="') == len(VIEWS)
    assets = explorer_assets()
    assert "<script>" in assets and "fetch(" not in assets
    assert "innerHTML" not in assets
    assert "localStorage" not in assets


def test_payload_escapes_markup_without_changing_source_meaning() -> None:
    view = VIEWS[0].model_copy(update={"summary": "</script><img src=x> & sample"})
    parser = ExplorerInspection()
    parser.feed(render_explorer(view))
    assert json.loads(parser.payload)["view"]["summary"] == view.summary
    assert "\\u003c/script\\u003e" in parser.payload
    assert not parser.remote_assets
