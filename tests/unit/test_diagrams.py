import xml.etree.ElementTree as ET
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from tests.conftest import REPO_ROOT

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.education.diagram_docs import (
    BEGIN,
    END,
    DiagramDocError,
    render_artifacts,
    render_block,
)
from fabric_foundry_accelerator.education.diagrams import (
    DiagramNode,
    DiagramView,
    load_view,
    load_views,
    render_mermaid,
    view_reference_errors,
    visible,
)
from fabric_foundry_accelerator.education.drawio import render_drawio
from fabric_foundry_accelerator.education.layout import Box, compute_layout
from fabric_foundry_accelerator.education.lessons import EducationLibrary, guide_diagram_errors
from fabric_foundry_accelerator.research.sources import load_registry
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.diagram_runtime import view_runtime

VIEWS = REPO_ROOT / "education" / "architecture" / "views"
VIEW_IDS = sorted(p.stem for p in VIEWS.glob("*.yaml"))


def _minimal(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "mini",
        "title": "Mini",
        "kind": "system",
        "summary": "s",
        "cue": "c",
        "columns": 3,
        "rows": 2,
        "steps": [
            {"id": "one", "label": "One", "cue": "c"},
            {"id": "two", "label": "Two", "cue": "c"},
        ],
        "nodes": [
            {
                "id": "a",
                "label": "A",
                "kind": "app",
                "state": "implemented",
                "col": 0,
                "row": 0,
                "summary": "a",
            },
            {
                "id": "b",
                "label": "B",
                "kind": "local",
                "state": "implemented",
                "col": 2,
                "row": 0,
                "summary": "b",
            },
            {
                "id": "c",
                "label": "C",
                "kind": "local",
                "state": "planned",
                "phase": 5,
                "col": 1,
                "row": 0,
                "step": "two",
                "summary": "c",
            },
        ],
        "edges": [{"id": "ab", "source": "a", "target": "b", "label": "Reads", "kind": "access"}],
        "traces": [
            {
                "id": "t",
                "title": "T",
                "summary": "s",
                "label": "LOCAL",
                "steps": [{"node": "a", "say": "go"}, {"node": "b", "edge": "ab", "say": "arrive"}],
            }
        ],
    }
    data.update(overrides)
    return data


@pytest.fixture(scope="module")
def views() -> tuple[DiagramView, ...]:
    return load_views(VIEWS)


# ------------------------------------------------------------------ model rules
def test_repository_views_load(views: tuple[DiagramView, ...]) -> None:
    assert {v.id for v in views} >= {
        "reference",
        "production",
        "system",
        "mcp-topology",
        "agentic-de",
        "hc-01",
        "live-vs-offline",
    }
    for view in views:
        assert view.traces, view.id
        assert all(n.state != "planned" or n.phase for n in view.nodes)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {
                "nodes": [
                    {
                        "id": "a",
                        "label": "A",
                        "kind": "app",
                        "state": "implemented",
                        "col": 0,
                        "row": 0,
                    }
                ]
            },
            "needs a component",
        ),
        (
            {
                "nodes": [
                    {
                        "id": "a",
                        "label": "A",
                        "kind": "app",
                        "state": "planned",
                        "col": 0,
                        "row": 0,
                        "summary": "s",
                    }
                ]
            },
            "must name the phase",
        ),
        (
            {
                "nodes": [
                    {
                        "id": "a",
                        "label": "A",
                        "kind": "app",
                        "state": "implemented",
                        "col": 0,
                        "row": 0,
                        "summary": "s",
                        "icon": "nope/Nope",
                    }
                ]
            },
            "unknown draw.io Azure icon",
        ),
    ],
)
def test_node_rules(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        DiagramView.model_validate(_minimal(**overrides))


def test_view_consistency_rules() -> None:
    DiagramView.model_validate(_minimal())
    bad_edge = [{"id": "x", "source": "a", "target": "zz", "kind": "access"}]
    with pytest.raises(ValidationError, match="unknown nodes"):
        DiagramView.model_validate(_minimal(edges=bad_edge))
    with pytest.raises(ValidationError, match="outside the 3x2 grid"):
        DiagramView.model_validate(
            _minimal(
                nodes=[
                    {
                        "id": "a",
                        "label": "A",
                        "kind": "app",
                        "state": "implemented",
                        "col": 3,
                        "row": 0,
                        "summary": "s",
                    },
                    {
                        "id": "z",
                        "label": "Z",
                        "kind": "app",
                        "state": "implemented",
                        "col": 0,
                        "row": 1,
                        "summary": "s",
                    },
                ],
                edges=[],
                traces=[],
            )
        )
    with pytest.raises(ValidationError, match="unknown step"):
        DiagramView.model_validate(
            _minimal(
                zones=[
                    {
                        "id": "z",
                        "label": "Z",
                        "kind": "local",
                        "col": 0,
                        "row": 0,
                        "cols": 1,
                        "rows": 1,
                        "step": "nope",
                    }
                ]
            )
        )
    with pytest.raises(ValidationError, match="zone z is outside"):
        DiagramView.model_validate(
            _minimal(
                zones=[
                    {
                        "id": "z",
                        "label": "Z",
                        "kind": "local",
                        "col": 2,
                        "row": 0,
                        "cols": 2,
                        "rows": 1,
                    }
                ]
            )
        )
    with pytest.raises(ValidationError, match="duplicate node ids"):
        data = _minimal()
        nodes = data["nodes"]
        assert isinstance(nodes, list)
        DiagramView.model_validate({**data, "nodes": [*nodes, nodes[0]]})
    bad_trace = [
        {
            "id": "t",
            "title": "T",
            "summary": "s",
            "label": "LOCAL",
            "steps": [{"node": "zz", "say": "x"}, {"node": "a", "edge": "nope", "say": "y"}],
        }
    ]
    with pytest.raises(ValidationError, match="unknown node zz") as error:
        DiagramView.model_validate(_minimal(traces=bad_trace))
    assert "unknown edge nope" in str(error.value)


def test_view_file_name_and_references(tmp_path: Path) -> None:
    import yaml  # noqa: PLC0415

    path = tmp_path / "other.yaml"
    path.write_text(yaml.safe_dump(_minimal()), encoding="utf-8")
    with pytest.raises(ValueError, match=r"must be saved as mini\.yaml"):
        load_view(path)
    view = DiagramView.model_validate(
        _minimal(
            aligned_to=["nope"],
            pattern_ids=["P99"],
            nodes=[
                {
                    "id": "a",
                    "label": "A",
                    "kind": "app",
                    "state": "implemented",
                    "col": 0,
                    "row": 0,
                    "component": "ghost",
                },
                {
                    "id": "z",
                    "label": "Z",
                    "kind": "app",
                    "state": "implemented",
                    "col": 0,
                    "row": 1,
                    "summary": "s",
                },
            ],
            edges=[],
            traces=[],
        )
    )
    errors = view_reference_errors(
        view, component_ids=set(), source_ids=frozenset(), pattern_ids=frozenset()
    )
    assert any("unknown component ghost" in e for e in errors)
    assert any("unknown source nope" in e for e in errors)
    assert any("unknown pattern P99" in e for e in errors)


def test_visibility_and_mermaid() -> None:
    view = DiagramView.model_validate(
        _minimal(
            zones=[
                {
                    "id": "z",
                    "label": 'Local "zone"',
                    "kind": "local",
                    "col": 0,
                    "row": 0,
                    "cols": 1,
                    "rows": 1,
                }
            ]
        )
    )
    assert visible(None, view.steps, "one") and visible("one", view.steps, "two")
    assert not visible("two", view.steps, "one")
    full = render_mermaid(view)
    assert full.startswith("flowchart LR") and "subgraph z[\"Local 'zone'\"]" in full
    assert "a -->|Reads| b" in full and "c[" in full and "· planned" in full
    assert "c[" not in render_mermaid(view, step="one")


# ------------------------------------------------------------------ layout
def _crosses(box: Box, a: tuple[float, float], b: tuple[float, float]) -> bool:
    """True when an axis-aligned segment passes through the interior of a box."""
    (x1, y1), (x2, y2) = a, b
    if y1 == y2:
        return box.y < y1 < box.bottom and max(min(x1, x2), box.x) < min(max(x1, x2), box.right)
    return box.x < x1 < box.right and max(min(y1, y2), box.y) < min(max(y1, y2), box.bottom)


@pytest.mark.parametrize("view_id", VIEW_IDS)
def test_edges_never_cross_other_cards(view_id: str) -> None:
    view = load_view(VIEWS / f"{view_id}.yaml")
    layout = compute_layout(view)
    for edge in view.edges:
        path = layout.edges[edge.id]
        assert all(a[0] == b[0] or a[1] == b[1] for a, b in pairwise(path.points)), "orthogonal"
        for node_id, box in layout.nodes.items():
            if node_id in (edge.source, edge.target):
                continue
            for a, b in pairwise(path.points):
                assert not _crosses(box, a, b), f"{view_id}: {edge.id} crosses {node_id}"
        assert 0 < path.label_fraction < 1


def test_layout_routing_strategies() -> None:
    def node(nid: str, col: int, row: int) -> dict[str, object]:
        return {
            "id": nid,
            "label": nid,
            "kind": "app",
            "state": "implemented",
            "col": col,
            "row": row,
            "summary": "s",
        }

    view = DiagramView.model_validate(
        _minimal(
            columns=4,
            rows=4,
            steps=[],
            nodes=[
                node("a", 0, 0),
                node("b", 3, 0),
                node("block", 1, 0),
                node("down", 0, 2),
                node("block2", 0, 1),
                node("c", 3, 3),
                node("block3", 1, 3),
                node("d", 2, 2),
            ],
            edges=[
                {"id": "around-row", "source": "a", "target": "b", "kind": "access"},
                {"id": "side", "source": "a", "target": "down", "kind": "access"},
                {"id": "gap", "source": "down", "target": "c", "kind": "access"},
                {"id": "left", "source": "d", "target": "down", "kind": "access"},
                {"id": "up", "source": "block2", "target": "a", "kind": "access"},
            ],
            traces=[],
        )
    )
    layout = compute_layout(view)
    assert len(layout.edges["around-row"].points) in (4, 6)
    assert layout.edges["side"].points[0][0] == layout.nodes["a"].right
    assert len(layout.edges["gap"].points) >= 4
    assert layout.edges["left"].points[-1][0] == layout.nodes["down"].right
    assert len(layout.edges["up"].points) == 2


# ------------------------------------------------------------------ draw.io and docs
@pytest.mark.parametrize("view_id", VIEW_IDS)
def test_drawio_is_well_formed_and_deterministic(view_id: str) -> None:
    view = load_view(VIEWS / f"{view_id}.yaml")
    text = render_drawio(view)
    assert text == render_drawio(view)
    root = ET.fromstring(text)  # noqa: S314 - parsing our own generated output
    pages = root.findall("diagram")
    assert len(pages) == 1 + len(view.steps)
    first = pages[0]
    cell_ids = [c.get("id") for c in first.iter("mxCell")]
    assert len(cell_ids) == len(set(cell_ids))
    for edge in first.iter("mxCell"):
        if edge.get("edge") == "1":
            assert edge.get("source") in cell_ids and edge.get("target") in cell_ids
    icons = [n.icon for n in view.nodes if n.icon]
    assert all(f"img/lib/azure2/{icon}.svg" in text for icon in icons)


def test_repository_docs_and_drawio_are_current(capsys: pytest.CaptureFixture[str]) -> None:
    args = [
        "diagrams",
        "check",
        "--education-root",
        str(REPO_ROOT / "education"),
        "--guides-root",
        str(REPO_ROOT / "guides"),
        "--sources",
        str(REPO_ROOT / "docs" / "research" / "sources.yaml"),
        "--docs-root",
        str(REPO_ROOT / "docs" / "architecture"),
    ]
    assert main(args) == 0
    assert "up to date" in capsys.readouterr().out


def test_render_and_check_in_a_scratch_docs_tree(
    tmp_path: Path, make_container: Callable[..., Container], capsys: pytest.CaptureFixture[str]
) -> None:
    library = make_container().education.library
    registry = load_registry(REPO_ROOT / "docs" / "research" / "sources.yaml")
    with pytest.raises(DiagramDocError, match="does not exist"):
        render_artifacts(library, registry, tmp_path)
    for view in library.views:
        if view.doc:
            (tmp_path / f"{view.doc}.md").write_text(
                f"# {view.title}\n\n{BEGIN}\n{END}\n", encoding="utf-8"
            )
    common = [
        "--education-root",
        str(REPO_ROOT / "education"),
        "--guides-root",
        str(REPO_ROOT / "guides"),
        "--sources",
        str(REPO_ROOT / "docs" / "research" / "sources.yaml"),
        "--docs-root",
        str(tmp_path),
    ]
    assert main(["diagrams", "check", *common]) == 1
    assert main(["diagrams", "render", *common]) == 0
    assert main(["diagrams", "check", *common]) == 0
    reference = (tmp_path / "reference-architecture.md").read_text(encoding="utf-8")
    assert (
        "```mermaid" in reference and "### Workflow" in reference and "### Aligned to" in reference
    )
    (tmp_path / "reference-architecture.md").write_text("# no markers\n", encoding="utf-8")
    assert main(["diagrams", "check", *common]) == 1
    assert "no generated-diagram markers" in capsys.readouterr().err


def test_doc_block_reports_repository_status(make_container: Callable[..., Container]) -> None:
    library = make_container().education.library
    registry = load_registry(REPO_ROOT / "docs" / "research" / "sources.yaml")
    block = render_block(library.view("system"), library, registry)
    assert "| FastAPI control plane | Implemented in this repository |" in block
    assert "| Foundry Agent Service | Planned (Phase 6) |" in block


# ------------------------------------------------------------------ runtime overlay, guides, API
def test_runtime_overlay_never_claims_unconfigured_services(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    overlay = {
        n.node: n for n in view_runtime(container, container.education.library.view("system")).nodes
    }
    assert (
        overlay["foundry"].status == "NOT CONFIGURED"
        and overlay["fabric-live"].status == "NOT CONFIGURED"
    )
    assert overlay["local-provider"].status == "ACTIVE" and overlay["api"].status == "ACTIVE"
    outage = make_container(environment="hybrid", simulate_fabric_outage=True)
    degraded = {
        n.node: n
        for n in view_runtime(outage, outage.education.library.view("live-vs-offline")).nodes
    }
    assert degraded["live"].status == "DEGRADED" and degraded["live"].label == "FAULT-INJECTION"
    assert "Approved fallback" in degraded["local"].detail


async def test_runtime_overlay_reports_open_breaker(
    make_container: Callable[..., Container],
) -> None:
    container = make_container(environment="hybrid", simulate_fabric_outage=True)
    for _ in range(4):
        await container.fabric.list_tables("local-lh-hc-lab-7file-v1")
    overlay = {
        n.node: n for n in view_runtime(container, container.education.library.view("system")).nodes
    }
    assert (
        "OPEN" in overlay["fabric-live"].detail and "fabric_data OPEN" in overlay["router"].detail
    )


def test_guide_diagram_references(make_container: Callable[..., Container]) -> None:
    container = make_container()
    library: EducationLibrary = container.education.library
    assert guide_diagram_errors(library, container.guides) == []
    guide = container.guides["hc-01-fabric-mcp-powerbi-medallion-lab"]
    bad_step = guide.steps[0].model_copy(update={"diagram_focus": ("ghost",)})
    broken = guide.model_copy(update={"steps": (bad_step, *guide.steps[1:])})
    assert guide_diagram_errors(library, {"g": broken}) == [
        f"guide {guide.id} step {bad_step.id}: unknown diagram node ghost"
    ]
    assert guide_diagram_errors(library, {"g": guide.model_copy(update={"diagram": "nope"})}) == [
        f"guide {guide.id}: unknown diagram nope"
    ]
    assert guide_diagram_errors(library, {"g": guide.model_copy(update={"diagram": None})})[
        0
    ].endswith("needs a guide diagram")


def test_view_endpoints(make_container: Callable[..., Container]) -> None:
    with TestClient(create_app(make_container())) as client:
        listed = client.get("/api/v1/education/views").json()
        assert {v["id"] for v in listed} >= {"reference", "system"} and "pattern_ids" in listed[0]
        rendered = client.get("/api/v1/education/views/system").json()
        assert rendered["view"]["id"] == "system" and rendered["layout"]["edges"]
        runtime = client.get("/api/v1/education/views/system/runtime").json()
        assert runtime["operating_mode"] == "OFFLINE"
        drawio = client.get("/api/v1/education/views/reference/drawio")
        assert drawio.status_code == 200 and drawio.text.startswith("<mxfile")
        assert "reference.drawio" in drawio.headers["content-disposition"]
        assert client.get("/api/v1/education/views/nope").status_code == 404


def test_node_model_accepts_documented_icon() -> None:
    node = DiagramNode(
        id="x",
        label="X",
        kind="gateway",
        state="documented",
        col=0,
        row=0,
        summary="s",
        icon="app_services/API_Management_Services",
    )
    assert node.icon == "app_services/API_Management_Services"
