export interface StatusItem {
  readonly label: string;
  readonly value: string;
}

interface StatusBarProps {
  readonly items: readonly StatusItem[];
}

/** Always-visible execution state. Values come from the backend from Phase 3 onward. */
export function StatusBar({ items }: StatusBarProps) {
  return (
    <footer className="status-bar" aria-label="Execution status">
      <dl>
        {items.map((item) => (
          <div key={item.label} className="status-bar__item">
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
    </footer>
  );
}
