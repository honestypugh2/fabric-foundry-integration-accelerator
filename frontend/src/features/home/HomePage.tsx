import { TalkTracks } from "../demo/TalkTracks";
import { Link } from "react-router";
import { useCompleteness, useWorkshop } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";
import { principles } from "../../content/principles";
import { Journeys } from "../workshop/Journeys";

export function HomePage() {
  usePageTitle("Home");
  const completeness = useCompleteness();
  const workshop = useWorkshop();
  return (
    <>
      <QueryState label="workshop" {...workshop}>
        {(data) => (
          <>
            <section className="workshop-hero" aria-labelledby="workshop-heading">
              <div>
                <p className="eyebrow">Fabric + Foundry · a build-and-learn workshop</p>
                <h1 id="workshop-heading">{data.content.title}</h1>
                <p className="lead">{data.content.summary}</p>
                <div className="hero-actions">
                  <Link className="button-link" to="/use-cases">
                    Build a use case
                  </Link>
                  <Link to="/learn">Understand the foundations</Link>
                </div>
              </div>
              <ol className="hero-loop" aria-label="Workshop cycle">
                <li>
                  <span>01</span>
                  <strong>Understand</strong>
                  <small>Foundations and assumptions</small>
                </li>
                <li>
                  <span>02</span>
                  <strong>Build</strong>
                  <small>Bounded, governed workflows</small>
                </li>
                <li>
                  <span>03</span>
                  <strong>Inspect</strong>
                  <small>Evidence and failure modes</small>
                </li>
                <li>
                  <span>04</span>
                  <strong>Investigate</strong>
                  <small>Experiment, compare, improve</small>
                </li>
              </ol>
            </section>
            <section aria-labelledby="paths-heading">
              <h2 id="paths-heading">Choose your learning journey</h2>
              <Journeys workshop={data} />
            </section>
          </>
        )}
      </QueryState>
      <section aria-labelledby="principles-heading">
        <h2 id="principles-heading">The central lesson</h2>
        <ul className="principles">
          {principles.map((principle) => (
            <li key={principle.id}>{principle.statement}</li>
          ))}
        </ul>
      </section>
      <section className="callout" aria-labelledby="present-heading">
        <h2 id="present-heading">Present, build or explore</h2>
        <p>
          Use Cases connect business outcomes to concepts and checkpoints. Labs rehearse safely.
          Evidence separates documented behavior from actual execution.
        </p>
        <TalkTracks />
        <Link to="/labs">Open hands-on labs</Link>
        {" · "}
        <Link to="/evidence">Inspect evidence</Link>
      </section>
      <details>
        <summary>Architecture coverage—not workshop or live certification</summary>
        <section aria-labelledby="completeness-heading">
          <h2 id="completeness-heading">Architecture completeness</h2>
          <QueryState label="completeness" {...completeness}>
            {(report) => (
              <>
                <p>
                  <strong>
                    {report.answered} of {report.total}
                  </strong>{" "}
                  architecture questions have linked content at every level. Presence is not a
                  measure of teaching quality or live certification.
                </p>
                <progress
                  max={report.total}
                  value={report.answered}
                  aria-label="Questions answered"
                >
                  {Math.round(report.coverage * 100)}%
                </progress>
                <details>
                  <summary>Questions still planned</summary>
                  <ul>
                    {report.items
                      .filter((item) => !item.answered)
                      .map((item) => (
                        <li key={item.id}>
                          {item.id}: {item.question}{" "}
                          {item.planned_phase === null ? null : (
                            <span>(Phase {item.planned_phase})</span>
                          )}
                        </li>
                      ))}
                  </ul>
                </details>
              </>
            )}
          </QueryState>
        </section>
      </details>
    </>
  );
}
