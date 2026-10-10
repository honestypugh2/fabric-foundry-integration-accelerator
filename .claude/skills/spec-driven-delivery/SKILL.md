---
name: spec-driven-delivery
description: "Use when adding a new Fabric or Foundry use case, specifying a PoC, or planning a cross-layer feature with Spec Kit. Connect outcomes, foundations, requirements, tests and convergence without changing MCP authority or granting cloud-write approval."
---

# Spec-driven delivery

This repository-owned workflow is LOCAL planning and verification. It is not an installed
Spec Kit CLI or a live cloud executor. Read `AGENTS.md` before starting.

## When to use

Use for a new use case, unclear business requirements, or changes crossing data, API, UI and
governance boundaries. For a narrow reproducible bug, use the normal fix-and-test workflow.
Do not make this a prerequisite for running the offline demo.

## Procedure

1. Establish ground rules from `AGENTS.md`; never create a conflicting constitution.
2. Specify the synthetic business problem, audience, measurable outcomes, exclusions and
   evidence. Keep customer source material and real identifiers outside the repository.
3. Clarify one consequential ambiguity at a time with the user.
4. Plan contracts, selected patterns, theory and assumptions, offline behavior, live
   prerequisites, failure recovery and production gaps.
5. Review requirement quality separately from implementation completion.
6. Create dependency-ordered tasks with tests linked to each acceptance criterion.
7. Analyze contradictions, missing controls and unresolved research assumptions before coding.
8. Implement reviewed repository changes; run the smallest relevant checks.
9. Converge: compare requirements with actual tests and output artifacts. Record gaps rather
   than marking an unmet requirement complete.
10. Any live mutation starts a separate PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT
    flow through `ffia-governed-fabric-change`. A reviewed spec is not write approval.

## Optional upstream Spec Kit integration

The public quickstart uses `/speckit-constitution`, `/speckit-specify`, `/speckit-clarify`,
`/speckit-plan`, `/speckit-checklist`, `/speckit-tasks`, `/speckit-analyze`,
`/speckit-implement` and `/speckit-converge`. These are agent skills, not terminal commands.

The stable PyPI release verified for this change is `specify-cli==1.1.3`. Before installation,
review its maintenance and dependency audit, and ask to install the optional tool. Trial
`specify init` in a separate scratch project for the selected integration. Compare generated
Skills, instructions and hooks with this repository before adopting files. Never overwrite
existing instructions, MCP profiles or policy automatically.

Active feature state is `.specify/feature.json` or `SPECIFY_FEATURE_DIRECTORY`; switching Git
branches does not select a different feature. Both Copilot and Claude can use this procedure,
but Claude execution remains DOCUMENTED ONLY until actually evaluated.

See [the lesson](../../../education/agentic-data-engineering/spec-driven-delivery/lesson.yaml)
and [onboarding contract](../../../docs/operations/use-case-onboarding.md).
