# Add a use case without forking the accelerator

**LOCAL engineering workflow.** Public use cases are sanitized and synthetic. Real customer
source material remains outside this repository; real bindings remain in ignored environment
files. No onboarding step grants cloud-write authority.

## Define the outcome and testable assumptions

Start with [readiness gates](use-case-readiness.md) and the
[authoring package](../../guides/_template/README.md). Use
[DQ-01](../../guides/dq-01-synthetic-quality-investigation/README.md) as the asset-reuse example.

1. Define the audience, business problem, measurable outcome and exclusions.
2. Select the smallest relevant patterns from `education/patterns/catalog.yaml`.
3. Identify the ideas and assumptions to test. Before claiming improvement, state a hypothesis
   that can be disproved, a controlled experiment, an independent baseline, metrics and limitations.
4. Use [spec-driven delivery](../../.claude/skills/spec-driven-delivery/SKILL.md) for a new
   cross-layer scenario. Upstream Spec Kit is optional and is not installed by this workflow.

## Register the guide and teaching assets

1. Add a folder under `guides/` and a validated `guide.yaml`. Reuse existing synthetic profiles
   or add a deterministic generator and baseline through the shared profile registry.
2. Give each step an exact tool path, read/write classification, approval requirement, evidence,
   failure modes and offline equivalent. Live writes never redirect to local execution.
3. Add a `use_cases` story to `education/workshop.yaml`, keyed by the guide ID. It explains the
   problem, audience, outcomes, prerequisites, capability stages, questions and production gaps.
4. Add lessons where needed. Every lesson supplies Executive-L400 bodies, knowledge checks and
   a matching instructional brief with an applied-research lens. References resolve through
   `docs/research/sources.yaml`.
5. Add a structured architecture view and export its PNG from draw.io. Register the static
   image in the frontend image component; missing static exports are explicitly disclosed.
6. Reuse a structured presenter talk track and reference its rendered path from the story.

Keep the root MCP profile unless the use case needs a reviewed narrower allowlist. A guide-scoped
MCP file is conditional, not a reason to duplicate connections. Rehearsal operations must exist
in global write policy and be permitted by the selected overlay; the actual plan validator
enforces the overlay at execution time.

Validated registries supply the use-case catalogue and pattern coverage matrix.
There are no two hard-coded scenario switches. A new story uses the same overview and runner.
Historical evidence links do not mark an entire use case live-certified.

## Validate

```bash
ffia prompts render
make fixtures
ffia education check --min-coverage 1.0
ffia prompts check
ffia diagrams check
ffia privacy scan
```

`education check` validates baseline identity, required guide instructions, workshop references,
diagram focus/PNG, presenter source/handout, skills, named MCP tools and policy rehearsal types.
Extension-managed servers without a pinned tool catalogue produce explicit warnings: their
documented operation names remain a connected-validation gap, not an offline tool-contract pass.
Use `--repo-root`, `--guides-root`, `--education-root`, `--config-root` and `--sources` for a
scratch authoring tree. Render sources only after source-registry edits, schemas only after
contract changes, and diagrams/talk tracks only after their authored content changes.

Run targeted Python, frontend and accessibility tests for the affected contracts and behavior.
Preview the practical and research lenses and both mobile and desktop layouts. Capture only
synthetic, identifier-free UI; label screenshots as interface evidence unless actual execution
has been independently recorded.

## Record evidence before promoting

Keep documented, LOCAL, SIMULATED and observed LIVE/PREVIEW outcomes separate. Record the
provider, server, actual operation, date, scope and limitations for live evidence. Follow
PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT for any cloud mutation. Production
identity, networking, operational ownership and deployment checks remain separate gates.
