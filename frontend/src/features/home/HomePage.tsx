import { Link } from "react-router";
import { useCompleteness, useGuides, useWorkshop } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";
import { principles } from "../../content/principles";
import { Journeys } from "../workshop/Journeys";

export function HomePage() {
  usePageTitle("Home");
  const completeness = useCompleteness();
  const workshop = useWorkshop();
  const guides = useGuides();
  return (
    <>
      <QueryState label="workshop" {...workshop}>
        {(data) => (
          <>
            <section className="workshop-hero" aria-labelledby="workshop-heading">
              <div>
                <p className="eyebrow">Solution accelerator · development showcase</p>
                <h1 id="workshop-heading">{data.content.title}</h1>
                <p className="lead">{data.content.summary}</p>
                <div className="hero-actions">
                  <Link className="button-link" to="/use-cases">
                    Build a use case
                  </Link>
                  <Link to="/learn">Understand the foundations</Link>
                </div>
              </div>
              <ol className="hero-loop" aria-label="What, why and how">
                <li>
                  <span>01</span>
                  <strong>What is this?</strong>
                  <small>A reference implementation and hands-on learning environment.</small>
                </li>
                <li>
                  <span>02</span>
                  <strong>Why use it?</strong>
                  <small>
                    Learn to improve data engineering and build grounded agents without confusing
                    access with authority.
                  </small>
                </li>
                <li>
                  <span>03</span>
                  <strong>How do I start?</strong>
                  <small>
                    Choose a use case, follow one checkpoint, verify its expected result.
                  </small>
                </li>
                <li>
                  <span>04</span>
                  <strong>What runs?</strong>
                  <small>
                    LIVE first in your development environment, with explicit LOCAL read fallback.
                    Offline learning is always available; live changes need approval.
                  </small>
                </li>
              </ol>
            </section>
            <nav className="workshop-flow" aria-label="Workshop flow">
              <Link to="/use-cases">
                <span>01 · Discover</span>
                <strong>Choose your outcome</strong>
              </Link>
              <Link to="/learn">
                <span>02 · Understand</span>
                <strong>Learn the concepts</strong>
              </Link>
              <Link to="/labs">
                <span>03 · Build</span>
                <strong>Practice step by step</strong>
              </Link>
              <Link to="/evidence">
                <span>04 · Verify</span>
                <strong>Show what actually ran</strong>
              </Link>
            </nav>
            <section className="start-paths" aria-labelledby="start-heading">
              <p className="eyebrow">Choose one path</p>
              <h2 id="start-heading">Build something you can explain</h2>
              <QueryState label="use-case catalog" {...guides}>
                {(catalog) => (
                  <div className="cards">
                    {data.content.use_cases.map((story, index) => (
                      <article className="card start-card" key={story.guide_id}>
                        <span className="path-number">0{index + 1}</span>
                        <h3>
                          {catalog.find((guide) => guide.id === story.guide_id)?.title ??
                            story.guide_id}
                        </h3>
                        <p>{story.problem}</p>
                        <p className="meta">For {story.audience}</p>
                        <Link className="button-link" to={`/use-cases/${story.guide_id}`}>
                          Open the build guide
                        </Link>
                      </article>
                    ))}
                  </div>
                )}
              </QueryState>
            </section>
            <details className="learning-library">
              <summary>Prefer to learn the concepts first?</summary>
              <section aria-labelledby="paths-heading">
                <h2 id="paths-heading">Choose your learning journey</h2>
                <Journeys workshop={data} />
              </section>
            </details>
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
        <h2 id="present-heading">Learn by doing, then inspect the evidence</h2>
        <p>
          Use Cases connect business outcomes to concepts and checkpoints. Labs rehearse safely.
          Evidence separates documented behavior from actual execution.
        </p>
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
