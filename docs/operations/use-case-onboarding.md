# Add a use case without forking the accelerator

**LOCAL engineering workflow.** Public use cases are sanitized and synthetic. Real customer
source material remains outside this repository; real bindings remain in ignored environment
files. No onboarding step grants cloud-write authority.

## Outcome and foundations

1. Define the audience, business problem, measurable outcome and exclusions.
2. Select the smallest relevant patterns from `education/patterns/catalog.yaml`.
3. Identify foundational ideas and assumptions. Specify a falsifiable hypothesis, controlled
   experiment, independent baseline, metrics and limitations before claiming improvement.
4. Use [spec-driven delivery](../../.claude/skills/spec-driven-delivery/SKILL.md) for a new
   cross-layer scenario. Upstream Spec Kit is optional and is not installed by this workflow.

## Registry contract

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

The use-case catalogue and pattern coverage matrix are derived from validated registries, not
two hard-coded scenario switches. A new story renders through the same overview and runner.
Historical evidence links do not mark an entire use case live-certified.

## Validate

```bash
ffia education check
ffia sources render
ffia schemas export
make fixtures
ffia diagrams check
ffia privacy scan
```

Run targeted Python, frontend and accessibility tests for the affected contracts and behavior.
Preview the practical and research lenses and both mobile and desktop layouts. Capture only
synthetic, identifier-free UI; label screenshots as interface evidence unless actual execution
has been independently recorded.

## Promote deliberately

Keep documented, LOCAL, SIMULATED and observed LIVE/PREVIEW outcomes separate. Record the
provider, server, actual operation, date, scope and limitations for live evidence. Follow
PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT for any cloud mutation. Production
identity, networking, operational ownership and deployment checks remain separate gates.
