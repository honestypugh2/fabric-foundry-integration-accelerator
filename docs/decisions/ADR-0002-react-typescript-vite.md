# ADR-0002: React + TypeScript + Vite for the educational application

- Status: Accepted
- Date: 2026-10-05

## Context

The interactive educational application is a first-class deliverable: an architecture explorer,
a pattern explorer, learning paths, labs, guides and demo mode. The brief mandates React,
TypeScript and Vite, with no other framework. It also requires strict TypeScript, ESLint,
formatting, Vitest, React Testing Library, accessibility, and latest stable, non-vulnerable
packages only.

## Options

1. React 19 + TypeScript + Vite 8 (single-page application) with npm
2. The same stack with pnpm
3. A framework such as Next.js (excluded by the brief)

## Decision

React 19.3.0, TypeScript 6.0.3 (strict), Vite 8.3.2, Vitest 5.0.3, React Testing Library 16.3.3,
ESLint 10.12.0 with typescript-eslint 8.71.1 (`strictTypeChecked`), Prettier 3.9.9 and axe-core
4.14.0.

- **npm**, with a committed `package-lock.json` and `--save-exact` pins.
- Node 24 LTS now, with Node 26 in the CI matrix.
- Runtime libraries (router, query, Markdown, Mermaid, accessible components) are added in
  Phase 4, when they are first used.

## Rationale

- These are the latest stable releases, verified on the npm registry on 2026-10-05.
- Installing them together showed no peer conflicts, and `npm audit` reported 0
  vulnerabilities.
- npm ships with Node; pnpm adds a tool without a requirement that justifies it.

## Trade-offs

- **TypeScript 7.0.2 is the latest, but typescript-eslint 8.71.x requires `<6.1.0`.**
  TypeScript stays at 6.0.3 until typescript-eslint supports 7.x. Dependabot ignores
  TypeScript `>=6.1.0`.
- **`eslint-plugin-jsx-a11y` does not support ESLint 10** and has had no release since 2024-10.
  Accessibility is enforced with axe-core assertions in tests, plus one Playwright and axe
  offline smoke test in a later phase.

## Security impact

- No credentials or Azure SDKs in the browser.
- `dangerouslySetInnerHTML` is banned by lint.
- A Content Security Policy is set in `index.html`.
- CI fails on HIGH/CRITICAL `npm audit` findings.

## Operations impact

- `npm ci` in CI on Node 24 and 26.
- Actions pinned by commit SHA.

## Offline impact

- The built application is static and runs fully offline against the local backend.

## Education impact

- Learning content is structured data rendered by components, not hard-coded copy.
- Accessibility and keyboard navigation are part of the teaching quality bar.

## Revisit trigger

- typescript-eslint supports TypeScript 7.
- Node 26 becomes LTS (2026-10-28).
- An accessibility lint plugin supports ESLint 10.

## Authoritative references

- `node-release-schedule` in `docs/research/sources.yaml`
- npm registry metadata for each package (retrieved 2026-10-05)
