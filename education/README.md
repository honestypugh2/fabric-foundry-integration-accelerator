# Structured educational content

Content is data, not React copy. The control plane validates it at startup, and
`make education-check` validates it in CI.

| Path | Contents |
|---|---|
| `<area>/<lesson-id>/` | `lesson.yaml`, `executive.md`, `l100.md`, `l200.md`, `l300.md`, `l400.md`, `checks.yaml` |
| `labs/<lab-id>/lab.yaml` | Eleven stages in the fixed order LEARN → … → PRODUCTION NOTES |
| `architecture/explorer.yaml` | Layers, components (with per-level descriptions) and flows |
| `architecture/views/<id>.yaml` | Diagram views (grid nodes, edges, zones, bands, build steps, traces). Rendered in the app, as draw.io files and in `docs/architecture` |
| `patterns/catalog.yaml` | The 25-pattern catalog, including optional spec-driven delivery |
| `workshop.yaml` | Outcome-led journeys, practical contracts, applied-research lenses, use-case stories and dated evidence |
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
  `ASSUMPTION`, `PRODUCTION RECOMMENDATION`, `PREVIEW LIMITATION`, `VERIFIED LIVE`).
- **References:** sources must exist in `docs/research/sources.yaml`. Pattern, lab, guide and
  prerequisite references must exist.
- **Content:** customer-neutral and synthetic only, with no clinical advice. Run
  `ffia privacy scan`.
- **Instructional contract:** when a workshop registry is present, every lesson needs a
  what/why/when/how brief, expected result, recovery guidance and research lens. Research
  lenses include foundations, conceptual evolution, hypothesis, experiment, baseline,
  metrics, limitations and resolvable sources.
- **Use-case contract:** every registered guide needs a business-to-build story; an unknown
  story or a missing registered story fails validation.

After changing content, run `make education-check` (all 30 completeness questions must be
answered). Refresh affected frontend fixtures after API model or content changes.
The production-readiness lesson covers customization, threats, secrets, Git/CI releases and
cost controls, including P14 secure deployment, P15 gateway governance and P18 overlays, at all
five levels. Domain/agent composition covers P02/P13; enrichment and event context covers P05/P07.
All 25 patterns link to five-level teaching. Missing labs and live evidence remain visible.
Tenant-specific production checks remain explicitly unverified.

See [workshop learning](../docs/operations/workshop-learning.md) and
[use-case onboarding](../docs/operations/use-case-onboarding.md). The architecture completeness
gate measures linked content presence, not pedagogy, production readiness or live certification.
