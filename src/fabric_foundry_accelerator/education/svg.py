"""Render an architecture view as a static, self-contained SVG (Azure Architecture Center style).

Uses the same layout engine and palette as the draw.io export, so the SVG embedded in a talk-track
handout matches the app's interactive diagram and the committed draw.io file. No scripts, no
external images: Azure icons are not embedded, so cards carry the brand colors instead.
"""

from xml.sax.saxutils import escape

from fabric_foundry_accelerator.education.diagrams import DiagramView
from fabric_foundry_accelerator.education.drawio import (
    BAND_FILL,
    EDGE_STROKE,
    KIND_STYLE,
    STATE_TEXT,
    ZONE_STROKE,
)
from fabric_foundry_accelerator.education.layout import BAND_GAP, BAND_H, LEFT, compute_layout

_FONT = "Segoe UI, system-ui, -apple-system, sans-serif"


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if len(candidate) > width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def render_svg(view: DiagramView, *, title_id: str | None = None) -> str:
    """Return an accessible SVG for the full view (all build steps visible)."""
    layout = compute_layout(view)
    width, height = layout.width, layout.height
    label_id = title_id or f"svg-{view.id}-title"
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" '
        f'role="img" aria-labelledby="{label_id}" class="arch-svg" font-family="{_FONT}">',
        f'<title id="{label_id}">{escape(view.title)}</title>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
        'fill="context-stroke"/></marker></defs>',
        f'<rect x="0" y="0" width="{width:g}" height="{height:g}" fill="#FFFFFF"/>',
        f'<text x="{LEFT}" y="44" font-size="20" font-weight="700" fill="#1B1B1F">'
        f"{escape(view.title)}</text>",
    ]
    for zone in view.zones:
        box = layout.zones[zone.id]
        stroke = ZONE_STROKE[zone.kind]
        dash = "6 4" if zone.kind in ("optional", "offline") else "8 4"
        parts.append(
            f'<rect x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}" rx="8" '
            f'fill="none" stroke="{stroke}" stroke-dasharray="{dash}"/>'
            f'<text x="{box.x + 10:g}" y="{box.y + 17:g}" font-size="11" font-weight="700" '
            f'fill="{stroke}">{escape(zone.label)}</text>'
        )
    for edge in view.edges:
        path = layout.edges[edge.id]
        stroke = EDGE_STROKE.get(edge.kind, "#505050")
        dash = ' stroke-dasharray="5 4"' if edge.planned or edge.kind == "fallback" else ""
        points = " ".join(f"{x:g},{y:g}" for x, y in path.points)
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="1.4"'
            f'{dash} marker-end="url(#arrow)"/>'
        )
        if edge.label:
            lx, ly = path.label_at
            text_w = 6.2 * len(edge.label) + 8
            parts.append(
                f'<rect x="{lx - text_w / 2:g}" y="{ly - 8:g}" width="{text_w:g}" height="15" '
                f'rx="3" fill="#FFFFFF"/><text x="{lx:g}" y="{ly + 3:g}" font-size="9.5" '
                f'text-anchor="middle" fill="#3B3B45">{escape(edge.label)}</text>'
            )
    for node in view.nodes:
        box = layout.nodes[node.id]
        fill, stroke = KIND_STYLE[node.kind]
        dash = ' stroke-dasharray="5 3"' if node.state in ("planned", "preview", "optional") else ""
        parts.append(
            f'<g><rect x="{box.x:g}" y="{box.y:g}" width="{box.w:g}" height="{box.h:g}" rx="7" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.3"{dash}/>'
        )
        lines = _wrap(node.label, 26)[:2]
        y = box.y + 22
        for line in lines:
            parts.append(
                f'<text x="{box.x + box.w / 2:g}" y="{y:g}" font-size="11.5" font-weight="700" '
                f'text-anchor="middle" fill="#1B1B1F">{escape(line)}</text>'
            )
            y += 14
        if node.sublabel:
            sub = _wrap(node.sublabel, 32)[0]
            parts.append(
                f'<text x="{box.x + box.w / 2:g}" y="{y:g}" font-size="9.5" text-anchor="middle" '
                f'fill="#505050">{escape(sub)}</text>'
            )
        if node.state in ("preview", "optional", "tenant-validation", "planned"):
            text = (
                f"Planned · Phase {node.phase}"
                if node.state == "planned"
                else STATE_TEXT[node.state]
            )
            parts.append(
                f'<text x="{box.x + box.w / 2:g}" y="{box.y + box.h - 7:g}" font-size="9" '
                f'font-style="italic" text-anchor="middle" fill="#8A5300">{escape(text)}</text>'
            )
        parts.append("</g>")
    if view.traces:
        seen: dict[str, int] = {}
        for number, hop in enumerate(view.traces[0].steps, start=1):
            box = layout.nodes[hop.node]
            repeat = seen.get(hop.node, 0)
            seen[hop.node] = repeat + 1
            cx, cy = box.x + repeat * 24, box.y
            parts.append(
                f'<circle cx="{cx:g}" cy="{cy:g}" r="11" fill="#0078D4" stroke="#FFFFFF" '
                f'stroke-width="1.5"/><text x="{cx:g}" y="{cy + 4:g}" font-size="11" '
                f'font-weight="700" text-anchor="middle" fill="#FFFFFF">{number}</text>'
            )
    for offset, band in enumerate(view.bands):
        y = layout.grid_bottom + 10 + offset * (BAND_H + BAND_GAP)
        parts.append(
            f'<rect x="{LEFT - 14:g}" y="{y:g}" width="{width - 2 * LEFT + 28:g}" '
            f'height="{BAND_H:g}" fill="{BAND_FILL[band.kind]}"/>'
            f'<text x="{LEFT - 4:g}" y="{y + BAND_H / 2 + 4:g}" font-size="11" fill="#1B1B1F">'
            f"{escape(band.text)}</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def workflow(view: DiagramView) -> list[str]:
    """The numbered workflow for the first trace (matches the numbered circles)."""
    if not view.traces:
        return []
    nodes = {n.id: n for n in view.nodes}
    return [f"{nodes[h.node].label}: {h.say}" for h in view.traces[0].steps]
