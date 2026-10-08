# Application control plane

The control plane gives the frontend, the coding agents and the demo one governed way to read
synthetic Fabric context, propose changes, approve them and see evidence. It is offline-first: it
starts and passes its release gate with no Azure configuration.

Status: **SIMULATED LOCALLY** by default. An opt-in live Fabric provider and a gated scoped writer
exist (`FFIA_FABRIC_LIVE=1` plus a git-ignored bindings file; see
[ADR-0012](../decisions/ADR-0012-live-fabric-integration.md)). Live reads of workspaces and items
through the router are **VERIFIED LIVE** in a demo tenant (HYBRID mode, no fallback). DAX
reconciliation, throttling and the scoped writer remain **REQUIRES TENANT VALIDATION**. Foundry
arrives in Phase 6.

## Components

| Component | Module | Responsibility |
|---|---|---|
| Settings | `config/settings.py` | `FFIA_*` environment variables and the git-ignored `.env.local`. No identifiers in code. |
| Environment | `config/environment.py` · `config/environments/*.yaml` | `OFFLINE`, `HYBRID` or `LIVE`: which provider each capability prefers, the fallback and the circuit breaker |
| Customer overlay | `config/overlay.py` · `config/customers/*.yaml` | Aliases, allowed reads and writes, approvals, feature flags and guides. See [customer-overlay.md](../customization/customer-overlay.md) |
| Policy engine | `policies/engine.py` · `config/policies/*.yaml` | Deterministic write policy and the MCP tool allow-list |
| Provider router | `fallback/router.py` · `fallback/circuit_breaker.py` | Timeouts, bounded retries, circuit breaker and approved read fallback. See [resilience.md](resilience.md) |
| Change service | `services/changes.py` | PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT for every write |
| Audit store | `audit/store.py` | Redacted, append-only records with correlation IDs (JSONL or in-memory) |
| Container | `services/container.py` | Wires the components together through dependency injection. No global clients. |
| REST API | `api/app.py` · `api/routes.py` | FastAPI. Thin routes that call the services. |
| Local MCP server | `mcp/server.py` · `config/policies/tools.yaml` | FastMCP. Allow-listed, rate-limited and audited tools. |
| Demo | `services/demo.py` | `ffia demo check` and the ten-act offline release gate |
| Education | `education/lessons.py` · `services/education.py` | Validated lessons, labs, architecture map and completeness gate |

## REST API (`make run-api`, OpenAPI at `/docs`)

The OpenAPI document is committed as `schemas/openapi.json`. The frontend's TypeScript contract
types are generated from it (`ffia schemas export`). See [frontend.md](frontend.md).

| Area | Paths |
|---|---|
| Health | `GET /health`, `GET /ready` |
| Runtime | `GET /api/v1/runtime/status`, `GET /api/v1/runtime/providers`, `GET /api/v1/capabilities` |
| Patterns | `GET /api/v1/patterns`, `GET /api/v1/patterns/signals`, `GET /api/v1/patterns/{pattern_id}`, `POST /api/v1/patterns/recommend` |
| Guides | `GET /api/v1/guides`, `GET /api/v1/guides/{guide_id}`, `GET /api/v1/guides/{guide_id}/steps/{step_id}` |
| Fabric reads | `POST /api/v1/fabric/read` (a discriminated union of allow-listed read operations, never free-form SQL) |
| Changes | `POST /api/v1/plans`, `GET /api/v1/plans`, `GET /api/v1/plans/{change_id}`, `POST /api/v1/approvals`, `POST /api/v1/fabric/change` |
| Recovery | `POST /api/v1/recovery/drill` |
| Evaluation | `POST /api/v1/evaluations/run` |
| Agents | `GET /api/v1/agents/{agent}` (providers and evaluated questions), `POST /api/v1/agents/ask`, `POST /api/v1/agents/evaluate` (`?suite=`), `POST /api/v1/agents/workflows/monthly-insights` (Agent Framework workflow; drafts only, nothing is sent) |
| Audit | `GET /api/v1/audit/{correlation_id}` |
| Demo and data | `GET /api/v1/demo/status`, `POST /api/v1/demo/run`, `GET /api/v1/profiles` |
| Education | `GET /api/v1/education/lessons` (`?area=`, `?pattern_id=`), `GET /api/v1/education/lessons/{id}` (answers withheld), `POST /api/v1/education/lessons/{id}/checks/{check_id}`, `GET /api/v1/education/labs`, `GET /api/v1/education/labs/{id}`, `GET /api/v1/education/architecture`, `GET /api/v1/education/completeness` |

- Every response carries `X-Correlation-ID`.
- Errors use a single problem shape:
  - unknown resource → 404
  - invalid request → 422
  - approval or state conflict → 409
  - capability unavailable → 503
- CORS is limited to the configured frontend origin.

## Local MCP server (`make run-mcp`, stdio)

`ffia-local` exposes exactly the tools enabled in `config/policies/tools.yaml`:

- **Read-only:** `get_demo_capabilities`, `get_runtime_status`, `get_architecture_pattern`,
  `recommend_architecture_pattern`, `inspect_healthcare_scenario`,
  `inspect_medallion_architecture`, `preview_table`, `evaluate_measures`, `get_guide_step`,
  `detect_duplicate_records`, `evaluate_against_baseline`, `get_audit_record`.
- **Proposal and simulation only:** `generate_fabric_change_plan`, `validate_change_plan`,
  `simulate_recovery_drill`.

Rules:

- **No tool can approve or execute a change.** An MCP client can propose a plan. Approval and
  execution need the REST approval flow and a human.
- **No shell, SQL, filesystem, URL-fetch or REST-proxy tool exists.** Table and profile
  arguments are checked against the built catalog.
- A tool that is enabled in the manifest but has no implementation stops the server at startup.
- Every call is rate limited per tool and audited. Tool annotations report `openWorldHint=false`.
- Logs go to stderr only, so stdio MCP traffic stays clean.

This server is an educational **LOCAL** server. It is not the Fabric MCP server, and a call to
it is never evidence of a Fabric operation. See
[ADR-0007](../decisions/ADR-0007-mcp-access-is-not-authority.md).

## Governed change flow

1. **PLAN.** `POST /api/v1/plans` or the MCP tool `generate_fabric_change_plan`. The plan
   records:
   - risk, reversibility, expected impact, validation steps and rollback;
   - policy reasons;
   - a duplicate or existence precondition;
   - a hash of the destination.

   Duplicates and policy violations are `BLOCKED`.
2. **VALIDATE.** `validate_change_plan` re-runs policy and preconditions without changing
   state. It is audited as `change:revalidate`.
3. **APPROVE.** `POST /api/v1/approvals`.
   - Separation of duties: the requester cannot approve their own change.
   - Approvals expire after `approval_ttl_minutes`.
   - Rejections are recorded too.
4. **EXECUTE.** `POST /api/v1/fabric/change`.
   - Needs a valid, unexpired, matching approval.
   - Rechecks the destination hash and the precondition.
   - `LOCAL` destinations run in the simulated workspace and are labeled `SIMULATED`.
   - `LIVE` destinations return `UNAVAILABLE` until an authorized live writer exists. They are
     **never** redirected to LOCAL.
5. **VERIFY.** The simulated workspace revision must change as expected.
6. **AUDIT.** Every step writes a redacted record under the plan's correlation ID.

Plans and approvals are held in memory per process. A plan proposed through `ffia-local` (its
own process) cannot be approved through the API process, so labs re-submit the reviewed plan to
the API. The audit log is a shared JSONL file, so both processes see every record. Refused
approval attempts are audited with `success=false`.

See [ADR-0006](../decisions/ADR-0006-human-approval-and-scoped-writer.md).
