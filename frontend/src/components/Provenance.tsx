import type { EnvelopeMeta } from "../api/contracts";
import { Badge } from "./Badge";

/** Who served a result, under which label, and whether a fallback or simulation was involved. */
export function Provenance({ envelope }: { readonly envelope: EnvelopeMeta }) {
  return (
    <p className="provenance">
      <Badge value={envelope.execution_label} /> served by {envelope.selected_provider}
      {envelope.fallback_used && envelope.fallback_reason
        ? ` (fallback: ${envelope.fallback_reason})`
        : ""}
      . Equivalent Fabric service: {envelope.equivalent_fabric_service}.
      {envelope.simulation_notice ? ` ${envelope.simulation_notice}` : ""}
    </p>
  );
}
