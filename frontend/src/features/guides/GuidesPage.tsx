import { Link } from "react-router";
import { useGuides } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";

export function GuidesPage() {
  usePageTitle("Use Cases");
  const guides = useGuides();
  return (
    <>
      <header className="page-intro">
        <p className="eyebrow">Business outcomes → working prototypes</p>
        <h1>Use Cases</h1>
        <p className="lead">
          Build a bounded PoC, understand the patterns behind it and prove what actually happened.
        </p>
      </header>
      <p>
        Sanitized, synthetic versions of real engagement patterns. Each use case connects the
        problem, fundamentals, implementation, checkpoints and production gaps. Registry status is
        not certification of every step.
      </p>
      <QueryState label="guides" {...guides}>
        {(all) => (
          <ul className="cards">
            {all.map((guide) => (
              <li key={guide.id} className="card">
                <h2 className="card__title">
                  <Link to={`/use-cases/${guide.id}`}>{guide.title}</Link>
                </h2>
                <p>{guide.summary}</p>
                <p className="eyebrow">
                  {guide.industry} · {guide.maturity_levels.join(" → ")}
                </p>
                <p className="meta">
                  {guide.steps.length} steps · {guide.status} · patterns {guide.patterns.join(", ")}
                </p>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </>
  );
}
