# Tooling and workshop alignment

This is a **development solution accelerator**: discover use cases, learn, build in a demo
environment, inspect the result and add another use case. Production deployment and enterprise
certification are not completion gates.

**LOCAL assessment of repository implementation against public documentation retrieved
2026-10-21.** Documentation retrieval is not tenant verification. No installation, cloud
mutation, model connection or notebook execution is established by this assessment.

## Microsoft integration alignment

| Resource | Repository alignment | Limit and next step |
|---|---|---|
| [Power BI Authoring MCP](https://learn.microsoft.com/power-bi/developer/mcp/power-bi-authoring-mcp) | Local server is pinned in [MCP profiles](../../config/mcp/profiles.yaml); HC-01 uses semantic-model, relationship, measure and DAX workflows. The older `modeling` package/profile names refer to the same local authoring server, not a separate product. | Configured tools and prior discovery do not prove model authoring. Complete the actual connection and DAX/model acceptance. Hosted authoring is PREVIEW, not configured; Microsoft recommends it when supported. Select hosted for workspace-only authoring or local for PBIP/Desktop needs, never duplicate both tool sets in the same client. |
| [Fabric Data Warehouse MCP](https://learn.microsoft.com/fabric/data-warehouse/data-warehouse-mcp-server) | Referenced by source `fabric-dw-mcp` and teaching content, but deliberately absent from default profiles and the app provider. | PREVIEW; its single `executeSQL` tool runs T-SQL, including metadata inspection, against a Warehouse or SQL analytics endpoint. It is not a notebook/Spark runner. Plan an optional item-scoped demonstration with database read-only permissions and reviewed bounded queries; do not expose arbitrary SQL through `ffia-local`. |
| [Core Microsoft Fabric VS Code extension](https://learn.microsoft.com/fabric/data-engineering/set-up-fabric-vs-code-extension) | Workspace/item management and MCP are part of the documented development workflow. | This is distinct from the Data Engineering extension. Verify the installed extension host, sign-in and actual callable tools; a recommendation or config is not installation evidence. |
| [Fabric Data Engineering extension](https://learn.microsoft.com/fabric/data-engineering/setup-vs-code-extension) | HC-01 uses notebooks, lakehouse exploration and remote Spark; [tooling guidance](notebook-powerbi-tooling.md) distinguishes extension-native tools from notebook MCP inspection. | Local downloaded files and VFS are both documented modes. Neither means execution ran remotely. Check the selected Microsoft Fabric Runtime and exact target. Keep the explicitly agreed operator-assisted route available when client tooling is blocked; label it accurately. |
| [Skills for Fabric overview](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-overview) | Four curated upstream skills are locked in [the skills manifest](../../config/skills/fabric-skills.lock.yaml): medallion, Spark, semantic modeling and Power BI reports. | Skills teach procedures; MCP supplies tool access; identity and approval supply authority. Skills alone neither execute nor prove a finished report. |
| [Install Skills for Fabric](https://learn.microsoft.com/fabric/fundamentals/skills-for-fabric-install) | `ffia skills install` provides a reproducible, SHA-256-verified subset, rather than installing the whole marketplace. | Current upstream guidance separates `fabric-skills` and `powerbi-authoring` plugins. Document both paths and verify the installed skills per client. Review upgrades before changing the lock; do not replace pinned tools with `@latest` or duplicate bundled MCP servers. |

The two Warehouse links in the request are the same resource; the two Power BI Authoring
links are also the same resource. They are not four distinct integrations.

### Why not enable every server by default?

- The default MCP profile intentionally exposes narrow read-only tools plus a labeled local
  fallback. Authoring profiles are opt-in.
- Preview tools remain optional. A developer showcase can demonstrate them, but they must
  not become prerequisites for offline learning.
- The React application's Fabric REST/Foundry SDK providers are separate from coding-client
  MCP integrations. A successful app read cannot certify an MCP operation.
- An MCP server running locally can operate on a live model. Server location and execution
  destination are different facts.

## Workshop references and adopted structure

These are information-architecture references, not templates copied into this repository.
The frontend remains React + strict TypeScript + Vite, with original styling and no new
runtime dependencies.

| Reference | Observed pattern | Application here |
|---|---|---|
| [Microsoft accelerator gallery](https://accelerators.ms/) | Rendered searchable catalog, product/industry filters, consistent cards | Search registered use cases by title, summary or tool; filter industry and tools/services; keep filters in the URL |
| [OpenAIWorkshop](https://github.com/microsoft/OpenAIWorkshop) | Quick links and sequenced setup/scenario/architecture entry | Discover → understand → build → verify navigation and within-step section links |
| [Fabric Workshops](https://microsoft.github.io/Fabric_Workshops/) | Numbered setup leading into lab selection | Overview and prerequisites before an explicit Start workshop action |
| [Azure Foundry workshop](https://github.com/Azure/ai-foundry-workshop) | Quick navigation, prerequisites and hands-on workshop framing | Setup visibility and focused module reader rather than a long undifferentiated page |
| [Community Foundry workshop](https://github.com/gilbertossoares/ai-foundry-workshop) | Progressive, consistently described labs and language choices | Consistent cards; localization is not implemented or claimed |
| [Older hybrid router workshop](https://github.com/honestypugh2/hybrid-router-workshop) | Educational disclaimer and prerequisite checklist | Development scope and explicit live/local boundaries; old dependencies and architecture are not imported |
| [AI Agents for IT Ops](https://github.com/microsoft/AIAgentsforITOps) | Choose a path before the implementation detail | Outcome-first catalog and separate concepts/build paths; no AKS requirement |
| [Databricks MLOps workshop](https://github.com/microsoft/databricks-mlops-workshop) | Dataset provenance and shared versus learner resource distinctions | Keep synthetic profile, independent baseline and exact resource ownership explicit; no Databricks dependency |
| [Apps and Agents workshop](https://github.com/microsoft/apps-agents-workshop) | Fast orientation, why and audience before modules | Clear value, audience and outcome before tool details |
| [Healthcare models workshop](https://github.com/microsoft/healthcare-models-and-agents-workshop) | Chapter structure, setup and consistent exercises | Numbered module outline, prerequisite table, per-step prompts and expected evidence |

The community and older personal repositories are supplemental references, not Microsoft
product guidance. Discovery of a workshop is not validation of its dependencies or cloud setup.

## Learner flow

1. **Discover:** searchable use-case catalog and clearly named workshops.
2. **Understand:** outcome, audience, concepts and selectable architecture.
3. **Prepare:** tools, prerequisites and development-environment constraints.
4. **Build:** explicitly start a workshop; open one numbered module, copy a prompt, inspect
   its tools and follow the checkpoint. The overview does not silently open module one.
5. **Verify:** compare actual results with the independent baseline. Browser checkmarks
   record a learning checklist, not cloud execution.
6. **Recover:** eligible failed reads can use a disclosed LOCAL equivalent. Invalid targets
   remain errors. A failed LIVE write stops; a simulated rehearsal is a separate choice.
7. **Extend:** use [use-case onboarding](use-case-onboarding.md) and the existing structured
   registries, not scenario-specific frontend branches.

The app does not execute cloud work just because a learner opens a module. Presenter talk
tracks remain separate standalone HTML documents; interactive architecture nodes and traces
remain available in the app and portable HTML.

## Remaining alignment work

1. Complete the core HC-01 and MFG-01 live demonstrations and their actual acceptance checks.
2. Verify actual tool exposure and skill loading in VS Code, GitHub Copilot CLI and Claude
   Code. Do not equate running a Claude model in Copilot with using Claude Code.
3. Decide the Power BI authoring deployment per exercise; use a separate optional profile
   and preview flag if hosted authoring is added.
4. Specify the optional Warehouse MCP exercise, scoped identity and read-only query
   contract before configuring it. Its broader SQL tool is not a default fallback.
5. Review current upstream skill/plugin changes against the pinned archive. Upgrade only
   after compatibility and regression checks.
6. Keep no-credential offline validation and isolated portable HTML testing as release gates.
   Production hardening and deployment remain optional future work.

Source records: `powerbi-authoring-mcp`, `fabric-dw-mcp`, `fabric-vscode-workspace`,
`fabric-vscode-data-engineering`, `skills-for-fabric`, `skills-for-fabric-install`,
`accelerator-gallery`, `workshop-fabric-readiness`, `workshop-openai`,
`workshop-itops-paths`, `workshop-healthcare-modules` in
[the source registry](../research/sources.yaml).
