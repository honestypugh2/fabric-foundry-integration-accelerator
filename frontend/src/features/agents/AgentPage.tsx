import { useId, useState } from "react";
import { describeError } from "../../api/client";
import type { AgentAnswer, AgentProfile } from "../../api/contracts";
import { useAgentEvaluation, useAgentProfile, useAskAgent } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { Markdown } from "../../components/Markdown";
import { Provenance } from "../../components/Provenance";
import { QueryState } from "../../components/QueryState";

const AGENT = "sales-insights-agent";

function Grounding({ answer }: { readonly answer: AgentAnswer }) {
  return answer.grounded ? (
    <p>
      <strong>Grounded.</strong> A governed data tool produced the numbers; the model only wrote the
      sentence around them.
    </p>
  ) : (
    <p>
      <strong>Not grounded.</strong> No data tool ran, so this answer contains no business numbers.
    </p>
  );
}

function AnswerView({ answer }: { readonly answer: AgentAnswer }) {
  return (
    <>
      <Grounding answer={answer} />
      <Markdown>{answer.answer}</Markdown>
      <h3>Tool calls</h3>
      {answer.tool_calls.length === 0 ? (
        <p>None.</p>
      ) : (
        <ul>
          {answer.tool_calls.map((call, index) => (
            // Tool calls have no id; the order is the order they ran.
            <li key={index}>
              <code>{call.name}</code>
              {call.summary ? ` — ${call.summary}` : ""}
            </li>
          ))}
        </ul>
      )}
      {!answer.grounded && answer.supported_questions.length > 0 ? (
        <>
          <h3>Questions this agent answers offline</h3>
          <ul>
            {answer.supported_questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </>
      ) : null}
    </>
  );
}

function AskAgent({ profile }: { readonly profile: AgentProfile }) {
  const ask = useAskAgent(profile.agent);
  const [question, setQuestion] = useState("");
  const questionId = useId();
  const submit = (text: string) => {
    const trimmed = text.trim();
    if (trimmed.length > 0) {
      ask.mutate(trimmed);
    }
  };
  return (
    <section aria-labelledby="ask-heading">
      <h2 id="ask-heading">Ask the agent</h2>
      <form
        className="agent-form"
        onSubmit={(event) => {
          event.preventDefault();
          submit(question);
        }}
      >
        <label htmlFor={questionId}>Question</label>
        <textarea
          id={questionId}
          rows={2}
          maxLength={2000}
          value={question}
          onChange={(event) => {
            setQuestion(event.target.value);
          }}
        />
        <button type="submit" disabled={ask.isPending || question.trim().length === 0}>
          Ask
        </button>
      </form>
      <h3>Suggested questions (from the evaluation suite)</h3>
      <ul className="suggestions">
        {profile.suggested_questions.map((suggestion) => (
          <li key={suggestion}>
            <button
              type="button"
              disabled={ask.isPending}
              onClick={() => {
                setQuestion(suggestion);
                submit(suggestion);
              }}
            >
              {suggestion}
            </button>
          </li>
        ))}
      </ul>
      <div aria-live="polite">
        {ask.isPending ? (
          <p className="loading" role="status">
            Asking the agent…
            {profile.live_provider === null
              ? ""
              : " Live Foundry calls can take a minute or more, especially the first one."}
          </p>
        ) : null}
      </div>
      {ask.error ? (
        <p className="notice notice--error" role="alert">
          {describeError(ask.error)}
        </p>
      ) : null}
      {ask.data ? (
        <section aria-labelledby="answer-heading">
          <h3 id="answer-heading">Answer</h3>
          <Provenance envelope={ask.data} />
          <AnswerView answer={ask.data.data} />
        </section>
      ) : null}
    </section>
  );
}

function EvaluateAgent({ profile }: { readonly profile: AgentProfile }) {
  const evaluation = useAgentEvaluation(profile.suite);
  const report = evaluation.data;
  return (
    <section aria-labelledby="agent-eval-heading">
      <h2 id="agent-eval-heading">Evaluate the agent</h2>
      <p>
        Runs every case in <code>config/evaluations/{profile.suite}.yaml</code> through the same
        router. Each case checks grounding and that every expected baseline value appears in the
        answer.
      </p>
      <button
        type="button"
        disabled={evaluation.isPending}
        onClick={() => {
          evaluation.mutate();
        }}
      >
        Run evaluation suite
      </button>
      <div aria-live="polite">
        {evaluation.isPending ? (
          <p className="loading" role="status">
            Running {profile.suggested_questions.length} cases…
          </p>
        ) : null}
      </div>
      {evaluation.error ? (
        <p className="notice notice--error" role="alert">
          {describeError(evaluation.error)}
        </p>
      ) : null}
      {report ? (
        <div>
          <p>
            <strong>
              {report.passed} of {report.compared}
            </strong>{" "}
            cases passed. Gate: <Badge value={report.status} kind="gate" /> Evaluated:{" "}
            {report.provider}, labels{" "}
            {report.labels.map((label) => (
              <Badge key={label} value={label} />
            ))}
          </p>
          <div className="table-scroll" tabIndex={0} role="region" aria-label="Agent evaluation">
            <table>
              <caption>Agent evaluation cases (synthetic data)</caption>
              <thead>
                <tr>
                  <th scope="col">Case</th>
                  <th scope="col">Question</th>
                  <th scope="col">Grounded</th>
                  <th scope="col">Label</th>
                  <th scope="col">Missing values</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {report.cases.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <code>{row.id}</code>
                    </td>
                    <td>{row.question}</td>
                    <td>{row.grounded ? "Yes" : "No"}</td>
                    <td>{row.label}</td>
                    <td>{row.missing.length === 0 ? "None" : row.missing.join(", ")}</td>
                    <td>{row.passed ? "Pass" : "Fail"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export function AgentPage() {
  usePageTitle("Agent");
  const profile = useAgentProfile(AGENT);
  return (
    <>
      <h1>Sales insights agent</h1>
      <p>
        Ask the agent from Guide MFG-01 through the provider router. Offline, a deterministic LOCAL
        agent answers allow-listed questions over synthetic data. With live Foundry enabled, the
        Foundry agent calls the Fabric data agent tool and the result is labeled PREVIEW. Either
        way, the numbers come from a governed data tool, never from the model.
      </p>
      <QueryState label="the agent" {...profile}>
        {(data) => (
          <>
            <dl className="definition-list">
              <div>
                <dt>Agent</dt>
                <dd>
                  <code>{data.agent}</code> over dataset <code>{data.dataset_profile}</code>
                </dd>
              </div>
              <div>
                <dt>Offline provider</dt>
                <dd>{data.local_provider}</dd>
              </div>
              <div>
                <dt>Live provider</dt>
                <dd>{data.live_provider ?? "Not configured (live Foundry is opt-in)"}</dd>
              </div>
            </dl>
            <AskAgent profile={data} />
            <EvaluateAgent profile={data} />
          </>
        )}
      </QueryState>
    </>
  );
}
