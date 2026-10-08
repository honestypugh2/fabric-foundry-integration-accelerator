import { describeError } from "../../api/client";
import { useDemoStatus, useRunDemo } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";
import { TalkTracks } from "./TalkTracks";

export function DemoPage() {
  usePageTitle("Demo");
  const status = useDemoStatus();
  const run = useRunDemo();
  return (
    <>
      <h1>Demo mode</h1>
      <TalkTracks />
      <section aria-labelledby="readiness-heading">
        <h2 id="readiness-heading">Readiness</h2>
        <QueryState label="demo readiness" {...status}>
          {(report) => (
            <>
              <div className="table-scroll" tabIndex={0} role="region" aria-label="Demo readiness">
                <table>
                  <caption>Each component is probed; nothing is assumed available.</caption>
                  <thead>
                    <tr>
                      <th scope="col">Component</th>
                      <th scope="col">Status</th>
                      <th scope="col">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.lines.map((line) => (
                      <tr key={line.component}>
                        <td>{line.component}</td>
                        <td>{line.status}</td>
                        <td>{line.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p>
                Recommended mode: <Badge value={report.recommended_mode} />. {report.reason}
              </p>
            </>
          )}
        </QueryState>
      </section>
      <section aria-labelledby="run-heading">
        <h2 id="run-heading">Ten-act offline demo</h2>
        <p>
          Runs the release-gate demo against the control plane. Every act is labeled; acts that need
          later phases are shown as unavailable rather than simulated.
        </p>
        <button
          type="button"
          disabled={run.isPending}
          onClick={() => {
            run.mutate();
          }}
        >
          {run.isPending ? "Running…" : "Run the offline demo"}
        </button>
        {run.error ? (
          <p role="alert" className="notice notice--error">
            {describeError(run.error)}
          </p>
        ) : null}
        {run.data ? (
          <div role="status">
            <p>
              <strong>Release gate: {run.data.passed ? "PASSED" : "FAILED"}</strong>. LIVE
              operations: {run.data.live_operations}. Cloud operations: {run.data.cloud_operations}.
            </p>
            <ol className="acts">
              {run.data.steps.map((step) => (
                <li key={step.act} className="act">
                  <h3>
                    Act {step.act}: {step.title} <Badge value={step.label} />{" "}
                    <span>{step.passed ? "Passed" : step.required ? "Failed" : "Skipped"}</span>
                  </h3>
                  <p>{step.summary}</p>
                  {step.evidence.filter(Boolean).length > 0 ? (
                    <ul>
                      {step.evidence.filter(Boolean).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </section>
    </>
  );
}
