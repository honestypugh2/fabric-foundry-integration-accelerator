# Architecture documentation

Start with HC-01 to follow the Fabric engineering lab. Use the reference view to explain the
platform, then the system view to trace this repository.

Each diagram doc follows the Azure Architecture Center layout. It links to a draw.io file and
includes a Mermaid preview, numbered workflow, implementation table and Microsoft guidance.

- The diagrams are generated from `education/architecture/views/*.yaml` (`make diagrams`).
- The same diagrams are interactive in the app at `/architecture/<view>`.

| Diagram | What it shows |
|---|---|
| [repository-map.md](repository-map.md) | Clickable mapping, actual draw.io PNGs with editable sources, and both-use-case runtime screenshots |
| [code-reading-path.md](code-reading-path.md) | Contracts-to-tests reading order, a request trace and code-shape decisions |
| [learning-foundations.md](learning-foundations.md) | Focused concepts connecting data meaning, context, reasoning and independent verification |
| [integration-paths.md](integration-paths.md) | Fabric MCP-first coding workflow versus application REST/SDK routing |
| [reference-architecture.md](reference-architecture.md) | Fabric + Foundry reference architecture (context, reasoning, access, authority, evidence) |
| [production-architecture.md](production-architecture.md) | Production deployment aligned to the baseline Foundry chat architecture, with Fabric |
| [system-architecture.md](system-architecture.md) | This repository at run time, with a live runtime overlay in the app |
| [mcp-topology.md](mcp-topology.md) | Which harness reaches which MCP server, for which job |
| [agentic-data-engineering.md](agentic-data-engineering.md) | The GitHub Copilot maturity ladder for Fabric data engineering |
| [hc-01-architecture.md](hc-01-architecture.md) | Guide HC-01, in the tenant and offline |
| [live-vs-offline.md](live-vs-offline.md) | LIVE, HYBRID and OFFLINE: reads fall back visibly, writes never do |

| Implementation | What to read |
|---|---|
| [control-plane.md](control-plane.md) | API, local MCP server, governed change flow |
| [resilience.md](resilience.md) | Router, circuit breaker, fallback configuration |
| [frontend.md](frontend.md) | Educational app structure, contracts and accessibility |

The draw.io sources are in [`diagrams/`](diagrams/). Open them in draw.io desktop, diagrams.net or
the VS Code Draw.io Integration extension. Do not edit them by hand: change the view YAML and run
`ffia diagrams render`. See [ADR-0011](../decisions/ADR-0011-architecture-diagrams-as-code.md).
