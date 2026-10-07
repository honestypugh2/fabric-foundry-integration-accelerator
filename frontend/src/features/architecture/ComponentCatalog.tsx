import { useState } from "react";
import { Link } from "react-router";
import type { ArchitectureComponent, ArchitectureMap } from "../../api/contracts";
import { useArchitecture } from "../../api/hooks";
import { levelLabel, useLevel } from "../../app/levelContext";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";

function ComponentDetail({
  component,
  map,
  onSelect,
}: {
  readonly component: ArchitectureComponent;
  readonly map: ArchitectureMap;
  readonly onSelect: (id: string) => void;
}) {
  const { level } = useLevel();
  const names = new Map(map.components.map((c) => [c.id, c.name]));
  const flows = map.flows.filter((f) => f.source === component.id || f.target === component.id);
  return (
    <article className="detail" aria-labelledby="component-heading" aria-live="polite">
      <h2 id="component-heading">
        {component.name} <Badge value={component.status} kind="status" />
      </h2>
      <p className="detail__level">
        <span className="visually-hidden">At {levelLabel(level)}: </span>
        {component.description[level]}
      </p>
      <div className="two-column">
        <section aria-label="Owns">
          <h3>Owns</h3>
          <ul>
            {component.owns.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
        {component.does_not_own.length > 0 ? (
          <section aria-label="Does not own">
            <h3>Does not own</h3>
            <ul>
              {component.does_not_own.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
      <p>
        <strong>Offline equivalent:</strong> {component.offline_equivalent}
      </p>
      {flows.length > 0 ? (
        <section aria-label="Interactions">
          <h3>Interactions</h3>
          <ul>
            {flows.map((flow) => {
              const other = flow.source === component.id ? flow.target : flow.source;
              return (
                <li key={flow.id}>
                  <Badge value={flow.kind} kind="flow" />{" "}
                  {flow.source === component.id ? "To" : "From"}{" "}
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => {
                      onSelect(other);
                    }}
                  >
                    {names.get(other) ?? other}
                  </button>
                  : {flow.label}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
      {component.pattern_ids.length > 0 ? (
        <p>
          <strong>Patterns:</strong>{" "}
          {component.pattern_ids.map((id, index) => (
            <span key={id}>
              {index > 0 ? ", " : null}
              <Link to={`/patterns/${id}`}>{id}</Link>
            </span>
          ))}
        </p>
      ) : null}
    </article>
  );
}

/** Every component by layer: the text-first companion to the diagrams. */
export function ComponentCatalog() {
  const architecture = useArchitecture();
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <>
      <p>
        Choose a component to see what it owns, what it does not, how it interacts and its offline
        equivalent. The description follows your learning level.
      </p>
      <QueryState label="the architecture" {...architecture}>
        {(map) => {
          const current = map.components.find((c) => c.id === selected) ?? map.components[0];
          return (
            <div className="explorer">
              <div className="explorer__layers">
                {map.layers.map((layer) => (
                  <section key={layer.id} className="layer" aria-labelledby={`layer-${layer.id}`}>
                    <h2 id={`layer-${layer.id}`}>{layer.name}</h2>
                    <p className="layer__question">{layer.question}</p>
                    <ul className="layer__components">
                      {map.components
                        .filter((c) => c.layer === layer.id)
                        .map((c) => (
                          <li key={c.id}>
                            <button
                              type="button"
                              aria-pressed={current?.id === c.id}
                              onClick={() => {
                                setSelected(c.id);
                              }}
                            >
                              {c.name} <Badge value={c.status} kind="status" />
                            </button>
                          </li>
                        ))}
                    </ul>
                  </section>
                ))}
              </div>
              {current ? (
                <ComponentDetail component={current} map={map} onSelect={setSelected} />
              ) : null}
            </div>
          );
        }}
      </QueryState>
    </>
  );
}
