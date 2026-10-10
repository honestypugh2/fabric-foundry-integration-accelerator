# Demo continuity

The demo must work in front of an audience whether or not the tenant cooperates.

## Before the session

```bash
source .venv/bin/activate
make demo-check      # probe each component and recommend a mode
make demo-offline    # ten-act release gate; must print "Release gate: PASSED"
```

`ffia demo check` gives each component a status, such as `PASS`, `READY`, `NOT READY`,
`NOT CONFIGURED`, `NOT AVAILABLE` or `FAIL`. The components are:

- Fabric Authentication (Azure CLI sign-in only; no token is read or printed)
- Fabric API
- Fabric MCP
- Foundry
- Local Dataset
- Offline Provider
- API
- Frontend
- MCP Server

It then recommends `LIVE`, `HYBRID` or `OFFLINE`. Use `--no-azure-cli` to skip the Azure CLI
probe and `--json` for machine-readable output.

## The ten acts (`ffia demo offline`)

| Act | Story | Label |
|---|---|---|
| 1 | Why: Fabric is context, Foundry is reasoning, MCP is access, identity is authority | LOCAL |
| 2 | Data: raw → Bronze → Silver → Gold → semantic model; measures match the baseline | LOCAL |
| 3 | A real MCP protocol call to the local educational server | LOCAL |
| 4 | Architecture pattern recommendation | LOCAL |
| 5 | Agentic change: plan, refused self-approval, approval, execute, verify, duplicate blocked, LIVE refused without redirect | SIMULATED |
| 6 | Agent over governed data: the LOCAL sales agent answers from a governed data tool, never from the model (the offline analog of a Foundry agent with the Fabric data agent tool) | LOCAL |
| 7 | Failure: simulated Fabric outage, circuit breaker, labeled fallback | LOCAL / HYBRID |
| 8 | Open Mirroring recovery drill | SIMULATED |
| 9 | Education: Executive → L400 path | LOCAL |
| 10 | Proof: evaluation and audit evidence | LOCAL |

The gate fails if any required act fails, if any act reports a LIVE or cloud operation, or if a
label is dishonest. `make validate` runs it, so a change that breaks the offline story cannot
merge.

## Switching modes during a session

| Situation | Action |
|---|---|
| The tenant is healthy | Confirm with `ffia fabric readiness`, opt in with `FFIA_FABRIC_LIVE=1` ([fabric-tenant-readiness.md](fabric-tenant-readiness.md)) and narrate the provider, server and tool before each call |
| Fabric is slow or failing | `FFIA_ENVIRONMENT=hybrid`. Reads fall back to LOCAL data in `HYBRID` mode, with `fallback_used` and a visible reason. |
| No network | `make run API_ARGS=--offline` (or `ffia serve api --offline`). Both guides are LOCAL/SIMULATED; cloud providers and live writes are disabled. |
| You want to teach failure | `FFIA_SIMULATE_FABRIC_OUTAGE=1` (act 7) |

Never describe a LOCAL or SIMULATED result as a Fabric, Foundry, Power BI or MCP operation.
For Guide HC-01, each step's `offline_equivalent` in `guide.yaml` gives the LOCAL substitute.

## Normal startup and bounded connected checks

`make run` and `ffia serve api` use live-first HYBRID defaults for both guides. The ignored
`.env` holds Azure, Fabric and Foundry configuration; `.env.local` and process variables
override it. See [environment configuration](environment-configuration.md).

Unconfigured HYBRID reads report an explicit LOCAL fallback; invalid bindings remain errors.
Strict LIVE never falls back, and live writes never become simulated writes.
`ffia-local` remains explicitly offline even when the app's `.env` enables live providers.

`make demo-live` performs an application Fabric REST workspace read and checks one synthetic
question against the existing Foundry agent. `make demo-hybrid` permits labeled read fallback,
but the agent evaluation still fails on fallback: it cannot certify an unavailable live agent.
These commands use metered inference, not MCP, do not create Fabric items or send messages,
and do not replace the ten-act offline release gate.
