# Structured educational content

Content is data, not React copy. The control plane validates it at startup, and
`make education-check` validates it in CI.

| Path | Contents |
|---|---|
| `<area>/<lesson-id>/` | `lesson.yaml`, `executive.md`, `l100.md`, `l200.md`, `l300.md`, `l400.md`, `checks.yaml` |
| `labs/<lab-id>/lab.yaml` | Eleven stages in the fixed order LEARN → … → PRODUCTION NOTES |
| `architecture/explorer.yaml` | Layers, components (with per-level descriptions) and flows |
| `patterns/catalog.yaml` | The 24-pattern catalog |
| `completeness.yaml` | The 30-question architecture completeness gate |

Areas: `architecture`, `patterns`, `fabric`, `foundry`, `fabric-iq`, `data-agents`, `mcp`,
`copilot`, `claude`, `agentic-data-engineering`, `recovery`, `security`, `evaluation`.

Rules (enforced by `education/lessons.py`; JSON Schemas are in `schemas/`):

- **Levels:** all five level bodies are required. Each is Markdown of at least 200 characters,
  with no raw HTML outside code.
- **Checks:** at least one knowledge check per level, with unique choices and a valid answer
  index.
- **Evidence:** every claim carries an evidence category (`SIMULATED LOCALLY`,
  `DOCUMENTED FABRIC BEHAVIOR`, `DOCUMENTED BEHAVIOR`, `REQUIRES TENANT VALIDATION`,
  `ASSUMPTION`, `PRODUCTION RECOMMENDATION`, `PREVIEW LIMITATION`).
- **References:** sources must exist in `docs/research/sources.yaml`. Pattern, lab, guide and
  prerequisite references must exist.
- **Content:** customer-neutral and synthetic only, with no clinical advice. Run
  `ffia privacy scan`.

After changing content, run `make education-check`. Run `make fixtures` when API models change;
it re-exports the frontend test fixtures.
