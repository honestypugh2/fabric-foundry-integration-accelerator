"""Deterministic layout for architecture views, shared by the draw.io files and the web app.

Nodes sit on a grid of cards. Edges are routed orthogonally through the gutters between columns
(one lane per owning node, so different fan-outs never share a line) and, when a straight run
would cross another card, through the gap between rows. The same geometry is rendered by
``drawio.py`` and by the frontend, so the files and the app always look the same.
"""

from dataclasses import dataclass
from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.education.diagrams import DiagramEdge, DiagramView

CELL_W = 260.0
CELL_H = 140.0
BOX_W = 180.0
BOX_H = 76.0
LEFT = 40.0
TOP = 110.0
GUTTER = CELL_W - BOX_W
BAND_H = 34.0
BAND_GAP = 8.0

Point = tuple[float, float]


class Box(BaseModel):
    """A rectangle in diagram coordinates."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        """Horizontal centre."""
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        """Vertical centre."""
        return self.y + self.h / 2

    @property
    def right(self) -> float:
        """Right edge."""
        return self.x + self.w

    @property
    def bottom(self) -> float:
        """Bottom edge."""
        return self.y + self.h


class EdgePath(BaseModel):
    """A routed edge: the full polyline (endpoints included) and its label anchor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    points: tuple[Point, ...]
    label_at: Point
    label_fraction: float


class ViewLayout(BaseModel):
    """Geometry for every node, zone and edge of a view."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    width: float
    height: float
    grid_bottom: float
    nodes: dict[str, Box]
    zones: dict[str, Box]
    edges: dict[str, EdgePath]


def node_box(col: float, row: float, width: float = 1) -> Box:
    """Return the card for a grid position."""
    return Box(x=LEFT + col * CELL_W, y=TOP + row * CELL_H + 4, w=width * CELL_W - GUTTER, h=BOX_H)


def _gutter_span(gutter: int) -> tuple[float, float]:
    """Gutter ``g`` is the gap just left of column ``g``."""
    right = LEFT + gutter * CELL_W
    return right - GUTTER, right


def _row_gap_y(row: int, *, below: bool) -> float:
    """The vertical middle of the gap above (or below) a row of cards."""
    top = TOP + row * CELL_H + 4
    return top + BOX_H + (CELL_H - BOX_H) / 2 if below else top - (CELL_H - BOX_H) / 2


Lane = tuple[int, str]
RouteKind = Literal["vertical", "side", "straight", "near-source", "near-target", "gap"]


@dataclass(frozen=True)
class _Plan:
    kind: RouteKind
    lane: Lane | None = None
    lane_in: Lane | None = None


class _Router:
    def __init__(self, view: DiagramView, boxes: dict[str, Box]) -> None:
        self.boxes = boxes
        self.cells: dict[str, tuple[int, int]] = {
            n.id: (int(n.col), int(n.row)) for n in view.nodes
        }
        self.occupied = set(self.cells.values())
        self.lanes: dict[int, list[str]] = {}
        self.plans: dict[str, _Plan] = {}

    def _free_between(self, row: int, col_a: int, col_b: int) -> bool:
        low, high = sorted((col_a, col_b))
        return all((col, row) not in self.occupied for col in range(low + 1, high))

    def _lane(self, gutter: int, owner: str) -> Lane:
        owners = self.lanes.setdefault(gutter, [])
        if owner not in owners:
            owners.append(owner)
        return gutter, owner

    def plan(self, edge: DiagramEdge) -> None:
        (sc, sr), (tc, tr) = self.cells[edge.source], self.cells[edge.target]
        if sc == tc:
            low, high = sorted((sr, tr))
            straight = all((sc, row) not in self.occupied for row in range(low + 1, high))
            self.plans[edge.id] = (
                _Plan("vertical") if straight else _Plan("side", self._lane(sc + 1, edge.source))
            )
            return
        rightward = tc > sc
        out_gutter = sc + 1 if rightward else sc
        in_gutter = tc if rightward else tc + 1
        if sr == tr and self._free_between(sr, sc, tc):
            plan = _Plan("straight")
        elif self._free_between(tr, sc, tc):
            plan = _Plan("near-source", self._lane(out_gutter, edge.source))
        elif self._free_between(sr, sc, tc):
            plan = _Plan("near-target", self._lane(in_gutter, edge.target))
        else:
            plan = _Plan(
                "gap", self._lane(out_gutter, edge.source), self._lane(in_gutter, edge.target)
            )
        self.plans[edge.id] = plan

    def lane_x(self, lane: Lane | None) -> float:
        if lane is None:
            raise ValueError("route needs a gutter lane")
        gutter, owner = lane
        owners = self.lanes[gutter]
        start, _ = _gutter_span(gutter)
        return start + GUTTER * (owners.index(owner) + 1) / (len(owners) + 1)

    def route(self, edge: DiagramEdge) -> tuple[Point, ...]:
        s, t = self.boxes[edge.source], self.boxes[edge.target]
        plan = self.plans[edge.id]
        rightward = t.cx > s.cx
        sx, tx = (s.right, t.x) if rightward else (s.x, t.right)
        match plan.kind:
            case "vertical":
                down = t.cy > s.cy
                return ((s.cx, s.bottom if down else s.y), (t.cx, t.y if down else t.bottom))
            case "side":
                x = self.lane_x(plan.lane)
                return ((s.right, s.cy), (x, s.cy), (x, t.cy), (t.right, t.cy))
            case "straight":
                return ((sx, s.cy), (tx, t.cy))
            case "near-source" | "near-target":
                x = self.lane_x(plan.lane)
                return ((sx, s.cy), (x, s.cy), (x, t.cy), (tx, t.cy))
            case "gap":
                x1, x2 = self.lane_x(plan.lane), self.lane_x(plan.lane_in)
                sr, tr = self.cells[edge.source][1], self.cells[edge.target][1]
                gy = _row_gap_y(tr, below=tr == 0 or sr > tr)
                return ((sx, s.cy), (x1, s.cy), (x1, gy), (x2, gy), (x2, t.cy), (tx, t.cy))


LABEL_CHAR_W = 5.2


def _label_anchor(points: tuple[Point, ...], label: str) -> tuple[Point, float]:
    """Anchor a label where it reads unambiguously; also return its fraction along the path.

    Prefer the final horizontal run into the target when the label fits there (so fan-out labels
    sit next to their target, not on a shared trunk); otherwise use the longest segment.
    """
    lengths = [abs(b[0] - a[0]) + abs(b[1] - a[1]) for a, b in pairwise(points)]
    total = sum(lengths) or 1.0
    last = len(lengths) - 1
    a, b = points[last], points[last + 1]
    fits_last = a[1] == b[1] and lengths[last] >= len(label) * LABEL_CHAR_W + 16
    index = last if fits_last else max(range(len(lengths)), key=lambda i: (lengths[i], -i))
    a, b = points[index], points[index + 1]
    anchor = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    travelled = sum(lengths[:index]) + lengths[index] / 2
    return anchor, travelled / total


def compute_layout(view: DiagramView) -> ViewLayout:
    """Lay out a view: cards, zones and routed edges."""
    boxes = {n.id: node_box(n.col, n.row, n.width) for n in view.nodes}
    zones = {
        z.id: Box(
            x=LEFT + z.col * CELL_W - 14,
            y=TOP + z.row * CELL_H - 26,
            w=z.cols * CELL_W - GUTTER + 28,
            h=(z.rows - 1) * CELL_H + BOX_H + 4 + 26 + 14,
        )
        for z in view.zones
    }
    router = _Router(view, boxes)
    for edge in view.edges:
        router.plan(edge)
    edges: dict[str, EdgePath] = {}
    for edge in view.edges:
        points = router.route(edge)
        anchor, fraction = _label_anchor(points, edge.label)
        edges[edge.id] = EdgePath(points=points, label_at=anchor, label_fraction=fraction)
    grid_bottom = TOP + view.rows * CELL_H
    width = LEFT * 2 + view.columns * CELL_W - GUTTER
    height = grid_bottom + len(view.bands) * (BAND_H + BAND_GAP) + 80
    return ViewLayout(
        width=width, height=height, grid_bottom=grid_bottom, nodes=boxes, zones=zones, edges=edges
    )
