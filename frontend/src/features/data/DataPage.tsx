import { useId, useState } from "react";
import { describeError } from "../../api/client";
import type { EnvelopeMeta } from "../../api/contracts";
import { useEvaluation, useLakehouses, usePreview, useProfiles, useTables } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";

function Provenance({ envelope }: { readonly envelope: EnvelopeMeta }) {
  return (
    <p className="provenance">
      <Badge value={envelope.execution_label} /> served by {envelope.selected_provider}
      {envelope.fallback_used && envelope.fallback_reason
        ? ` (fallback: ${envelope.fallback_reason})`
        : ""}
      . Equivalent Fabric service: {envelope.equivalent_fabric_service}.
      {envelope.simulation_notice ? ` ${envelope.simulation_notice}` : ""}
    </p>
  );
}

function TableExplorer({ lakehouseId }: { readonly lakehouseId: string }) {
  const tables = useTables(lakehouseId);
  const [table, setTable] = useState<string | null>(null);
  const preview = usePreview(lakehouseId, table);
  return (
    <QueryState label="tables" {...tables}>
      {(envelope) => (
        <>
          <Provenance envelope={envelope} />
          <div className="table-scroll" tabIndex={0} role="region" aria-label="Lakehouse tables">
            <table>
              <caption>Tables by medallion layer</caption>
              <thead>
                <tr>
                  <th scope="col">Layer</th>
                  <th scope="col">Table</th>
                  <th scope="col">Rows</th>
                  <th scope="col">Preview</th>
                </tr>
              </thead>
              <tbody>
                {envelope.data.map((info) => (
                  <tr key={info.name}>
                    <td>{info.layer}</td>
                    <td>
                      <code>{info.name}</code>
                    </td>
                    <td>{info.row_count.toLocaleString()}</td>
                    <td>
                      <button
                        type="button"
                        aria-pressed={table === info.name}
                        onClick={() => {
                          setTable(info.name);
                        }}
                      >
                        Preview <span className="visually-hidden">{info.name}</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {table === null ? null : (
            <section aria-labelledby="preview-heading">
              <h3 id="preview-heading">Preview: {table}</h3>
              <QueryState label="the preview" {...preview}>
                {(result) => (
                  <>
                    <Provenance envelope={result} />
                    <div
                      className="table-scroll"
                      tabIndex={0}
                      role="region"
                      aria-label="Table preview"
                    >
                      <table>
                        <caption>
                          First {result.data.rows.length} of {result.data.total_rows} rows
                          (synthetic)
                        </caption>
                        <thead>
                          <tr>
                            {result.data.columns.map((column) => (
                              <th key={column.name} scope="col">
                                {column.name}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {result.data.rows.map((row, index) => (
                            // Preview rows have no stable key; the order is fixed per request.
                            <tr key={index}>
                              {result.data.columns.map((column) => (
                                <td key={column.name}>{String(row[column.name] ?? "")}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </QueryState>
            </section>
          )}
        </>
      )}
    </QueryState>
  );
}

function Evaluation() {
  const profiles = useProfiles();
  const evaluation = useEvaluation();
  const [profile, setProfile] = useState("hc-lab-7file-v1");
  const selectId = useId();
  return (
    <section aria-labelledby="evaluation-heading">
      <h2 id="evaluation-heading">Evaluate measures against the baseline</h2>
      <QueryState label="profiles" {...profiles}>
        {(all) => (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              evaluation.mutate(profile);
            }}
          >
            <label htmlFor={selectId}>Dataset profile</label>
            <select
              id={selectId}
              value={profile}
              onChange={(event) => {
                setProfile(event.target.value);
              }}
            >
              {all.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <button type="submit" disabled={evaluation.isPending}>
              Run evaluation
            </button>
          </form>
        )}
      </QueryState>
      {evaluation.error ? <p role="alert">{describeError(evaluation.error)}</p> : null}
      {evaluation.data ? (
        <div role="status">
          <Provenance envelope={evaluation.data} />
          <p>
            <strong>
              {evaluation.data.data.passed} of {evaluation.data.data.compared}
            </strong>{" "}
            measures match the expected baseline. Gate:{" "}
            {evaluation.data.data.gate_passed ? "passed" : "failed"}.
          </p>
          <div className="table-scroll" tabIndex={0} role="region" aria-label="Measure comparison">
            <table>
              <caption>Synthetic demonstration measures (not clinical measures)</caption>
              <thead>
                <tr>
                  <th scope="col">Measure</th>
                  <th scope="col">Expected</th>
                  <th scope="col">Observed</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {evaluation.data.data.comparisons.map((row) => (
                  <tr key={row.name}>
                    <td>{row.name}</td>
                    <td>{row.expected ?? "null"}</td>
                    <td>{row.observed ?? "null"}</td>
                    <td>{row.passed ? "Pass" : "Fail"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export function DataPage() {
  usePageTitle("Data");
  const lakehouses = useLakehouses();
  const [selected, setSelected] = useState<string | null>(null);
  const selectId = useId();
  return (
    <>
      <h1>Medallion data explorer</h1>
      <p>
        Read-only, allow-listed reads through the provider router. Offline, results come from the
        Local Fabric Educational Provider and are labeled LOCAL. They are not Fabric operations.
      </p>
      <QueryState label="lakehouses" {...lakehouses}>
        {(items) => {
          const current = selected ?? items[0]?.id ?? null;
          return (
            <>
              <label htmlFor={selectId}>Lakehouse</label>
              <select
                id={selectId}
                value={current ?? ""}
                onChange={(event) => {
                  setSelected(event.target.value);
                }}
              >
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.display_name} ({item.label})
                  </option>
                ))}
              </select>
              {current === null ? (
                <p>No lakehouse is available. Build the data with make data.</p>
              ) : (
                <TableExplorer key={current} lakehouseId={current} />
              )}
            </>
          );
        }}
      </QueryState>
      <Evaluation />
    </>
  );
}
