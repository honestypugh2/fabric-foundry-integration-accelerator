import { Link } from "react-router";
import { useCompleteness } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";
import { principles } from "../../content/principles";

const START: readonly { readonly to: string; readonly title: string; readonly text: string }[] = [
  {
    to: "/guides/hc-01-fabric-mcp-powerbi-medallion-lab",
    title: "Run Guide HC-01",
    text: "Fabric MCP + Power BI medallion lab with GitHub Copilot or Claude Code, step by step.",
  },
  {
    to: "/architecture",
    title: "Explore the architecture",
    text: "Who owns context, reasoning, access, authority and evidence, at your level.",
  },
  {
    to: "/learn/copilot-maturity-ladder",
    title: "Level up with GitHub Copilot",
    text: "From assisted coding to governed change: the Fabric data-engineering maturity ladder.",
  },
  {
    to: "/demo",
    title: "Run the offline demo",
    text: "Ten acts, honestly labeled, with no cloud access required.",
  },
];

export function HomePage() {
  usePageTitle("Home");
  const completeness = useCompleteness();
  return (
    <>
      <h1>Fabric Foundry Integration Accelerator</h1>
      <section aria-labelledby="principles-heading">
        <h2 id="principles-heading">The central lesson</h2>
        <ul className="principles">
          {principles.map((principle) => (
            <li key={principle.id}>{principle.statement}</li>
          ))}
        </ul>
      </section>
      <section aria-labelledby="start-heading">
        <h2 id="start-heading">Start here</h2>
        <ul className="cards">
          {START.map((item) => (
            <li key={item.to} className="card">
              <h3>
                <Link to={item.to}>{item.title}</Link>
              </h3>
              <p>{item.text}</p>
            </li>
          ))}
        </ul>
      </section>
      <section aria-labelledby="completeness-heading">
        <h2 id="completeness-heading">Architecture completeness</h2>
        <QueryState label="completeness" {...completeness}>
          {(report) => (
            <>
              <p>
                <strong>
                  {report.answered} of {report.total}
                </strong>{" "}
                architecture questions are answered at every level (Executive to L400).
              </p>
              <progress max={report.total} value={report.answered} aria-label="Questions answered">
                {Math.round(report.coverage * 100)}%
              </progress>
              <details>
                <summary>Questions still planned</summary>
                <ul>
                  {report.items
                    .filter((item) => !item.answered)
                    .map((item) => (
                      <li key={item.id}>
                        {item.id}: {item.question}{" "}
                        {item.planned_phase === null ? null : (
                          <span>(Phase {item.planned_phase})</span>
                        )}
                      </li>
                    ))}
                </ul>
              </details>
            </>
          )}
        </QueryState>
      </section>
    </>
  );
}
