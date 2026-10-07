import { NavLink, useParams } from "react-router";
import { useViews } from "../../api/hooks";
import { usePageTitle } from "../../app/usePageTitle";
import { QueryState } from "../../components/QueryState";
import { ArchitectureStudio } from "./ArchitectureStudio";
import { ComponentCatalog } from "./ComponentCatalog";

const COMPONENTS = "components";

export function ArchitecturePage() {
  const { viewId = "reference" } = useParams();
  usePageTitle("Architecture");
  const views = useViews();
  return (
    <>
      <h1>Architecture</h1>
      <QueryState label="architecture views" {...views}>
        {(all) => (
          <>
            <nav aria-label="Architecture views" className="view-tabs">
              <ul>
                {all.map((view) => (
                  <li key={view.id}>
                    <NavLink to={`/architecture/${view.id}`}>{view.title}</NavLink>
                  </li>
                ))}
                <li>
                  <NavLink to={`/architecture/${COMPONENTS}`}>All components</NavLink>
                </li>
              </ul>
            </nav>
            {viewId === COMPONENTS ? (
              <ComponentCatalog />
            ) : (
              <ArchitectureStudio key={viewId} viewId={viewId} />
            )}
          </>
        )}
      </QueryState>
    </>
  );
}
