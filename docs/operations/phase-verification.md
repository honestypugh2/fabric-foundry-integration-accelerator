# Phase verification

Reviewed against the original nine-phase proposal, not merely the README checkmarks.
**Implementation completion is not the same as live certification or production readiness.**

| Phase | Verified repository outcome | Qualification / remaining evidence |
|---|---|---|
| 0 Research and architecture | Source registry, architecture views and decision records | Sources and preview availability are dated; revalidate before production |
| 1 Foundation | Locked Python/uv and React/TypeScript/Vite builds, strict checks and instructions | GitHub execution is separate from local tooling |
| 2 Offline data | Synthetic medallion, deterministic baselines, LOCAL Fabric and recovery drill | Open Mirroring recovery is SIMULATED, not a tenant recovery operation |
| 3 Control plane | Typed provider ports, router/breakers, approvals, audit, API and local MCP | Deterministic LOCAL agent and Agent Framework workflow are distinct from a hosted agent |
| 4 Educational app | Workshop navigation, both Use Cases, practical/research lenses, 21 five-level lessons, five labs, 25-pattern teaching coverage and 30/30 architecture coverage | Teaching coverage and learner checkpoints are not implemented-lab or live-certification badges |
| 5 Fabric integration | Read-only application REST provider, scoped gated writer, MCP profiles/skills/notebooks | Original Core/IQ MCP adapter scope is represented by external profiles/documented patterns, not independent in-process live adapters. Fresh Guide 1 MCP, notebook and Power BI execution is not certified by an application REST read |
| 6 Foundry integration | Stable SDK, existing-agent adapter, evaluation, Agent Framework workflow, client tracing and connected demo targets | Stable core + SDK substitutes for the originally proposed preview adapter package (ADR-0013). Foundry IQ/OneLake knowledge is a flagged LOCAL analog. Fabric tool is PREVIEW. New server-side traces and cloud evaluation service are not certified here |
| 7 Copilot and Claude Code | Shared profiles, skills, prompt packs and ten Copilot CLI model recordings | Claude Code remains DOCUMENTED ONLY by user decision; this is not a completed cross-harness bake-off |
| 8 Security/CI/production | Threat model, production checklist, CodeQL/release workflows, SBOM and evaluation gates | GitHub Actions is disabled; GitHub quality/CodeQL/release execution is DEFERRED by user decision. Production checklist is not completed tenant certification |
| 9 Final validation | Local release gates and bounded current live checks | Not a new publication, full Guide 1 live run, server-trace verification or production sign-off |

## Current connected evidence (2026-10-09)

- Fabric application readiness: PASS, including active F8 capacity and bound dev workspace.
  Optional GitHub workspace-sync tenant setting remains a warning; preview switches are not required.
- Foundry readiness: resource, project, deployment, data-plane, existing agent and Fabric
  connection PASS. These are metadata GETs, not inference evidence.
- Running app: `/health` returns 200; runtime HYBRID, live writes disabled.
  An actual routed workspace read returned LIVE, `fallback_used=false`,
  `cloud_operation_performed=true`, and two workspaces. No identifiers are included here.
- `ffia demo live --json`: PASSED, `live_verified=true`; Fabric read LIVE and one baseline
  question PASSED, grounded with no fallback. Foundry reported
  `fabric_dataagent_preview_call`; its answer is correctly labeled PREVIEW.
  This is application REST/SDK evidence, **not Fabric MCP execution**.
- Root `.env` is populated with named Azure, Fabric and Foundry variables, loaded by typed
  settings, and ignored by Git. Values are not printed. Entra authentication requires no static key.
- After populating the cloud variables and restarting the app, its actual HYBRID API returned
  LIVE for the Fabric read and PREVIEW for the Foundry answer, both with
  `cloud_operation_performed=true` and no fallback. The agent's reported Fabric tool calls
  and the Enclosures/+55.78% baseline comparison passed. This verifies the environment-backed
  application path, not merely the earlier strict-LIVE CLI configuration.
- `FFIA_FABRIC_LIVE=1 pytest -m live tests/integration/test_fabric_live_readonly.py -q --no-cov`:
  PASSED (one test), using the same environment resolver for pinned-tenant readiness and
  bound-workspace visibility. The test performs only token acquisition and REST GETs.
- HYBRID missing-binding/outage fallback, strict LIVE refusal and write gating are covered by
  offline tests. A fallback cannot pass the live-agent evaluation gate.

The connected demo is intentionally bounded to one synthetic question; it does not re-run
the complete five-case live evaluation, send a monthly brief or modify data.
Previous five-case live evidence remains dated, not a new run.

## Current LOCAL validation after the workshop redesign

- `ruff format --check src tests`, `ruff check src tests`, `pyright`: PASSED.
- Latest full `pytest --cov --cov-report=term-missing -q`: 616 PASSED, one opt-in live test skipped;
  95.96% coverage, above the 85% gate. Private dotenv files are isolated from offline tests.
- Frontend lint, formatting, strict types, `npm run test:coverage` and `npm run build`: PASSED;
  99 tests, 98.75% statement and 86.28% branch coverage.
- Evidence-page follow-up: targeted workshop/education/API/fixture regressions, 100 PASSED;
  strict Python checks passed. Existing Azure/Fabric verification is now surfaced as dated
  resource and operation records, with separate OFFLINE/HYBRID/LIVE instructions.
- `ffia demo offline --json`: PASSED; zero LIVE and cloud operations.
- Sources, schemas, education (30/30), talk tracks, prompts, diagrams, MCP profiles, notebooks,
  skills, bake-off and harness checks: PASSED.
- Separate LOCAL Playwright browser: seven redesigned routes at 1440px and 390px,
  no detected WCAG-tagged axe violations or horizontal overflow. Legacy deep redirects and
  asynchronous journey/evidence anchors passed. No browser errors were recorded.
- All six verification download links returned the exact bytes of their two public source
  documents. The dark L400 evidence page also passed automated WCAG-tagged axe checks.
- Ten PNGs exported directly from draw.io: CRCs, decompressed pixels and embedded Architecture
  pages verified against their sources. Redesigned screenshots are interface evidence, not
  fresh cloud-operation proof.
- `ffia privacy scan`: zero findings; private `.env` remains ignored. `git diff --check`: PASSED.

These checks do not replace the deferred GitHub runs or claim fresh dependency audit/SBOM
generation; dependencies did not change.

## Not verified in this session

Fabric MCP/browser tools were not discoverable through the session tool search. No REST
replacement was used for an assigned Guide 1 MCP step. Guide screenshots are captured with
local browser automation and are UI/configuration evidence, not publication evidence.
Power BI publication, hosted/Core/Fabric IQ MCP execution, Azure knowledge indexing,
server-side agent trace ingestion, GitHub checks and a real Claude Code bake-off remain
separate verification or explicitly documented scope.

See the [repository map](../architecture/repository-map.md),
[release gates](release-validation.md) and [environment configuration](environment-configuration.md).
Capacity is active at the last check and incurs billing; the presenter should pause it after use.
