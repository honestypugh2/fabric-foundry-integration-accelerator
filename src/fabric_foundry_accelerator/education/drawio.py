"""Render architecture views as draw.io (diagrams.net) files in Azure Architecture Center style.

Azure services use the official Azure icons that ship with draw.io (``img/lib/azure2``),
referenced by path. Microsoft Fabric, GitHub and Claude have no draw.io icon and are drawn as
styled shapes. The first trace is numbered on the diagram, matching the numbered "Workflow" list
in the generated documentation. Output is deterministic so ``ffia diagrams check`` can detect
drift. Open the files in draw.io desktop, diagrams.net or the VS Code Draw.io Integration.
"""

from xml.sax.saxutils import escape, quoteattr

from fabric_foundry_accelerator.education.diagrams import (
    DiagramEdge,
    DiagramNode,
    DiagramView,
    visible,
)
from fabric_foundry_accelerator.education.layout import (
    BAND_GAP,
    BAND_H,
    BOX_H,
    LEFT,
    Box,
    EdgePath,
    ViewLayout,
    compute_layout,
)

ICON = 36

# Fills follow the brand families used across Azure Architecture Center diagrams.
_KIND_STYLE: dict[str, tuple[str, str]] = {
    "fabric": ("#E3F4F1", "#117865"),
    "data": ("#E3F4F1", "#117865"),
    "foundry": ("#F0EAFB", "#5C2D91"),
    "mcp": ("#FFF1E5", "#C55A11"),
    "gateway": ("#E8F1FB", "#0078D4"),
    "identity": ("#E8F1FB", "#0078D4"),
    "policy": ("#FFF8E1", "#8A5300"),
    "evidence": ("#E9F5EA", "#107C10"),
    "local": ("#F3F3F3", "#5E5E5E"),
    "knowledge": ("#F3F3F3", "#5E5E5E"),
    "harness": ("#F3F3F3", "#24292F"),
    "client": ("#F3F3F3", "#24292F"),
    "person": ("#F3F3F3", "#24292F"),
    "app": ("#E8F1FB", "#0078D4"),
    "service": ("#E8F1FB", "#0078D4"),
    "external": ("#FFFFFF", "#5E5E5E"),
}
_ZONE_STROKE: dict[str, str] = {
    "fabric": "#117865",
    "foundry": "#5C2D91",
    "tenant": "#0078D4",
    "local": "#5E5E5E",
    "github": "#24292F",
    "optional": "#8A8886",
    "offline": "#8A5300",
}
_EDGE_STROKE: dict[str, str] = {
    "authority": "#8A5300",
    "evidence": "#107C10",
    "change": "#A4262C",
    "fallback": "#5E5E5E",
    "config": "#8A8886",
}
_BAND_FILL: dict[str, str] = {
    "identity": "#E8F1FB",
    "policy": "#FFF8E1",
    "evidence": "#E9F5EA",
    "failure": "#FDE7E9",
    "network": "#F3F3F3",
}
STATE_TEXT: dict[str, str] = {
    "implemented": "Implemented in this repository",
    "planned": "Planned",
    "documented": "Microsoft-documented",
    "preview": "Preview",
    "tenant-validation": "Requires tenant validation",
    "optional": "Optional",
}


def _state_suffix(node: DiagramNode) -> str:
    if node.state == "planned":
        return f"Planned · Phase {node.phase}"
    if node.state in ("preview", "optional", "tenant-validation"):
        return STATE_TEXT[node.state]
    return ""


def _label(node: DiagramNode) -> str:
    parts = [f"<b>{escape(node.label)}</b>"]
    if node.sublabel:
        parts.append(f'<font style="font-size:10px" color="#505050">{escape(node.sublabel)}</font>')
    suffix = _state_suffix(node)
    if suffix:
        parts.append(f'<font style="font-size:10px" color="#8A5300"><i>{escape(suffix)}</i></font>')
    return "<br>".join(parts)


def _node_cell(prefix: str, node: DiagramNode, box: Box) -> str:
    """A card per node; Azure nodes carry their official icon inside the card.

    Edges attach to the card, never to the icon, so arrows don't cross labels.
    """
    fill, stroke = _KIND_STYLE[node.kind]
    dashed = "dashed=1;" if node.state in ("planned", "preview", "optional") else ""
    card_id = f"{prefix}n-{node.id}"
    if node.icon:
        style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=8;fontSize=11;align=left;spacingLeft=50;"
            f"spacingRight=6;fillColor=#FFFFFF;strokeColor={stroke};{dashed}"
        )
    else:
        style = (
            "rounded=1;whiteSpace=wrap;html=1;arcSize=8;fontSize=11;spacingLeft=6;spacingRight=6;"
            f"fillColor={fill};strokeColor={stroke};{dashed}"
        )
    card = (
        f'<mxCell id="{card_id}" value={quoteattr(_label(node))} style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}" as="geometry"/>'
        "</mxCell>"
    )
    if not node.icon:
        return card
    icon = (
        f'<mxCell id="{card_id}-icon" value="" style="image;aspect=fixed;html=1;points=[];'
        f'image=img/lib/azure2/{node.icon}.svg;" vertex="1" connectable="0" parent="{card_id}">'
        f'<mxGeometry x="8" y="{(BOX_H - ICON) / 2:g}" width="{ICON}" height="{ICON}" as="geometry"/>'
        "</mxCell>"
    )
    return card + icon


def _edge_cell(prefix: str, edge: DiagramEdge, path: EdgePath) -> str:
    stroke = _EDGE_STROKE.get(edge.kind, "#505050")
    dashed = "dashed=1;" if edge.planned or edge.kind == "fallback" else ""
    style = (
        "edgeStyle=none;rounded=1;html=1;endArrow=block;endFill=1;jumpStyle=arc;"
        f"fontSize=9;labelBackgroundColor=#FFFFFF;strokeColor={stroke};{dashed}"
    )
    waypoints = "".join(f'<mxPoint x="{x:g}" y="{y:g}"/>' for x, y in path.points[1:-1])
    points = f'<Array as="points">{waypoints}</Array>' if waypoints else ""
    (sx, sy), (tx, ty) = path.points[0], path.points[-1]
    return (
        f'<mxCell id="{prefix}e-{edge.id}" value={quoteattr(escape(edge.label))} style="{style}" '
        f'edge="1" parent="1" source="{prefix}n-{edge.source}" target="{prefix}n-{edge.target}">'
        f'<mxGeometry x="{path.label_fraction * 2 - 1:.3f}" relative="1" as="geometry">'
        f'<mxPoint x="{sx:g}" y="{sy:g}" as="sourcePoint"/><mxPoint x="{tx:g}" y="{ty:g}" as="targetPoint"/>'
        f"{points}</mxGeometry></mxCell>"
    )


def _badges(prefix: str, view: DiagramView, layout: ViewLayout, upto: str | None) -> list[str]:
    """Number the first trace next to each step's component, Architecture Center style."""
    if not view.traces:
        return []
    nodes = {n.id: n for n in view.nodes}
    seen: dict[str, int] = {}
    cells: list[str] = []
    for number, hop in enumerate(view.traces[0].steps, start=1):
        if not visible(nodes[hop.node].step, view.steps, upto):
            continue
        box = layout.nodes[hop.node]
        repeat = seen.get(hop.node, 0)
        seen[hop.node] = repeat + 1
        cx, cy = box.x - 11 + repeat * 24, box.y - 11
        cells.append(
            f'<mxCell id="{prefix}b-{number}" value="{number}" style="ellipse;whiteSpace=wrap;html=1;'
            'aspect=fixed;fillColor=#0078D4;strokeColor=#FFFFFF;fontColor=#FFFFFF;fontStyle=1;fontSize=11;" '
            f'vertex="1" parent="1"><mxGeometry x="{cx:g}" y="{cy:g}" width="22" height="22" as="geometry"/>'
            "</mxCell>"
        )
    return cells


def _page(view: DiagramView, layout: ViewLayout, index: int, name: str, upto: str | None) -> str:
    prefix = f"p{index}-"
    width = layout.width
    bands = [b for b in view.bands if visible(b.step, view.steps, upto)]
    height = layout.height
    cells: list[str] = [
        f'<mxCell id="{prefix}title" value={quoteattr(f"<b>{escape(view.title)}</b>")} '
        'style="text;html=1;fontSize=20;align=left;verticalAlign=top;" vertex="1" parent="1">'
        f'<mxGeometry x="{LEFT}" y="20" width="{width - 2 * LEFT}" height="30" as="geometry"/></mxCell>',
        f'<mxCell id="{prefix}subtitle" value={quoteattr(escape(name))} '
        'style="text;html=1;fontSize=12;fontColor=#505050;align=left;verticalAlign=top;" vertex="1" '
        f'parent="1"><mxGeometry x="{LEFT}" y="52" width="{width - 2 * LEFT}" height="24" as="geometry"/>'
        "</mxCell>",
    ]
    for zone in view.zones:
        if not visible(zone.step, view.steps, upto):
            continue
        box = layout.zones[zone.id]
        stroke = _ZONE_STROKE[zone.kind]
        dashed = (
            "dashed=1;" if zone.kind in ("optional", "offline") else "dashed=1;dashPattern=8 4;"
        )
        cells.append(
            f'<mxCell id="{prefix}z-{zone.id}" value={quoteattr(escape(zone.label))} '
            'style="rounded=1;arcSize=3;html=1;fillColor=none;verticalAlign=top;align=left;spacingLeft=8;'
            f'fontStyle=1;fontSize=11;fontColor={stroke};strokeColor={stroke};{dashed}" vertex="1" parent="1">'
            f'<mxGeometry x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}" as="geometry"/>'
            "</mxCell>"
        )
    shown = {n.id for n in view.nodes if visible(n.step, view.steps, upto)}
    cells += [_node_cell(prefix, n, layout.nodes[n.id]) for n in view.nodes if n.id in shown]
    cells += [
        _edge_cell(prefix, e, layout.edges[e.id])
        for e in view.edges
        if e.source in shown and e.target in shown and visible(e.step, view.steps, upto)
    ]
    cells += _badges(prefix, view, layout, upto)
    for offset, band in enumerate(bands):
        y = layout.grid_bottom + 10 + offset * (BAND_H + BAND_GAP)
        cells.append(
            f'<mxCell id="{prefix}band-{band.id}" value={quoteattr(escape(band.text))} '
            f'style="rounded=0;whiteSpace=wrap;html=1;align=left;spacingLeft=10;fontSize=11;'
            f'fillColor={_BAND_FILL[band.kind]};strokeColor=none;" vertex="1" parent="1">'
            f'<mxGeometry x="{LEFT - 14}" y="{y:g}" width="{width - 2 * LEFT + 28:g}" height="{BAND_H:g}" '
            'as="geometry"/></mxCell>'
        )
    legend = (
        "<b>Legend</b> · solid = implemented here or Microsoft-documented · dashed = planned, preview "
        "or optional · numbered circles = workflow steps · generated from "
        f"education/architecture/views/{view.id}.yaml (edit the YAML, then run ffia diagrams render)"
    )
    cells.append(
        f'<mxCell id="{prefix}legend" value={quoteattr(legend)} style="text;html=1;fontSize=10;'
        'fontColor=#505050;align=left;verticalAlign=top;whiteSpace=wrap;" vertex="1" parent="1">'
        f'<mxGeometry x="{LEFT}" y="{height - 50:g}" width="{width - 2 * LEFT}" height="40" as="geometry"/>'
        "</mxCell>"
    )
    body = "".join(cells)
    return (
        f'<diagram id="{view.id}-{index}" name={quoteattr(name)}>'
        f'<mxGraphModel grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" '
        f'page="1" pageScale="1" pageWidth="{width:g}" pageHeight="{height:g}" math="0" shadow="0">'
        f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>'
    )


def render_drawio(view: DiagramView) -> str:
    """Render a view as a multi-page draw.io file: the full architecture, then each build step."""
    layout = compute_layout(view)
    pages = [_page(view, layout, 0, "Architecture", None)]
    pages += [
        _page(view, layout, index, f"{index} · {step.label}", step.id)
        for index, step in enumerate(view.steps, start=1)
    ]
    return (
        '<mxfile host="ffia" agent="ffia diagrams render" version="1">\n'
        + "\n".join(pages)
        + "\n</mxfile>\n"
    )
