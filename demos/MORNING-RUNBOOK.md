# Morning runbook: Guide 1 and Guide 2, live or offline

Decide the mode **30 minutes before** each meeting. The offline path always works; the live path
needs the steps below. Every live step names its provider and tool, and the cloud changes in
section B need the presenter's explicit approval before they run.

## 0. Both guides, always (5 minutes)

```bash
cd fabric-foundry-integration-accelerator && source .venv/bin/activate
make demo-prep          # clears the dev-server cache, runs every offline check
ffia skills status      # four pinned skills (run `ffia skills install` if missing)
make run                # app on http://localhost:5173 → Demo → Workshop talk tracks
```

Open the handouts from the app's **Demo** page, or directly:

- Guide 1: `demos/fabric-copilot-level-up/index.html`
- Guide 2: `demos/foundry-fabric-agents-workshop/index.html`

## A. Live read-only Fabric (Guide 1 live MCP segment), 5 minutes, no approval needed for reads

1. Resume the F capacity. Provider: Azure Resource Manager. Tool: `az rest POST .../capacities/<name>/resume`. This starts billing (an F8 in Central US is about $1.44/hour); pause it after the meeting.
2. `az login --tenant <DEMO_TENANT_ID>`, then `ffia fabric readiness`. Expect "Fabric ready for live labs: YES".
3. `mkdir -p ~/hc-01-lab/.vscode && ffia mcp render fabric-readonly --client vscode --output ~/hc-01-lab/.vscode/mcp.json`. Open `~/hc-01-lab` in a second VS Code window, then MCP: List Servers → start.

**Go/no-go:** if readiness isn't YES within 5 minutes, present the MCP segment offline using prompt
P-MCP-3.

## B. Live Foundry + Fabric (Guide 2 live demo, Guide 1 Foundry segment), about 25 to 35 minutes, **needs approval**

Each step is a cloud write. Plan, approve, execute, verify, audit.

| # | Change | Provider / tool | Verify |
|---|---|---|---|
| B1 | Foundry resource and project in `rg-ffia-fabric-dev` (East US 2) | Azure CLI `az cognitiveservices account create --kind AIServices --custom-domain ...`, then `az rest PUT .../projects/<project>` | Portal shows the project; endpoint resolves |
| B2 | Model deployment (GA model, Data Zone Standard, small TPM) | `az cognitiveservices account deployment create` | Deployment listed and Succeeded |
| B3 | Role: Foundry User on the project for the presenter | `az role assignment create` | Agent playground opens |
| B4 | Lakehouse `mfg_lakehouse` in `ffia-dev`; upload the 6 CSVs from `data/synthetic/raw/mfg-sales-v1`; load them as tables | Fabric portal (Get data → Upload; Load to tables) or the `hc01-lab`-style Fabric MCP profile with per-call approval | Six tables with the row counts in `data/synthetic/expected/mfg-sales-v1.json` |
| B5 | Fabric data agent `mfg-sales-data-agent` over the lakehouse tables; publish | Fabric portal → New item → Data agent | Ask "booked revenue by product line in September 2026" in the data agent |
| B6 | Foundry project connection to the data agent (workspace ID + artifact ID) | Foundry portal → Management → Connected resources → Microsoft Fabric | Connection listed |
| B7 | Create `sales-insights-agent` | `python demos/foundry-fabric-agents-workshop/code/fabric_sales_agent.py` | Answer names Enclosures as the fastest grower |

**Status 2026-10-08: B1–B7 completed and verified live** (Enclosures +55.78% and 12 duplicate lines, matching the baseline). Warm up the agent 10 minutes before: the first call took about 2.5 minutes.

**One-command check (read-only):** `ffia foundry readiness` verifies the Foundry resource, project, model deployment, data-plane access, `sales-insights-agent` and the Fabric connection. It reads the `foundry:` section of the git-ignored bindings file. Expect "Foundry ready for agent demos: YES".

**Go/no-go:** if B1–B7 aren't verified 15 minutes before the meeting, run Guide 2 in **hybrid**
mode: the Foundry portal tour, the code walkthrough labeled REQUIRES TENANT VALIDATION, and
`ffia mfg brief` / `ffia mfg quality` for the numbers (LOCAL).

**Known constraints:**

- The Fabric data agent tool in Foundry is **preview**. It uses the signed-in user's identity;
  service principals aren't supported.
- Keep the data agent and its data in the same tenant and region.
- The tenant setting "Users can use Copilot and other features powered by Azure OpenAI" must be on.

## After the meetings

- Pause the F capacity.
- Optional: delete the Foundry resource. A deployed model has no idle cost, but delete it if you
  won't reuse it.
- Nothing is committed with identifiers. Keep IDs in `config/customers/*.local.yaml` and
  environment variables only.
