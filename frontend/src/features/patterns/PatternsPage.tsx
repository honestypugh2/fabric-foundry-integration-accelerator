import { useId, useState } from "react";
import { Link } from "react-router";
import type { Pattern } from "../../api/contracts";
import { describeError } from "../../api/client";
import { usePatterns, useRecommend, useSelectionSignals } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";
import { PatternCoverage } from "./PatternCoverage";

const MAX_COMPARE = 3;
const STATUSES = ["ALL", "GA", "MIXED", "PREVIEW"] as const;
type StatusFilter = (typeof STATUSES)[number];

const COMPARE_ROWS: readonly { readonly key: keyof Pattern; readonly label: string }[] = [
  { key: "status", label: "Status" },
  { key: "when_to_use", label: "When to use" },
  { key: "when_not_to_use", label: "When not to use" },
  { key: "fabric_role", label: "Fabric role" },
  { key: "foundry_role", label: "Foundry role" },
  { key: "mcp_role", label: "MCP role" },
  { key: "authority", label: "Authority" },
  { key: "offline_equivalent", label: "Offline equivalent" },
  { key: "default_demo_path", label: "Default demo path" },
];

function cell(value: Pattern[keyof Pattern]): string {
  return Array.isArray(value) ? value.join(", ") : value;
}

function Selector() {
  const signals = useSelectionSignals();
  const recommend = useRecommend();
  const [needs, setNeeds] = useState<readonly string[]>([]);
  return (
    <section aria-labelledby="selector-heading">
      <h2 id="selector-heading">Pattern selector</h2>
      <QueryState label="selection needs" {...signals}>
        {(vocabulary) => (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              recommend.mutate(needs);
            }}
          >
            <fieldset className="checkbox-grid">
              <legend>What do you need?</legend>
              {vocabulary.map((signal) => (
                <label key={signal.id}>
                  <input
                    type="checkbox"
                    checked={needs.includes(signal.id)}
                    onChange={(event) => {
                      setNeeds(
                        event.target.checked
                          ? [...needs, signal.id]
                          : needs.filter((n) => n !== signal.id),
                      );
                    }}
                  />
                  {signal.description}
                </label>
              ))}
            </fieldset>
            <button type="submit" disabled={needs.length === 0 || recommend.isPending}>
              Recommend patterns
            </button>
          </form>
        )}
      </QueryState>
      {recommend.error ? (
        <p role="alert" className="notice notice--error">
          {describeError(recommend.error)}
        </p>
      ) : null}
      {recommend.data ? (
        <ol className="recommendations" aria-label="Recommended patterns">
          {recommend.data.map((rec) => (
            <li key={rec.pattern_id}>
              <Link to={`/patterns/${rec.pattern_id}`}>
                {rec.pattern_id} {rec.name}
              </Link>{" "}
              <Badge value={rec.status} kind="status" /> <span>score {rec.score}</span>
              <p>{rec.why}</p>
              {rec.preview_dependencies.length > 0 ? (
                <p>
                  <strong>Requires preview:</strong> {rec.preview_dependencies.join(", ")}
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}

function Comparison({ patterns }: { readonly patterns: readonly Pattern[] }) {
  if (patterns.length < 2) {
    return <p>Select two or three patterns to compare them side by side.</p>;
  }
  return (
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Pattern comparison">
      <table>
        <caption>Pattern comparison</caption>
        <thead>
          <tr>
            <th scope="col">Aspect</th>
            {patterns.map((p) => (
              <th key={p.id} scope="col">
                {p.id} {p.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {COMPARE_ROWS.map((row) => (
            <tr key={row.key}>
              <th scope="row">{row.label}</th>
              {patterns.map((p) => (
                <td key={p.id}>{cell(p[row.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function PatternsPage() {
  usePageTitle("Patterns");
  const patterns = usePatterns();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("ALL");
  const [compare, setCompare] = useState<readonly string[]>([]);
  const searchId = useId();
  const statusId = useId();
  return (
    <>
      <h1>Pattern catalog</h1>
      <QueryState label="patterns" {...patterns}>
        {(all) => {
          const needle = query.trim().toLowerCase();
          const visible = all.filter(
            (p) =>
              (status === "ALL" || p.status === status) &&
              (needle === "" || `${p.id} ${p.name} ${p.summary}`.toLowerCase().includes(needle)),
          );
          return (
            <>
              <div className="filters">
                <label htmlFor={searchId}>Search</label>
                <input
                  id={searchId}
                  type="search"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                  }}
                />
                <label htmlFor={statusId}>Status</label>
                <select
                  id={statusId}
                  value={status}
                  onChange={(event) => {
                    const next = STATUSES.find((s) => s === event.target.value);
                    setStatus(next ?? "ALL");
                  }}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s === "ALL" ? "All statuses" : s}
                    </option>
                  ))}
                </select>
              </div>
              <p role="status">
                Showing {visible.length} of {all.length} patterns.
              </p>
              <ul className="cards">
                {visible.map((p) => (
                  <li key={p.id} className="card">
                    <h2 className="card__title">
                      <Link to={`/patterns/${p.id}`}>
                        {p.id} {p.name}
                      </Link>{" "}
                      <Badge value={p.status} kind="status" />
                    </h2>
                    <p>{p.summary}</p>
                    <label>
                      <input
                        type="checkbox"
                        checked={compare.includes(p.id)}
                        disabled={!compare.includes(p.id) && compare.length >= MAX_COMPARE}
                        onChange={(event) => {
                          setCompare(
                            event.target.checked
                              ? [...compare, p.id]
                              : compare.filter((id) => id !== p.id),
                          );
                        }}
                      />
                      Compare
                    </label>
                  </li>
                ))}
              </ul>
              <section aria-labelledby="compare-heading">
                <h2 id="compare-heading">Compare</h2>
                <Comparison patterns={all.filter((p) => compare.includes(p.id))} />
              </section>
            </>
          );
        }}
      </QueryState>
      <Selector />
      <PatternCoverage />
    </>
  );
}
