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
      <h1>Labs</h1>
      <p>
        Every lab follows the same eleven stages: learn, see, build, inspect, break it, recover,
        verify, go deeper, try with GitHub Copilot, try with Claude Code, and production notes.
      </p>
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
