# Use-case authoring verification

Recorded **2026-10-13**. **LOCAL authoring gate: PASSED. Connected gate: PARTIAL.
Production gate: NOT CERTIFIED.**

This record covers the authoring implementation based on revision `e90b09c` plus the DQ-01
worktree changes. It is not a tagged release or an actual GitHub workflow result. The
implementation and this record must be reviewed together before publishing a release.

## Requirements and observed proof

| Requirement | Evidence | Scope |
|---|---|---|
| Extend without scenario-specific UI | DQ-01 registered in guide/workshop YAML; real API catalogue, story, all six steps and shared UI runner | LOCAL |
| Reuse rather than fork | Manufacturing profile/baseline, existing five-level lessons, manufacturing draw.io/PNG and presenter handout | LOCAL authored content |
| Reject broken authoring assets | Parameterized tests for instructions, baseline identity/JSON/path, diagram source/PNG, presenter source/handout, skills, tools, fallback and policy | LOCAL |
| Exact quality threshold | All nine categories match committed expected counts; `--check` exits nonzero for a scratch mismatch | LOCAL deterministic calculation |
| Authority stays separate | Real API plan, self-approval refusal, independent approval, SIMULATED execution, verification, duplicate-execution refusal and audit | SIMULATED notebook creation only |
| Prove another extension | An isolated fourth guide copied from the template is registered, validated and served without core changes | LOCAL regression |
| No cloud requirement | Network-blocked offline tests; isolated checkout without private dotenv or bindings | LOCAL |
| Shared UI usability | Six steps at 1440px and 390px; actual offline API rehearsal; no detected WCAG-tagged axe violations, overflow or browser errors | LOCAL interface evidence |

## Commands and results

```bash
source .venv/bin/activate
ffia education check --min-coverage 1.0
ffia mfg quality --check --json
pytest tests/offline/test_use_case_authoring.py --no-cov -q
```

**PASSED:** 21 lessons at five levels, 130 knowledge checks, 30/30 completeness; nine quality
categories reconciled; 20 offline authoring tests passed. These architecture-completeness
counts are not live-certification percentages.

```bash
FFIA_ENVIRONMENT=offline FFIA_FABRIC_LIVE=0 FFIA_FOUNDRY_LIVE=0 \
  FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING='' make validate
```

**PASSED:**

- Backend: 638 passed, one opt-in live test skipped; 96.05% coverage.
- Frontend: 100 passed; 98.86% statements, 86.58% branches.
- Python/TypeScript strict types, lint/format, package/bundle builds.
- Data determinism, generated schemas/sources/diagrams, MCP, notebooks, skills, prompts,
  talk tracks, harness and recorded bake-off drift checks.
- LOCAL agent evaluation: 5/5; offline demo passed.
- Dependency audits: no known Python vulnerabilities; npm reported zero vulnerabilities.
- CycloneDX schemas/runtime pins passed: 163 Python and 345 frontend components.
- Privacy scan at that gate: 772 files, zero findings.

The session-only browser verifier checked 12 step/viewport combinations against the real
offline API and completed a SIMULATED rehearsal. No cloud tools were invoked by that test.

### Pre-commit refresh: 2026-10-13

`make validate` **PASSED** against the combined authoring, tooling and evidence changes:
639 backend tests passed, one opt-in live test skipped, 96.05% backend coverage; 100 frontend
tests passed, 98.86% statements and 86.58% branches. Lint, strict types, both builds, dependency
audits, SBOM validation, generated-artifact checks, LOCAL evaluation and offline demo passed.
The privacy gate checked 775 files with zero findings.

Review then corrected the workshop's stale trace-verification gap: server-side traces were
observed, but complete assistant answers and revenue reconciliation remain unverified.
`make fixtures` regenerated the API fixtures. `ffia education check --min-coverage 1.0` and
`pytest tests/contract/test_frontend_fixtures.py tests/offline/test_use_case_authoring.py tests/unit/test_education.py --no-cov`
**PASSED**, with 83 targeted tests. These checks do not execute or certify connected workloads.

### Isolated checkout rehearsal

Materialized tracked HEAD plus the authoring changes into a temporary checkout. No private
dotenv or customer binding files were copied. The initial check confirmed missing local tools;
created and activated a new Python 3.14 virtual environment, then restored `uv.lock` using
`uv sync --frozen --offline`. Restored frontend dependencies with `npm ci --offline` after the
fresh typecheck demonstrated missing packages.

**PASSED:** education gate, exact quality baseline, 20 network-blocked authoring tests,
offline demo, frontend strict types, 28 targeted guide/workshop tests and production bundle.
The temporary checkout was cleaned up. This is an isolated snapshot rehearsal, not evidence
that a remote clone of uncommitted changes already contains the implementation.

## Explicit warnings

The existing Power BI Modeling MCP profile has no pinned tool catalogue. Education checks
disclose three HC-01 steps whose documented operation names require connected validation.
Their tool contracts were not certified offline. Validated Fabric allowlists and local
tool/skill references remain blocking checks; a warning grants no tool or write authority.

## Connected verification: sign-in corrected, execution gates open

An actual read-only call used **Microsoft Fabric / `fabric-mcp` / `core_search-catalog`**,
searching the synthetic manufacturing lakehouse name with a Lakehouse filter and page size five.
The server returned HTTP 200, but the returned metadata did not match the requested synthetic
scope. No returned tenant/workspace/item identifiers or unrelated resource names are retained
in public evidence.

This proves only that the tool returned a response. It does **not** establish the intended demo
tenant, an exact target match, quality calculations, notebook execution or publication.
No LOCAL fallback was used to convert that response into a connected-verification pass.
The operator chose to pause and confirm/correct MCP sign-in before more tenant inspection.

After the operator confirmed corrected sign-in, the scoped retry established:

- Azure CLI tenant/subscription matched the private bindings.
- Read-only Fabric readiness passed authentication, API access, active capacity and the
  bound dev workspace. Required tenant settings passed; optional GitHub sync warned and
  preview checks were skipped.
- Read-only Foundry readiness passed resource/project/deployment/data-plane metadata checks
  and checks for the existing synthetic agent and Fabric connection. No inference ran.
- Actual **Microsoft Fabric / `fabric-mcp` / `core_search-catalog`** returned exactly one
  expected synthetic manufacturing lakehouse; its workspace matched the private dev binding.
- Actual **Microsoft Fabric / `fabric-mcp` / `onelake_list-items`** succeeded within that
  workspace and returned the expected manufacturing lakehouse/data-agent items.

Identifiers remain private. These checks certify metadata access and target scope only,
not notebook outputs, agent answer quality, monitoring ingestion or publication.

The operator subsequently installed Fabric Data Engineering 1.26.0 and Power BI Authoring
1.0.0 in the Linux extension host. Actual MCP discovery succeeded for both servers.
Power BI read-only startup was independently checked. The extension-managed notebook MCP
catalogue has no publish/run tool; publication uses a separate VS Code extension tool and
execution uses the remote kernel. See [tooling setup](notebook-powerbi-tooling.md).
After explicit operator approval, **LOCAL / Power BI Authoring MCP / `accept_eula`** completed,
and `connection_operations` with `ListConnections` returned an empty connection array. A fresh
server process verified persistence without accepting again. No model was connected.

Actual **Microsoft Fabric / extension-managed `fabric-notebook-mcp` / `list_artifacts`**
also succeeded for the expected synthetic lakehouse within the privately bound dev workspace.
Independent response comparison verified the exact workspace binding, name/type and single
result. This extends LIVE metadata evidence, not notebook/model execution evidence.
Native `fabricPublishNotebook` was unavailable in the earlier SDK chat's exposed inventory.
The operator reported enabling tools and reconnecting; a subsequent discovery retry still
did not expose the native publication/workspace tools. This is an unresolved client-exposure
boundary, not an extension installation failure. Repeating reloads is not additional evidence.
On the subsequent resumed session the native tools became exposed. `fabricWorkspaceInfo`
first reported a mismatched personal workspace; after the operator switched workspaces, the
next call matched the private dev binding exactly. Actual `fabricListNotebook` returned no
entries, and an independent workspace-scoped `fabric-notebook-mcp` `list_artifacts` call
confirmed zero Notebook items. No publication tool was invoked.
The reviewed HC-01 reference notebooks also passed `ffia notebooks check` (LOCAL).
The operator selected completing HC-01 as well as continuing MFG-01/DQ-01. Recommended
sequencing keeps HC-01 in a separate dedicated lab workspace and retains the existing dev
workspace for manufacturing. HC-01 step 03 explicitly assigns workspace creation to the
operator in the Fabric portal; no automatic workspace creation or alternate transport was used.
An isolated HC-01 export completed locally, and `sha256sum -c SHA256SUMS` passed for all seven
synthetic CSVs. The export is source-preparation evidence, not OneLake upload evidence.
The operator then requested local HC-01 preparation while continuing MFG-01/DQ-01. The
isolated lab now includes all seven exported CSVs, three reviewed Fabric Git-format notebook
definitions, scoped instructions, the expected baseline, safe Power BI startup settings and
authoritative HC-01 MCP renderings for VS Code and Claude. Independent comparison verified
the copied definitions, baseline and both renderings. No server was started from those configs.
The LOCAL HC build matched the baseline: 24 tables and 58/58 checks passed. LOCAL MFG quality
reconciled all nine categories, and the Enclosures brief reproduced the independent baseline.
Extension activation generated local dependency stubs and private workspace/VFS caches.
Root-scoped ignore rules now isolate them without deleting state or excluding public source
files. The subsequent privacy scan passed: 776 files, zero findings.

## Resume boundary

1. Native notebook tools are now exposed and the selected workspace matches the private dev
   binding. Confirm which use case and exact target the next publication plan covers; the
   reviewed HC-01 notebooks consume seven healthcare CSVs, not the manufacturing dataset.
   Restart Power BI read-only without automatic EULA acceptance;
   this operator has explicitly authorized acceptance, which was executed and verified.
   Root app bindings do not configure external servers.
2. Confirm the extension's sign-in, selected workspace and remote Spark kernel privately.
   HC-01 expects a dedicated lab workspace; an existing populated manufacturing workspace
   is not automatically its approved target.
3. Refresh capacity/readiness before capacity-dependent work. Capacity was active at the
   resumed check; actual billing/cost totals have not been queried.
4. Plan exact-target mutations, check duplicates, obtain separate human approval, execute only
   the approved operations, independently verify outputs and retain audit/rollback evidence.
5. Complete unresolved agent answer checks; server-side traces are now observed as described
   below. Scheduling/delivery still needs separate use-case-specific approval and verification.
6. Complete applicable production controls and actual release checks before certification.

No resource deployment, data mutation, capacity change, notebook run, publication, schedule, GitHub workflow
dispatch or Claude Code bake-off was performed. Capacity/readiness was refreshed; billing
and actual cost totals were not queried.
GitHub execution remains deferred. Full connected and production gates remain open.

## MFG-01/DQ-01: approved invocation and monitoring checks

Actual **Microsoft Foundry / Azure MCP / `agent_get`** inspected only the existing
`sales-insights-agent`: prompt agent, active version 3, expected Fabric connection. Private
binding comparison confirmed the connection. The sample agent-creation script was not run.

The operator explicitly approved two synthetic **`agent_invoke`** calls against version 3:
September/August Enclosures revenue and growth, then excess duplicate order-line count.
Both MCP calls returned HTTP 504. Neither was retried; no new agent version was created.
The operator also confirmed the dev Application Insights target and bounded trace queries.

Actual **Azure Monitor / Azure MCP / `monitor_resource_log_query`** observed recent
server-side spans for both questions. Exact user-message comparison correlated the revenue
trace; the duplicate trace showed the exact approved question. Fabric tool spans are present.
Span-level success flags do not prove a numeric answer or baseline reconciliation.
The first monitoring attempt cancelled immediately at a client timeout of zero seconds;
an explicit 60-second timeout allowed the read-only query to succeed.

The revenue trace contains a Fabric response reporting input-length rejection rather than
numeric results. It also shows a shorter follow-up query. This is observed tool-response
content, not independent proof of the downstream SQL error or its root cause.

With separate explicit approval, **Microsoft Foundry / Python SDK / `responses.retrieve`**
read only the two existing response IDs recovered from traces. No `responses.create` call
was made. Revenue retrieval returned HTTP 404. Duplicate retrieval returned a top-level
completed response with a completed Fabric preview call and its result document:

| Check | Expected | Observed | Result and boundary |
|---|---:|---:|---|
| Excess duplicate order-line records | 12 | 12 | PREVIEW Fabric tool result matches independent baseline |
| September/August Enclosures revenue and growth | Independent LOCAL brief | Not verified | MCP timed out; existing revenue response was not retrieved |
| All nine quality categories | Independent LOCAL quality baseline | Nine LOCAL categories matched | LOCAL only; not a nine-category live-agent pass |

The duplicate result defines the key as `(order_id, line_number)` and excess duplicates as
the sum of `group_count - 1`. Its source workspace independently matched the private dev
binding. The response also describes 12 duplicate keys and 24 rows in duplicate groups;
these are distinct metrics, not additive counts.
The Fabric output item still reports `in_progress`, and no final assistant message was
recovered. Therefore the result certifies the recovered tool payload's baseline match,
not a fully verified end-to-end assistant answer. Raw IDs, source URLs and results remain private.

Remaining work: establish the HC dedicated lab workspace through its assigned portal step,
plan and approve HC lakehouse/upload/publication/run/model/report operations, diagnose the
revenue timeout/tool limit without duplicate inference, and verify final assistant answers.
Production controls, schedule/delivery, actual billing and release checks remain uncertified.

## Interface capture

![DQ-01 offline use-case page](../architecture/screenshots/app-dq01-local.png)

Synthetic LOCAL interface capture, not live Fabric/Foundry evidence. The shared manufacturing
architecture includes connected branches that remain outside DQ-01's offline acceptance scope.
