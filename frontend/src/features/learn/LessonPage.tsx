import { Link, useParams } from "react-router";
import type { Lesson } from "../../api/contracts";
import { useLesson } from "../../api/hooks";
import { LEVELS, levelLabel, useLevel } from "../../app/levelContext";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { Markdown } from "../../components/Markdown";
import { PromptBlock } from "../../components/PromptBlock";
import { QueryState } from "../../components/QueryState";
import { KnowledgeCheck } from "./KnowledgeCheck";
import { LearningContract } from "./LearningContract";

function LessonBody({ lesson }: { readonly lesson: Lesson }) {
  const { level, setLevel } = useLevel();
  const body = lesson.levels.find((entry) => entry.level === level);
  const checks = lesson.checks.filter((check) => check.level === level);
  return (
    <article aria-labelledby="lesson-heading">
      <h1 id="lesson-heading">
        {lesson.title} <Badge value={lesson.status} kind="status" />
      </h1>
      <p className="lead">{lesson.summary}</p>
      <p className="meta">
        Choose a practical or research lens, then select your depth. Research exercises are designs
        to investigate—not preclaimed results.
      </p>
      {lesson.teaching ? (
        <LearningContract key={lesson.id} brief={lesson.teaching} />
      ) : (
        <p className="notice">An instructional brief has not been authored for this lesson.</p>
      )}
      <nav aria-label="Lesson level" className="level-tabs">
        <ul>
          {LEVELS.map((entry) => (
            <li key={entry.id}>
              <button
                type="button"
                aria-pressed={entry.id === level}
                onClick={() => {
                  setLevel(entry.id);
                }}
              >
                {entry.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <h2>Go deeper at {levelLabel(level)}</h2>
      <section aria-label={`${levelLabel(level)} content`} className="lesson-body">
        {body ? <Markdown>{body.markdown}</Markdown> : <p>This level is not available.</p>}
      </section>

      <section aria-labelledby="objectives-heading">
        <h2 id="objectives-heading">Learning objectives</h2>
        <ul>
          {lesson.learning_objectives.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="concepts-heading">
        <h2 id="concepts-heading">Concepts</h2>
        <dl className="definition-list">
          {lesson.concepts.map((concept) => (
            <div key={concept.term}>
              <dt>{concept.term}</dt>
              <dd>{concept.definition}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section aria-labelledby="evidence-heading">
        <h2 id="evidence-heading">How strongly is this supported?</h2>
        <ul className="evidence">
          {lesson.evidence.map((claim) => (
            <li key={claim.statement}>
              <Badge value={claim.category} kind="evidence" /> {claim.statement}
              {claim.sources.length > 0 ? (
                <span className="evidence__sources"> Sources: {claim.sources.join(", ")}</span>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      {lesson.try_it.length > 0 ? (
        <section aria-labelledby="try-heading">
          <h2 id="try-heading">Try it offline</h2>
          {lesson.try_it.map((item) => (
            <div key={item.command}>
              <p>
                {item.label} <Badge value={item.result_label} />
              </p>
              <PromptBlock title="Command" text={item.command} />
            </div>
          ))}
        </section>
      ) : null}

      <section aria-labelledby="agents-heading">
        <h2 id="agents-heading">Try with an agent</h2>
        <PromptBlock title="GitHub Copilot prompt" text={lesson.copilot_prompt} />
        <PromptBlock title="Claude Code prompt" text={lesson.claude_code_prompt} />
      </section>

      <section aria-labelledby="production-heading">
        <h2 id="production-heading">Production notes</h2>
        <ul>
          {lesson.production_notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="checks-heading">
        <h2 id="checks-heading">Knowledge check ({levelLabel(level)})</h2>
        {checks.map((check) => (
          <KnowledgeCheck key={check.id} lessonId={lesson.id} check={check} />
        ))}
        <details>
          <summary>All levels ({lesson.checks.length} checks)</summary>
          {lesson.checks
            .filter((check) => check.level !== level)
            .map((check) => (
              <KnowledgeCheck key={check.id} lessonId={lesson.id} check={check} />
            ))}
        </details>
      </section>

      <section aria-labelledby="related-heading">
        <h2 id="related-heading">Related</h2>
        <ul>
          {lesson.pattern_ids.map((id) => (
            <li key={id}>
              Pattern <Link to={`/patterns/${id}`}>{id}</Link>
            </li>
          ))}
          {lesson.related_labs.map((id) => (
            <li key={id}>
              Lab <Link to={`/labs/${id}`}>{id}</Link>
            </li>
          ))}
          {lesson.related_guides.map((id) => (
            <li key={id}>
              Use case <Link to={`/use-cases/${id}`}>{id}</Link>
            </li>
          ))}
          {lesson.prerequisites.map((id) => (
            <li key={id}>
              Prerequisite <Link to={`/learn/${id}`}>{id}</Link>
            </li>
          ))}
        </ul>
        <p>Sources: {lesson.sources.join(", ")}</p>
      </section>
    </article>
  );
}

export function LessonPage() {
  const { lessonId = "" } = useParams();
  usePageTitle("Lesson");
  const lesson = useLesson(lessonId);
  return (
    <QueryState label="the lesson" {...lesson}>
      {(data) => <LessonBody lesson={data} />}
    </QueryState>
  );
}
