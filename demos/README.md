# Demonstrations

Every demo labels what ran LIVE, LOCAL or SIMULATED, and names the provider, server and tool before
any cloud call.

| Demo | Status | Covers |
|---|---|---|
| [Leveling up Fabric data engineering with GitHub Copilot](fabric-copilot-level-up.md) | Ready (offline path verified; live read-only segments verified in the demo tenant) | Reference architecture and patterns, Fabric MCP, Fabric Skills, GitHub Copilot (what it does, L1→L6), Power BI, options |
| [Talk track Q&A](fabric-copilot-level-up-qa.md) | Ready | Anticipated customer questions with labeled answers |

Prepare with `make demo-prep`. Prompts are in [`../prompts/github-copilot/fabric-level-up.md`](../prompts/github-copilot/fabric-level-up.md).

Planned: `open-mirroring-recovery`, `foundry-data-agent`, `fabric-iq` (preview), `evaluation-observability`,
`copilot-vs-claude-bakeoff`, and `offline-fallback` as stand-alone scripts (Phases 6–7). Their content
already exists as lessons and labs.
