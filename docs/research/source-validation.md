# Source validation

<!-- GENERATED FILE: edit docs/research/sources.yaml, then run `uv run ffia sources render`. -->

Official product documentation overrides older samples. Community content never
overrides authoritative product documentation. Status values: GA, PREVIEW,
DEPRECATED, UNKNOWN/NEEDS VALIDATION, GUIDANCE (architecture guidance), OSS
(official open-source project without a product lifecycle label).

## Summary

| Technology | Source | Status | Retrieved |
|---|---|---|---|
| AI agents | [AI agent orchestration patterns](#ai-agent-orchestration) | GUIDANCE | 2026-10-07 |
| Azure API Management | [Overview of MCP servers in Azure API Management](#apim-mcp) | GA | 2026-10-05 |
| Azure Logic Apps | [Automate Microsoft Foundry agents with workflows in Azure Logic Apps](#logic-apps-foundry-agents) | PREVIEW | 2026-10-08 |
| Azure Monitor | [Enable OpenTelemetry in Application Insights (Azure Monitor OpenTelemetry Distro)](#azure-monitor-opentelemetry) | GA | 2026-10-08 |
| Developer experience | [How Claude remembers your project (CLAUDE.md and AGENTS.md)](#claude-code-memory) | GA | 2026-10-05 |
| Developer experience | [Extend Claude with skills](#claude-code-skills) | GA | 2026-10-05 |
| Developer experience | [GitHub Copilot CLI is now generally available](#copilot-cli-ga) | GA | 2026-10-05 |
| Developer experience | [Support for different types of custom instructions](#copilot-instructions-support) | GA | 2026-10-05 |
| Developer experience | [Skills for Fabric overview](#skills-for-fabric) | OSS | 2026-10-05 |
| Developer experience | [Add and manage MCP servers in VS Code](#vscode-mcp-servers) | GA | 2026-10-05 |
| Fabric IQ and Data Agents | [Fabric data agent concepts](#fabric-data-agent) | GA | 2026-10-05 |
| Fabric IQ and Data Agents | [Ontology overview (Fabric IQ)](#fabric-iq-ontology) | PREVIEW | 2026-10-05 |
| Fabric IQ and Data Agents | [What is Fabric IQ?](#fabric-iq-overview) | PREVIEW | 2026-10-05 |
| GitHub CodeQL | [Workflow configuration options for code scanning](#github-codeql-configuration) | GUIDANCE | 2026-10-09 |
| Microsoft Agent 365 | [Overview of Microsoft Agent 365](#agent-365) | GA | 2026-10-08 |
| Microsoft Agent Framework | [Microsoft Agent Framework overview](#agent-framework) | GA | 2026-10-08 |
| Microsoft Agent Framework | [Microsoft Agent Framework workflow capabilities](#agent-framework-workflows) | GA | 2026-10-08 |
| Microsoft Fabric | [What is Fabric Activator?](#fabric-activator) | GA | 2026-10-08 |
| Microsoft Fabric | [Tenants - List Tenant Settings (Fabric Admin REST API)](#fabric-admin-tenant-settings) | GA | 2026-10-07 |
| Microsoft Fabric | [AI functions in Fabric](#fabric-ai-functions) | GA | 2026-10-05 |
| Microsoft Fabric | [Items - Create Lakehouse (Fabric REST API)](#fabric-create-lakehouse) | GA | 2026-10-07 |
| Microsoft Fabric | [Microsoft Fabric deployment patterns](#fabric-deployment-patterns) | GUIDANCE | 2026-10-05 |
| Microsoft Fabric | [Direct Lake overview](#fabric-direct-lake) | GA | 2026-10-05 |
| Microsoft Fabric | [Fabric Git integration overview](#fabric-git-integration) | GA | 2026-10-05 |
| Microsoft Fabric | [Tables - List Tables (Fabric REST API, Lakehouse)](#fabric-lakehouse-list-tables) | PREVIEW | 2026-10-07 |
| Microsoft Fabric | [Implement medallion lakehouse architecture in Microsoft Fabric](#fabric-medallion) | GUIDANCE | 2026-10-05 |
| Microsoft Fabric | [Notebook definition (Fabric REST API item definitions)](#fabric-notebook-definition) | GA | 2026-10-07 |
| Microsoft Fabric | [Open mirroring landing zone requirements and format](#fabric-open-mirroring-format) | GA | 2026-10-07 |
| Microsoft Fabric | [What is Microsoft Fabric?](#fabric-overview) | GA | 2026-10-05 |
| Microsoft Fabric | [Fabric REST API identity support](#fabric-rest-identity) | GA | 2026-10-05 |
| Microsoft Fabric | [Runtime 1.3 in Fabric](#fabric-runtime-1-3) | GA | 2026-10-07 |
| Microsoft Fabric | [Fabric trial capacity](#fabric-trial) | GA | 2026-10-07 |
| Microsoft Fabric | [Azure Well-Architected Framework service guide for Microsoft Fabric](#fabric-waf) | GUIDANCE | 2026-10-05 |
| Microsoft Fabric | [Data quality in materialized lake views](#mlv-data-quality) | GA | 2026-10-08 |
| Microsoft Fabric | [Detect, explore and validate functional dependencies in your data](#semantic-link-validate) | GA | 2026-10-08 |
| Microsoft Fabric and Microsoft Foundry | [Data architecture for AI agents across your organization](#caf-agent-data-architecture) | GUIDANCE | 2026-10-07 |
| Microsoft Foundry | [Baseline Microsoft Foundry chat reference architecture](#baseline-foundry-chat) | GUIDANCE | 2026-10-05 |
| Microsoft Foundry | [Baseline Microsoft Foundry chat reference architecture in an Azure landing zone](#baseline-foundry-landing-zone) | GUIDANCE | 2026-10-07 |
| Microsoft Foundry | [Basic Microsoft Foundry chat reference architecture](#basic-foundry-chat) | GUIDANCE | 2026-10-07 |
| Microsoft Foundry | [Foundry Agent Service FAQ (pricing)](#foundry-agent-faq) | GA | 2026-10-08 |
| Microsoft Foundry | [Agent identity concepts in Microsoft Foundry](#foundry-agent-identity) | GA | 2026-10-08 |
| Microsoft Foundry | [Foundry Agent Service overview](#foundry-agent-service) | GA | 2026-10-05 |
| Microsoft Foundry | [Use Grounding with Bing Search tools with the agents API](#foundry-bing-grounding) | GA | 2026-10-08 |
| Microsoft Foundry | [Built-in evaluators in Microsoft Foundry](#foundry-evaluators) | GA | 2026-10-05 |
| Microsoft Foundry | [Use the Microsoft Fabric data agent tool in Foundry Agent Service](#foundry-fabric-tool) | PREVIEW | 2026-10-05 |
| Microsoft Foundry | [Add a human-in-the-loop approval step](#foundry-human-in-the-loop) | PREVIEW | 2026-10-08 |
| Microsoft Foundry | [What is Foundry IQ?](#foundry-iq) | PREVIEW | 2026-10-08 |
| Microsoft Foundry | [Govern MCP tools by using an AI gateway (Microsoft Foundry)](#foundry-mcp-governance) | PREVIEW | 2026-10-07 |
| Microsoft Foundry | [What is Microsoft Foundry?](#foundry-overview) | GA | 2026-10-05 |
| Microsoft Foundry | [Set up private networking for Foundry Agent Service](#foundry-private-networking) | GA | 2026-10-08 |
| Microsoft Foundry | [Routines in Foundry Agent Service](#foundry-routines) | UNKNOWN/NEEDS VALIDATION | 2026-10-08 |
| Microsoft Foundry | [What is Toolbox in Microsoft Foundry?](#foundry-toolbox) | GA | 2026-10-08 |
| Microsoft Foundry | [Use web search tool in Foundry Agent Service](#foundry-web-search) | GA | 2026-10-08 |
| Microsoft Purview | [Data quality supported sources (Microsoft Purview Unified Catalog)](#purview-data-quality) | UNKNOWN/NEEDS VALIDATION | 2026-10-08 |
| Model Context Protocol | [Fabric Data Warehouse MCP server (Preview)](#fabric-dw-mcp) | PREVIEW | 2026-10-05 |
| Model Context Protocol | [Get started with Fabric IQ MCP](#fabric-iq-mcp) | GA | 2026-10-05 |
| Model Context Protocol | [Fabric MCP Server (local) tools reference](#fabric-mcp-local) | GA | 2026-10-05 |
| Model Context Protocol | [Choose a Microsoft Fabric MCP server](#fabric-mcp-servers-list) | GUIDANCE | 2026-10-05 |
| Model Context Protocol | [Model Context Protocol specification versioning](#mcp-specification) | GA | 2026-10-05 |
| Model Context Protocol | [Power BI Authoring (Modeling) MCP server](#powerbi-authoring-mcp) | GA | 2026-10-05 |
| Power BI | [Datasets - Execute Queries In Group (Power BI REST API)](#powerbi-execute-queries) | GA | 2026-10-07 |
| Power BI | [Create report subscriptions with Copilot summaries](#powerbi-subscription-summaries) | PREVIEW | 2026-10-08 |
| Relational data foundations | [A relational model of data for large shared data banks](#research-relational-model) | GUIDANCE | 2026-10-09 |
| Retrieval and grounding foundations | [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](#research-rag) | GUIDANCE | 2026-10-09 |
| Spec-driven engineering | [Spec-Driven Development Quickstart](#spec-kit-quickstart) | OSS | 2026-10-09 |
| Tool-using agent foundations | [ReAct: Synergizing Reasoning and Acting in Language Models](#research-react) | GUIDANCE | 2026-10-09 |
| Toolchain | [Node.js release schedule](#node-release-schedule) | GA | 2026-10-05 |
| Toolchain | [Status of Python versions](#python-lifecycle) | GA | 2026-10-05 |
| Transformer foundations | [Attention Is All You Need](#research-transformers) | GUIDANCE | 2026-10-09 |

## AI agents

<a id="ai-agent-orchestration"></a>

### AI agent orchestration patterns

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/architecture/ai-ml/guide/ai-agent-design-patterns |
| Publisher | Azure Architecture Center |
| Retrieved | 2026-10-07 |
| Last updated | 2026-02-12 |
| Status | GUIDANCE |
| Associated patterns | P02, P13 |
| Key architecture statement | Use the lowest complexity that works - a direct model call, a single agent with tools, then multi-agent orchestration (sequential, concurrent, group chat, handoff, magentic). |
| Implementation relevance | Pattern 13 (multi-domain is not multi-agent) and orchestration choices in Foundry lessons. |
| Security implications | More agents mean more tool surfaces and identities to govern. |
| Limitations | Guidance only. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

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

## Azure Logic Apps

<a id="logic-apps-foundry-agents"></a>

### Automate Microsoft Foundry agents with workflows in Azure Logic Apps

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/logic-apps/automate-foundry-agents-with-workflows |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-08-13 |
| Status | PREVIEW |
| Associated patterns | P06 |
| Key architecture statement | Standard Logic Apps workflows can call Foundry agents; combine with the Recurrence trigger and Teams/Outlook connectors. |
| Implementation relevance | Monthly insights: schedule and deliver. |
| Security implications | Connections use managed identity; scope mailbox and Teams permissions. |
| Limitations | Preview; Standard tier. |
| Fallback | Azure Functions timer trigger (GA) calling the Foundry SDK. |
| Deprecation / replacement | — |

## Azure Monitor

<a id="azure-monitor-opentelemetry"></a>

### Enable OpenTelemetry in Application Insights (Azure Monitor OpenTelemetry Distro)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-enable |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | GA |
| Associated patterns | P16 |
| Key architecture statement | The Azure Monitor OpenTelemetry Distro sends OpenTelemetry traces, metrics and logs to Application Insights using a connection string. |
| Implementation relevance | Opt-in export of the ffia.agent.ask spans when FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING is set. |
| Security implications | The connection string is a secret (local .env only); spans never record question text. |
| Limitations | The distro pulls beta instrumentation packages; only the span API is used directly. |
| Fallback | Spans stay in-process (no exporter) when no connection string is set. |
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

## GitHub CodeQL

<a id="github-codeql-configuration"></a>

### Workflow configuration options for code scanning

| Field | Value |
|---|---|
| URL | https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options |
| Publisher | GitHub Docs |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P08, P09 |
| Key architecture statement | Advanced code scanning workflows support push, pull request and scheduled analysis with language-specific configuration. |
| Implementation relevance | Two-language CodeQL workflow complements deterministic offline quality and evaluation release gates. |
| Security implications | Scope security-events write to analysis jobs and protect publication through reviewed release artifacts. |
| Limitations | Workflow configuration is not evidence of a completed scan or zero alerts; repository code-scanning availability and branch protections need operator verification. |
| Fallback | Local lint, strict types, tests, dependency audits and privacy scan; not equivalent to CodeQL. |
| Deprecation / replacement | — |

## Microsoft Agent 365

<a id="agent-365"></a>

### Overview of Microsoft Agent 365

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/microsoft-agent-365/overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | GA |
| Associated patterns | P14 |
| Key architecture statement | A governance and security control plane for AI agents: registry, Entra-based access, Purview and Defender integration; generally available since May 1, 2026, licensed per user. |
| Implementation relevance | Governance and licensing questions at enterprise scale. |
| Security implications | Central inventory and policy for agents. |
| Limitations | Per-user licensing; works best with Microsoft 365 E5. |
| Fallback | Not used in the offline demo. |
| Deprecation / replacement | — |

## Microsoft Agent Framework

<a id="agent-framework"></a>

### Microsoft Agent Framework overview

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/agent-framework/overview/ |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06, P08, P13 |
| Key architecture statement | Successor to Semantic Kernel and AutoGen with agents, graph workflows, checkpointing, tool approval, MCP client support and OpenTelemetry. |
| Implementation relevance | agent-framework-core 1.21.0 runs the monthly-insights workflow; Foundry calls stay in the azure-ai-projects provider (ADR-0013). |
| Security implications | Tool approval enables human-in-the-loop for high-impact actions. |
| Limitations | agent-framework-foundry 1.14.1 requires azure-ai-projects<2.8.0 and the pre-release azure-ai-inference 1.0.0b9, so it is not used; agent-framework-azure-ai is a stale release candidate. |
| Fallback | The same workflow over the deterministic LOCAL agent. |
| Deprecation / replacement | — |

<a id="agent-framework-workflows"></a>

### Microsoft Agent Framework workflow capabilities

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/agent-framework/workflows/ |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06, P08, P16 |
| Key architecture statement | Graph workflows of executors and edges, with agents as participants, human-in-the-loop pauses, checkpoints and observability. |
| Implementation relevance | The monthly-insights workflow fans out one drafting executor per team and ends in a deterministic review gate. |
| Security implications | A workflow orchestrates; it does not authorize. Delivery remains a governed write. |
| Limitations | Checkpointing and human-in-the-loop pauses are not used yet; approval runs through the change flow. |
| Fallback | Run the same executors over the LOCAL agent offline. |
| Deprecation / replacement | — |

## Microsoft Fabric

<a id="fabric-activator"></a>

### What is Fabric Activator?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-introduction |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-04-17 |
| Status | GA |
| Associated patterns | P07 |
| Key architecture statement | No-code rules on semantic models and eventstreams trigger email, Teams messages, pipelines or Power Automate flows. |
| Implementation relevance | Monthly insights alternative: threshold alerts between briefs. |
| Security implications | Rules run under the creator's permissions. |
| Limitations | Event-driven, not calendar-driven. |
| Fallback | Local brief only. |
| Deprecation / replacement | — |

<a id="fabric-admin-tenant-settings"></a>

### Tenants - List Tenant Settings (Fabric Admin REST API)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/admin/tenants/list-tenant-settings |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | — |
| Status | GA |
| Associated patterns | P09 |
| Key architecture statement | Returns tenant settings (settingName, title, enabled, security groups) in a value array with continuation; requires Tenant.Read.All and a Fabric administrator. |
| Implementation relevance | ffia fabric readiness reads it to confirm the settings the labs rely on, matching by name or portal title. |
| Security implications | Admin-only read; non-admins get a SKIPPED readiness check rather than a guess. |
| Limitations | Setting names are not published as a stable catalog; titles can change. |
| Fallback | Manual confirmation in the Fabric admin portal. |
| Deprecation / replacement | — |

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

<a id="fabric-create-lakehouse"></a>

### Items - Create Lakehouse (Fabric REST API)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/lakehouse/items/create-lakehouse |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2026-10-05 |
| Status | GA |
| Associated patterns | P08, P20 |
| Key architecture statement | Creates a lakehouse in a workspace; supports long-running operations; requires a contributor workspace role and Lakehouse.ReadWrite.All or Item.ReadWrite.All. |
| Implementation relevance | One of the two operations of the gated scoped writer (create_lakehouse), with live duplicate re-check and verification. |
| Security implications | Contributor role is broader than the single operation; the accelerator narrows it with policy, approval and a bound dev workspace. |
| Limitations | Display names must be unique per workspace and type; 202 responses must be polled. |
| Fallback | LOCAL simulated change flow; LIVE requests are refused, never redirected, without a writer. |
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

<a id="fabric-lakehouse-list-tables"></a>

### Tables - List Tables (Fabric REST API, Lakehouse)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/list-tables |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | — |
| Status | PREVIEW |
| Associated patterns | P10 |
| Key architecture statement | Lists lakehouse tables in a data array with continuationToken pagination; documented as preview and not recommended for production. |
| Implementation relevance | Live provider's list_tables; row counts and columns are not part of the response. |
| Security implications | Requires Lakehouse.Read.All or Lakehouse.ReadWrite.All. |
| Limitations | Preview API; schema-enabled lakehouses are not supported (use the Fabric MCP onelake_list-tables tool). |
| Fallback | Local lakehouse tables (LOCAL) in HYBRID mode. |
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

<a id="fabric-notebook-definition"></a>

### Notebook definition (Fabric REST API item definitions)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/notebook-definition |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2025-07-02 |
| Status | GA |
| Associated patterns | P10, P20 |
| Key architecture statement | Notebook definitions use the fabricGitSource (default) or ipynb format; a PySpark notebook is one notebook-content.py part plus an optional .platform part, each InlineBase64. |
| Implementation relevance | Format of the committed reference notebooks under fabric/workspace/ and of the scoped writer's create-notebook request. |
| Security implications | A definition is code that runs with the caller's Spark identity; only reviewed, committed definitions are published. |
| Limitations | The default lakehouse binding lives in notebook metadata; the reference notebooks leave it empty so no IDs are committed. |
| Fallback | Local rendering and a local Spark 3.5 run of the same notebook code. |
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

<a id="fabric-runtime-1-3"></a>

### Runtime 1.3 in Fabric

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-engineering/runtime-1-3 |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2026-09-18 |
| Status | GA |
| Associated patterns | P10 |
| Key architecture statement | Runtime 1.3 runs Apache Spark 3.5, Java 11, Scala 2.12, Python 3.11 and Delta Lake 3.2. |
| Implementation relevance | The reference notebooks are verified locally on Apache Spark 3.5.9 (Java 17), the same Spark line as Runtime 1.3. |
| Security implications | Notebook code runs with the caller's identity on the workspace capacity. |
| Limitations | A local Spark run is LOCAL evidence only; Delta, OneLake paths and capacity behavior require tenant validation. |
| Fallback | Local DuckDB build of the same SQL. |
| Deprecation / replacement | — |

<a id="fabric-trial"></a>

### Fabric trial capacity

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/fundamentals/fabric-trial |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2026-09-29 |
| Status | GA |
| Associated patterns | P10 |
| Key architecture statement | A Fabric trial capacity gives free access for 60 days to most Fabric workloads; it is started from the account manager in the Fabric portal. |
| Implementation relevance | Fastest path to make a demo tenant ready for the live labs (see docs/operations/fabric-tenant-readiness.md). |
| Security implications | Trial capacity is per user; assign a dedicated dev workspace to it. |
| Limitations | Time-limited; some features and regions differ from paid F SKUs. |
| Fallback | An F2+ capacity in an Azure subscription of the tenant. |
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

<a id="mlv-data-quality"></a>

### Data quality in materialized lake views

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views/data-quality |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-03-18 |
| Status | GA |
| Associated patterns | P10 |
| Key architecture statement | Materialized lake views support CONSTRAINT ... CHECK rules that drop or fail rows on mismatch. |
| Implementation relevance | Data-quality question: enforce rules in Silver. |
| Security implications | Rules run in the lakehouse under workspace permissions. |
| Limitations | Spark SQL only. |
| Fallback | Local Silver data-quality flags. |
| Deprecation / replacement | — |

<a id="semantic-link-validate"></a>

### Detect, explore and validate functional dependencies in your data

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/fabric/data-science/semantic-link-validate-data |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-03-03 |
| Status | GA |
| Associated patterns | P10, P12 |
| Key architecture statement | Semantic Link functions such as find_dependencies and list_relationship_violations validate data against a semantic model's relationships. |
| Implementation relevance | Data-quality question: detect issues behind a semantic model. |
| Security implications | Runs in Fabric notebooks with the user's permissions. |
| Limitations | Detection only; fixes happen upstream. |
| Fallback | Local DuckDB data-quality flags (ffia mfg quality). |
| Deprecation / replacement | — |

## Microsoft Fabric and Microsoft Foundry

<a id="caf-agent-data-architecture"></a>

### Data architecture for AI agents across your organization

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/data-architecture-plan |
| Publisher | Cloud Adoption Framework |
| Retrieved | 2026-10-07 |
| Last updated | 2025-12-01 |
| Status | GUIDANCE |
| Associated patterns | P01, P02, P06 |
| Key architecture statement | OneLake is the central governed data lake for data products; agents consume them through Fabric IQ, Foundry IQ and Copilot Studio, inside an Azure landing zone. |
| Implementation relevance | The closest first-party guidance combining Fabric and Foundry; the reference architecture follows its framing. |
| Security implications | Prefer built-in retrieval before custom MCP servers; govern data products per domain. |
| Limitations | Conceptual guidance, not a deployable reference architecture. |
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

<a id="baseline-foundry-landing-zone"></a>

### Baseline Microsoft Foundry chat reference architecture in an Azure landing zone

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone |
| Publisher | Azure Architecture Center |
| Retrieved | 2026-10-07 |
| Last updated | 2026-06-17 |
| Status | GUIDANCE |
| Associated patterns | P14 |
| Key architecture statement | Splits the baseline between a workload landing zone and a platform landing zone (hub network, firewall, connectivity). |
| Implementation relevance | Production deployment view and operating-model notes for platform versus workload teams. |
| Security implications | Egress and connectivity are owned by the platform team; the workload team owns application resources. |
| Limitations | Guidance only. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="basic-foundry-chat"></a>

### Basic Microsoft Foundry chat reference architecture

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/architecture/ai-ml/architecture/basic-microsoft-foundry-chat |
| Publisher | Azure Architecture Center |
| Retrieved | 2026-10-07 |
| Last updated | 2026-06-17 |
| Status | GUIDANCE |
| Associated patterns | P06, P17 |
| Key architecture statement | Introductory, not-for-production chat architecture that uses identity as its perimeter (App Service with Easy Auth, Foundry Agent Service, AI Search, Application Insights). |
| Implementation relevance | The local accelerator corresponds to this proof-of-concept tier; production diagrams follow the baseline. |
| Security implications | No network isolation or egress control; the article itself defers those to the baseline. |
| Limitations | Explicitly not for production. |
| Fallback | Not applicable. |
| Deprecation / replacement | — |

<a id="foundry-agent-faq"></a>

### Foundry Agent Service FAQ (pricing)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/faq |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | GA |
| Associated patterns | P06 |
| Key architecture statement | There is no separate Foundry license; Agent Service orchestration is not separately charged; you pay for model tokens and specific tools. |
| Implementation relevance | Licensing question. |
| Security implications | Cost governance through quotas, budgets and an AI gateway. |
| Limitations | Tool charges (Bing grounding, file search storage, code interpreter sessions) vary by region. |
| Fallback | Offline demo costs nothing. |
| Deprecation / replacement | — |

<a id="foundry-agent-identity"></a>

### Agent identity concepts in Microsoft Foundry

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-09-24 |
| Status | GA |
| Associated patterns | P14 |
| Key architecture statement | Foundry integrates with Microsoft Entra Agent ID, provisioning agent identities that are governed, authenticated and authorized like other Entra identities. |
| Implementation relevance | Security segment: who the agent is. |
| Security implications | Grant agent identities least-privilege RBAC on target resources. |
| Limitations | Tools such as the Fabric data agent use the end user's identity instead. |
| Fallback | Local process identity (offline). |
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

<a id="foundry-bing-grounding"></a>

### Use Grounding with Bing Search tools with the agents API

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/tools/bing-tools |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-08-27 |
| Status | GA |
| Associated patterns | P06, P14 |
| Key architecture statement | Grounding with Bing Search returns public web search results with citations; Bing Custom Search (preview) restricts results to configured domains. |
| Implementation relevance | Answers the external-data question: search grounding with citations, not crawling or scraping. |
| Security implications | Queries and the resource key leave the Azure compliance and geo boundary; Bing terms of use and use-and-display requirements apply; the Data Protection Addendum does not apply. |
| Limitations | Separate Bing resource and per-transaction billing; results must show website and Bing query URLs. |
| Fallback | Curated public data loaded into Fabric through a reviewed pipeline. |
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

<a id="foundry-human-in-the-loop"></a>

### Add a human-in-the-loop approval step

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/add-human-in-the-loop |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-08-05 |
| Status | PREVIEW |
| Associated patterns | P08 |
| Key architecture statement | Pause an agent workflow until a person approves, then resume. |
| Implementation relevance | Data-quality fixes need approval. |
| Security implications | Approval is a control, not a replacement for authorization. |
| Limitations | Preview. |
| Fallback | Accelerator change flow: plan, approve, execute, verify. |
| Deprecation / replacement | — |

<a id="foundry-iq"></a>

### What is Foundry IQ?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/concepts/what-is-foundry-iq |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | — |
| Status | PREVIEW |
| Associated patterns | P04 |
| Key architecture statement | Knowledge bases built on Azure AI Search agentic retrieval over sources such as Blob, SharePoint, OneLake and web, with citations. |
| Implementation relevance | Unstructured knowledge retrieval (Pattern 4), contrasted with structured Fabric context. Offline analog `ffia knowledge search` behind the preview flag foundry_iq_knowledge (SIMULATED, cited). |
| Security implications | OneLake knowledge source indexes with the search service managed identity, not end-user passthrough. |
| Limitations | Mixed GA/preview by API version; portal experience preview. |
| Fallback | Local keyword retrieval over synthetic policy documents with citations (data/synthetic/knowledge). |
| Deprecation / replacement | — |

<a id="foundry-mcp-governance"></a>

### Govern MCP tools by using an AI gateway (Microsoft Foundry)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/tools/governance |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2026-08-19 |
| Status | PREVIEW |
| Associated patterns | P09, P15 |
| Key architecture statement | The Foundry AI gateway for MCP tools is backed by an Azure API Management instance; policies such as rate limits and IP filtering are API Management policies. |
| Implementation relevance | Diagrams show one API Management-backed gateway for MCP tools rather than two separate gateways. |
| Security implications | Gateway policy adds central controls but does not replace authorization in the MCP server or data platform. |
| Limitations | Preview; applies only to new MCP tools created in the Foundry portal that do not use managed OAuth. |
| Fallback | Local rate limiting and audit in ffia-local. |
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

<a id="foundry-private-networking"></a>

### Set up private networking for Foundry Agent Service

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/virtual-networks |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-08-27 |
| Status | GA |
| Associated patterns | P14 |
| Key architecture statement | Standard agent setup supports subnet injection and private resource access, with bring-your-own Storage, Azure AI Search and Cosmos DB so agent data stays in your tenant. |
| Implementation relevance | Security segment: network isolation and data residency. |
| Security implications | Private endpoints and BYO resources keep agent state in the customer's tenant. |
| Limitations | Bing grounding still leaves the boundary by design. |
| Fallback | Basic setup for demos. |
| Deprecation / replacement | — |

<a id="foundry-routines"></a>

### Routines in Foundry Agent Service

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/concepts/routines |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-09-24 |
| Status | UNKNOWN/NEEDS VALIDATION |
| Associated patterns | P06 |
| Key architecture statement | Project-native triggers (schedule or cron, plus event triggers) invoke an agent without external orchestration. |
| Implementation relevance | Monthly insights: a Foundry-native schedule option. |
| Security implications | Runs under the configured identity; review what it can reach. |
| Limitations | Status not stated on the page; minimum 5-minute interval. |
| Fallback | Logic Apps Recurrence trigger (GA). |
| Deprecation / replacement | — |

<a id="foundry-toolbox"></a>

### What is Toolbox in Microsoft Foundry?

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/concepts/toolbox-overview |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-07-31 |
| Status | GA |
| Associated patterns | P06, P09 |
| Key architecture statement | Lists Foundry tools: MCP, web search, Azure AI Search, code interpreter, file search, OpenAPI, A2A, browser automation, Fabric IQ, Work IQ, SharePoint, Fabric data agent, Azure Functions, Grounding with Bing. |
| Implementation relevance | Catalog for the connecting-data segment. |
| Security implications | Each tool has its own identity and data-handling model; curate tools once and reuse them. |
| Limitations | Some tools are direct-only (Fabric data agent, SharePoint, Bing). |
| Fallback | Local MCP tools in ffia-local. |
| Deprecation / replacement | — |

<a id="foundry-web-search"></a>

### Use web search tool in Foundry Agent Service

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/azure/foundry/agents/how-to/tools/web-search |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-09-11 |
| Status | GA |
| Associated patterns | P06, P14 |
| Key architecture statement | The web search tool grounds agents in current web results through Grounding with Bing; domain-restricted search uses a Bing Custom Search connection. |
| Implementation relevance | Code-first example for the market-context agent. |
| Security implications | Same boundary as Bing grounding; external_web_access can be disabled. |
| Limitations | Requires Foundry User role; domain restriction needs a toolbox and project connection. |
| Fallback | Offline: cite a stored, approved public document instead. |
| Deprecation / replacement | — |

## Microsoft Purview

<a id="purview-data-quality"></a>

### Data quality supported sources (Microsoft Purview Unified Catalog)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/purview/unified-catalog-data-quality-supported-sources-file-formats |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-04-09 |
| Status | UNKNOWN/NEEDS VALIDATION |
| Associated patterns | P14 |
| Key architecture statement | Purview data quality supports profiling and scans for Fabric lakehouse Delta and Parquet tables. |
| Implementation relevance | Data-quality question: governed, catalog-level rules. |
| Security implications | Governance team owns rules and scores. |
| Limitations | Capability-level status not stated; Iceberg is preview. |
| Fallback | Local data-quality report. |
| Deprecation / replacement | — |

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

## Power BI

<a id="powerbi-execute-queries"></a>

### Datasets - Execute Queries In Group (Power BI REST API)

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/rest/api/power-bi/datasets/execute-queries-in-group |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-07 |
| Last updated | 2025-02-05 |
| Status | GA |
| Associated patterns | P10, P12 |
| Key architecture statement | Runs one DAX query per call against a semantic model; needs the Dataset Execute Queries REST API tenant setting and dataset read and build permissions. |
| Implementation relevance | Live provider evaluates each governed measure with EVALUATE ROW to reconcile the live model with the baseline. |
| Security implications | Respects the caller's permissions and row-level security; read-only. |
| Limitations | One query and one table per call; at most 100,000 rows or 1,000,000 values; models with live AAS connections unsupported. |
| Fallback | Local DuckDB measure evaluation (LOCAL). |
| Deprecation / replacement | — |

<a id="powerbi-subscription-summaries"></a>

### Create report subscriptions with Copilot summaries

| Field | Value |
|---|---|
| URL | https://learn.microsoft.com/power-bi/create-reports/copilot-summaries-in-subscriptions |
| Publisher | Microsoft Learn |
| Retrieved | 2026-10-08 |
| Last updated | 2026-07-06 |
| Status | PREVIEW |
| Associated patterns | P12 |
| Key architecture statement | Standard Power BI email subscriptions can include an AI-generated summary of the report. |
| Implementation relevance | Monthly insights: the low-code option. |
| Security implications | Uses Copilot in Fabric under capacity rules. |
| Limitations | Preview; standard subscriptions only. |
| Fallback | Scheduled email subscription without summary (GA). |
| Deprecation / replacement | — |

## Relational data foundations

<a id="research-relational-model"></a>

### A relational model of data for large shared data banks

| Field | Value |
|---|---|
| URL | https://research.ibm.com/publications/a-relational-model-of-data-for-large-shared-data-banks |
| Publisher | IBM Research / ACM |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P10, P12 |
| Key architecture statement | Relations and data independence separate a logical data model from physical representation. |
| Implementation relevance | Teaches keys, grain, relational operations and stable business meaning before modern lakehouse and semantic-model implementation. |
| Security implications | Logical abstraction does not replace access control or disclose permitted data automatically. |
| Limitations | Foundational research, not a Fabric implementation specification or evidence of product lineage. |
| Fallback | Reproducible synthetic SQL and semantic-model exercises. |
| Deprecation / replacement | — |

## Retrieval and grounding foundations

<a id="research-rag"></a>

### Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

| Field | Value |
|---|---|
| URL | https://arxiv.org/abs/2005.11401 |
| Publisher | arXiv |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P01, P04, P06 |
| Key architecture statement | Retrieval combines external non-parametric information with a generative model rather than relying only on information encoded in model weights. |
| Implementation relevance | Teaches why evidence selection, source relevance and separate numeric baselines matter for grounded answers. |
| Security implications | Retrieved content is untrusted input and must not grant permissions or override instructions. |
| Limitations | Governed structured queries and Fabric data agents are not automatically the original RAG architecture; retrieval can be irrelevant or incomplete. |
| Fallback | Synthetic retrieved context compared with deterministic reference answers. |
| Deprecation / replacement | — |

## Spec-driven engineering

<a id="spec-kit-quickstart"></a>

### Spec-Driven Development Quickstart

| Field | Value |
|---|---|
| URL | https://github.github.io/spec-kit/quickstart.html |
| Publisher | GitHub Spec Kit |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | OSS |
| Associated patterns | P20, P25 |
| Key architecture statement | A specification-led workflow connects constitution, requirements, planning, tasks, implementation and convergence; current skills use the speckit-hyphen invocation form. |
| Implementation relevance | Optional engineering pattern for new use cases and cross-layer changes; specify-cli 1.1.3 was verified through PyPI metadata without installation. |
| Security implications | Generated instructions must preserve repository policy; requirements and agent implementation do not authorize live writes. |
| Limitations | Tool integration requires scratch initialization and review before adoption; active feature selection is independent of checking out a Git branch. |
| Fallback | Use the repository's spec-driven-delivery skill with reviewed requirements and existing test gates, explicitly without claiming Spec Kit CLI execution. |
| Deprecation / replacement | — |

## Tool-using agent foundations

<a id="research-react"></a>

### ReAct: Synergizing Reasoning and Acting in Language Models

| Field | Value |
|---|---|
| URL | https://arxiv.org/abs/2210.03629 |
| Publisher | arXiv |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P06, P08, P09, P19 |
| Key architecture statement | Interleaving reasoning and environment actions can support task solving with external observations. |
| Implementation relevance | Teaches the distinction between a proposed action, an actual tool invocation and an observed result. |
| Security implications | Tool availability is not authority; constrain actions with deterministic validation and approval. |
| Limitations | Research task results are not a Copilot or Foundry benchmark; tool loops can still make unsafe or incorrect choices. |
| Fallback | Read-only synthetic agent exercises and labeled execution traces. |
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

## Transformer foundations

<a id="research-transformers"></a>

### Attention Is All You Need

| Field | Value |
|---|---|
| URL | https://arxiv.org/abs/1706.03762 |
| Publisher | arXiv |
| Retrieved | 2026-10-09 |
| Last updated | — |
| Status | GUIDANCE |
| Associated patterns | P06, P19 |
| Key architecture statement | The Transformer uses attention mechanisms to model sequence relationships without the recurrent architecture used in earlier sequence models. |
| Implementation relevance | Distinguishes learned next-token behavior from retrieval, deterministic calculation, tool execution and authority. |
| Security implications | Fluent output is not evidence of factual accuracy, tool execution or authorization. |
| Limitations | Original translation experiments do not establish the behavior or performance of today's proprietary models. |
| Fallback | Conceptual teaching and bounded synthetic prompt experiments; no model training required. |
| Deprecation / replacement | — |
