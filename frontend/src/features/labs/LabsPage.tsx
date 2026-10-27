import { Link } from "react-router";
import { useLabs } from "../../api/hooks";
import { levelLabel } from "../../app/levelContext";
import { usePageTitle } from "../../app/usePageTitle";
import { Badge } from "../../components/Badge";
import { QueryState } from "../../components/QueryState";

export function LabsPage() {
  usePageTitle("Labs");
  const labs = useLabs();
  return (
    <>
      <div className="page-intro">
        <p className="eyebrow">Practice one skill at a time</p>
        <h1>Hands-on labs</h1>
        <p className="lead">
          Choose an exercise, work through one focused stage, and check the expected result before
          moving on.
        </p>
        <p>
          Each lab includes a failure-and-recovery exercise and equivalent assistant prompts.
          Progress stays in your browser; it never certifies live execution.
        </p>
      </div>
      <QueryState label="labs" {...labs}>
        {(all) => (
          <ul className="cards">
            {all.map((lab) => (
              <li key={lab.id} className="card">
                <h2 className="card__title">
                  <Link to={`/labs/${lab.id}`}>{lab.title}</Link> <Badge value={lab.mode} />
                </h2>
                <p>{lab.summary}</p>
                <p className="meta">
                  {levelLabel(lab.level)} · about {lab.duration_minutes} minutes
                </p>
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </>
  );
}
