# ADR-0012: Live Fabric integration — read-only provider, gated scoped writer, MCP profiles as code, reference notebooks

- Status: Accepted
- Date: 2026-10-07
- Supersedes the Phase 5 follow-ups in ADR-0003, ADR-0005, ADR-0006 and ADR-0007

## Context

Phase 5 connects the accelerator to a real Fabric tenant without weakening the offline default or
the authority rules. Four facts shaped it:

- **The presenter's demo tenant was not Fabric-ready at first.** `ffia fabric readiness`
  found:
  - `401 UserNotLicensed` from the Fabric API;
  - no Fabric capacity;
  - the `Microsoft.Fabric` resource provider not registered.

  Live code therefore had to be built and proven offline, with tenant runs left as
  REQUIRES TENANT VALIDATION.
- **Fabric MCP 1.4.0 is no longer docs-only.** Its own `tools list` shows 48 tools: 22 can write
  and 5 are destructive. `datafactory_execute-query` is flagged read-only but runs arbitrary M
  queries, and `onelake_download-file` copies data out of OneLake.
- **Fabric REST has no row preview or model-definition read.** The Lakehouse List Tables API is
  preview.
- **The medallion SQL targets DuckDB.** No local Spark was available until a user-space JDK 17
  and PySpark 3.5.9 were installed outside the project.

## Options

1. Use the Fabric MCP server as the live provider.
2. Use a thin, typed Fabric REST client as the live provider. The Fabric MCP server is offered to
   harnesses through pinned, allow-listed profiles.
3. Hand-write Spark notebooks.
4. Generate notebooks from the same SQL the offline build runs.

## Decision

Options 2 and 4.

- **`LiveFabricProvider`** reads over the Fabric REST API and Power BI `executeQueries` (DAX):
  - Results are labeled LIVE, or PREVIEW for preview APIs, with `cloud_operation_performed: true`.
  - Row previews and model definitions raise clear errors instead of being faked.
  - The client has bounded `Retry-After` handling, long-running-operation polling and
    continuation-token pagination.
  - Errors map to router classes: 404 never falls back, 401/429/5xx/timeout may fall back for
    reads in HYBRID mode, and writes never fall back.
  - Tokens come from `az` for one pinned tenant, with a 30-second process timeout.
- **Explicit opt-in.** Live reads need all of:
  - `FFIA_FABRIC_LIVE=1`;
  - a hybrid or live environment;
  - the git-ignored `config/customers/<overlay>.local.yaml` bindings file, which pins the tenant
    and workspace IDs.
- **`FabricScopedWriter`** supports only `create_lakehouse` and `create_notebook`.
  - It runs only after policy allows the change, a different person approves it,
    `FFIA_ALLOW_LIVE_MUTATION=1` is set, and the workspace alias is bound.
  - It re-checks duplicates live before writing and verifies after writing, with VERIFIED LIVE
    evidence.
  - It audits failures and re-raises them.
  - Notebooks are created only from committed definitions.
  - The writer is tested with mocks only. It has never run against a tenant, and it never runs
    without a person approving the plan.
- **`ffia fabric readiness`.** Read-only tenant checks, each with a remediation.
- **MCP profiles as code.** `config/mcp/profiles.yaml` holds five profiles and a pinned tool
  catalog, rendered per client with `ffia mcp render` for VS Code (`servers`), Claude Code
  (`mcpServers`) and Copilot CLI (`mcpServers`, `type: local`, `tools`). `ffia mcp check` (in
  validate and CI) requires:
  - exact stable pins;
  - no `--dangerously-*` and no EULA flags;
  - read-only profiles use `--read-only` and an explicit allow-list of catalog read tools, minus
    the query and egress exclusions;
  - destructive tools are never exposed;
  - write-capable profiles are opt-in with per-call approval;
  - the default profile is read-only, GA-only, names `ffia-local` as its fallback, and equals the
    committed `.mcp.json` (amended 2026-10-08; see "Amendment" below).
- **Reference notebooks.**
  - `ffia notebooks render` writes `MCP_01_Bronze`, `MCP_02_Silver` and `MCP_03_Gold` in Fabric
    Git source format, using a closed set of DuckDB→Spark rewrites. Any unknown construct fails
    generation.
  - `ffia notebooks check` (in validate and CI) keeps them current.
  - `scripts/verify_spark_notebooks.py` executes the committed notebook code on Apache Spark
    3.5.9.

## Rationale

- A typed REST client gives deterministic, testable behavior and exact error semantics. An MCP
  server is a capability surface for agents, not a dependency of domain code.
- An explicit tool allow-list is enforced by the server itself. We verified this: the rendered
  profiles expose exactly 6 tools (`fabric-docs`) and 16 tools (`fabric-readonly`), all
  `readOnlyHint: true`. That is stronger than trusting a client to ignore tools.
- Generating notebooks from one SQL source prevents drift between the offline and Fabric paths.
  The local Spark run passed all 85 notebook checks against the committed baseline: row counts,
  keys, missing dimension keys, diagnostics, reconciliation to the cent, and readmissions of 35 out
  of 211.

## Live verification (2026-10-07, presenter's demo tenant)

The tenant was first made ready through an approved plan. A person approved it, and each step was
verified and audited:

1. A dedicated resource group.
2. An F8 Fabric capacity.
3. A `ffia-dev` workspace on that capacity.

Then the following were observed (labels as recorded):

| What | Tool | Result |
|---|---|---|
| Tenant readiness | `ffia fabric readiness` (GET only) | READY: F8 active, bound workspace on capacity, required settings enabled. GitHub workspace sync off (optional, not used by HC-01) |
| Live smoke test | `FFIA_FABRIC_LIVE=1 pytest -m live` | VERIFIED LIVE: passed |
| Router → live provider | API `POST /api/v1/fabric/read` in HYBRID | VERIFIED LIVE: `list_workspaces` and `list_items` labeled LIVE, `cloud_operation_performed: true`, no fallback |
| Fabric MCP `fabric-readonly` profile | `@microsoft/fabric-mcp@1.4.0` over stdio | VERIFIED LIVE: 16 tools exposed; `core_search-catalog` found the workspace; `onelake_list-workspaces` returned an empty list for the new, empty workspace (cause unverified); `core_create-item` refused by the server as not found |

Readiness also found a defect, now fixed: it had counted a Premium Per User (PP) capacity as
Fabric-capable. PPU cannot host Fabric items, so only F, FT (trial) and P SKUs count now.

Still **REQUIRES TENANT VALIDATION**:

- DAX reconciliation (no semantic model yet);
- the preview List Tables API;
- throttling;
- the reference notebooks on Fabric Spark;
- the scoped writer.

## Trade-offs

- **Live reads are verified in one tenant; the rest is not.** Throttling, Delta writes, OneLake
  paths, DAX reconciliation and the writer still require tenant validation.
- **The rewriter is intentionally small.** New SQL idioms need a rule and a test.
- **The Bronze reference reads strings, where the lab prompt says `inferSchema`.** This is
  documented as a comparison point.
- **List Tables is a preview API.** Its results are labeled PREVIEW.

## Security impact

- No identifiers are committed. Tokens are never logged or returned.
- Live access is opt-in. Writes need two flags, policy, separation of duties and a bound dev
  workspace.
- MCP profiles exclude arbitrary query and data-egress tools from read-only use, and never expose
  destructive tools.

## Operations impact

- New commands: `ffia fabric readiness`, `ffia mcp profiles|render|check` and
  `ffia notebooks render|check`.
- Runbook: [fabric-tenant-readiness.md](../operations/fabric-tenant-readiness.md).

## Offline impact

None on the default experience:

- With `FFIA_FABRIC_LIVE` unset, the container never builds a live client.
- The default MCP profile starts Fabric MCP read-only tools, but every answer still works offline
  through the `ffia-local` fallback, and `ffia demo offline` never uses `.mcp.json`.
- Every live test is skipped unless explicitly enabled.

## Education impact

- The Q24 preview-isolation lesson.
- Lessons now describe real profiles, the provider, the writer and the notebooks with honest
  labels.
- Diagram nodes moved from planned to implemented or tenant-validation.

## Amendment (2026-10-08): Fabric MCP first, `ffia-local` as the fallback

The presenter asked for the repository and Guide HC-01 to use the real Fabric MCP server, with the
local educational server as the fallback.

- The default profile `fabric-first` renders the root `.mcp.json`:
  - Fabric MCP 1.4.0 with `--read-only` and 8 metadata tools;
  - Microsoft Learn;
  - `ffia-local`, declared as `fallback`.

  The previous default, `offline`, remains available.
- `hc01-lab` (Guide HC-01's `.mcp.json`) adds `ffia-local` as its fallback.
- `ffia-local` adds two typed reads through the provider router, `list_fabric_workspaces` and
  `list_fabric_items`, as fallbacks for `core_search-catalog` and `onelake_list-items`.
- **The fallback is an instruction, not automatic failover.** MCP clients do not fail over between
  servers. AGENTS.md (root and guide) requires the agent to:
  - say the Fabric MCP tool is unavailable, with the error;
  - then use the named `ffia-local` tool, labeled LOCAL;
  - for a failed write, only rehearse it (SIMULATED) and never perform a local write.
- Each guide step names its Fabric Skills and its fallback.
- `ffia mcp check` enforces:
  - the default profile is read-only, GA-only and declares the fallback;
  - every committed client configuration declares a fallback server;
  - a write step's fallback is SIMULATED.
- **VERIFIED LIVE (2026-10-08, demo tenant):**
  - MCP handshake with Fabric MCP 1.4.0, which exposed exactly the 8 allow-listed tools;
  - `core_search-catalog` found `mfg_lakehouse` and the data agent;
  - `onelake_list-items` and `onelake_list-tables` (`namespace: dbo`) returned the 6 tables;
  - `ffia-local` over MCP returned LOCAL offline and LIVE through the router in hybrid mode.

## Revisit trigger

- A successful tenant run, or a Fabric MCP or Power BI Modeling MCP release. Re-capture the tool
  catalog and re-pin.
- A GA replacement for List Tables.
- A Fabric runtime change to Spark 4.

## Authoritative references

`fabric-rest-identity`, `fabric-notebook-definition`, `fabric-create-lakehouse`,
`fabric-lakehouse-list-tables`, `fabric-admin-tenant-settings`, `powerbi-execute-queries`,
`fabric-runtime-1-3`, `fabric-trial`, `fabric-mcp-local`, `powerbi-authoring-mcp`
(see `docs/research/sources.yaml`).
