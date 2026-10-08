# Demonstrations

Every demo labels what ran LIVE, LOCAL or SIMULATED, and names the provider, server and tool before
any cloud call.

| Demo | Status | Covers |
|---|---|---|
| [Leveling up Fabric data engineering with GitHub Copilot](fabric-copilot-level-up.md) | Ready (offline path verified; live read-only segments verified in the demo tenant) | Reference architecture and patterns, Fabric MCP, Fabric Skills, GitHub Copilot (what it does, L1→L6), Power BI, options |
| [Talk track Q&A](fabric-copilot-level-up-qa.md) | Ready | Anticipated customer questions with labeled answers |
| [Guide 1 talk track (HTML)](fabric-copilot-level-up/index.html) | Ready | Generated from `fabric-copilot-level-up/talk-track.yaml` |
| [Guide 2: Foundry + Fabric agent workshop (HTML)](foundry-fabric-agents-workshop/index.html) | Ready offline; live needs the runbook | Foundry capabilities and Fabric, building and orchestrating agents, internal and external data, security and governance, the five customer questions |
| [Morning runbook](MORNING-RUNBOOK.md) | Ready | Offline, live read-only and live Foundry setup with go/no-go |

Prepare with `make demo-prep`. Prompts are in [`../prompts/github-copilot/fabric-level-up.md`](../prompts/github-copilot/fabric-level-up.md).

Planned: `open-mirroring-recovery`, `foundry-data-agent`, `fabric-iq` (preview), `evaluation-observability`,
`copilot-vs-claude-bakeoff`, and `offline-fallback` as stand-alone scripts (Phases 6–7). Their content
already exists as lessons and labs.
