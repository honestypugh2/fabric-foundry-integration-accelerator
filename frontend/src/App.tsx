import { StatusBar, type StatusItem } from "./components/StatusBar";
import { principles } from "./content/principles";

const foundationStatus: readonly StatusItem[] = [
  { label: "Operating mode", value: "Not connected" },
  { label: "Data provider", value: "Not configured" },
  { label: "Agent provider", value: "Not configured" },
  { label: "MCP", value: "Not configured" },
  { label: "Write mode", value: "Read only" },
  { label: "Preview features", value: "Disabled" },
];

export function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <header className="app-header">
        <p className="app-header__eyebrow">Reference architecture · Pattern catalog · Workshop</p>
        <h1>Fabric Foundry Integration Accelerator</h1>
      </header>
      <main id="main" tabIndex={-1}>
        <section aria-labelledby="principles-heading">
          <h2 id="principles-heading">The central lesson</h2>
          <ul className="principles">
            {principles.map((principle) => (
              <li key={principle.id}>{principle.statement}</li>
            ))}
          </ul>
        </section>
        <section aria-labelledby="build-heading">
          <h2 id="build-heading">Build status</h2>
          <p>
            Repository foundation. The architecture explorer, pattern explorer, learning paths,
            labs, and demo mode arrive in later phases. Nothing on this page performs a cloud
            operation.
          </p>
        </section>
      </main>
      <StatusBar items={foundationStatus} />
    </>
  );
}
