## What Fabric Skills change

Coding agents such as GitHub Copilot and Claude Code are fast but often wrong about
product-specific details: which Fabric API to call, which item format to use, which Spark
setting matters. **Fabric Skills** - Microsoft's open-source `skills-for-fabric` project - give
the agent Microsoft-authored procedures for Fabric data engineering, administration and Power BI
authoring.

The result is more **correct** agent work, sooner. It is not more **authorized** agent work.

| Question | Answer |
|---|---|
| What is it? | Versioned knowledge packs (25 skills as of October 2026) plus experimental persona agents |
| Who publishes it? | Microsoft, as open source |
| Is it GA? | No GA label. It is pre-1.0 (v0.3.18) and the persona agents are experimental |
| What does it run as? | The signed-in user - every command uses that person's Fabric permissions |
| Main risk | The bundled server list includes write-capable model authoring and arbitrary SQL |

## The five-part model

| Part | Role | Example |
|---|---|---|
| Knowledge | How to do it correctly | Fabric Skills, repository instructions |
| Execution | The hands | MCP servers, Azure CLI, Git |
| Harness | The agent loop and its permissions | Copilot CLI, VS Code, Claude Code |
| Authority | Who may do it | Entra identity, Fabric roles, policy, approval |
| Evidence | Proof it happened | Pull requests, audit records, Fabric request IDs |

Skills improve only the first row. The other four rows are where governance lives.

## Decisions for leaders

- **Where may skills run?** Recommend: developer workstations against a dev workspace.
- **With which identity?** A least-privilege identity, never a tenant administrator.
- **How do changes reach production?** Through Git, pull requests and the approved change flow -
  not through an interactive session.
- **Who owns upgrades?** A pre-1.0 project needs pinned versions and a reviewer for each upgrade.

> Status: **MIXED.** The harnesses are GA; Fabric Skills are official open source without a GA
> label; several bundled MCP servers are preview.
