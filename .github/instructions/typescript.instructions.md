---
applyTo: "frontend/**/*.ts,frontend/**/*.tsx"
---

# TypeScript / React instructions

- React + TypeScript strict + Vite. No other application framework.
- Use typed API contracts and a single central API client (added in Phase 4).
- Keep business rules in the backend; never duplicate them in the UI.
- Build accessible, semantic HTML with keyboard navigation and visible focus. Target WCAG 2.2
  AA practices.
- Every data view handles loading, error and offline states explicitly.
- Do not use `any`. Do not use `dangerouslySetInnerHTML`; render Markdown through the sanitized
  renderer.
- The UI must always show execution state (mode, providers, MCP, identity, write mode,
  learning level, preview flags). Never imply a live connection that does not exist.
- Tests use Vitest with React Testing Library, plus axe-core assertions for accessibility.
