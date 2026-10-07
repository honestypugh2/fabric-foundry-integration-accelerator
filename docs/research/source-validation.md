# Source validation

<!-- GENERATED FILE: edit docs/research/sources.yaml, then run `uv run ffia sources render`. -->

Official product documentation overrides older samples. Community content never
overrides authoritative product documentation. Status values: GA, PREVIEW,
DEPRECATED, UNKNOWN/NEEDS VALIDATION, GUIDANCE (architecture guidance), OSS
(official open-source project without a product lifecycle label).

## Summary

| Technology | Source | Status | Retrieved |
|---|---|---|---|
| Azure API Management | [Overview of MCP servers in Azure API Management](#apim-mcp) | GA | 2026-10-05 |
| Developer experience | [How Claude remembers your project (CLAUDE.md and AGENTS.md)](#claude-code-memory) | GA | 2026-10-05 |
| Developer experience | [Extend Claude with skills](#claude-code-skills) | GA | 2026-10-05 |
| Developer experience | [GitHub Copilot CLI is now generally available](#copilot-cli-ga) | GA | 2026-10-05 |
| Developer experience | [Support for different types of custom instructions](#copilot-instructions-support) | GA | 2026-10-05 |
| Developer experience | [Skills for Fabric overview](#skills-for-fabric) | OSS | 2026-10-05 |
| Developer experience | [Add and manage MCP servers in VS Code](#vscode-mcp-servers) | GA | 2026-10-05 |
| Fabric IQ and Data Agents | [Fabric data agent concepts](#fabric-data-agent) | GA | 2026-10-05 |
| Fabric IQ and Data Agents | [Ontology overview (Fabric IQ)](#fabric-iq-ontology) | PREVIEW | 2026-10-05 |
| Fabric IQ and Data Agents | [What is Fabric IQ?](#fabric-iq-overview) | PREVIEW | 2026-10-05 |
| Microsoft Agent Framework | [Microsoft Agent Framework overview](#agent-framework) | GA | 2026-10-05 |
| Microsoft Fabric | [AI functions in Fabric](#fabric-ai-functions) | GA | 2026-10-05 |
| Microsoft Fabric | [Microsoft Fabric deployment patterns](#fabric-deployment-patterns) | GUIDANCE | 2026-10-05 |
| Microsoft Fabric | [Direct Lake overview](#fabric-direct-lake) | GA | 2026-10-05 |
| Microsoft Fabric | [Fabric Git integration overview](#fabric-git-integration) | GA | 2026-10-05 |
| Microsoft Fabric | [Implement medallion lakehouse architecture in Microsoft Fabric](#fabric-medallion) | GUIDANCE | 2026-10-05 |
| Microsoft Fabric | [Open mirroring landing zone requirements and format](#fabric-open-mirroring-format) | GA | 2026-10-07 |
| Microsoft Fabric | [What is Microsoft Fabric?](#fabric-overview) | GA | 2026-10-05 |
| Microsoft Fabric | [Fabric REST API identity support](#fabric-rest-identity) | GA | 2026-10-05 |
| Microsoft Fabric | [Azure Well-Architected Framework service guide for Microsoft Fabric](#fabric-waf) | GUIDANCE | 2026-10-05 |
| Microsoft Foundry | [Baseline Microsoft Foundry chat reference architecture](#baseline-foundry-chat) | GUIDANCE | 2026-10-05 |
| Microsoft Foundry | [Foundry Agent Service overview](#foundry-agent-service) | GA | 2026-10-05 |
| Microsoft Foundry | [Built-in evaluators in Microsoft Foundry](#foundry-evaluators) | GA | 2026-10-05 |
| Microsoft Foundry | [Use the Microsoft Fabric data agent tool in Foundry Agent Service](#foundry-fabric-tool) | PREVIEW | 2026-10-05 |
| Microsoft Foundry | [What is Foundry IQ?](#foundry-iq) | PREVIEW | 2026-10-05 |
| Microsoft Foundry | [What is Microsoft Foundry?](#foundry-overview) | GA | 2026-10-05 |
| Model Context Protocol | [Fabric Data Warehouse MCP server (Preview)](#fabric-dw-mcp) | PREVIEW | 2026-10-05 |
| Model Context Protocol | [Get started with Fabric IQ MCP](#fabric-iq-mcp) | GA | 2026-10-05 |
| Model Context Protocol | [Fabric MCP Server (local) tools reference](#fabric-mcp-local) | GA | 2026-10-05 |
| Model Context Protocol | [Choose a Microsoft Fabric MCP server](#fabric-mcp-servers-list) | GUIDANCE | 2026-10-05 |
| Model Context Protocol | [Model Context Protocol specification versioning](#mcp-specification) | GA | 2026-10-05 |
| Model Context Protocol | [Power BI Authoring (Modeling) MCP server](#powerbi-authoring-mcp) | GA | 2026-10-05 |
| Toolchain | [Node.js release schedule](#node-release-schedule) | GA | 2026-10-05 |
| Toolchain | [Status of Python versions](#python-lifecycle) | GA | 2026-10-05 |

## Azure API Management

<a id="apim-mcp"></a>

### Overview of MCP servers in Azure API Management

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/api-management/mcp-server-overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P15 |
| Key architecture statement | APIM can expose REST APIs as governed MCP tools with centralized authentication, rate limiting and logging. |
| Implementation relevance | Pattern 15 governance option and when-not-to-use criteria. |
| Security implications | Central policy enforcement point for tool access. |
| Limitations | Tools only (no resources or prompts); not supported in APIM workspaces. |
| Fallback | Local policy simulation. |
| Deprecation / replacement | — |

## Developer experience

<a id="claude-code-memory"></a>

### How Claude remembers your project (CLAUDE.md and AGENTS.md)

| Field | Value |
|---|---|
| URL | https://code.claude.com/docs/en/memory |
| Publisher | Anthropic |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P19, P23 |
| Key architecture statement | Claude Code reads AGENTS.md only when no CLAUDE.md or CLAUDE.local.md exists; a CLAUDE.md can import it with @AGENTS.md. |
| Implementation relevance | CLAUDE.md imports AGENTS.md so both tools share one instruction source. |
| Security implications | Instruction files are context, not enforced configuration; use permissions and hooks to enforce. |
| Limitations | Direct AGENTS.md reading requires Claude Code 2.1.277 or later. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="claude-code-skills"></a>

### Extend Claude with skills

| Field | Value |
|---|---|
| URL | https://code.claude.com/docs/en/skills |
| Publisher | Anthropic |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P19 |
| Key architecture statement | Project skills load from .claude/skills/<name>/SKILL.md; custom commands are merged into skills. |
| Implementation relevance | .claude/skills is the single skill folder read by both Copilot and Claude Code. |
| Security implications | Skills folders with plugin manifests require workspace trust. |
| Limitations | Claude Code does not load .github/skills or .agents/skills. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="copilot-cli-ga"></a>

### GitHub Copilot CLI is now generally available

| Field | Value |
|---|---|
| URL | https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/ |
| Publisher | GitHub |
| Retrieved | 2026-10-05 |
| Last updated | 2026-02-25 |
| Status | GA |
| Associated patterns | P19, P23 |
| Key architecture statement | Terminal agent with plan mode, tool permissions, skills, plugins, MCP and headless prompt mode. |
| Implementation relevance | Primary harness for Fabric Skills (plugin marketplace install). |
| Security implications | --allow-all-tools grants full local access; use scoped --allow-tool rules. |
| Limitations | Local and cloud sandboxes are preview. |
| Fallback | Recorded replay transcripts. |
| Deprecation / replacement | — |

<a id="copilot-instructions-support"></a>

### Support for different types of custom instructions

| Field | Value |
|---|---|
| URL | https://docs.github.com/en/copilot/reference/custom-instructions-support |
| Publisher | GitHub Docs |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P19, P21 |
| Key architecture statement | Copilot surfaces read copilot-instructions.md, path-specific instructions and AGENTS.md with surface-specific support. |
| Implementation relevance | AGENTS.md is the single source of truth; client-specific files stay thin. |
| Security implications | Instructions are guidance, not enforcement; enforcement lives in policy and permissions. |
| Limitations | github.com web chat does not read AGENTS.md. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="skills-for-fabric"></a>

### Skills for Fabric overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-06-29 |
| Status | OSS |
| Associated patterns | P19, P20 |
| Key architecture statement | Skills provide static procedural knowledge; MCP servers provide live execution; persona agents are experimental. |
| Implementation relevance | Fabric Skills (microsoft/skills-for-fabric v0.3.18) power maturity level L3 in the Copilot labs. |
| Security implications | Bundled MCP config grants all tools on write-capable servers; use the hardened profile. |
| Limitations | Pre-1.0 open-source project without a product lifecycle label. |
| Fallback | Accelerator repo skills derived from public documentation. |
| Deprecation / replacement | — |

<a id="vscode-mcp-servers"></a>

### Add and manage MCP servers in VS Code

| Field | Value |
|---|---|
| URL | https://code.visualstudio.com/docs/agent-customization/mcp-servers |
| Publisher | Visual Studio Code documentation |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P09 |
| Key architecture statement | Portable workspace .mcp.json (mcpServers) is preferred; .vscode/mcp.json is deprecated for new servers. |
| Implementation relevance | One root .mcp.json serves VS Code, Copilot CLI and Claude Code. |
| Security implications | Local MCP servers can run arbitrary code; add only trusted, pinned servers. |
| Limitations | Agent Host does not forward servers requiring interactive input variables. |
| Fallback | Not applicable. |
| Deprecation / replacement | .vscode/mcp.json is deprecated in favor of .mcp.json or ~/.copilot/mcp-config.json. |

## Fabric IQ and Data Agents

<a id="fabric-data-agent"></a>

### Fabric data agent concepts

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-science/concept-data-agent |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-05-11 |
| Status | GA |
| Associated patterns | P01, P02 |
| Key architecture statement | Conversational Q&A over up to five sources (lakehouse, warehouse, semantic model, KQL, mirrored DB, ontology, Graph) running under the requesting user's identity. |
| Implementation relevance | Fabric owns governed structured context; Foundry orchestrates. |
| Security implications | Least-privilege by user identity; responses may leave Fabric's compliance boundary depending on the consuming client. |
| Limitations | Ontology source is preview; Copilot Studio and M365 Copilot consumption are preview. |
| Fallback | Local deterministic data agent over semantic YAML with allow-listed queries. |
| Deprecation / replacement | — |

<a id="fabric-iq-ontology"></a>

### Ontology overview (Fabric IQ)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/iq/ontology/overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-15 |
| Status | PREVIEW |
| Associated patterns | P03 |
| Key architecture statement | Entities, properties, directional relationships and bindings virtualize business meaning over Fabric data without copying it. |
| Implementation relevance | Teaches data versus semantics versus knowledge versus reasoning. |
| Security implications | Bindings inherit underlying item permissions. |
| Limitations | Preview. |
| Fallback | Local semantic YAML. |
| Deprecation / replacement | — |

<a id="fabric-iq-overview"></a>

### What is Fabric IQ?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/iq/overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-07-08 |
| Status | PREVIEW |
| Associated patterns | P02, P03 |
| Key architecture statement | Fabric IQ combines ontology, semantic models, data agents and graph as the business-semantics layer of Microsoft IQ. |
| Implementation relevance | Preview-flagged patterns 2 and 3; simulated offline; never required by the default demo. |
| Security implications | Identity-delegated access; same-tenant requirements for Foundry integration. |
| Limitations | Preview; behavior may change. |
| Fallback | Local semantic YAML (ontology analog). |
| Deprecation / replacement | — |

## Microsoft Agent Framework

<a id="agent-framework"></a>

### Microsoft Agent Framework overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/agent-framework/overview/ |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06, P08, P13 |
| Key architecture statement | Successor to Semantic Kernel and AutoGen with agents, graph workflows, checkpointing, tool approval, MCP client support and OpenTelemetry. |
| Implementation relevance | Orchestration runtime for live and local agent paths (agent-framework-core 1.20.0). |
| Security implications | Tool approval enables human-in-the-loop for high-impact actions. |
| Limitations | agent-framework-azure-ai is a stale release candidate; use agent-framework-foundry. |
| Fallback | Same framework with a deterministic local chat client. |
| Deprecation / replacement | — |

## Microsoft Fabric

<a id="fabric-ai-functions"></a>

### AI functions in Fabric

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-science/ai-functions/overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-07-21 |
| Status | GA |
| Associated patterns | P05 |
| Key architecture statement | ai.classify, ai.extract, ai.summarize and related functions run in pandas, PySpark, T-SQL and Dataflow Gen2, optionally using Foundry models. |
| Implementation relevance | Pattern 5 (AI in data engineering rather than interactive agents). |
| Security implications | Requires tenant switches for Copilot/Azure OpenAI; prompts and data are not logged per documentation. |
| Limitations | Requires paid capacity (F2 or higher). |
| Fallback | Deterministic local enrichment, labeled SIMULATED. |
| Deprecation / replacement | — |

<a id="fabric-deployment-patterns"></a>

### Microsoft Fabric deployment patterns

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/architecture/data-guide/technology-choices/fabric-deployment-patterns |
| Publisher | Azure Architecture Center |
| Retrieved | 2026-10-05 |
| Last updated | 2026-04-20 |
| Status | GUIDANCE |
| Associated patterns | P14, P18 |
| Key architecture statement | Four-level hierarchy (tenant, capacity, workspace, item) determines isolation and governance choices. |
| Implementation relevance | Drives environment separation (dev/test/prod workspaces) and customer overlay design. |
| Security implications | Workspace-level isolation is the primary blast-radius control for agentic changes. |
| Limitations | Guidance only. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="fabric-direct-lake"></a>

### Direct Lake overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-02 |
| Status | GA |
| Associated patterns | P12 |
| Key architecture statement | Direct Lake on OneLake (no DirectQuery fallback, composite-capable) and Direct Lake on SQL analytics endpoint (DirectLakeBehavior controls fallback). |
| Implementation relevance | Semantic model storage-mode comparison and role-playing dimension options in Pattern 12. |
| Security implications | Direct Lake on SQL falls back to DirectQuery when SQL RLS/OLS/DDM is present; identity mode affects shortcut authorization. |
| Limitations | Adding multiple tables from the same source table is not supported through the standard UI. |
| Fallback | Local semantic YAML and PBIP/TMDL reference model. |
| Deprecation / replacement | — |

<a id="fabric-git-integration"></a>

### Fabric Git integration overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-01 |
| Status | GA |
| Associated patterns | P11, P20 |
| Key architecture statement | Git stores item definitions and metadata, never table data; some item types remain preview. |
| Implementation relevance | Basis for repo-first agentic change (Pattern 20) and the Git-versus-data-backup lesson. |
| Security implications | From 2026-12-01 users without read-write item permission lose Git integration access. |
| Limitations | Cloud-hosted Azure DevOps/GitHub only; per-item-type support varies. |
| Fallback | Local fabric/workspace definitions and dry-run deployment plans. |
| Deprecation / replacement | — |

<a id="fabric-medallion"></a>

### Implement medallion lakehouse architecture in Microsoft Fabric

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-02-12 |
| Status | GUIDANCE |
| Associated patterns | P10 |
| Key architecture statement | Medallion (bronze, silver, gold) is the recommended design approach for Fabric lakehouses. |
| Implementation relevance | Defines the raw/bronze/silver/gold/semantic layering used by the synthetic dataset and labs. |
| Security implications | Layer separation supports least-privilege access (e.g., analysts read gold only). |
| Limitations | Guidance, not an enforced product feature. |
| Fallback | Local medallion pipeline over Parquet/DuckDB. |
| Deprecation / replacement | — |

<a id="fabric-open-mirroring-format"></a>

### Open mirroring landing zone requirements and format

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/mirroring/open-mirroring-landing-zone-format |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2026-02-03 |
| Status | GA |
| Associated patterns | P11 |
| Key architecture statement | Landing zone uses _metadata.json keyColumns, 20-digit continuous file names and a trailing __rowMarker__ column (0 insert with no duplicate-key check, 1 update, 2 delete, 4 upsert); processed files are purged after 7 days. |
| Implementation relevance | Local Open Mirroring simulation (ffia recovery run) reproduces this documented format and row-marker semantics. |
| Security implications | Mirroring does not propagate source RLS/OLS/dynamic data masking. |
| Limitations | Schema changes require recreating the table folder; mirroring is not documented as a backup/DR mechanism. |
| Fallback | Local landing-zone simulation and recovery lab. |
| Deprecation / replacement | — |

<a id="fabric-overview"></a>

### What is Microsoft Fabric?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/fundamentals/microsoft-fabric-overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-03-18 |
| Status | GA |
| Associated patterns | P06, P10 |
| Key architecture statement | SaaS analytics platform for end-to-end data workflows that uses OneLake as a single logical data lake. |
| Implementation relevance | Fabric is the governed-context layer of the reference architecture. |
| Security implications | Tenant, capacity, workspace and item boundaries drive authorization; Entra ID authenticates all access. |
| Limitations | Requires a Fabric capacity for most workloads; features vary by region and SKU. |
| Fallback | Local Fabric Educational Provider (synthetic, clearly labeled SIMULATED). |
| Deprecation / replacement | — |

<a id="fabric-rest-identity"></a>

### Fabric REST API identity support

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/articles/identity-support |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06, P09 |
| Key architecture statement | Fabric REST APIs accept user, service principal and managed identity tokens, gated by tenant settings and per-API support. |
| Implementation relevance | Live Fabric provider uses a thin typed httpx client over the GA REST API (no GA Python SDK exists). |
| Security implications | Service-principal access requires an admin tenant switch; least-privilege workspace roles apply. |
| Limitations | Per-API identity support varies; long-running operations require polling. |
| Fallback | Local Fabric provider. |
| Deprecation / replacement | — |

<a id="fabric-waf"></a>

### Azure Well-Architected Framework service guide for Microsoft Fabric

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/well-architected/microsoft-fabric/overview |
| Publisher | Microsoft Learn (Well-Architected Framework) |
| Retrieved | 2026-10-05 |
| Last updated | 2026-05-13 |
| Status | GUIDANCE |
| Associated patterns | P06, P14 |
| Key architecture statement | Pillar guidance (reliability, security, cost, operations, performance) for Fabric workloads. |
| Implementation relevance | Production-readiness notes in every pattern map to these pillars. |
| Security implications | Security pillar guidance on identity, network isolation and data protection. |
| Limitations | Guidance only. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

## Microsoft Foundry

<a id="baseline-foundry-chat"></a>

### Baseline Microsoft Foundry chat reference architecture

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat |
| Publisher | Azure Architecture Center |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P14 |
| Key architecture statement | Private endpoints, App Service front end, Agent Service and monitoring form the production baseline. |
| Implementation relevance | Pattern 14 (secure enterprise) and production notes. |
| Security implications | Private networking and identity-based access are primary controls. |
| Limitations | Guidance only. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="foundry-agent-service"></a>

### Foundry Agent Service overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06, P08 |
| Key architecture statement | Managed platform for prompt agents and hosted agents built on the Responses API, with tool catalogs and toolboxes. |
| Implementation relevance | Live agent provider; MCP tool require_approval and allowed_tools support governed tool use. |
| Security implications | Agent identity in Entra; MCP tool output must be treated as untrusted input. |
| Limitations | Several tools (Fabric data agent, Fabric IQ, Browser Automation) are preview. |
| Fallback | Local Agent Framework runtime with deterministic client. |
| Deprecation / replacement | — |

<a id="foundry-evaluators"></a>

### Built-in evaluators in Microsoft Foundry

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/concepts/built-in-evaluators |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P16 |
| Key architecture statement | Quality, tool-use, agent-behavior and safety evaluators; several agent evaluators are preview. |
| Implementation relevance | Cloud evaluation option complementing deterministic local evaluation gates. |
| Security implications | Safety evaluators support responsible AI release gates. |
| Limitations | Intent resolution and task adherence evaluators are preview. |
| Fallback | Deterministic local evaluators in CI. |
| Deprecation / replacement | — |

<a id="foundry-fabric-tool"></a>

### Use the Microsoft Fabric data agent tool in Foundry Agent Service

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-14 |
| Status | PREVIEW |
| Associated patterns | P01, P02 |
| Key architecture statement | Foundry agents call a Fabric data agent using identity passthrough (on-behalf-of) of the end user. |
| Implementation relevance | Pattern 1 live path, preview-flagged. |
| Security implications | User identity only (no service principal); responses may leave the Fabric compliance boundary. |
| Limitations | Same tenant; data agent and sources in the same region; one Fabric data agent per Foundry agent. |
| Fallback | Local data agent simulation; Fabric data agent MCP endpoint as alternative live path. |
| Deprecation / replacement | — |

<a id="foundry-iq"></a>

### What is Foundry IQ?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | PREVIEW |
| Associated patterns | P04 |
| Key architecture statement | Knowledge bases built on Azure AI Search agentic retrieval over sources such as Blob, SharePoint, OneLake and web, with citations. |
| Implementation relevance | Unstructured knowledge retrieval (Pattern 4), contrasted with structured Fabric context. |
| Security implications | OneLake knowledge source indexes with the search service managed identity, not end-user passthrough. |
| Limitations | Mixed GA/preview by API version; portal experience preview. |
| Fallback | Local retrieval over synthetic documents with citations. |
| Deprecation / replacement | — |

<a id="foundry-overview"></a>

### What is Microsoft Foundry?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/what-is-foundry |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06 |
| Key architecture statement | A Foundry resource with child projects unifies models, agents and tools under one RBAC, networking and policy boundary. |
| Implementation relevance | Foundry is the reasoning, orchestration, evaluation and action layer. |
| Security implications | Managed identity and Entra RBAC per project; private networking supported. |
| Limitations | Hub-based (classic) projects are legacy. |
| Fallback | Local deterministic agent runtime, labeled SIMULATED. |
| Deprecation / replacement | Classic hub-based agents retire 2027-03-31; use Foundry Agent Service on new projects. |

## Model Context Protocol

<a id="fabric-dw-mcp"></a>

### Fabric Data Warehouse MCP server (Preview)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-warehouse/data-warehouse-mcp-server |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-06-16 |
| Status | PREVIEW |
| Associated patterns | P09 |
| Key architecture statement | Remote server exposing a single T-SQL execution tool against a warehouse or SQL analytics endpoint. |
| Implementation relevance | Teaching contrast for governed MCP; excluded from default agent configuration. |
| Security implications | Arbitrary T-SQL under the caller's identity; use read-only roles in dev workspaces only. |
| Limitations | Preview. |
| Fallback | Local allow-listed queries over DuckDB. |
| Deprecation / replacement | — |

<a id="fabric-iq-mcp"></a>

### Get started with Fabric IQ MCP

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-14 |
| Status | GA |
| Associated patterns | P12, P09 |
| Key architecture statement | Remote, read-only MCP for discovering and querying semantic models with RLS/OLS enforced for the delegated user. |
| Implementation relevance | Preferred live semantic-model consumption path. |
| Security implications | Delegated OAuth; caller permissions enforced. |
| Limitations | Read-only; the client composes DAX. |
| Fallback | Local semantic YAML measures over DuckDB. |
| Deprecation / replacement | — |

<a id="fabric-mcp-local"></a>

### Fabric MCP Server (local) tools reference

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/pro-dev-local/tools-local-mcp-server |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-15 |
| Status | GA |
| Associated patterns | P09, P19 |
| Key architecture statement | Local stdio server with offline docs/schema/best-practice tools plus OneLake, core and Data Factory tools; npm @microsoft/fabric-mcp 1.4.0 (2026-08-27). |
| Implementation relevance | Primary developer-time server; docs tools give genuine grounding without a tenant. |
| Security implications | OneLake write/delete and pipeline run tools exist; restrict with tool allow-lists. |
| Limitations | Live tools require Azure CLI/Entra credentials; credential selector behavior is version-specific. |
| Fallback | Local FastMCP equivalents (SIMULATED). |
| Deprecation / replacement | — |

<a id="fabric-mcp-servers-list"></a>

### Choose a Microsoft Fabric MCP server

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/articles/mcp-servers/fabric-mcp-servers-list |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | 2026-09-15 |
| Status | GUIDANCE |
| Associated patterns | P09, P19 |
| Key architecture statement | Thirteen distinct Fabric-related MCP servers (remote and local) with different purposes; they must not be conflated. |
| Implementation relevance | MCP topology and per-job server selection (narrowest server and tool set). |
| Security implications | Each server runs with the caller's permissions; several expose write tools. |
| Limitations | The directory page carries no per-server status column; status comes from each server's page. |
| Fallback | Local FastMCP educational server. |
| Deprecation / replacement | — |

<a id="mcp-specification"></a>

### Model Context Protocol specification versioning

| Field | Value |
|---|---|
| URL | https://modelcontextprotocol.io/specification/versioning |
| Publisher | Model Context Protocol project |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P09 |
| Key architecture statement | Current specification version 2026-07-28; authorization builds on OAuth 2.1 with servers as resource servers. |
| Implementation relevance | FastMCP 4.0.11 (mcp 2.3.0) reports protocol 2026-07-28. |
| Security implications | MCP standardizes capability access; it does not grant authorization. |
| Limitations | Some Microsoft servers do not support dynamic client registration. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="powerbi-authoring-mcp"></a>

### Power BI Authoring (Modeling) MCP server

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | P12 |
| Key architecture statement | Local server (GA, npm @microsoft/powerbi-modeling-mcp 1.0.0) and hosted deployment (preview) for semantic model authoring. |
| Implementation relevance | Semantic model authoring labs on PBIP/TMDL and Guide HC-01. |
| Security implications | Read/write; back up models first; metadata may appear in chat logs. |
| Limitations | Hosted deployment is preview; local deployment reaches Power BI Desktop (Windows) and PBIP files. |
| Fallback | Reference TMDL and local PBIR validation. |
| Deprecation / replacement | — |

## Toolchain

<a id="node-release-schedule"></a>

### Node.js release schedule

| Field | Value |
|---|---|
| URL | https://github.com/nodejs/Release |
| Publisher | Node.js project |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | — |
| Key architecture statement | Node 24 is Active LTS until maintenance on 2026-10-20; Node 26 becomes LTS on 2026-10-28. |
| Implementation relevance | Frontend and MCP servers target Node 24 now, with Node 26 in the CI matrix. |
| Security implications | LTS lines receive security releases. |
| Limitations | Plan the default switch to Node 26 after 2026-10-28. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="python-lifecycle"></a>

### Status of Python versions

| Field | Value |
|---|---|
| URL | https://devguide.python.org/versions/ |
| Publisher | Python Software Foundation |
| Retrieved | 2026-10-05 |
| Last updated | — |
| Status | GA |
| Associated patterns | — |
| Key architecture statement | Python 3.14 is in bugfix support until 2027-10; 3.13 moved to security-only support on 2026-10-01. |
| Implementation relevance | Project targets Python 3.14 (requires-python >=3.14,<3.15). |
| Security implications | Bugfix-supported runtime receives timely fixes. |
| Limitations | Some Fabric tools (fabric-cicd, ms-fabric-cli, fabric-data-agent-sdk) declare Python below 3.14 and run as isolated tools. |
| Fallback | Python 3.13 validated as an alternative. |
| Deprecation / replacement | — |
