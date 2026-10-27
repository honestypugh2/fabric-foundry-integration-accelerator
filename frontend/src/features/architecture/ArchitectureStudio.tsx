import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Link } from "react-router";
import type { ArchitectureComponent, NodeRuntime, RenderedView } from "../../api/contracts";
import { useArchitecture, useView, useViewRuntime } from "../../api/hooks";
import { levelLabel, useLevel } from "../../app/levelContext";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";
import { DiagramCanvas } from "./DiagramCanvas";
import { stateText, visibleAt } from "./diagramText";

interface Inspection {
  readonly rendered: RenderedView;
  readonly nodeId: string;
  readonly components: ReadonlyMap<string, ArchitectureComponent>;
  readonly runtime: NodeRuntime | undefined;
  readonly onSelect: (node: string) => void;
}

function Inspector({ rendered, nodeId, components, runtime, onSelect }: Inspection) {
  const { level } = useLevel();
  const node = rendered.view.nodes.find((n) => n.id === nodeId);
  if (node === undefined) {
    return null;
  }
  const component = node.component ? components.get(node.component) : undefined;
  const names = new Map(rendered.view.nodes.map((n) => [n.id, n.label]));
  const links = rendered.view.edges.filter((e) => e.source === node.id || e.target === node.id);
  return (
    <>
      <h3>{node.label}</h3>
      <p>
        <Badge value={stateText(node.state, node.phase)} kind="state" />{" "}
        {component ? <Badge value={component.status} kind="status" /> : null}
      </p>
      <h4>What it is and why it matters</h4>
      <p>
        <span className="visually-hidden">At {levelLabel(level)}: </span>
        {component ? component.description[level] : node.summary}
      </p>
      {component && node.summary ? (
        <>
          <h4>Role in this workflow</h4>
          <p>{node.summary}</p>
        </>
      ) : null}
      {runtime ? (
        <p className="inspector__runtime">
          <strong>Now:</strong> <Badge value={runtime.status} kind="runtime" /> {runtime.detail}
        </p>
      ) : null}
      {component ? (
        <dl className="definition-list">
          <div>
            <dt>Owns</dt>
            <dd>{component.owns.join(", ")}</dd>
          </div>
          {component.does_not_own.length > 0 ? (
            <div>
              <dt>Does not own</dt>
              <dd>{component.does_not_own.join(", ")}</dd>
            </div>
          ) : null}
          <div>
            <dt>Offline</dt>
            <dd>{component.offline_equivalent}</dd>
          </div>
        </dl>
      ) : null}
      {node.repo_path ? (
        <p>
          In this repository: <code>{node.repo_path}</code>
        </p>
      ) : null}
      {links.length > 0 ? (
        <>
          <h4>Connections</h4>
          <ul className="tight">
            {links.map((edge) => (
              <li key={edge.id}>
                {edge.source === node.id ? "To " : "From "}
                <button
                  type="button"
                  className="connection-link"
                  onClick={() => {
                    onSelect(edge.source === node.id ? edge.target : edge.source);
                  }}
                >
                  {names.get(edge.source === node.id ? edge.target : edge.source)}
                </button>
                {edge.label ? `: ${edge.label}` : ""}
                {` (${edge.kind}${edge.planned ? ", planned" : ""})`}
              </li>
            ))}
          </ul>
        </>
      ) : null}
      {[...node.sources, ...(component?.sources ?? [])].length > 0 ? (
        <p className="meta">
          Sources: {[...new Set([...node.sources, ...(component?.sources ?? [])])].join(", ")}
        </p>
      ) : null}
    </>
  );
}

function Studio({ rendered }: { readonly rendered: RenderedView }) {
  const { view } = rendered;
  const architecture = useArchitecture();
  const components = useMemo(
    () => new Map((architecture.data?.components ?? []).map((c) => [c.id, c])),
    [architecture.data],
  );
  const hasRuntime = view.nodes.some((n) => n.runtime !== null);
  const [upto, setUpto] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [traceId, setTraceId] = useState(view.traces[0]?.id ?? "");
  const [hop, setHop] = useState(-1);
  const [showRuntime, setShowRuntime] = useState(hasRuntime);
  const [showStates, setShowStates] = useState(true);
  const [fit, setFit] = useState(true);
  const headingId = useId();
  const runtimeQuery = useViewRuntime(view.id, showRuntime && hasRuntime);
  const runtime = useMemo(
    () => new Map((runtimeQuery.data?.nodes ?? []).map((n) => [n.node, n])),
    [runtimeQuery.data],
  );
  const traceSelect = useId();
  const order = view.steps.map((s) => s.id);
  const trace = view.traces.find((t) => t.id === traceId);
  const current = trace && hop >= 0 ? trace.steps[hop] : undefined;
  const badges = useMemo(() => {
    const map = new Map<string, number[]>();
    trace?.steps.forEach((step, index) => {
      map.set(step.node, [...(map.get(step.node) ?? []), index + 1]);
    });
    return map;
  }, [trace]);
  const stepIndex = upto === null ? -1 : order.indexOf(upto);
  const canvasRef = useRef<HTMLDivElement>(null);
  const activeNode = current?.node ?? null;
  useEffect(() => {
    // Keep the traced component on screen while presenting at actual size.
    if (activeNode === null) {
      return;
    }
    const element = canvasRef.current?.querySelector(`[data-node="${activeNode}"]`);
    if (element && typeof element.scrollIntoView === "function") {
      element.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
    }
  }, [activeNode]);
  const cue = current
    ? `${current.say}${current.note ? ` ${current.note}` : ""}`
    : upto !== null
      ? (view.steps.find((s) => s.id === upto)?.cue ?? view.cue)
      : view.cue;

  const startTrace = () => {
    setUpto(null);
    setHop(0);
    setSelected(trace?.steps[0]?.node ?? null);
  };
  const moveTrace = (delta: number) => {
    if (!trace) {
      return;
    }
    const next = Math.min(Math.max(hop + delta, 0), trace.steps.length - 1);
    setHop(next);
    setSelected(trace.steps[next]?.node ?? null);
  };

  return (
    <section aria-labelledby={headingId} className="studio">
      <h2 id={headingId}>{view.title}</h2>
      <p className="lead">{view.summary}</p>
      {architecture.isError ? (
        <p role="alert" className="notice">
          Component descriptions could not be loaded. Diagram-specific summaries remain available;
          retry the page for full ownership and learning-depth detail.
        </p>
      ) : null}
      {showRuntime && runtimeQuery.isError ? (
        <p role="alert" className="notice">
          Runtime state could not be loaded. The diagram is a design view, not evidence of current
          service health.
        </p>
      ) : null}
      <p className="notice">
        Explore the design, not a recorded execution. Click any node or use Tab and Enter for
        details. Start a trace to follow the data, access and approval boundaries one hop at a time.
      </p>

      <div className="studio__controls">
        {view.steps.length > 0 ? (
          <div className="segmented" role="group" aria-label="Build the diagram">
            <button
              type="button"
              aria-pressed={upto === null}
              onClick={() => {
                setUpto(null);
              }}
            >
              Full picture
            </button>
            {view.steps.map((step) => (
              <button
                key={step.id}
                type="button"
                aria-pressed={upto === step.id}
                onClick={() => {
                  setHop(-1);
                  setUpto(step.id);
                }}
              >
                {step.label}
              </button>
            ))}
            <button
              type="button"
              disabled={stepIndex >= order.length - 1}
              onClick={() => {
                setHop(-1);
                setUpto(order[stepIndex + 1] ?? null);
              }}
            >
              Next layer →
            </button>
          </div>
        ) : null}
        {view.traces.length > 0 ? (
          <div className="trace-controls">
            <label htmlFor={traceSelect}>Request</label>
            <select
              id={traceSelect}
              value={traceId}
              onChange={(event) => {
                setTraceId(event.target.value);
                setHop(-1);
              }}
            >
              {view.traces.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                </option>
              ))}
            </select>
            {hop < 0 ? (
              <button type="button" className="primary" onClick={startTrace}>
                ▶ Trace a request
              </button>
            ) : (
              <>
                <button
                  type="button"
                  disabled={hop === 0}
                  onClick={() => {
                    moveTrace(-1);
                  }}
                >
                  ← Back
                </button>
                <button
                  type="button"
                  disabled={trace !== undefined && hop >= trace.steps.length - 1}
                  onClick={() => {
                    moveTrace(1);
                  }}
                >
                  Next step →
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setHop(-1);
                  }}
                >
                  Stop
                </button>
              </>
            )}
          </div>
        ) : null}
        <fieldset className="overlays">
          <legend>Overlays</legend>
          {hasRuntime ? (
            <label>
              <input
                type="checkbox"
                checked={showRuntime}
                onChange={(event) => {
                  setShowRuntime(event.target.checked);
                }}
              />
              Live runtime state
            </label>
          ) : null}
          <label>
            <input
              type="checkbox"
              checked={showStates}
              onChange={(event) => {
                setShowStates(event.target.checked);
              }}
            />
            Status labels
          </label>
          <label>
            <input
              type="checkbox"
              checked={fit}
              onChange={(event) => {
                setFit(event.target.checked);
              }}
            />
            Fit to width
          </label>
        </fieldset>
      </div>

      <div className="studio__cue" role="status" aria-live="polite">
        {trace ? (
          <p>
            <strong>{trace.title}:</strong> {trace.summary}
          </p>
        ) : null}
        {trace && current ? (
          <p>
            <Badge value={trace.label} /> {trace.title} · step {hop + 1} of {trace.steps.length}
            {trace.demo_act ? (
              <>
                {" "}
                · <Link to="/demo">offline demo act {trace.demo_act}</Link>
              </>
            ) : null}
          </p>
        ) : null}
        <p>
          <strong>Step explanation:</strong> {cue}
        </p>
        {current ? (
          <p className="meta">
            Active node: {view.nodes.find((node) => node.id === current.node)?.label}.{" "}
            {current.edge
              ? `Connection: ${view.edges.find((edge) => edge.id === current.edge)?.label ?? current.edge}.`
              : "This is the entry point."}{" "}
            The trace label describes the learning path, not proof of a new operation.
          </p>
        ) : null}
      </div>
      {trace ? (
        <details className="trace-outline">
          <summary>Explore all {trace.steps.length} trace steps</summary>
          <ol>
            {trace.steps.map((step, index) => (
              <li key={`${step.node}-${String(index)}`}>
                <button
                  type="button"
                  aria-current={hop === index ? "step" : undefined}
                  onClick={() => {
                    setUpto(null);
                    setHop(index);
                    setSelected(step.node);
                  }}
                >
                  {view.nodes.find((node) => node.id === step.node)?.label}
                </button>
                <p>{step.say}</p>
                {step.note ? <p className="meta">{step.note}</p> : null}
              </li>
            ))}
          </ol>
        </details>
      ) : (
        <p className="notice">No request trace has been authored for this view.</p>
      )}

      <p className="meta">
        Start with the full picture, then choose a build layer or select a component for details.
        Turn off Fit to width to scroll through the diagram at its readable drawing size.
      </p>
      <div className="studio__body">
        <div className="studio__canvas" ref={canvasRef}>
          <DiagramCanvas
            rendered={rendered}
            upto={upto}
            selected={selected}
            onSelect={setSelected}
            highlight={current ? { node: current.node, edge: current.edge } : undefined}
            badges={hop >= 0 ? badges : undefined}
            runtime={showRuntime ? runtime : undefined}
            showStates={showStates}
            fit={fit}
            label={`${view.title} diagram. Select a component for details.`}
          />
        </div>
        <aside className="inspector" aria-label="Component details" aria-live="polite">
          {selected ? (
            <Inspector
              rendered={rendered}
              nodeId={selected}
              components={components}
              runtime={showRuntime ? runtime.get(selected) : undefined}
              onSelect={(node) => {
                setHop(-1);
                setSelected(node);
              }}
            />
          ) : (
            <p>
              Select any box for what it is, what it owns, where it lives in this repository and its
              status.
            </p>
          )}
        </aside>
      </div>

      {view.bands.filter((b) => visibleAt(b.step, order, upto)).length > 0 ? (
        <ul className="bands" aria-label="Cross-cutting rules">
          {view.bands
            .filter((b) => visibleAt(b.step, order, upto))
            .map((band) => (
              <li key={band.id} className={`band band--${band.kind}`}>
                {band.text}
              </li>
            ))}
        </ul>
      ) : null}

      <p className="legend">
        Solid boxes are implemented here or documented by Microsoft; dashed boxes are planned,
        preview or optional.{" "}
        {showRuntime && hasRuntime
          ? "Runtime badges come from the control plane and refresh every 10 seconds."
          : ""}
      </p>
      <p className="studio__links">
        <a href={`/api/v1/education/views/${view.id}/drawio`} download={`${view.id}.drawio`}>
          Download draw.io file
        </a>
        {view.doc ? (
          <>
            {" "}
            · Documentation: <code>docs/architecture/{view.doc}.md</code>
          </>
        ) : null}
        {view.pattern_ids.length > 0 ? (
          <>
            {" "}
            · Patterns:{" "}
            {view.pattern_ids.map((id, index) => (
              <span key={id}>
                {index > 0 ? ", " : null}
                <Link to={`/patterns/${id}`}>{id}</Link>
              </span>
            ))}
          </>
        ) : null}
      </p>
      {view.aligned_to.length > 0 ? (
        <p className="meta">Aligned to: {view.aligned_to.join(", ")}</p>
      ) : null}

      <details className="text-alternative">
        <summary>Text description of this diagram</summary>
        <h3>Components</h3>
        <ul>
          {view.nodes.map((node) => (
            <li key={node.id}>
              <strong>{node.label}</strong> ({stateText(node.state, node.phase)})
              {node.sublabel ? `: ${node.sublabel}` : ""}
            </li>
          ))}
        </ul>
        <h3>Connections</h3>
        <ul>
          {view.edges.map((edge) => (
            <li key={edge.id}>
              {view.nodes.find((n) => n.id === edge.source)?.label} →{" "}
              {view.nodes.find((n) => n.id === edge.target)?.label}
              {edge.label ? `: ${edge.label}` : ""}
              {edge.planned ? " (planned)" : ""}
            </li>
          ))}
        </ul>
        {view.traces.map((t) => (
          <section key={t.id}>
            <h3>
              {t.title} ({t.label})
            </h3>
            <ol>
              {t.steps.map((step, index) => (
                <li key={`${t.id}-${String(index)}`}>{step.say}</li>
              ))}
            </ol>
          </section>
        ))}
      </details>
    </section>
  );
}

export function ArchitectureStudio({ viewId }: { readonly viewId: string }) {
  const view = useView(viewId);
  return (
    <QueryState label="the diagram" {...view}>
      {(rendered) => <Studio rendered={rendered} />}
    </QueryState>
  );
}
