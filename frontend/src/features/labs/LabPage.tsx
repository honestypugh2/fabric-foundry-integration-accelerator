import { Link, useParams } from "react-router";
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
      <ol className="stages">
        {lab.steps.map((step) => (
          <li key={step.stage} className="stage">
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
          </li>
        ))}
      </ol>
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
