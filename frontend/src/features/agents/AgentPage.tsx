import { useId, useState } from "react";
import { describeError } from "../../api/client";
import type { AgentAnswer, AgentProfile } from "../../api/contracts";
import {
  useAgentEvaluation,
  useAgentProfile,
  useAskAgent,
  useKnowledgeSearch,
  useMonthlyInsights,
} from "../../api/hooks";
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

function MonthlyInsights() {
  const workflow = useMonthlyInsights();
  const run = workflow.data;
  return (
    <section aria-labelledby="workflow-heading">
      <h2 id="workflow-heading">Orchestrate: monthly insights workflow</h2>
      <p>
        A Microsoft Agent Framework workflow drafts each business team&apos;s monthly brief through
        the same agent, in parallel. A deterministic review gate checks every draft against the
        baseline. Nothing is sent: delivering briefs is a governed write that needs approval.
      </p>
      <button
        type="button"
        disabled={workflow.isPending}
        onClick={() => {
          workflow.mutate();
        }}
      >
        Run monthly insights workflow
      </button>
      <div aria-live="polite">
        {workflow.isPending ? (
          <p className="loading" role="status">
            Drafting team briefs…
          </p>
        ) : null}
      </div>
      {workflow.error ? (
        <p className="notice notice--error" role="alert">
          {describeError(workflow.error)}
        </p>
      ) : null}
      {run ? (
        <div>
          <p>
            <strong>
              {run.ready} ready for approval, {run.held} held
            </strong>{" "}
            for {run.observation_month.slice(0, 7)}. Engine: {run.engine}. Labels{" "}
            {run.labels.map((label) => (
              <Badge key={label} value={label} />
            ))}
          </p>
          <ol>
            {run.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <ul className="drafts">
            {run.drafts.map((draft) => (
              <li key={draft.team_id}>
                <article aria-labelledby={`draft-${draft.team_id}`}>
                  <h3 id={`draft-${draft.team_id}`}>
                    {draft.team_name} <Badge value={draft.status} kind="gate" />
                  </h3>
                  <p className="meta">
                    {draft.reason}
                    {draft.missing.length > 0 ? ` Missing: ${draft.missing.join(", ")}.` : ""}{" "}
                    <Badge value={draft.label} /> {draft.provider}
                    {draft.fallback_used ? " (fallback)" : ""}
                  </p>
                  <Markdown>{draft.answer}</Markdown>
                </article>
              </li>
            ))}
          </ul>
          <p className="notice">{run.delivery}</p>
          <p className="meta">{run.synthetic_notice}</p>
        </div>
      ) : null}
    </section>
  );
}

const KNOWLEDGE_SUGGESTIONS = [
  "Can agents fix data quality issues in the source?",
  "Can we scrape a competitor's website?",
  "Are briefs sent automatically?",
];

function Knowledge() {
  const search = useKnowledgeSearch();
  const [question, setQuestion] = useState("");
  const questionId = useId();
  const result = search.data;
  return (
    <section aria-labelledby="knowledge-heading">
      <h2 id="knowledge-heading">
        Knowledge with citations <Badge value="PREVIEW" kind="status" />
      </h2>
      <p>
        Policy questions are answered from documents, with a citation for every passage: the Foundry
        IQ pattern. Offline, a local retriever over synthetic policy documents simulates it, and
        only when the preview flag is on. Numbers still come from the governed sales model.
      </p>
      <form
        className="agent-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (question.trim().length > 0) {
            search.mutate(question.trim());
          }
        }}
      >
        <label htmlFor={questionId}>Policy question</label>
        <textarea
          id={questionId}
          rows={2}
          maxLength={500}
          value={question}
          onChange={(event) => {
            setQuestion(event.target.value);
          }}
        />
        <button type="submit" disabled={search.isPending || question.trim().length < 3}>
          Search knowledge
        </button>
      </form>
      <ul className="suggestions" aria-label="Suggested policy questions">
        {KNOWLEDGE_SUGGESTIONS.map((suggestion) => (
          <li key={suggestion}>
            <button
              type="button"
              disabled={search.isPending}
              onClick={() => {
                setQuestion(suggestion);
                search.mutate(suggestion);
              }}
            >
              {suggestion}
            </button>
          </li>
        ))}
      </ul>
      {search.error ? (
        <p className="notice notice--error" role="alert">
          {describeError(search.error)}
        </p>
      ) : null}
      {result ? (
        <section aria-labelledby="passages-heading">
          <h3 id="passages-heading">Passages</h3>
          <Provenance envelope={result} />
          {result.data.passages.length === 0 ? null : (
            <ol>
              {result.data.passages.map((passage) => (
                <li key={`${passage.citation.document}#${passage.citation.section}`}>
                  <blockquote>{passage.text}</blockquote>
                  <p className="meta">
                    Source: {passage.citation.title}, section &ldquo;{passage.citation.section}
                    &rdquo; (<code>{passage.citation.path}</code>)
                  </p>
                </li>
              ))}
            </ol>
          )}
          <p className={result.data.enabled ? "meta" : "notice"}>{result.data.note}</p>
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
            <MonthlyInsights />
            <Knowledge />
            <EvaluateAgent profile={data} />
          </>
        )}
      </QueryState>
    </>
  );
}
