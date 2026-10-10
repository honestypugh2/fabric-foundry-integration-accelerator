import { Link } from "react-router";
import system from "../../../docs/architecture/diagrams/system.png";
import reference from "../../../docs/architecture/diagrams/reference.png";
import production from "../../../docs/architecture/diagrams/production.png";
import mcp from "../../../docs/architecture/diagrams/mcp-topology.png";
import ladder from "../../../docs/architecture/diagrams/agentic-de.png";
import healthcare from "../../../docs/architecture/diagrams/hc-01.png";
import manufacturing from "../../../docs/architecture/diagrams/mfg-01.png";
import routing from "../../../docs/architecture/diagrams/live-vs-offline.png";
import foundations from "../../../docs/architecture/diagrams/theory-to-tools.png";
import integration from "../../../docs/architecture/diagrams/integration-paths.png";

const IMAGES: Readonly<Record<string, string>> = {
  system,
  reference,
  production,
  "mcp-topology": mcp,
  "agentic-de": ladder,
  "hc-01": healthcare,
  "mfg-01": manufacturing,
  "live-vs-offline": routing,
  "theory-to-tools": foundations,
  "integration-paths": integration,
};

export function ArchitectureImage({
  viewId,
  title,
}: {
  readonly viewId: string;
  readonly title: string;
}) {
  const image = IMAGES[viewId];
  return (
    <figure className="architecture-image">
      {image ? (
        <a href={image} target="_blank" rel="noreferrer">
          <img src={image} alt={title} loading="lazy" />
        </a>
      ) : (
        <p>No static export is available for this view.</p>
      )}
      <figcaption>
        Static architecture, not execution proof.{" "}
        <Link to={`/architecture/${viewId}`}>Open interactive explanation</Link>
        {image ? (
          <>
            {" · "}
            <a href={image} target="_blank" rel="noreferrer">
              Open full-size PNG
            </a>
          </>
        ) : null}
      </figcaption>
    </figure>
  );
}
