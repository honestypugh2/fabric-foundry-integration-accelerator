import { Link, useSearchParams } from "react-router";
import { useGuides } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";

export function GuidesPage() {
  usePageTitle("Use Cases");
  const guides = useGuides();
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";
  const industry = params.get("industry") ?? "";
  const tool = params.get("tool") ?? "";
  function filter(name: string, value: string) {
    setParams(
      (current) => {
        const updated = new URLSearchParams(current);
        if (value) updated.set(name, value);
        else updated.delete(name);
        return updated;
      },
      { replace: true },
    );
  }
  return (
    <>
      <header className="page-intro">
        <p className="eyebrow">Discover · build · explain</p>
        <h1>Use Cases</h1>
        <p className="lead">
          Find your next workshop. Choose an outcome, explore the architecture, then build one
          checkpoint at a time.
        </p>
      </header>
      <p>
        Sanitized, synthetic versions of real engagement patterns. Each use case connects the
        problem, fundamentals, implementation and checkpoints in a development environment. Registry
        status is not proof that every connected step has run.
      </p>
      <QueryState label="guides" {...guides}>
        {(all) => {
          const matches = all.filter(
            (guide) =>
              (!industry || guide.industry === industry) &&
              (!tool || guide.tools.some((item) => item.required && item.name === tool)) &&
              [guide.title, guide.summary, guide.industry, ...guide.tools.map((tool) => tool.name)]
                .join(" ")
                .toLocaleLowerCase()
                .includes(query.trim().toLocaleLowerCase()),
          );
          return (
            <>
              <form
                className="catalog-filters"
                role="search"
                onSubmit={(event) => {
                  event.preventDefault();
                }}
              >
                <label>
                  Search use cases
                  <input
                    type="search"
                    value={query}
                    placeholder="Try Fabric, Power BI or agents"
                    onChange={(event) => {
                      filter("q", event.target.value);
                    }}
                  />
                </label>
                <label>
                  Industry
                  <select
                    value={industry}
                    onChange={(event) => {
                      filter("industry", event.target.value);
                    }}
                  >
                    <option value="">All industries</option>
                    {[...new Set(all.map((guide) => guide.industry))].sort().map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Tool or service
                  <select
                    value={tool}
                    onChange={(event) => {
                      filter("tool", event.target.value);
                    }}
                  >
                    <option value="">All tools and services</option>
                    {[
                      ...new Set(
                        all.flatMap((guide) =>
                          guide.tools.filter((item) => item.required).map((item) => item.name),
                        ),
                      ),
                    ]
                      .sort()
                      .map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                  </select>
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setParams({});
                  }}
                >
                  Clear filters
                </button>
              </form>
              <p className="meta" role="status">
                {matches.length} of {all.length} use cases
              </p>
              {matches.length === 0 ? (
                <p className="notice">No use cases match. Try another term or clear the filters.</p>
              ) : null}
              <ul className="cards accelerator-catalog">
                {matches.map((guide, index) => (
                  <li key={guide.id} className="card accelerator-card">
                    <div className="accelerator-card__top">
                      <span className="path-number" aria-hidden="true">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="eyebrow">{guide.industry} · synthetic data</span>
                    </div>
                    <h2 className="card__title">
                      <Link to={`/use-cases/${guide.id}`}>{guide.title}</Link>
                    </h2>
                    <p>{guide.summary}</p>
                    <details className="catalog-requirements">
                      <summary>Tools and services</summary>
                      <ul className="technology-tags" aria-label="Required tools">
                        {guide.tools
                          .filter((tool) => tool.required)
                          .map((tool) => (
                            <li key={tool.name}>{tool.name}</li>
                          ))}
                      </ul>
                    </details>
                    <p className="meta">
                      {guide.steps.length} steps · registry: {guide.status} · patterns{" "}
                      {guide.patterns.join(", ")}
                    </p>
                    <Link className="text-link" to={`/use-cases/${guide.id}`}>
                      Explore workshop <span aria-hidden="true">→</span>
                      <span className="visually-hidden">: {guide.title}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          );
        }}
      </QueryState>
    </>
  );
}
