import { Link } from "react-router";
import { ArchitectureStudio } from "../features/architecture/ArchitectureStudio";

export function ArchitectureExplorer({
  viewId,
  title,
}: {
  readonly viewId: string;
  readonly title: string;
}) {
  return (
    <div className="architecture-explorer" aria-label={title}>
      <ArchitectureStudio viewId={viewId} />
      <Link to={`/architecture/${viewId}`}>Open dedicated architecture workspace</Link>
    </div>
  );
}
