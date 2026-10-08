import { Link } from "react-router";

interface TalkTrackLink {
  readonly id: string;
  readonly guide: string;
  readonly title: string;
  readonly covers: string;
  readonly view: string;
}

/** Presenter handouts rendered by `ffia talktracks render` into public/talktracks/. */
const TALK_TRACKS: readonly TalkTrackLink[] = [
  {
    id: "fabric-copilot-level-up",
    guide: "Guide 1",
    title: "Leveling up Fabric data engineering with GitHub Copilot",
    covers:
      "What GitHub Copilot is doing, Fabric MCP, Fabric Skills, Power BI, Foundry with Copilot, and the L1 → L6 level-up.",
    view: "agentic-de",
  },
  {
    id: "foundry-fabric-agents-workshop",
    guide: "Guide 2",
    title: "Foundry + Fabric agent workshop",
    covers:
      "Foundry capabilities and Fabric, building and orchestrating agents, internal and external data, security and governance, monthly insights, data quality and licensing.",
    view: "mfg-01",
  },
];

export function TalkTracks({ headingLevel = 2 }: { readonly headingLevel?: 2 | 3 }) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  return (
    <section aria-labelledby="talk-tracks-heading">
      <Heading id="talk-tracks-heading">Workshop talk tracks</Heading>
      <p>
        Presenter scripts with portal, VS Code and web app steps, offline fallbacks, architecture
        diagrams and anticipated questions. Each opens as a printable page.
      </p>
      <ul className="talk-tracks">
        {TALK_TRACKS.map((track) => (
          <li key={track.id} className="talk-tracks__item">
            <p className="talk-tracks__guide">{track.guide}</p>
            <p className="talk-tracks__title">{track.title}</p>
            <p>{track.covers}</p>
            <p className="talk-tracks__links">
              <a href={`/talktracks/${track.id}.html`} target="_blank" rel="noreferrer">
                Open talk track
              </a>
              <Link to={`/architecture/${track.view}`}>Architecture</Link>
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
