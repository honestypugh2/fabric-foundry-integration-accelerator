# Architecture decision records

One ADR per decision. Required sections: Context, Options, Decision, Rationale, Trade-offs,
Security impact, Operations impact, Offline impact, Education impact, Revisit trigger,
Authoritative references.

| ADR | Decision |
|---|---|
| [0001](ADR-0001-python-uv.md) | Python 3.14 with uv |
| [0002](ADR-0002-react-typescript-vite.md) | React + TypeScript + Vite |
| [0003](ADR-0003-local-fabric-provider-duckdb.md) | Local Fabric Educational Provider on DuckDB |
| [0004](ADR-0004-synthetic-dataset-profiles.md) | Synthetic dataset profiles |
| [0005](ADR-0005-provider-router-and-fallback.md) | Provider ports, router and approved read fallback |
| [0006](ADR-0006-human-approval-and-scoped-writer.md) | Human approval, scoped writer, and no silent LIVE → LOCAL redirect |
| [0007](ADR-0007-mcp-access-is-not-authority.md) | MCP access is not authority; local educational MCP server |
| [0008](ADR-0008-offline-demo-release-gate.md) | The offline demo is a release gate |
| [0009](ADR-0009-frontend-architecture.md) | Frontend architecture and typed API contracts |
| [0010](ADR-0010-education-content-as-data.md) | Education content as validated data, with a completeness gate |
| [0011](ADR-0011-architecture-diagrams-as-code.md) | Architecture diagrams as code (draw.io, Azure Architecture Center style) |
| [0012](ADR-0012-live-fabric-integration.md) | Live Fabric integration: read-only provider, gated scoped writer, MCP profiles as code, reference notebooks |

More ADRs are added in Phases 4–8.
