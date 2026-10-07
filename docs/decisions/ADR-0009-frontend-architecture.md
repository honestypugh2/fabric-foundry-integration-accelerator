# ADR-0009: Frontend architecture and typed API contracts

- Status: Accepted
- Date: 2026-10-07

## Context

The educational app must show execution state honestly, work against a local control plane with
no credentials in the browser, and stay correct as backend models evolve. Phase 0 planned React
Router, TanStack Query, Zod, a Markdown pipeline, react-aria-components, Mermaid and
openapi-typescript.

## Options

1. A component library plus generated clients.
2. Hand-written fetch calls and TypeScript interfaces.
3. One central client with Zod runtime validation, and TypeScript types generated from the
   backend OpenAPI document, checked against each Zod view at compile time.

## Decision

Option 3, with these choices (all exact pins, latest stable on 2026-10-07):

| Need | Choice |
|---|---|
| Routing | `react-router` 8.4.0, declarative mode, lazy-loaded feature pages |
| Server state | `@tanstack/react-query` 5.104.1 |
| Runtime validation | `zod` 4.6.5 |
| Lesson Markdown | `react-markdown` 10.1.0 + `remark-gfm` 4.0.1 + `rehype-sanitize` 6.0.0, `skipHtml` |
| Contract types | `ffia schemas export` writes `schemas/openapi.json` and `frontend/src/api/generated.ts` |

**Deviations from the Phase 0 plan:**

- `openapi-typescript` is **not** used. 7.13.0 has a TypeScript `^5.x` peer and we pin 6.0.3.
  A small, tested generator (`api/typescript.py`) translates the JSON Schema subset that Pydantic
  and FastAPI emit, and fails loudly on anything else.
- `react-aria-components` is **not** added. Native elements (radio groups, checkboxes,
  `details`, buttons with `aria-pressed`) cover every interaction so far. Add it only when a
  widget needs it.
- Mermaid is deferred until a lesson needs a diagram that the React-rendered architecture
  explorer cannot show.

`contracts.ts` declares a Zod view per response. `contractChecks` asserts that each generated
type, with server-defaulted fields made required, satisfies the view. A renamed, removed or
retyped field fails `npm run typecheck`.

## Rationale

- Runtime validation catches a wrong server. Compile-time checks catch drift.
- No business rules live in the UI. Policy, duplicates, approval and grading stay server-side.
  Knowledge-check answers are never sent until a learner answers.

## Trade-offs

- The generator must grow when new JSON Schema constructs appear. It raises
  `UnsupportedSchemaError` so this is never silent.
- Views are projections, so the UI ignores fields it does not use.

## Security impact

- No credentials, tokens or API hosts are in the bundle. The dev server proxies `/api` to the
  loopback control plane.
- Markdown is sanitized, and raw HTML is skipped and rejected at content load time.
- ESLint forbids `any` and `dangerouslySetInnerHTML`.

## Operations impact

- `make schemas` regenerates the types, and `ffia schemas check` (in `make validate`) fails when
  they are stale.
- `make fixtures` re-exports test fixtures from the real API. A contract test validates them
  against the Pydantic models.

## Offline impact

- The app runs fully offline against `make run-api`. When the control plane is unreachable,
  every view says so and nothing is shown as live.

## Education impact

- The architecture explorer, lessons and labs re-render per level (Executive to L400). The level
  is stored only in the browser.

## Revisit trigger

- `openapi-typescript` supports TypeScript 6.
- A widget needs complex accessible behavior (combobox, dialog stacking) beyond native elements.

## Authoritative references

- [frontend.md](../architecture/frontend.md)
