import { LEVELS, useLevel } from "../app/levelContext";

/**
 * A segmented control built on a native radio group: arrow keys move between levels, screen
 * readers announce "Learning level", and the choice applies everywhere.
 */
export function LevelSwitcher() {
  const { level, setLevel } = useLevel();
  return (
    <fieldset className="level-switcher">
      <legend className="visually-hidden">Learning level</legend>
      <span className="level-switcher__label" aria-hidden="true">
        Level
      </span>
      <div className="level-switcher__options">
        {LEVELS.map((entry) => (
          <label key={entry.id} title={entry.audience} className="level-switcher__option">
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
      </div>
    </fieldset>
  );
}
