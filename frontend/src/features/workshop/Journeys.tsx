import { Link } from "react-router";
import type { Workshop } from "../../api/contracts";

export function Journeys({ workshop }: { readonly workshop: Workshop }) {
  return (
    <ul className="cards journey-cards">
      {workshop.content.journeys.map((journey, index) => (
        <li className="card journey-card" key={journey.id} id={`journey-${journey.id}`}>
          <span className="eyebrow">
            Path {index + 1} · estimated {journey.duration_minutes} min
          </span>
          <h2>
            <Link to={`/learn#path-${journey.id}`}>{journey.title}</Link>
          </h2>
          <p>{journey.summary}</p>
          {journey.lesson_ids.slice(0, 1).map((id) => (
            <Link key={id} className="text-link" to={`/learn/${id}`}>
              Start this path →
            </Link>
          ))}
        </li>
      ))}
    </ul>
  );
}
