# Frontend (educational app)

React 19 + TypeScript (strict) + Vite. It runs against the local control plane:

```bash
make run          # API on :8000 and the Vite dev server on :5173 (proxying /api)
# or separately: make run-api  and  make run-frontend
```

## Structure (`frontend/src/`)

| Path | Purpose |
|---|---|
| `api/client.ts` | The single API client. Distinguishes `ApiError`, `ControlPlaneUnreachableError` and `ContractError`. |
| `api/generated.ts` | **Generated** from `schemas/openapi.json` by `ffia schemas export`. Do not edit. |
| `api/contracts.ts` | Zod views of each response, with compile-time `contractChecks` against the generated types |
| `api/hooks.ts` | TanStack Query hooks, one per endpoint |
| `app/` | Routes (lazy-loaded pages), layout, learning-level context, page titles, local progress |
| `components/` | Status bar, level switcher, badges, provenance, query states, sanitized Markdown, copyable prompts |
| `features/` | `home`, `architecture`, `patterns`, `learn`, `labs`, `guides`, `data`, `agents`, `bakeoff`, `demo` |
| `test/` | Fetch mock, fixtures exported from the real API, render helper |

## Pages

| Route | What it does |
|---|---|
| `/` | The central lesson, starting points, completeness coverage |
| `/architecture/:view` | **Architecture Studio**: interactive diagrams (reference, production, system, MCP topology, maturity ladder, HC-01, LIVE/HYBRID/OFFLINE) built layer by layer, request traces with a presenter cue, an inspector that follows the level, a live runtime overlay, a text alternative and draw.io download. `/architecture/components` keeps the per-layer component catalog. |
| `/patterns`, `/patterns/:id` | Search and filter 24 patterns, compare up to three, recommend by need, pattern detail with lessons |
| `/learn`, `/learn/:id` | Lessons by area; reader with level tabs, evidence categories, prompts, server-graded checks |
| `/labs`, `/labs/:id` | Eleven-stage labs with commands and local progress |
| `/guides`, `/guides/:id/:step` | **Guide runner** (HC-01): provider/server/tool, Copilot and Claude Code prompts, checkpoint, evidence checklist, "not evidence", offline equivalent, where the step happens on the HC-01 diagram, and rehearsal of the step's governed write |
| `/data` | Lakehouse tables and previews through the router, and evaluation against the baseline |
| `/agent` | **Sales insights agent** (Guide MFG-01): ask through the agent router, see the execution label, provider, fallback, grounding and tool calls, run the Agent Framework monthly-insights workflow (drafts per team, review gate, nothing sent), search policy knowledge with citations (PREVIEW flag; SIMULATED offline), and run the evaluation suite. Suggested questions come from `config/evaluations/<suite>.yaml`. LOCAL offline; the live Foundry agent (PREVIEW tool) only with `FFIA_FOUNDRY_LIVE=1`. |
| `/bakeoff`, `/bakeoff/runs/:id` | **Bake-off**: the five tasks with exact prompts and how to run them, the scorecard by harness and model (UNAVAILABLE until a real run is recorded), and a replay viewer for recorded runs |
| `/demo` | Readiness probes and the ten-act offline demo |

## Rules

- **Execution state is always visible.** The status bar shows mode, providers, MCP, identity,
  write mode, preview flags and learning level from `/api/v1/runtime/status`. When the API is
  down it says so, and nothing implies a live connection.
- **No business rules in the UI.** Policy, duplicate checks, separation of duties and grading all
  happen in the backend. The rehearsal panel shows the backend's decisions, including refusals.
- **Accessibility.** Semantic landmarks, a skip link, one `h1` per page, visible focus, native
  form controls, live regions for results, keyboard-scrollable tables, and text labels that
  never rely on color alone. axe-core runs in tests.
- **Privacy.** No credentials or identifiers in the browser. Learning level and progress are
  stored in `localStorage` only.

See [ADR-0009](../decisions/ADR-0009-frontend-architecture.md).
