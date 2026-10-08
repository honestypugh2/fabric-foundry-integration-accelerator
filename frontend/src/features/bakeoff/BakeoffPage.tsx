import { Link, useParams } from "react-router";
import type { BakeoffTasks, RunRecord, Scorecard } from "../../api/contracts";
import { useBakeoffRun, useBakeoffTasks, useScorecard } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { PromptBlock } from "../../components/PromptBlock";
import { QueryState } from "../../components/QueryState";

const HOW_TO_RUN = [
  "ffia bakeoff prepare <task> --dest ~/bakeoff/<task>-<model>",
  "# open that folder in your harness; give it exactly the prompt in BAKEOFF_TASK.md",
  "ffia bakeoff grade <task> --workspace ~/bakeoff/<task>-<model>",
].join("\n");

function Tasks({ tasks }: { readonly tasks: BakeoffTasks }) {
  return (
    <section aria-labelledby="tasks-heading">
      <h2 id="tasks-heading">The five tasks</h2>
      <p>
        Same wording, same commit, same synthetic profile (<code>{tasks.profile}</code>) for every
        harness and model. Each task is graded by deterministic checks that rebuild the data,
        compare it with the committed baseline, read the audit log and list every changed file.
      </p>
      <ol className="bakeoff-tasks">
        {tasks.tasks.map((task) => (
          <li key={task.id}>
            <h3>
              {task.title} <code>{task.id}</code>
            </h3>
            <p>{task.summary}</p>
            <p className="meta">
              Checks: {task.checks.join(", ")}. May change:{" "}
              {task.allowed_changes.length > 0 ? task.allowed_changes.join(", ") : "nothing"}.
            </p>
            <PromptBlock title={`Prompt: ${task.id}`} text={task.prompt.trim()} />
          </li>
        ))}
      </ol>
    </section>
  );
}

function ScorecardView({ card }: { readonly card: Scorecard }) {
  return (
    <section aria-labelledby="scorecard-heading">
      <h2 id="scorecard-heading">
        Scorecard <Badge value={card.label} />
      </h2>
      <p className={card.label === "UNAVAILABLE" ? "notice" : "meta"}>{card.note}</p>
      {card.rows.length === 0 ? null : (
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Scorecard by model">
          <table>
            <caption>By harness and model (recorded runs)</caption>
            <thead>
              <tr>
                <th scope="col">Harness</th>
                <th scope="col">Model</th>
                <th scope="col">Tasks passed</th>
                <th scope="col">Median time</th>
                <th scope="col">Approvals requested</th>
                <th scope="col">Denied tool calls</th>
                <th scope="col">Unsafe attempts</th>
                <th scope="col">Premium requests</th>
              </tr>
            </thead>
            <tbody>
              {card.rows.map((row) => (
                <tr key={`${row.harness}|${row.model}`}>
                  <td>{row.harness}</td>
                  <td>{row.model}</td>
                  <td>
                    {row.tasks_passed} of {row.runs}
                  </td>
                  <td>{row.median_duration_seconds} s</td>
                  <td>{row.approvals_requested}</td>
                  <td>{row.denied_tool_calls}</td>
                  <td>{row.unsafe_attempts}</td>
                  <td>{row.premium_requests ?? "Not shown"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {card.runs.length === 0 ? null : (
        <>
          <h3>Recorded runs</h3>
          <ul>
            {card.runs.map((run) => (
              <li key={run.run_id}>
                <Link to={`/bakeoff/runs/${run.run_id}`}>{run.run_id}</Link>: {run.task},{" "}
                {run.harness}, {run.model}, {run.passed ? "passed" : "failed"} ({run.checks_passed}/
                {run.checks} checks), {run.recorded_on}
                {run.current_prompt ? "" : " (recorded with an older prompt)"}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

export function BakeoffPage() {
  usePageTitle("Bake-off");
  const tasks = useBakeoffTasks();
  const card = useScorecard();
  return (
    <>
      <h1>Bake-off: same tasks, every harness</h1>
      <p>
        GitHub Copilot with different models (including Claude models inside Copilot) runs the same
        five data-engineering tasks. Claude Code is documented with the same prompts and sandbox,
        and its runs appear here only when someone records them. Results are dated observations on
        this repository&apos;s synthetic tasks, not product claims.
      </p>
      <PromptBlock title="How to run a task" text={HOW_TO_RUN} />
      <QueryState label="the scorecard" {...card}>
        {(data) => <ScorecardView card={data} />}
      </QueryState>
      <QueryState label="the tasks" {...tasks}>
        {(data) => <Tasks tasks={data} />}
      </QueryState>
    </>
  );
}

function Replay({ run }: { readonly run: RunRecord }) {
  return (
    <>
      <dl className="definition-list">
        <div>
          <dt>Harness</dt>
          <dd>
            {run.harness.name} {run.harness.version}
          </dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{run.model}</dd>
        </div>
        <div>
          <dt>Task</dt>
          <dd>
            <code>{run.task}</code>, recorded {run.recorded_on}, {run.duration_seconds} s
          </dd>
        </div>
        <div>
          <dt>Safety</dt>
          <dd>
            {run.safety.approvals_requested} approvals requested, {run.safety.denied_tool_calls}{" "}
            denied tool calls, {run.safety.unsafe_attempts} unsafe attempts
          </dd>
        </div>
      </dl>
      <h2>
        Grade <Badge value={run.grade.passed ? "PASSED" : "FAILED"} kind="gate" />
      </h2>
      <ul>
        {run.grade.checks.map((check) => (
          <li key={check.name}>
            <strong>{check.passed ? "Pass" : "Fail"}</strong> {check.name}: {check.detail}
          </li>
        ))}
      </ul>
      <h2>Transcript (sanitized)</h2>
      <ol className="transcript">
        {run.transcript.map((event, index) => (
          // Events have no id; the order is the recorded order.
          <li key={index}>
            <span className="meta">
              {event.t.toFixed(1)} s · {event.kind}
              {event.name ? ` · ${event.name}` : ""}
            </span>
            <pre>{event.summary}</pre>
          </li>
        ))}
      </ol>
      {run.notes ? <p className="meta">{run.notes}</p> : null}
    </>
  );
}

export function BakeoffRunPage() {
  const { runId = "" } = useParams();
  usePageTitle(`Bake-off run ${runId}`);
  const run = useBakeoffRun(runId);
  return (
    <>
      <p>
        <Link to="/bakeoff">← Bake-off</Link>
      </p>
      <h1>
        Replay: <code>{runId}</code> <Badge value="LIVE" />
      </h1>
      <p>A recorded live run, replayed from its sanitized transcript. Nothing runs now.</p>
      <QueryState label="the run" {...run}>
        {(data) => <Replay run={data} />}
      </QueryState>
    </>
  );
}
