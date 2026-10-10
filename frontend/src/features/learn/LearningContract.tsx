import { useState } from "react";
import type { LearningBrief } from "../../api/contracts";
import { useWorkshop } from "../../api/hooks";
import { ArchitectureImage } from "../../components/ArchitectureImage";
import { QueryState } from "../../components/QueryState";

function Research({ brief }: { readonly brief: LearningBrief }) {
  const workshop = useWorkshop();
  const research = brief.research;
  return (
    <section aria-labelledby="research-heading" className="research-lens">
      <p className="eyebrow">Applied research · proposed experiment, not a reported result</p>
      <h2 id="research-heading">{research.question}</h2>
      <h3>Fundamentals and theory</h3>
      <div className="foundation-grid">
        {research.foundations.map((item) => (
          <article className="card" key={item.idea}>
            <h4>{item.idea}</h4>
            <p>{item.explanation}</p>
            <p>
              <strong>In today's workflow:</strong> {item.application}
            </p>
          </article>
        ))}
      </div>
      <h3>How the ideas connect to today's tools</h3>
      <ol className="evolution-timeline">
        {research.evolution.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ol>
      <p className="meta">
        Conceptual connections are not claims that a product implements a research paper exactly.
      </p>
      <h3>Design a reproducible experiment</h3>
      <dl className="definition-list">
        <div>
          <dt>Falsifiable hypothesis</dt>
          <dd>{research.hypothesis}</dd>
        </div>
        <div>
          <dt>Controlled experiment</dt>
          <dd>{research.experiment}</dd>
        </div>
        <div>
          <dt>Independent baseline</dt>
          <dd>{research.baseline}</dd>
        </div>
        <div>
          <dt>Metrics</dt>
          <dd>
            <ul>
              {research.metrics.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </dd>
        </div>
      </dl>
      <h3>Limitations and threats to validity</h3>
      <ul>
        {research.limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <h3>Read the primary sources</h3>
      <QueryState label="reading sources" {...workshop}>
        {(data) => (
          <ul>
            {research.sources.map((id) => {
              const source = data.sources.find((item) => item.id === id);
              return (
                <li key={id}>
                  {source ? (
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.title} · {source.publisher}
                    </a>
                  ) : (
                    <span>Unresolved reading reference: {id}</span>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </QueryState>
    </section>
  );
}

export function LearningContract({ brief }: { readonly brief: LearningBrief }) {
  const [mode, setMode] = useState<"practice" | "research">("practice");
  return (
    <div className="learning-contract">
      <div className="learning-mode" role="group" aria-label="Learning lens">
        <button
          type="button"
          aria-pressed={mode === "practice"}
          onClick={() => {
            setMode("practice");
          }}
        >
          Build and verify
        </button>
        <button
          type="button"
          aria-pressed={mode === "research"}
          onClick={() => {
            setMode("research");
          }}
        >
          Foundations and research
        </button>
      </div>
      {mode === "practice" ? (
        <section aria-label="Practical learning contract">
          <div className="foundation-grid">
            <div>
              <h2>What is it?</h2>
              <p>{brief.what}</p>
            </div>
            <div>
              <h2>Why learn this?</h2>
              <p>{brief.why}</p>
            </div>
            <div>
              <h2>When to use it</h2>
              <p>{brief.when}</p>
            </div>
            <div>
              <h2>When not to use it</h2>
              <p>{brief.when_not}</p>
            </div>
          </div>
          <h2>How to implement it here</h2>
          <ol>
            {brief.how.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <div className="callout">
            <h3>Expected result</h3>
            <p>{brief.expected_result}</p>
            <h3>Failure and recovery</h3>
            <p>{brief.failure_and_recovery}</p>
          </div>
          {brief.diagram ? (
            <ArchitectureImage
              viewId={brief.diagram}
              title={`Architecture for ${brief.lesson_id}`}
            />
          ) : null}
        </section>
      ) : (
        <Research brief={brief} />
      )}
    </div>
  );
}
