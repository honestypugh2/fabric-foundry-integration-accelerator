import type { KeyboardEvent } from "react";
import type { NodeRuntime, RenderedView } from "../../api/contracts";
import { stateText, visibleAt, wrap } from "./diagramText";

export interface Highlight {
  readonly node: string | null;
  readonly edge: string | null;
}

interface DiagramCanvasProps {
  readonly rendered: RenderedView;
  readonly upto: string | null;
  readonly selected: string | null;
  readonly onSelect: (nodeId: string) => void;
  readonly highlight?: Highlight | undefined;
  readonly focus?: readonly string[] | undefined;
  readonly badges?: ReadonlyMap<string, readonly number[]> | undefined;
  readonly runtime?: ReadonlyMap<string, NodeRuntime> | undefined;
  readonly showStates?: boolean;
  readonly interactive?: boolean;
  readonly fit?: boolean;
  readonly label: string;
}

const ARROW_ID = "ffia-arrow";

/**
 * Renders an architecture view from the shared backend layout (the same geometry as the draw.io
 * files). Nodes are keyboard-focusable buttons; everything else is presentational.
 */
export function DiagramCanvas({
  rendered,
  upto,
  selected,
  onSelect,
  highlight,
  focus,
  badges,
  runtime,
  showStates = true,
  interactive = true,
  fit = true,
  label,
}: DiagramCanvasProps) {
  const { view, layout } = rendered;
  const order = view.steps.map((s) => s.id);
  const shownNodes = view.nodes.filter((n) => visibleAt(n.step, order, upto));
  const shown = new Set(shownNodes.map((n) => n.id));
  const tracing = highlight !== undefined && highlight.node !== null;
  const focusSet = focus && focus.length > 0 ? new Set(focus) : null;
  const dimmed = (nodeId: string) =>
    (tracing && highlight.node !== nodeId) || (focusSet !== null && !focusSet.has(nodeId));

  const onKey = (event: KeyboardEvent<SVGGElement>, nodeId: string) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(nodeId);
    }
  };

  return (
    <svg
      className="diagram"
      viewBox={`0 60 ${String(layout.width)} ${String(layout.grid_bottom - 30)}`}
      style={fit ? undefined : { width: `${String(layout.width)}px` }}
      role="group"
      aria-label={label}
    >
      <defs>
        <marker
          id={ARROW_ID}
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth="7"
          markerHeight="7"
          orient="auto-start-reverse"
        >
          <path d="M0 0 L10 5 L0 10 Z" className="diagram__arrow" />
        </marker>
      </defs>
      {view.zones
        .filter((z) => visibleAt(z.step, order, upto))
        .map((zone) => {
          const box = layout.zones[zone.id];
          if (box === undefined) {
            return null;
          }
          return (
            <g key={zone.id} className={`diagram__zone diagram__zone--${zone.kind}`}>
              <rect x={box.x} y={box.y} width={box.w} height={box.h} rx={10} />
              <text x={box.x + 10} y={box.y + 16}>
                {zone.label}
              </text>
            </g>
          );
        })}
      {view.edges
        .filter((e) => shown.has(e.source) && shown.has(e.target) && visibleAt(e.step, order, upto))
        .map((edge) => {
          const path = layout.edges[edge.id];
          if (path === undefined) {
            return null;
          }
          const d = path.points
            .map(([x, y], index) => `${index === 0 ? "M" : "L"}${String(x)} ${String(y)}`)
            .join(" ");
          const active = highlight?.edge === edge.id;
          const faded =
            (tracing && !active) ||
            (focusSet !== null && !(focusSet.has(edge.source) && focusSet.has(edge.target)));
          const classes = [
            "diagram__edge",
            `diagram__edge--${edge.kind}`,
            edge.planned || edge.kind === "fallback" ? "diagram__edge--dashed" : "",
            active ? "diagram__edge--active" : "",
            faded ? "diagram__faded" : "",
          ].join(" ");
          return (
            <g key={edge.id} className={classes}>
              <path d={d} markerEnd={`url(#${ARROW_ID})`} />
              {edge.label ? (
                <text
                  x={path.label_at[0]}
                  y={path.label_at[1] + 3}
                  textAnchor="middle"
                  className="diagram__edge-label"
                >
                  {edge.label}
                </text>
              ) : null}
            </g>
          );
        })}
      {shownNodes.map((node) => {
        const box = layout.nodes[node.id];
        if (box === undefined) {
          return null;
        }
        const live = runtime?.get(node.id);
        const title = wrap(node.label, 24, 2);
        const sub = node.sublabel ? wrap(node.sublabel, 30, 1) : [];
        const tag = showStates && node.state !== "implemented" && node.state !== "documented";
        const classes = [
          "diagram__node",
          `diagram__node--${node.kind}`,
          `diagram__node--${node.state}`,
          selected === node.id ? "diagram__node--selected" : "",
          highlight?.node === node.id || focusSet?.has(node.id) ? "diagram__node--active" : "",
          live ? `diagram__node--rt-${live.status.toLowerCase().replace(" ", "-")}` : "",
          dimmed(node.id) ? "diagram__faded" : "",
        ].join(" ");
        const description = `${node.label}. ${stateText(node.state, node.phase)}${
          live ? `. Runtime: ${live.status}` : ""
        }`;
        let line = 0;
        return (
          <g
            key={node.id}
            className={classes}
            data-node={node.id}
            {...(interactive
              ? {
                  role: "button",
                  tabIndex: 0,
                  "aria-pressed": selected === node.id,
                  "aria-label": description,
                  onClick: () => {
                    onSelect(node.id);
                  },
                  onKeyDown: (event: KeyboardEvent<SVGGElement>) => {
                    onKey(event, node.id);
                  },
                }
              : { "aria-hidden": true })}
          >
            <rect x={box.x} y={box.y} width={box.w} height={box.h} rx={8} />
            {title.map((text) => (
              <text
                key={`t${String(line)}`}
                x={box.x + box.w / 2}
                y={box.y + 22 + line++ * 14}
                textAnchor="middle"
                className="diagram__title"
              >
                {text}
              </text>
            ))}
            {sub.map((text) => (
              <text
                key={`s${String(line)}`}
                x={box.x + box.w / 2}
                y={box.y + 22 + line++ * 14}
                textAnchor="middle"
                className="diagram__sub"
              >
                {text}
              </text>
            ))}
            {tag ? (
              <text
                x={box.x + box.w / 2}
                y={box.y + box.h - 8}
                textAnchor="middle"
                className="diagram__state"
              >
                {stateText(node.state, node.phase)}
              </text>
            ) : null}
            {live ? (
              <g className="diagram__runtime">
                <rect x={box.x + box.w - 92} y={box.y - 10} width={90} height={18} rx={9} />
                <text x={box.x + box.w - 47} y={box.y + 3} textAnchor="middle">
                  {live.status}
                </text>
              </g>
            ) : null}
            {(badges?.get(node.id) ?? []).map((number, index) => (
              <g key={number} className="diagram__badge" aria-hidden="true">
                <circle cx={box.x + index * 22} cy={box.y} r={10} />
                <text x={box.x + index * 22} y={box.y + 4} textAnchor="middle">
                  {number}
                </text>
              </g>
            ))}
          </g>
        );
      })}
    </svg>
  );
}
