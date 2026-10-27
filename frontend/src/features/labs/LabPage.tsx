import { Link, useParams, useSearchParams } from "react-router";
import type { Lab } from "../../api/contracts";
import { useLab } from "../../api/hooks";
import { levelLabel } from "../../app/levelContext";
import { useLocalProgress } from "../../app/useLocalProgress";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { Markdown } from "../../components/Markdown";
import { PromptBlock } from "../../components/PromptBlock";
import { QueryState } from "../../components/QueryState";

function LabStages({ lab }: { readonly lab: Lab }) {
  const { done, toggle } = useLocalProgress(`lab.${lab.id}`);
  const [params, setParams] = useSearchParams();
  const selected = lab.steps.findIndex((item) => item.stage === params.get("stage"));
  const index = selected < 0 ? 0 : selected;
  const current = lab.steps[index];
  const go = (next: number) => {
    const step = lab.steps[next];
    if (step) {
      const updated = new URLSearchParams(params);
      updated.set("stage", step.stage);
      setParams(updated);
    }
  };
  return (
    <article aria-labelledby="lab-heading">
      <h1 id="lab-heading">
        {lab.title} <Badge value={lab.mode} />
      </h1>
      <p className="lead">{lab.summary}</p>
      <p className="meta">
        {levelLabel(lab.level)} · about {lab.duration_minutes} minutes · {done.length} of{" "}
        {lab.steps.length} stages done
      </p>
      <progress max={lab.steps.length} value={done.length} aria-label="Stages done" />
      {lab.prerequisites.length > 0 ? (
        <section aria-labelledby="lab-prereq">
          <h2 id="lab-prereq">Before you start</h2>
          <ul>
            {lab.prerequisites.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <p className="notice">
        Your checklist is saved in this browser only. Marking a stage done is not proof that a tool
        ran or a cloud change succeeded.
      </p>
      <div className="lab-workspace">
        <nav className="lab-outline" aria-label="Lab stages">
          <ol>
            {lab.steps.map((step, position) => (
              <li key={step.stage}>
                <button
                  type="button"
                  aria-label={`${String(position + 1).padStart(2, "0")} ${step.stage}: ${step.title}`}
                  aria-current={position === index ? "step" : undefined}
                  onClick={() => {
                    go(position);
                  }}
                >
                  <span className="stage-index">{String(position + 1).padStart(2, "0")}</span>
                  <span>
                    {step.stage}
                    <small>{step.title}</small>
                  </span>
                  {done.includes(step.stage) ? <span aria-label="Completed">✓</span> : null}
                </button>
              </li>
            ))}
          </ol>
        </nav>
        {current ? (
          [current].map((step) => (
            <section
              key={step.stage}
              className="stage stage--focused"
              aria-label={`Stage ${String(index + 1)}: ${step.stage}`}
            >
              <p className="eyebrow">
                Stage {index + 1} of {lab.steps.length}
              </p>
              <h2>
                <span className="stage__name">{step.stage}</span> {step.title}
              </h2>
              <Markdown>{step.instructions}</Markdown>
              {step.commands.map((command) => (
                <PromptBlock key={command} title="Command" text={command} />
              ))}
              {step.expected ? (
                <p>
                  <strong>Expected:</strong> {step.expected}
                </p>
              ) : null}
              {step.evidence_category ? (
                <Badge value={step.evidence_category} kind="evidence" />
              ) : null}
              <label className="stage__done">
                <input
                  type="checkbox"
                  checked={done.includes(step.stage)}
                  onChange={(event) => {
                    toggle(step.stage, event.target.checked);
                  }}
                />
                Mark {step.stage} done
              </label>
              <div className="stage-actions">
                <button
                  type="button"
                  disabled={index === 0}
                  onClick={() => {
                    go(index - 1);
                  }}
                >
                  Previous stage
                </button>
                <button
                  type="button"
                  className="primary"
                  disabled={index === lab.steps.length - 1}
                  onClick={() => {
                    go(index + 1);
                  }}
                >
                  Next stage
                </button>
              </div>
            </section>
          ))
        ) : (
          <p className="notice">No stages have been authored for this lab.</p>
        )}
      </div>
      {lab.lessons.length > 0 ? (
        <p>
          Lessons:{" "}
          {lab.lessons.map((id, index) => (
            <span key={id}>
              {index > 0 ? ", " : null}
              <Link to={`/learn/${id}`}>{id}</Link>
            </span>
          ))}
        </p>
      ) : null}
    </article>
  );
}

export function LabPage() {
  const { labId = "" } = useParams();
  usePageTitle("Lab");
  const lab = useLab(labId);
  return (
    <QueryState label="the lab" {...lab}>
      {(data) => <LabStages lab={data} />}
    </QueryState>
  );
}
