# Architecture documentation

Each diagram doc follows the Azure Architecture Center layout. It contains a draw.io file, a
Mermaid preview, a numbered workflow, a components table showing what is implemented in this
repository, and the Microsoft guidance it is aligned to.

- The diagrams are generated from `education/architecture/views/*.yaml` (`make diagrams`).
- The same diagrams are interactive in the app at `/architecture/<view>`.

| Diagram | What it shows |
|---|---|
| [reference-architecture.md](reference-architecture.md) | Fabric + Foundry reference architecture (context, reasoning, access, authority, evidence) |
| [production-architecture.md](production-architecture.md) | Production deployment aligned to the baseline Foundry chat architecture, with Fabric |
| [system-architecture.md](system-architecture.md) | This repository at run time, with a live runtime overlay in the app |
| [mcp-topology.md](mcp-topology.md) | Which harness reaches which MCP server, for which job |
| [agentic-data-engineering.md](agentic-data-engineering.md) | The GitHub Copilot maturity ladder for Fabric data engineering |
| [hc-01-architecture.md](hc-01-architecture.md) | Guide HC-01, in the tenant and offline |
| [live-vs-offline.md](live-vs-offline.md) | LIVE, HYBRID and OFFLINE: reads fall back visibly, writes never do |

| Mechanics | |
|---|---|
| [control-plane.md](control-plane.md) | API, local MCP server, governed change flow |
| [resilience.md](resilience.md) | Router, circuit breaker, fallback configuration |
| [frontend.md](frontend.md) | Educational app structure, contracts and accessibility |

The draw.io sources are in [`diagrams/`](diagrams/). Open them in draw.io desktop, diagrams.net or
the VS Code Draw.io Integration extension. Do not edit them by hand: change the view YAML and run
`ffia diagrams render`. See [ADR-0011](../decisions/ADR-0011-architecture-diagrams-as-code.md).
