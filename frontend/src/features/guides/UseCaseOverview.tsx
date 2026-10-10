import { Link } from "react-router";
import type { Guide } from "../../api/contracts";
import { useWorkshop } from "../../api/hooks";
import { ArchitectureImage } from "../../components/ArchitectureImage";
import { QueryState } from "../../components/QueryState";

export function UseCaseOverview({ guide }: { readonly guide: Guide }) {
  const workshop = useWorkshop();
  return (
    <QueryState label="use-case learning story" {...workshop}>
      {(data) => {
        const story = data.content.use_cases.find((item) => item.guide_id === guide.id);
        if (!story)
          return (
            <p className="notice">
              A business-to-build story has not been authored for this use case.
            </p>
          );
        return (
          <section className="use-case-overview" aria-labelledby="outcome-heading">
            <div className="foundation-grid">
              <div>
                <p className="eyebrow">The business problem</p>
                <h2 id="outcome-heading">What are we improving?</h2>
                <p>{story.problem}</p>
                <p className="meta">For {story.audience}</p>
              </div>
              <div className="callout">
                <h3>What you will demonstrate</h3>
                <ul>
                  {story.outcomes.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <details open>
              <summary>Learn the concepts before building</summary>
              <ul className="concept-links">
                {story.lesson_ids.map((id) => (
                  <li key={id}>
                    <Link to={`/learn/${id}`}>
                      {data.content.briefs.find((brief) => brief.lesson_id === id)?.what ?? id}
                    </Link>
                  </li>
                ))}
              </ul>
            </details>
            <h2>How the capability develops</h2>
            <ol className="capability-stages">
              {story.stages.map((stage) => (
                <li className="card" key={stage.title}>
                  <h3>{stage.title}</h3>
                  <p>{stage.task}</p>
                  <p>{stage.capability}</p>
                  <p>
                    <strong>Control:</strong> {stage.control}
                  </p>
                  <p>
                    <strong>Proof:</strong> {stage.evidence}
                  </p>
                </li>
              ))}
            </ol>
            {story.questions.length ? (
              <section>
                <h3>Business questions to explain</h3>
                <ol>
                  {story.questions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
              </section>
            ) : null}
            {guide.diagram ? (
              <ArchitectureImage
                viewId={guide.diagram}
                title={`Intended architecture for ${guide.title}`}
              />
            ) : null}
            <details>
              <summary>Prototype boundaries and production gaps</summary>
              <ul>
                {story.production_gaps.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </details>
            <p className="hero-actions">
              <a href={story.presenter_path} target="_blank" rel="noreferrer">
                Open presenter talk track
              </a>
              <Link to="/evidence">Inspect recorded evidence</Link>
            </p>
          </section>
        );
      }}
    </QueryState>
  );
}
