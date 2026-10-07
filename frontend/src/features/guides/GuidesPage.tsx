import { Link } from "react-router";
import { useGuides } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";

export function GuidesPage() {
  usePageTitle("Guides");
  const guides = useGuides();
  return (
    <>
      <h1>Use-Case Guides</h1>
      <p>
        Customer-neutral, synthetic-data walkthroughs. Each step names the provider, server and tool
        to use, the evidence that proves it, and an offline equivalent.
      </p>
      <QueryState label="guides" {...guides}>
        {(all) => (
          <ul className="cards">
            {all.map((guide) => (
              <li key={guide.id} className="card">
                <h2 className="card__title">
                  <Link to={`/guides/${guide.id}`}>{guide.title}</Link>
                </h2>
                <p>{guide.summary}</p>
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
