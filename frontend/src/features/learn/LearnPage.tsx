import { Link } from "react-router";
import type { LessonSummary } from "../../api/contracts";
import { useLessons, useWorkshop } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { usePageAnchor } from "../../app/usePageAnchor";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";

const AREA_NAMES: Readonly<Record<string, string>> = {
  architecture: "Architecture",
  "agentic-data-engineering": "Agentic data engineering",
  copilot: "GitHub Copilot",
  claude: "Claude Code",
  fabric: "Fabric",
  mcp: "MCP",
  patterns: "Anchor patterns",
};

function groupByArea(lessons: readonly LessonSummary[]): [string, LessonSummary[]][] {
  const groups = new Map<string, LessonSummary[]>();
  for (const lesson of lessons) {
    groups.set(lesson.area, [...(groups.get(lesson.area) ?? []), lesson]);
  }
  return [...groups.entries()];
}

export function LearnPage() {
  usePageTitle("Learn");
  const lessons = useLessons();
  const workshop = useWorkshop();
  usePageAnchor(workshop.isSuccess);
  return (
    <>
      <header className="page-intro">
        <p className="eyebrow">Breadth first · depth when you need it</p>
        <h1>Understand. Build. Investigate.</h1>
        <p className="lead">
          Learn the what, why, when and how. Then investigate the foundations, theory and evidence
          behind today's data and agent workflows.
        </p>
      </header>
      <p>
        Every lesson has Executive through L400 explanations. The research lens adds hypotheses,
        controlled experiments, independent baselines and limitations—not unsupported product
        claims.
      </p>
      <QueryState label="learning journeys" {...workshop}>
        {(data) => (
          <div className="learning-paths">
            {data.content.journeys.map((journey) => (
              <section key={journey.id} id={`path-${journey.id}`} className="card">
                <p className="eyebrow">Estimated {journey.duration_minutes} minutes</p>
                <h2>{journey.title}</h2>
                <p>{journey.summary}</p>
                <ol>
                  {journey.lesson_ids.map((id) => (
                    <li key={id}>
                      <Link to={`/learn/${id}`}>
                        {lessons.data?.find((item) => item.id === id)?.title ?? id}
                      </Link>
                    </li>
                  ))}
                </ol>
              </section>
            ))}
          </div>
        )}
      </QueryState>
      <h2>Explore the full concept library</h2>
      <QueryState label="lessons" {...lessons}>
        {(all) =>
          groupByArea(all).map(([area, items]) => (
            <section key={area} aria-labelledby={`area-${area}`}>
              <h2 id={`area-${area}`}>{AREA_NAMES[area] ?? area}</h2>
              <ul className="cards">
                {items.map((lesson) => (
                  <li key={lesson.id} className="card">
                    <h3 className="card__title">
                      <Link to={`/learn/${lesson.id}`}>{lesson.title}</Link>{" "}
                      <Badge value={lesson.status} kind="status" />
                    </h3>
                    <p>{lesson.summary}</p>
                  </li>
                ))}
              </ul>
            </section>
          ))
        }
      </QueryState>
    </>
  );
}
