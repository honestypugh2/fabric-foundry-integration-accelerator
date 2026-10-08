"""Architecture diagram views: data for the interactive SVG diagrams and the generated Mermaid docs.

A view is a grid of nodes, edges, zones and bands that can be built up step by step (like a
whiteboard), traced one request at a time, and overlaid with the live runtime state. Nodes link
to components in ``education/architecture/explorer.yaml`` so descriptions have a single source.
Every node states what it is in this repository (implemented, planned, documented, preview,
requires tenant validation or optional), so diagrams never overstate what exists.
"""

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

_SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"

ViewKind = Literal["reference", "system", "topology", "flow", "maturity", "resilience"]
NodeState = Literal[
    "implemented", "planned", "documented", "preview", "tenant-validation", "optional"
]
NodeKind = Literal[
    "person",
    "client",
    "harness",
    "knowledge",
    "app",
    "service",
    "foundry",
    "fabric",
    "data",
    "mcp",
    "gateway",
    "identity",
    "policy",
    "evidence",
    "local",
    "external",
]
EdgeKind = Literal[
    "context",
    "reasoning",
    "access",
    "authority",
    "evidence",
    "fallback",
    "change",
    "data",
    "config",
]
ZoneKind = Literal["local", "tenant", "fabric", "foundry", "github", "optional", "offline"]
BandKind = Literal["identity", "policy", "evidence", "failure", "network"]
RuntimeBinding = Literal[
    "agents",
    "api",
    "mcp",
    "fabric-local",
    "fabric-live",
    "foundry",
    "changes",
    "audit",
    "education",
    "evaluation",
    "router",
]
TraceLabel = Literal["PLANNED FLOW", "LOCAL", "SIMULATED", "PREVIEW", "DOCUMENTED"]

# Official Azure architecture icons that ship with draw.io (img/lib/azure2/<path>.svg), verified in
# the jgraph/drawio repository on 2026-10-07. Diagrams reference them by path; the repository
# never copies icon files. Microsoft Fabric, GitHub and Claude have no draw.io icon, so those
# nodes are drawn as styled shapes instead.
AZURE_ICONS: frozenset[str] = frozenset(
    {
        "ai_machine_learning/AI_Foundry",
        "ai_machine_learning/AI_Foundry_IQ",
        "ai_machine_learning/Azure_OpenAI",
        "ai_machine_learning/Foundry_Agent_Service",
        "ai_machine_learning/Foundry_Models",
        "ai_machine_learning/Foundry_Project",
        "app_services/API_Management_Services",
        "app_services/App_Services",
        "app_services/Search_Services",
        "analytics/Log_Analytics_Workspaces",
        "databases/Azure_Cosmos_DB",
        "databases/Azure_Purview_Accounts",
        "devops/Application_Insights",
        "general/Browser",
        "general/Code",
        "general/File",
        "general/Folder_Blank",
        "general/Workflow",
        "identity/Entra_Managed_Identities",
        "identity/Users",
        "networking/Application_Gateways",
        "networking/Firewalls",
        "networking/Private_Endpoint",
        "networking/Web_Application_Firewall_Policies_WAF",
        "other/Entra_Identity",
        "power_platform/PowerBI",
        "security/Key_Vaults",
        "storage/Storage_Accounts",
    }
)


class DiagramStep(BaseModel):
    """One build-up step of a whiteboard view."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    label: str
    cue: str


class DiagramZone(BaseModel):
    """A labeled region (trust boundary, tenant, local machine, optional add-on)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    label: str
    kind: ZoneKind
    col: float = Field(ge=0)
    row: float = Field(ge=0)
    cols: float = Field(gt=0)
    rows: float = Field(gt=0)
    step: str | None = None


class DiagramNode(BaseModel):
    """A box on the diagram."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    label: str
    sublabel: str = ""
    kind: NodeKind
    state: NodeState
    col: float = Field(ge=0)
    row: float = Field(ge=0)
    width: float = Field(default=1, gt=0, le=6)
    step: str | None = None
    component: str | None = None
    summary: str = ""
    repo_path: str | None = None
    phase: int | None = Field(default=None, ge=1, le=9)
    runtime: RuntimeBinding | None = None
    icon: str | None = None
    sources: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _described(self) -> Self:
        if self.icon is not None and self.icon not in AZURE_ICONS:
            raise ValueError(f"node {self.id}: unknown draw.io Azure icon {self.icon!r}")
        if self.component is None and not self.summary:
            raise ValueError(f"node {self.id}: needs a component reference or a summary")
        if self.state == "planned" and self.phase is None:
            raise ValueError(f"node {self.id}: planned nodes must name the phase that adds them")
        return self


class DiagramEdge(BaseModel):
    """A directed arrow between two nodes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    source: str
    target: str
    label: str = ""
    kind: EdgeKind
    step: str | None = None
    planned: bool = False


class DiagramBand(BaseModel):
    """A cross-cutting rule drawn as a band under the diagram (identity, policy, evidence…)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    kind: BandKind
    text: str
    step: str | None = None


class TraceStep(BaseModel):
    """One hop of a traced request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    node: str
    edge: str | None = None
    say: str
    note: str = ""


class DiagramTrace(BaseModel):
    """A request followed one hop at a time."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    title: str
    summary: str
    label: TraceLabel
    demo_act: int | None = Field(default=None, ge=1, le=10)
    steps: tuple[TraceStep, ...] = Field(min_length=2)


class DiagramView(BaseModel):
    """``education/architecture/views/<id>.yaml``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=_SLUG)
    title: str
    kind: ViewKind
    summary: str
    cue: str
    columns: int = Field(ge=2, le=8)
    rows: int = Field(ge=1, le=10)
    aligned_to: tuple[str, ...] = ()
    pattern_ids: tuple[str, ...] = ()
    doc: str | None = None
    steps: tuple[DiagramStep, ...] = ()
    zones: tuple[DiagramZone, ...] = ()
    nodes: tuple[DiagramNode, ...] = Field(min_length=2)
    edges: tuple[DiagramEdge, ...] = ()
    bands: tuple[DiagramBand, ...] = ()
    traces: tuple[DiagramTrace, ...] = ()

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        errors = [*self._duplicate_errors(), *self._placement_errors(), *self._reference_errors()]
        if errors:
            raise ValueError(f"view {self.id}: " + "; ".join(errors))
        return self

    def _duplicate_errors(self) -> list[str]:
        groups = {
            "step": [s.id for s in self.steps],
            "zone": [z.id for z in self.zones],
            "node": [n.id for n in self.nodes],
            "edge": [e.id for e in self.edges],
            "trace": [t.id for t in self.traces],
        }
        return [
            f"duplicate {label} ids" for label, ids in groups.items() if len(set(ids)) != len(ids)
        ]

    def _placement_errors(self) -> list[str]:
        step_ids = {s.id for s in self.steps}
        placed = (*self.zones, *self.nodes, *self.edges, *self.bands)
        errors = [
            f"{item.id}: unknown step {item.step!r}"
            for item in placed
            if item.step is not None and item.step not in step_ids
        ]
        errors += [
            f"node {n.id} is outside the {self.columns}x{self.rows} grid"
            for n in self.nodes
            if n.col + n.width > self.columns or n.row >= self.rows
        ]
        errors += [
            f"zone {z.id} is outside the {self.columns}x{self.rows} grid"
            for z in self.zones
            if z.col + z.cols > self.columns or z.row + z.rows > self.rows
        ]
        return errors

    def _reference_errors(self) -> list[str]:
        node_ids = {n.id for n in self.nodes}
        edge_ids = {e.id for e in self.edges}
        errors = [
            f"edge {e.id}: unknown nodes {sorted({e.source, e.target} - node_ids)}"
            for e in self.edges
            if {e.source, e.target} - node_ids
        ]
        for trace in self.traces:
            errors += [
                f"trace {trace.id}: unknown node {hop.node}"
                for hop in trace.steps
                if hop.node not in node_ids
            ]
            errors += [
                f"trace {trace.id}: unknown edge {hop.edge}"
                for hop in trace.steps
                if hop.edge is not None and hop.edge not in edge_ids
            ]
        return errors


class FlowStep(BaseModel):
    """One box of a pattern's compact flow diagram."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    kind: NodeKind
    note: str = ""


def load_view(path: Path) -> DiagramView:
    """Load one view and check that its ID matches the file name."""
    view = DiagramView.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if view.id != path.stem:
        raise ValueError(f"view {view.id!r} must be saved as {view.id}.yaml (found {path.name})")
    return view


def load_views(views_root: Path) -> tuple[DiagramView, ...]:
    """Load every view under ``education/architecture/views``."""
    return tuple(load_view(path) for path in sorted(views_root.glob("*.yaml")))


def view_reference_errors(
    view: DiagramView,
    *,
    component_ids: set[str],
    source_ids: frozenset[str],
    pattern_ids: frozenset[str],
) -> list[str]:
    """Return references from a view to components, sources or patterns that do not exist."""
    errors = [
        f"view {view.id} node {n.id}: unknown component {n.component}"
        for n in view.nodes
        if n.component is not None and n.component not in component_ids
    ]
    cited = {*view.aligned_to, *(s for n in view.nodes for s in n.sources)}
    errors += [f"view {view.id}: unknown source {s}" for s in sorted(cited - source_ids)]
    errors += [
        f"view {view.id}: unknown pattern {p}" for p in view.pattern_ids if p not in pattern_ids
    ]
    return errors


def visible(item_step: str | None, steps: tuple[DiagramStep, ...], upto: str | None) -> bool:
    """Return True when an item placed at ``item_step`` is visible at build step ``upto``."""
    if item_step is None or upto is None:
        return True
    order = [s.id for s in steps]
    return order.index(item_step) <= order.index(upto)


def render_mermaid(view: DiagramView, *, step: str | None = None) -> str:
    """Render a view as a Mermaid flowchart (zones become subgraphs)."""
    lines = ["flowchart LR"]
    nodes = [n for n in view.nodes if visible(n.step, view.steps, step)]
    shown = {n.id for n in nodes}
    zoned: set[str] = set()
    for zone in view.zones:
        if not visible(zone.step, view.steps, step):
            continue
        members = [
            n
            for n in nodes
            if zone.col <= n.col < zone.col + zone.cols
            and zone.row <= n.row < zone.row + zone.rows
            and n.id not in zoned
        ]
        if not members:
            continue
        lines.append(f'  subgraph {_mid(zone.id)}["{_text(zone.label)}"]')
        for node in members:
            lines.append(f"    {_mermaid_node(node)}")
            zoned.add(node.id)
        lines.append("  end")
    lines += [f"  {_mermaid_node(n)}" for n in nodes if n.id not in zoned]
    for edge in view.edges:
        if edge.source in shown and edge.target in shown and visible(edge.step, view.steps, step):
            arrow = "-.->" if edge.planned or edge.kind == "fallback" else "-->"
            label = f"|{_text(edge.label)}|" if edge.label else ""
            lines.append(f"  {_mid(edge.source)} {arrow}{label} {_mid(edge.target)}")
    states = sorted({n.state for n in nodes})
    for state in states:
        members = ",".join(_mid(n.id) for n in nodes if n.state == state)
        lines.append(f"  class {members} {state.replace('-', '_')}")
    lines += [
        "  classDef implemented stroke-width:2px",
        "  classDef planned stroke-dasharray: 6 4",
        "  classDef preview stroke-dasharray: 2 3",
        "  classDef optional stroke-dasharray: 8 4",
        "  classDef documented stroke-width:1px",
        "  classDef tenant_validation stroke-dasharray: 3 3",
    ]
    return "\n".join(lines) + "\n"


def _mid(identifier: str) -> str:
    return identifier.replace("-", "_")


def _text(value: str) -> str:
    return value.replace('"', "'").replace("|", "/")


_STATE_TAG = {
    "implemented": "",
    "planned": " · planned",
    "documented": "",
    "preview": " · PREVIEW",
    "tenant-validation": " · tenant",
    "optional": " · optional",
}


def _mermaid_node(node: DiagramNode) -> str:
    sub = f"<br/><small>{_text(node.sublabel)}</small>" if node.sublabel else ""
    return f'{_mid(node.id)}["{_text(node.label)}{_STATE_TAG[node.state]}{sub}"]'
