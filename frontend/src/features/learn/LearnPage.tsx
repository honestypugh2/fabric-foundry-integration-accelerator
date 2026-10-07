import { Link } from "react-router";
import type { LessonSummary } from "../../api/contracts";
import { useLessons } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
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
  return (
    <>
      <h1>Learning paths</h1>
      <p>
        Every lesson teaches five levels: Executive, L100, L200, L300 and L400. Pick your level in
        the header; lessons, the architecture explorer and labs follow it.
      </p>
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
