import { Link, useParams } from "react-router";
import { useLessons, usePattern } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";

const FIELDS = [
  ["when_to_use", "When to use"],
  ["when_not_to_use", "When not to use"],
  ["fabric_role", "Fabric role"],
  ["foundry_role", "Foundry role"],
  ["mcp_role", "MCP role"],
  ["authority", "Authority"],
  ["offline_equivalent", "Offline equivalent"],
] as const;

export function PatternDetailPage() {
  const { patternId = "" } = useParams();
  usePageTitle(`Pattern ${patternId}`);
  const pattern = usePattern(patternId);
  const lessons = useLessons();
  return (
    <QueryState label={`pattern ${patternId}`} {...pattern}>
      {(p) => {
        const related = (lessons.data ?? []).filter((l) => l.pattern_ids.includes(p.id));
        return (
          <article>
            <h1>
              {p.id} {p.name} <Badge value={p.status} kind="status" />
            </h1>
            <p className="lead">{p.summary}</p>
            {p.preview_dependencies.length > 0 ? (
              <p className="notice">
                <strong>Preview dependencies:</strong> {p.preview_dependencies.join(", ")}. Never
                required by the default demo.
              </p>
            ) : null}
            <dl className="definition-list">
              {FIELDS.map(([key, label]) => (
                <div key={key}>
                  <dt>{label}</dt>
                  <dd>{p[key]}</dd>
                </div>
              ))}
              <div>
                <dt>Default demo path</dt>
                <dd>
                  <Badge value={p.default_demo_path} />
                </dd>
              </div>
              <div>
                <dt>Sources</dt>
                <dd>{p.sources.join(", ")}</dd>
              </div>
            </dl>
            <section aria-labelledby="pattern-lessons">
              <h2 id="pattern-lessons">Lessons</h2>
              {related.length === 0 ? (
                <p>No lesson covers this pattern yet. Its catalog entry above is the summary.</p>
              ) : (
                <ul>
                  {related.map((lesson) => (
                    <li key={lesson.id}>
                      <Link to={`/learn/${lesson.id}`}>{lesson.title}</Link>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <p>
              <Link to="/patterns">Back to the catalog</Link>
            </p>
          </article>
        );
      }}
    </QueryState>
  );
}
