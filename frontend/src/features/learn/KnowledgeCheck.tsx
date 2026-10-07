import { useId, useState } from "react";
import type { KnowledgeCheck as Check } from "../../api/contracts";
import { describeError } from "../../api/client";
import { useAnswerCheck } from "../../api/hooks";
import { levelLabel } from "../../app/levelContext";

/** A multiple-choice check graded by the backend (answers are never shipped to the browser). */
export function KnowledgeCheck({
  lessonId,
  check,
}: {
  readonly lessonId: string;
  readonly check: Check;
}) {
  const [choice, setChoice] = useState<number | null>(null);
  const grade = useAnswerCheck(lessonId, check.id);
  const name = useId();
  return (
    <form
      className="check"
      onSubmit={(event) => {
        event.preventDefault();
        if (choice !== null) {
          grade.mutate(choice);
        }
      }}
    >
      <fieldset>
        <legend>
          <span className="check__level">{levelLabel(check.level)}</span> {check.question}
        </legend>
        {check.choices.map((text, index) => (
          <label key={text}>
            <input
              type="radio"
              name={name}
              value={index}
              checked={choice === index}
              onChange={() => {
                setChoice(index);
              }}
            />
            {text}
          </label>
        ))}
      </fieldset>
      <button type="submit" disabled={choice === null || grade.isPending}>
        Check answer
      </button>
      <div role="status" aria-live="polite">
        {grade.data ? (
          <p className={grade.data.correct ? "result result--pass" : "result result--fail"}>
            <strong>{grade.data.correct ? "Correct." : "Not quite."}</strong>{" "}
            {grade.data.correct
              ? null
              : `The answer is: ${check.choices[grade.data.correct_choice] ?? ""}. `}
            {grade.data.explanation}
          </p>
        ) : null}
        {grade.error ? <p className="result result--fail">{describeError(grade.error)}</p> : null}
      </div>
    </form>
  );
}
