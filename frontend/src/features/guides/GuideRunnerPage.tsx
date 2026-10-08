import { Link, useParams } from "react-router";
import type { Guide, GuideStep } from "../../api/contracts";
import { useGuide } from "../../api/hooks";
import { useLocalProgress } from "../../app/useLocalProgress";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { PromptBlock } from "../../components/PromptBlock";
import { QueryState } from "../../components/QueryState";
import { DiagramCanvas } from "../architecture/DiagramCanvas";
import { useView } from "../../api/hooks";
import { ChangeRehearsal } from "./ChangeRehearsal";

function StepDiagram({
  viewId,
  focus,
  stepTitle,
}: {
  readonly viewId: string;
  readonly focus: readonly string[];
  readonly stepTitle: string;
}) {
  const view = useView(viewId);
  const names = new Map((view.data?.view.nodes ?? []).map((n) => [n.id, n.label]));
  return (
    <section aria-labelledby="step-diagram-heading" className="guide-diagram">
      <h3 id="step-diagram-heading">Where this step happens</h3>
      <QueryState label="the guide diagram" {...view}>
        {(rendered) => (
          <>
            <div className="studio__canvas">
              <DiagramCanvas
                rendered={rendered}
                upto={null}
                selected={null}
                onSelect={() => undefined}
                focus={focus}
                interactive={false}
                label={`Guide diagram for ${stepTitle}`}
              />
            </div>
            <p>
              Highlighted: {focus.map((id) => names.get(id) ?? id).join(", ")}.{" "}
              <Link to={`/architecture/${viewId}`}>Open the full interactive diagram</Link>
            </p>
          </>
        )}
      </QueryState>
    </section>
  );
}

function StepView({ guide, step }: { readonly guide: Guide; readonly step: GuideStep }) {
  const evidence = useLocalProgress(`guide.${guide.id}.${step.id}.evidence`);
  const index = guide.steps.findIndex((s) => s.id === step.id);
  const previous = guide.steps[index - 1];
  const next = guide.steps[index + 1];
  return (
    <article className="step" aria-labelledby="step-heading">
      <h2 id="step-heading">
        Step {index + 1}: {step.title}
      </h2>
      <p className="lead">{step.objective}</p>
      <ul className="step__flags">
        {step.writes ? (
          <li>
            <Badge value="WRITE" kind="flag" /> Human approval required before this step changes
            anything.
          </li>
        ) : (
          <li>
            <Badge value="READ-ONLY" kind="flag" /> This step does not change anything.
          </li>
        )}
        {step.requires_windows ? <li>Needs a Windows workstation for the live path.</li> : null}
      </ul>

      <section aria-labelledby="tool-heading">
        <h3 id="tool-heading">Provider, server and tool</h3>
        <dl className="definition-list">
          <div>
            <dt>Provider</dt>
            <dd>{step.tool_path.provider}</dd>
          </div>
          <div>
            <dt>Server</dt>
            <dd>{step.tool_path.server ?? "None"}</dd>
          </div>
          <div>
            <dt>Tools</dt>
            <dd>{step.tool_path.tools.length > 0 ? step.tool_path.tools.join(", ") : "None"}</dd>
          </div>
          <div>
            <dt>Fabric Skills</dt>
            <dd>{step.skills.length > 0 ? step.skills.join(", ") : "None"}</dd>
          </div>
          <div>
            <dt>Fallback</dt>
            <dd>
              {step.tool_path.fallback === null ? (
                "None: report the limitation and stop"
              ) : (
                <>
                  <Badge value={step.tool_path.fallback.label} />{" "}
                  <code>{step.tool_path.fallback.server}</code>:{" "}
                  {step.tool_path.fallback.tools.join(", ")}
                  {step.tool_path.fallback.note ? `. ${step.tool_path.fallback.note}` : ""}
                </>
              )}
            </dd>
          </div>
        </dl>
        {step.tool_path.substitution_allowed ? null : (
          <p className="notice">
            {step.tool_path.fallback === null
              ? "Use exactly this tool. If it is unavailable, report the limitation and stop. Do not substitute REST, a CLI or another tool."
              : "Use exactly this tool first. If it is unavailable, say so, then use only the labeled ffia-local fallback above. Never REST or a CLI, and never a local write in place of a live one."}
          </p>
        )}
      </section>

      <section aria-labelledby="prompts-heading">
        <h3 id="prompts-heading">Prompts (one at a time, stop at the checkpoint)</h3>
        <PromptBlock title="GitHub Copilot prompt" text={step.copilot_prompt} />
        <PromptBlock title="Claude Code prompt" text={step.claude_code_prompt} />
      </section>

      <section aria-labelledby="checkpoint-heading">
        <h3 id="checkpoint-heading">Checkpoint</h3>
        <p>{step.checkpoint}</p>
        <fieldset>
          <legend>Evidence required</legend>
          {step.evidence_required.map((item) => (
            <label key={item} className="evidence-item">
              <input
                type="checkbox"
                checked={evidence.done.includes(item)}
                onChange={(event) => {
                  evidence.toggle(item, event.target.checked);
                }}
              />
              {item}
            </label>
          ))}
        </fieldset>
        {step.not_evidence.length > 0 ? (
          <div className="notice">
            <p>
              <strong>This is not evidence:</strong>
            </p>
            <ul>
              {step.not_evidence.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      {step.failure_modes.length > 0 ? (
        <section aria-labelledby="failures-heading">
          <h3 id="failures-heading">Failure modes</h3>
          <ul>
            {step.failure_modes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section aria-labelledby="offline-heading">
        <h3 id="offline-heading">
          Offline equivalent <Badge value="LOCAL" />
        </h3>
        <p>{step.offline_equivalent}</p>
        {step.offline_command ? (
          <PromptBlock title="Offline command" text={step.offline_command} />
        ) : null}
      </section>

      {guide.diagram && step.diagram_focus.length > 0 ? (
        <StepDiagram viewId={guide.diagram} focus={step.diagram_focus} stepTitle={step.title} />
      ) : null}

      {step.rehearsal ? (
        <ChangeRehearsal key={step.id} rehearsal={step.rehearsal} stepTitle={step.title} />
      ) : step.writes ? (
        <p className="notice">
          This write has no simulated equivalent. It happens in the live tenant after approval.
        </p>
      ) : null}

      <nav aria-label="Step navigation" className="pager">
        {previous ? (
          <Link to={`/guides/${guide.id}/${previous.id}`}>Previous: {previous.title}</Link>
        ) : (
          <span />
        )}
        {next ? <Link to={`/guides/${guide.id}/${next.id}`}>Next: {next.title}</Link> : null}
      </nav>
    </article>
  );
}

function GuideView({
  guide,
  stepId,
}: {
  readonly guide: Guide;
  readonly stepId: string | undefined;
}) {
  const steps = useLocalProgress(`guide.${guide.id}.steps`);
  const step = guide.steps.find((s) => s.id === stepId) ?? guide.steps[0];
  return (
    <>
      <h1>{guide.title}</h1>
      <p className="lead">{guide.summary}</p>
      <p className="meta">
        <Badge value={guide.status} kind="guide" /> Dataset profile{" "}
        <code>{guide.dataset_profile}</code> · patterns{" "}
        {guide.patterns.map((id, index) => (
          <span key={id}>
            {index > 0 ? ", " : null}
            <Link to={`/patterns/${id}`}>{id}</Link>
          </span>
        ))}{" "}
        · maturity {guide.maturity_levels.join(", ")}
      </p>
      <details>
        <summary>Operating rules ({guide.operating_rules.length})</summary>
        <ul>
          {guide.operating_rules.map((rule) => (
            <li key={rule}>{rule}</li>
          ))}
        </ul>
      </details>
      <details>
        <summary>Tools ({guide.tools.length})</summary>
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Guide tools">
          <table>
            <caption className="visually-hidden">Tools the guide needs</caption>
            <thead>
              <tr>
                <th scope="col">Tool</th>
                <th scope="col">Purpose</th>
                <th scope="col">Status</th>
                <th scope="col">Install</th>
              </tr>
            </thead>
            <tbody>
              {guide.tools.map((tool) => (
                <tr key={tool.name}>
                  <td>
                    {tool.name}
                    {tool.version ? ` ${tool.version}` : ""}
                    {tool.required ? "" : " (optional)"}
                  </td>
                  <td>{tool.purpose}</td>
                  <td>{tool.status}</td>
                  <td>
                    <code>{tool.install}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
      <div className="runner">
        <nav aria-label="Guide steps" className="runner__steps">
          <ol>
            {guide.steps.map((s) => (
              <li key={s.id}>
                <Link
                  to={`/guides/${guide.id}/${s.id}`}
                  aria-current={s.id === step?.id ? "step" : undefined}
                >
                  {s.title}
                </Link>
                {s.writes ? <span className="runner__flag"> (write)</span> : null}
                <label className="runner__done">
                  <input
                    type="checkbox"
                    checked={steps.done.includes(s.id)}
                    onChange={(event) => {
                      steps.toggle(s.id, event.target.checked);
                    }}
                  />
                  <span className="visually-hidden">Mark {s.title} done</span>
                </label>
              </li>
            ))}
          </ol>
          <p role="status">
            {steps.done.length} of {guide.steps.length} steps done
          </p>
        </nav>
        {step ? <StepView guide={guide} step={step} /> : null}
      </div>
    </>
  );
}

export function GuideRunnerPage() {
  const { guideId = "", stepId } = useParams();
  usePageTitle("Guide");
  const guide = useGuide(guideId);
  return (
    <QueryState label="the guide" {...guide}>
      {(data) => <GuideView guide={data} stepId={stepId} />}
    </QueryState>
  );
}
