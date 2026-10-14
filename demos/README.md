# Demonstrations

Every demo labels what ran LIVE, LOCAL or SIMULATED, and names the provider, server and tool before
any cloud call.

| Demo | Status | Covers |
|---|---|---|
| [Leveling up Fabric data engineering with GitHub Copilot](fabric-copilot-level-up.md) | Ready offline; live read-only observations are dated, not current-health or end-to-end certification | Architecture, Fabric MCP, Fabric Skills, GitHub Copilot levels L1 to L6, Power BI and alternatives |
| [Talk track Q&A](fabric-copilot-level-up-qa.md) | Ready | Anticipated customer questions with labeled answers |
| [Guide 1 talk track (HTML)](fabric-copilot-level-up/index.html) | Ready | Generated from `fabric-copilot-level-up/talk-track.yaml` |
| [Guide 2: Foundry + Fabric agent workshop (HTML)](foundry-fabric-agents-workshop/index.html) | Ready offline; live needs the runbook | Foundry capabilities and Fabric, building and orchestrating agents, internal and external data, security and governance, the five customer questions |
| [Morning runbook](MORNING-RUNBOOK.md) | Ready | Offline, live read-only and live Foundry setup with go/no-go |

Prepare with `make demo-prep`. Prompts are in [`../prompts/github-copilot/fabric-level-up.md`](../prompts/github-copilot/fabric-level-up.md).

For sharing, start with the [customer](../docs/field-playbooks/customer.html) or
[SE/developer](../docs/field-playbooks/se-developer.html) field playbook. HC-01 and MFG-01
remain featured; unfinished connected execution and Claude setup are tracked
[for later](../docs/operations/resume-later.md), not removed.

GitHub displays HTML source. Download the handout and open it in a browser to see the page.

Planned: `open-mirroring-recovery`, `foundry-data-agent`, `fabric-iq` (preview), `evaluation-observability`,
`copilot-vs-claude-bakeoff`, and `offline-fallback` as stand-alone scripts (Phases 6 to 7). Their content
already exists as lessons and labs.
