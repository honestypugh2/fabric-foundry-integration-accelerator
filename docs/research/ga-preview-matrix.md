# GA / PREVIEW matrix

Verified 2026-10-05. Sources are listed in [`sources.yaml`](sources.yaml), rendered as
[`source-validation.md`](source-validation.md).

**Policy:** the default demo uses only **GA** capabilities and **LOCAL** equivalents. Every
PREVIEW item is:

- feature-flagged;
- labeled `PREVIEW` in the UI and in results;
- simulated offline;
- never required.

UNKNOWN items are re-validated before each release.

| Area | GA | PREVIEW | DEPRECATED | UNKNOWN / NEEDS VALIDATION |
|---|---|---|---|---|
| Fabric data | Fabric; OneLake; shortcuts (core); medallion guidance; Lakehouse/Warehouse; Mirroring; **Open Mirroring**; Direct Lake on OneLake and on SQL endpoint; Git integration; deployment pipelines (core); Real-Time Intelligence (core); AI functions; Fabric REST API | S3-compatible shortcuts; schema-aware eventstream; some Git item types; new deployment-pipelines UI | — | OneLake security and OneLake catalog GA dates; role-playing dimensions in Direct Lake; mirroring as backup/DR (not documented — never claimed) |
| Fabric AI | **Fabric Data Agent**; Fabric IQ MCP | **Fabric IQ**; **ontology**; Ontology MCP; Data Agent in Copilot Studio / Microsoft 365 Copilot | "AI skill" name (renamed to data agent) | Data Agent MCP endpoint status |
| Fabric MCP | Fabric MCP Server (local) 1.4.0; Power BI Authoring/Modeling MCP (local) 1.0.0; Fabric IQ MCP | Power BI hosted authoring MCP; **Data Warehouse MCP**; Ontology MCP | `.vscode/mcp.json` location (use `.mcp.json`) | Fabric Core MCP Server; Eventhouse, Activator, Operations-agent, RTI and Data Factory MCP |
| Foundry | Foundry (new); Agent Service; hosted agents; MCP/OpenAPI/function tools; tracing; core evaluators; OneLake knowledge source; AI Gateway | Fabric data agent tool; Fabric IQ tool; Foundry IQ portal and Fabric knowledge sources; intent/task evaluators; AI Red Teaming Agent; azd evaluation; Entra trace ingestion; Browser Automation | Classic agents (retire 2027-03-31); hub-based projects (legacy) | Foundry MCP server status; official Foundry skills repository |
| Frameworks/SDKs | Agent Framework 1.20.0; azure-ai-projects 2.8.0; azure-identity 1.26.0; azure-monitor-opentelemetry 1.8.10; FastMCP 4.0.11 (mcp 2.3.0) | microsoft-fabric-api (beta); semantic-link (beta); fabric-data-agent-sdk (alpha); @azure/mcp 3.x (beta) | agent-framework-azure-ai (stale RC) | fabric-cicd formal lifecycle (official OSS) |
| Developer tools | Copilot instructions; AGENTS.md; Copilot CLI (GA 2026-02-25); Copilot cloud agent; Claude Code (CLAUDE.md, `.mcp.json`, skills, hooks); Agent Skills standard; Fabric VS Code extensions; PBIP/TMDL | **Copilot app** (technical preview); VS Code custom agents; Copilot CLI sandboxes; TMDL web view | VS Code prompt files for Agent Host sessions | skills-for-fabric lifecycle label (official OSS, v0.3.18) |
