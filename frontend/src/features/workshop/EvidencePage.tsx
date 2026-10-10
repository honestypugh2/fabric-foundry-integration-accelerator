import { Link } from "react-router";
import { useWorkshop } from "../../api/hooks";
import type { Workshop } from "../../api/contracts";
import { usePageTitle } from "../../app/usePageTitle";
import { usePageAnchor } from "../../app/usePageAnchor";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";
import phaseRecord from "../../../../docs/operations/phase-verification.md?url";
import observabilityRecord from "../../../../infra/observability/README.md?url";

const RECORDS: Readonly<Record<string, string>> = {
  "docs/operations/phase-verification.md": phaseRecord,
  "infra/observability/README.md": observabilityRecord,
};

const GROUPS = [
  { category: "DEPLOYMENT", title: "Deployed Azure and Fabric resources" },
  { category: "OPERATION", title: "Recorded operations" },
  { category: "INTERFACE", title: "Local interface evidence" },
] as const;

function EvidenceCard({ entry }: { readonly entry: Workshop["content"]["evidence"][number] }) {
  const record = entry.verification_record ? RECORDS[entry.verification_record] : undefined;
  return (
    <article className="card" id={entry.id}>
      <p className="eyebrow">
        <time dateTime={entry.recorded_on}>{entry.recorded_on}</time> · recorded result{" "}
        <Badge value={entry.label} />
      </p>
      <h3>{entry.title}</h3>
      <p>{entry.scope}</p>
      <dl className="definition-list">
        <div>
          <dt>Provider</dt>
          <dd>{entry.provider}</dd>
        </div>
        <div>
          <dt>Server / path</dt>
          <dd>{entry.server}</dd>
        </div>
        <div>
          <dt>Actual tool / operation</dt>
          <dd>{entry.tool}</dd>
        </div>
      </dl>
      {entry.verification_record ? (
        record ? (
          <a href={record} download={entry.verification_record.replaceAll("/", "-")}>
            Download verification record: {entry.verification_record}
          </a>
        ) : (
          <p className="notice">
            Verification record is not published in this interface: {entry.verification_record}
          </p>
        )
      ) : null}
      {entry.screenshot ? (
        <figure>
          <img
            className="evidence-image"
            src={entry.screenshot}
            alt={`${entry.title}: synthetic UI only, not cloud execution`}
            loading="lazy"
          />
          <figcaption>Interface evidence only; captured before this redesign.</figcaption>
        </figure>
      ) : null}
      <h4>What this does not prove</h4>
      <ul>
        {entry.limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </article>
  );
}

export function EvidencePage() {
  usePageTitle("Evidence");
  const workshop = useWorkshop();
  usePageAnchor(workshop.isSuccess);
  return (
    <>
      <header className="page-intro">
        <p className="eyebrow">Inspect, don't assume</p>
        <h1>Local and Azure/Fabric live evidence</h1>
        <p className="lead">
          Choose an offline or connected path. Inspect the deployed environment, actual recorded
          operations and interface evidence separately.
        </p>
      </header>
      <p className="notice">
        These dated records are not a current health check. LOCAL describes reading this catalogue,
        not every operation inside it: LIVE records describe actual Azure/Fabric checks, and PREVIEW
        identifies the preview agent integration. Tenant identifiers stay private.
      </p>
      <QueryState label="workshop evidence" {...workshop}>
        {(data) => (
          <>
            <section aria-labelledby="execution-paths-heading">
              <h2 id="execution-paths-heading">Choose your execution path</h2>
              <p>{data.content.execution_summary}</p>
              <ul className="cards execution-path-cards">
                {data.content.execution_paths.map((path) => (
                  <li className="card" key={path.mode}>
                    <Badge value={path.mode} />
                    <h3>{path.title}</h3>
                    <p>{path.description}</p>
                    <p>{path.results}</p>
                    <p>
                      <strong>Fallback:</strong> {path.fallback}
                    </p>
                    <details>
                      <summary>Setup commands and safeguards</summary>
                      <h4>Prerequisites</h4>
                      <ul>
                        {path.prerequisites.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                      <h4>Commands to run deliberately</h4>
                      {path.commands.map((command) => (
                        <pre key={command}>
                          <code>{command}</code>
                        </pre>
                      ))}
                      <p className="notice">{path.safety}</p>
                    </details>
                  </li>
                ))}
              </ul>
              <Link to="/demo">Inspect readiness and demo options</Link>
            </section>
            {GROUPS.map((group) => {
              const entries = data.content.evidence.filter(
                (entry) => entry.category === group.category,
              );
              return (
                <section key={group.category} aria-labelledby={`evidence-${group.category}`}>
                  <h2 id={`evidence-${group.category}`}>{group.title}</h2>
                  {entries.length ? (
                    <div className="evidence-grid">
                      {entries.map((entry) => (
                        <EvidenceCard key={entry.id} entry={entry} />
                      ))}
                    </div>
                  ) : (
                    <p className="notice">No evidence recorded for this category.</p>
                  )}
                </section>
              );
            })}
          </>
        )}
      </QueryState>
      <section className="callout">
        <h2>Compare observable outcomes</h2>
        <p>
          Copilot recordings are measured observations. Claude Code remains DOCUMENTED ONLY, not a
          scored competitor.
        </p>
        <Link to="/bakeoff">Inspect the bake-off</Link>
        {" · "}
        <Link to="/demo">Run the labeled offline demonstration</Link>
      </section>
    </>
  );
}
