export interface Principle {
  readonly id: string;
  readonly statement: string;
}

/** The central lesson of the accelerator, rendered on the home page. */
export const principles: readonly Principle[] = [
  { id: "fabric", statement: "Fabric provides governed business context." },
  {
    id: "foundry",
    statement: "Foundry turns that context into reasoning, orchestration, evaluation, and action.",
  },
  { id: "mcp", statement: "MCP standardizes access to capabilities. It does not grant authority." },
  { id: "identity", statement: "Enterprise identity and policy determine authority." },
  {
    id: "oversight",
    statement: "Deterministic validation and human oversight constrain high-impact actions.",
  },
  { id: "evidence", statement: "Observability and evaluation provide evidence." },
  {
    id: "resilience",
    statement: "Offline resilience ensures the architecture can always be demonstrated and taught.",
  },
];
