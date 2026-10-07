# ADR-0010: Education content as validated data, with a completeness gate

- Status: Accepted
- Date: 2026-10-07

## Context

The accelerator teaches Executive, L100, L200, L300 and L400 audiences, and future Use-Case
Guides will add content. Content hard-coded in React would drift, could not be validated, and
could not be reused by agents or other surfaces.

## Options

1. Lesson copy in React components.
2. Free-form Markdown folders.
3. Structured data validated by Pydantic: `lesson.yaml`, five level bodies, `checks.yaml`, lab
   files with a fixed stage order, an architecture map and a completeness gate.

## Decision

Option 3 (`education/lessons.py`).

- **Lessons** live in `education/<area>/<id>/`.
  - Each lesson needs all five level bodies, at least 200 characters each.
  - Raw HTML outside code is rejected.
  - Each lesson needs at least one knowledge check per level.
  - Every claim carries an evidence category.
  - Sources must exist in `docs/research/sources.yaml`.
- **Labs** live in `education/labs/<id>/lab.yaml`. They must follow LEARN → SEE → BUILD → INSPECT
  → BREAK IT → RECOVER → VERIFY → GO DEEPER → TRY WITH COPILOT → TRY WITH CLAUDE CODE →
  PRODUCTION NOTES exactly.
- **The architecture map** (`education/architecture/explorer.yaml`) holds layers, components with
  per-level descriptions, and flows.
- **The completeness gate** (`education/completeness.yaml`) has 30 questions.
  - Each question is answered by lessons, or names the phase that will answer it.
  - `ffia education check --min-coverage 1.0` becomes the Phase 9 gate.
- **Cross-references are validated at load time:** patterns, sources, labs, guides,
  prerequisites, and completeness → lessons.
- **The API** serves lessons without check answers. `POST
  /api/v1/education/lessons/{id}/checks/{check_id}` grades an answer.

## Rationale

- Content can be reviewed, diffed and validated like code.
- Guides can add lessons and labs without touching the UI.
- Knowledge checks stay honest: answers are graded server-side.

## Trade-offs

- Authors must follow the schema. JSON Schemas (`schemas/lesson.schema.json`,
  `lab.schema.json`, …) document it for editors.

## Security impact

- Content goes through the privacy scan and the raw-HTML guard, and is rendered through the
  sanitizer.

## Operations impact

- `make education-check`. `make validate` runs it.

## Offline impact

- All content is local and needs no network.

## Education impact

- Phase 4 ships 14 lessons, including the anchor patterns P06, P08, P09, P10, P11, P16 and P17,
  plus 5 labs. Coverage is 24 of 30 questions; the other 6 are assigned to Phases 5, 7 and 8.

## Revisit trigger

- A need for per-level labs, translations or richer media.

## Authoritative references

- [learning-paths.md](../education/learning-paths.md)
