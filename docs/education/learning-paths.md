# Learning paths

Every lesson teaches five levels. The level is chosen once (header or lesson tabs) and applies
across the architecture explorer, lessons and labs.

| Level | Audience | Focus |
|---|---|---|
| Executive | Decision makers | Outcome, value, risk, governance, what is GA versus preview |
| L100 | Newcomers | What, why and where, simple diagrams, key terms |
| L200 | Architects | Components, boundaries, identity paths, trade-offs, online versus offline |
| L300 | Engineers | Commands, APIs, MCP tools, configuration and tests in this repository |
| L400 | Practitioners | Enforcement details, failure modes, threat model, production gaps |

## Suggested paths

| Goal | Path |
|---|---|
| **Improve Fabric data engineering with GitHub Copilot** (main goal) | `fabric-foundry-boundaries` → `fabric-mcp-landscape` → `fabric-skills` → `copilot-maturity-ladder` → `copilot-surfaces` → `copilot-vs-claude-code` → lab `lab-copilot-maturity-ladder` → Guide HC-01 |
| Governed agents | `fabric-foundry-boundaries` → `p06-enterprise-agent` → `p08-human-in-the-loop` → `p09-governed-mcp` → labs `lab-governed-change`, `lab-mcp-allow-list` |
| Data and resilience | `p10-medallion-ai` → `p11-mirroring-ai` → `p16-evaluation-observability` → `p17-resilience` → labs `lab-resilience-break-it`, `lab-open-mirroring-recovery` |
| Power BI semantic models | `power-bi-agentic-tooling` → Guide HC-01, steps 11–15 |

## Content model

See [ADR-0010](../decisions/ADR-0010-education-content-as-data.md) and `education/README.md`.

- Validate the content with `make education-check`.
- The 30-question completeness gate is reported on the home page and by
  `ffia education check`.
