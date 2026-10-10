import { useRuntimeStatus } from "../api/hooks";
import { levelLabel, useLevel } from "../app/levelContext";

export interface StatusItem {
  readonly label: string;
  readonly value: string;
}

/** Always-visible execution state. Values come from the control plane; nothing is assumed. */
export function StatusBar() {
  const { level } = useLevel();
  const status = useRuntimeStatus();
  const items: StatusItem[] = status.data
    ? [
        { label: "Operating mode", value: status.data.operating_mode },
        { label: "Data provider", value: status.data.data_provider },
        { label: "Agent provider", value: status.data.agent_provider },
        { label: "MCP", value: status.data.mcp },
        { label: "Identity", value: status.data.identity },
        { label: "Write mode", value: status.data.write_mode },
        {
          label: "Preview features",
          value: status.data.preview_features.length
            ? status.data.preview_features.join(", ")
            : "None enabled",
        },
      ]
    : [
        {
          label: "Control plane",
          value: status.isPending ? "Connecting…" : "Not reachable: nothing is live",
        },
      ];
  items.push({ label: "Learning level", value: levelLabel(level) });
  return (
    <footer className="status-bar" aria-label="Execution status">
      <dl>
        {items.map((item) => (
          <div key={item.label} className="status-bar__item" data-field={item.label}>
            <dt>{item.label}</dt>
            <dd title={item.value}>{item.value}</dd>
          </div>
        ))}
      </dl>
      <details>
        <summary>Configuration, not execution · inspect full state and evidence limits</summary>
        <ul>
          {items.map((item) => (
            <li key={item.label}>
              {item.label}: {item.value}
            </li>
          ))}
        </ul>
        <p className="meta">
          Configuration is not execution evidence. Inspect each result's label and fallback reason;
          live writes never redirect.
        </p>
        {status.data?.providers.map((provider) => (
          <p className="meta" key={`${provider.capability}:${provider.name}:${provider.kind}`}>
            {provider.capability}: {provider.name} · {provider.kind} · {provider.note}
          </p>
        ))}
      </details>
    </footer>
  );
}
