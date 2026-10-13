# Use-Case Guides

Customer-neutral, synthetic-data implementation guides: sanitized re-expressions of engagements
or original scenarios. Each guide has a validated `guide.yaml`, scoped `AGENTS.md`/`CLAUDE.md`,
prompts, checkpoints, evidence and offline equivalents. Guides inherit root MCP unless a narrower
profile is needed. Source documents never enter this repository. `_template/` scaffolds new guides.

## Choose an outcome

| Use case | Audience and result | First checkpoint |
|---|---|---|
| [HC-01: level up Fabric engineering with Copilot](hc-01-fabric-mcp-powerbi-medallion-lab/README.md) | Data engineers: reviewed notebooks, semantic model and report over synthetic healthcare data | Verify tools and the seven-file dataset before any cloud write |
| [MFG-01: agents over Fabric context](mfg-01-foundry-fabric-sales-insights/README.md) | Agent builders/business teams: governed answers, reviewed briefs and quality proposals | Explain data, reasoning and authority boundaries without cloud calls |
| [DQ-01: synthetic quality investigation](dq-01-synthetic-quality-investigation/README.md) | Engineers/stewards and new authors: exact baseline checks and governed proposal rehearsal | Define grain and quality categories without cloud calls |

Install from the [root quick start](../README.md#quick-start), launch offline, then open
**Use Cases** at `/use-cases`. Each guide separates local rehearsal from connected steps.
Run one manifest step at a time and stop at its checkpoint; checkboxes are not live evidence.

For another scenario, follow [onboarding](../docs/operations/use-case-onboarding.md).
Claude Code alternate prompts are documented, not a completed comparative run.
