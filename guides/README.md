# Use-Case Guides

Choose a guide, explain the outcome, then build one step at a time.
Every guide uses synthetic data and includes prompts, checkpoints, evidence and an offline path.

Read its `guide.yaml` and scoped `AGENTS.md`/`CLAUDE.md` before starting.
Use the root MCP configuration unless the guide needs a narrower profile.
Customer source documents never enter this repo.

## Choose an outcome

| Use case | Audience and result | First checkpoint |
|---|---|---|
| [HC-01: level up Fabric engineering with GitHub Copilot](hc-01-fabric-mcp-powerbi-medallion-lab/README.md) | Data engineers: reviewed notebooks, semantic model and report over synthetic healthcare data | Verify tools and the seven-file dataset before any cloud write |
| [MFG-01: agents over Fabric context](mfg-01-foundry-fabric-sales-insights/README.md) | Agent builders/business teams: governed answers, reviewed briefs and quality proposals | Explain data, reasoning and authority boundaries without cloud calls |
| [DQ-01: synthetic quality investigation](dq-01-synthetic-quality-investigation/README.md) | Engineers/stewards and new authors: exact baseline checks and governed proposal rehearsal | Define grain and quality categories without cloud calls |

Install from the [root quick start](../README.md#quick-start), launch offline, then open
**Use Cases** at `/use-cases`. Each guide separates local rehearsal from connected steps.
Run one manifest step at a time. Stop at its checkpoint.
A checked box does not prove a live operation ran.

To add a scenario, follow [onboarding](../docs/operations/use-case-onboarding.md).
Claude Code alternate prompts are documented, not a completed comparative run.
HC-01 live completion and Claude setup are [tracked for later](../docs/operations/resume-later.md).
