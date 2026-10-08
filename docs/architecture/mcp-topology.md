# MCP topology for Fabric data engineering

Which harness reaches which MCP server, for which job, under whose identity. Every harness reads
the same `AGENTS.md`, skills and `.mcp.json`. Each job uses the narrowest server:

- documentation tools for *how*;
- read-only tools for *what is*;
- Git or the approved change flow for *change it*.

## Architecture

<!-- BEGIN GENERATED DIAGRAM: run `ffia diagrams render`; do not edit by hand -->

> Generated from [`education/architecture/views/mcp-topology.yaml`](../../education/architecture/views/mcp-topology.yaml). Edit the YAML, then run `ffia diagrams render`.

- **draw.io:** [diagrams/mcp-topology.drawio](diagrams/mcp-topology.drawio). Open it in draw.io desktop, diagrams.net or the VS Code Draw.io Integration extension. Page 1 is the full architecture; the next pages build it up one step at a time.
- **Interactive:** run `make run`, then open `http://localhost:5173/architecture/mcp-topology` to build it step by step, trace requests, switch Executive to L400 and see live runtime state.

```mermaid
flowchart LR
  subgraph harness_zone["Agent harnesses"]
    vscode["VS Code agent mode<br/><small>GitHub Copilot</small>"]
    copilot_cli["Copilot CLI<br/><small>Terminal agent, GA</small>"]
    copilot_app["Copilot app · PREVIEW<br/><small>Worktrees, technical preview</small>"]
    cloud_agent["Copilot cloud agent<br/><small>Issue to pull request</small>"]
    claude_code["Claude Code<br/><small>CLAUDE.md imports AGENTS.md</small>"]
  end
  subgraph knowledge_zone["Shared knowledge and configuration"]
    agents_md["AGENTS.md and instructions<br/><small>How to work here</small>"]
    skills["Skills<br/><small>Fabric Skills + repo skills</small>"]
    mcp_json[".mcp.json<br/><small>One config for every harness</small>"]
  end
  subgraph gateway_zone["Optional gateway"]
    apim["API Management · optional<br/><small>MCP gateway</small>"]
  end
  subgraph server_zone["MCP servers"]
    learn_mcp["Microsoft Learn MCP<br/><small>How - documentation</small>"]
    fabric_mcp_local["Fabric MCP Server (local)<br/><small>Docs, OneLake, core items</small>"]
    fabric_iq_mcp["Fabric IQ MCP<br/><small>What is - read-only DAX</small>"]
    dw_mcp["Data Warehouse MCP · PREVIEW<br/><small>Arbitrary T-SQL - preview</small>"]
    pbi_mcp["Power BI Authoring MCP<br/><small>Change it - sandbox PBIP</small>"]
    ffia_local["ffia-local (this repo)<br/><small>Allow-listed, plan-only</small>"]
    data_agent_mcp["Fabric data agent MCP · tenant<br/><small>Curated Q&A endpoint</small>"]
  end
  subgraph target_zone["Fabric and local targets"]
    onelake["OneLake and items<br/><small>Lakehouses, notebooks, files</small>"]
    semantic_model["Semantic models<br/><small>Measures and relationships</small>"]
    warehouse["Warehouse or SQL endpoint<br/><small>T-SQL</small>"]
    pbip["PBIP / TMDL in Git · planned<br/><small>Reviewed definitions</small>"]
    synthetic["Synthetic local data<br/><small>Offline equivalent</small>"]
  end
  entra["Entra ID<br/><small>Caller's permissions</small>"]
  change_flow["Approved change flow<br/><small>Plan, approve, PR</small>"]
  vscode --> mcp_json
  copilot_cli --> mcp_json
  copilot_app --> mcp_json
  cloud_agent -->|Repository settings| mcp_json
  claude_code --> mcp_json
  mcp_json -->|How| learn_mcp
  mcp_json -->|How and what is| fabric_mcp_local
  mcp_json -->|What is| fabric_iq_mcp
  mcp_json -.->|Off by default| dw_mcp
  mcp_json -->|Change it (reviewed)| pbi_mcp
  mcp_json -->|Offline| ffia_local
  mcp_json -.->|Ask| data_agent_mcp
  mcp_json -->|One front door| apim
  apim -->|Policy, quota, audit| fabric_iq_mcp
  fabric_mcp_local --> onelake
  fabric_iq_mcp -->|DAX (read)| semantic_model
  dw_mcp -->|T-SQL| warehouse
  pbi_mcp -->|Edit a copy| pbip
  ffia_local -->|LOCAL| synthetic
  entra -->|Decides access| onelake
  pbip -->|Publish after approval| change_flow
  class vscode,copilot_cli,cloud_agent,claude_code,skills,learn_mcp,fabric_mcp_local,fabric_iq_mcp,pbi_mcp,onelake,semantic_model,warehouse,entra documented
  class agents_md,mcp_json,ffia_local,synthetic,change_flow implemented
  class apim optional
  class pbip planned
  class copilot_app,dw_mcp preview
  class data_agent_mcp tenant_validation
  classDef implemented stroke-width:2px
  classDef planned stroke-dasharray: 6 4
  classDef preview stroke-dasharray: 2 3
  classDef optional stroke-dasharray: 8 4
  classDef documented stroke-width:1px
  classDef tenant_validation stroke-dasharray: 3 3
```

Solid boxes are implemented here or documented by Microsoft; dashed boxes are planned, preview or optional.

### Workflow

*PLANNED FLOW.* One data-engineering task, three kinds of question, three different servers.

1. An engineer asks Copilot CLI to add a Silver table for encounters.
2. The harness loads the shared MCP configuration and repo instructions.
3. How - documentation tools explain the right notebook and Delta patterns. No tenant needed.
4. What is - read-only tools list the lakehouse tables with the engineer's permissions.
5. Fabric permissions decide what the engineer can see.
6. Change it - the notebook arrives as a reviewed pull request or an approved plan, not a direct write.

### Flow: Practice offline

*LOCAL.* The same questions answered against synthetic data with no tenant. Offline demo act 3.

1. Claude Code (or Copilot) uses the same .mcp.json.
2. It starts ffia-local over stdio.
3. Read tools inspect the medallion; plan tools propose but never execute.
4. Answers come from synthetic data, labeled LOCAL.

### Components

| Component | Status | Role | In this repository |
|---|---|---|---|
| VS Code agent mode | Microsoft-documented | Copilot agent mode in VS Code with tool approvals, terminal auto-approve rules, custom agents, skills and MCP servers from .mcp.json. | - |
| Copilot CLI | Microsoft-documented | Terminal agent with plan mode, tool permissions, skills, plugins, MCP and a headless -p mode. | - |
| Copilot app | Preview | Desktop app running parallel agent sessions in isolated git worktrees, with Plan and Autopilot modes. Technical preview. | - |
| Copilot cloud agent | Microsoft-documented | Assign an issue and the agent works in a sandbox and opens a pull request. MCP servers come from repository settings; there is no per-call approval, so the pull request is the control. | - |
| Claude Code | Microsoft-documented | Anthropic's agentic CLI. In this repository CLAUDE.md imports AGENTS.md and the same .mcp.json and .claude/skills are shared. | - |
| AGENTS.md and instructions | Implemented in this repository | The single source of truth for every coding agent - rules, commands, safety and evidence requirements. | `AGENTS.md` |
| Skills | Microsoft-documented | Skills are knowledge, not execution; they drive REST, SQL, KQL or PySpark under the user's identity. | - |
| .mcp.json | Implemented in this repository | The project MCP configuration, rendered from config/mcp/profiles.yaml (default profile: Microsoft Learn and ffia-local). Opt-in Fabric MCP profiles are rendered per client with `ffia mcp render`; `ffia mcp check` keeps them pinned and least-privilege. | `.mcp.json` |
| API Management | Optional | Adds authentication, rate limits, logging and policies in front of MCP servers and model endpoints. | - |
| Microsoft Learn MCP | Microsoft-documented | Public documentation search and fetch. Answers how questions without any tenant access. | - |
| Fabric MCP Server (local) | Microsoft-documented | Local server with documentation and item-definition tools that work without a tenant, plus OneLake and core item tools that run with your Fabric permissions. Some tools can write. | - |
| Fabric IQ MCP | Microsoft-documented | Remote, read-only server for querying semantic models. Good for what is questions in a live workspace. | - |
| Data Warehouse MCP | Preview | Remote server that runs T-SQL against a warehouse or SQL endpoint. Preview, and broad by design - off by default, read-only labs against a dev workspace only. | - |
| Power BI Authoring MCP | Microsoft-documented | Local server for authoring semantic models (TMDL, relationships, measures, DAX queries). Write-capable, so use it on a reviewed copy and publish through approval. | - |
| ffia-local (this repo) | Implemented in this repository | Allow-listed from config/policies/tools.yaml; no approve, execute, shell or SQL tools. | `config/policies/tools.yaml` |
| Fabric data agent MCP | Requires tenant validation | A published Fabric data agent can be reached as an MCP endpoint. Read-only and scoped to the agent's sources; validate availability and behavior in your tenant. | - |
| OneLake and items | Microsoft-documented | Lakehouses in OneLake hold each layer; notebooks transform; tests check row counts and baselines. | - |
| Semantic models | Microsoft-documented | Direct Lake reads Gold Delta tables; measures are the governed definitions agents should reuse. | - |
| Warehouse or SQL endpoint | Microsoft-documented | Fabric Data Warehouse or a lakehouse SQL analytics endpoint. | - |
| PBIP / TMDL in Git | Planned (Phase 7) | Power BI project files under version control, so model changes are diffs that can be reviewed before publication. | - |
| Synthetic local data | Implemented in this repository | Read-only, allow-listed operations over synthetic Parquet; never presented as Fabric. | - |
| Entra ID | Microsoft-documented | User, approver and writer are different identities; agents act on behalf of users or as scoped identities. | - |
| Approved change flow | Implemented in this repository | Separation of duties, expiry and destination binding protect the decision. | - |

### Aligned to

- [Choose a Microsoft Fabric MCP server](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/fabric-mcp-servers-list) (GUIDANCE)
- [Fabric MCP Server (local) tools reference](https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/pro-dev-local/tools-local-mcp-server) (GA)
- [Get started with Fabric IQ MCP](https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp) (GA)
- [Fabric Data Warehouse MCP server (Preview)](https://learn.microsoft.com/fabric/data-warehouse/data-warehouse-mcp-server) (PREVIEW)
- [Power BI Authoring (Modeling) MCP server](https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp) (GA)
- [Overview of MCP servers in Azure API Management](https://learn.microsoft.com/azure/api-management/mcp-server-overview) (GA)
- [Model Context Protocol specification versioning](https://modelcontextprotocol.io/specification/versioning) (GA)
- [Add and manage MCP servers in VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers) (GA)

<!-- END GENERATED DIAGRAM -->

## Notes

- **Hosting is not processing location.** The Fabric MCP servers list separates *remote*
  servers (hosted by Microsoft) from *local* servers (run by you). Local servers can still reach
  live Fabric resources.
- **`ffia-local` is a local teaching server.** It is not a Microsoft-hosted endpoint, and a call
  to it is never evidence of a Fabric operation.
- **Gateways.** API Management can expose a REST API as an MCP server or pass through an
  existing MCP server. It supports MCP tools, but not MCP resources or prompts. The Foundry AI
  gateway for MCP tools runs on API Management, so draw one gateway.
- **Status.** The status of each server comes from its own documentation page. The overview list
  does not state status per server. See [ga-preview-matrix.md](../research/ga-preview-matrix.md).
