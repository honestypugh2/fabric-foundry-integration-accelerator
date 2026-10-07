## One sentence per layer

Fabric and Foundry are often presented as one "AI on your data" story. They solve different
problems, and the value comes from keeping their responsibilities separate:

- **Fabric provides governed business context.** Your curated tables, semantic models and data
  agents, protected by the permissions you already manage.
- **Foundry turns that context into reasoning, orchestration, evaluation and action.** Agents
  plan, call tools, combine answers and ask for approval.
- **MCP standardizes how tools are reached.** It does not decide who may use them.
- **Entra identity and policy decide authority.** Who may read, who may change, who approves.
- **Business systems remain the authority for transactions.** An agent asks; the system of
  record decides and records.

| Layer | Owns | Never owns |
|---|---|---|
| Fabric | Data, definitions, data permissions | Business decisions or approvals |
| Foundry | Reasoning, orchestration, evaluation | Data permissions or final authority |
| MCP | A standard way to call tools | Authorization |
| Identity and policy | Who may do what, approvals | The data or the reasoning |
| Business systems | Transactions of record | Analytics context |
| Observability and evaluation | Evidence that it worked | The outcome itself |

## Why leaders should care

Most AI risk in this space is a **boundary failure**: an agent that can both decide and write,
a tool connection treated as permission, or a demo that hides simulated results. Clear
boundaries let you approve the architecture once and reuse it for every new use case.

## What is GA and what is not

The core building blocks - Fabric, Foundry Agent Service, Agent Framework and the local Fabric
MCP server - are **GA**. Fabric IQ, ontology and the Foundry Fabric data agent tool are
**PREVIEW** and stay optional. That is why this lesson is labeled **MIXED**.

## How this accelerator stays honest

Every result is labeled (LIVE, HYBRID, LOCAL, SIMULATED, PREVIEW or UNAVAILABLE), and the full
demo runs offline. When something is not built yet - Foundry arrives in Phase 6 - the demo says
UNAVAILABLE instead of pretending.

**Decision for leaders:** which identities hold authority for which actions, and who is
accountable for approving them.
