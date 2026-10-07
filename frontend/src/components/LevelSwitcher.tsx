import { LEVELS, useLevel } from "../app/levelContext";

/** A native radio group: arrow keys move between levels, and the choice applies everywhere. */
export function LevelSwitcher() {
  const { level, setLevel } = useLevel();
  return (
    <fieldset className="level-switcher">
      <legend>Learning level</legend>
      {LEVELS.map((entry) => (
        <label key={entry.id} title={entry.audience}>
          <input
            type="radio"
            name="learning-level"
            value={entry.id}
            checked={level === entry.id}
            onChange={() => {
              setLevel(entry.id);
            }}
          />
          <span>{entry.label}</span>
        </label>
      ))}
    </fieldset>
  );
}
