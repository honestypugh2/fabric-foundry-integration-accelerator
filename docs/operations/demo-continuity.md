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
| 6 | Foundry agent over governed context (Phase 6). Shown honestly as not yet available. | UNAVAILABLE (optional) |
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
| No network | `FFIA_ENVIRONMENT=offline`. Everything is LOCAL or SIMULATED and labeled that way. |
| You want to teach failure | `FFIA_SIMULATE_FABRIC_OUTAGE=1` (act 7) |

Never describe a LOCAL or SIMULATED result as a Fabric, Foundry, Power BI or MCP operation.
For Guide HC-01, each step's `offline_equivalent` in `guide.yaml` gives the LOCAL substitute.
