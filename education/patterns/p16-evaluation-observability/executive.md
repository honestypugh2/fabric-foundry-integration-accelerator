## Why it matters

An agent demo that "looks right" is not evidence. Leaders need to know three things before trusting
an AI-and-data solution: **are the numbers correct, are the answers good, and can we prove what
happened?** Pattern P16 turns each into a measurable gate.

| Question | Technique | Nature |
|---|---|---|
| Are the numbers correct? | Compare every measure with an owned expected baseline | Deterministic — same verdict every time |
| Are the answers good? | Model-graded evaluators (groundedness, relevance, tool-call accuracy, safety) | Probabilistic — calibrate thresholds |
| What actually happened? | Correlation IDs, audit records, execution labels, traces | Evidence trail |

**Execution labels are evidence.** Every result says whether it was `LIVE`, `HYBRID`, `LOCAL`,
`SIMULATED`, `MOCKED`, `PREVIEW` or `UNAVAILABLE`. A simulated result can never be presented as a
production one.

## Status as of October 2026

| Capability | Status |
|---|---|
| Foundry core evaluators (quality, safety, tool usage) | GA |
| Several agent behavior evaluators and AI red teaming | **PREVIEW** |
| Foundry tracing with OpenTelemetry | GA |
| This accelerator's baseline evaluator, agent evaluation and audit trail | **SIMULATED LOCALLY** (labeled `LOCAL`) |
| Agent tracing in this accelerator | One OpenTelemetry span per agent ask; export to Application Insights is opt-in and **REQUIRES TENANT VALIDATION** |

**Decision for leaders:** which thresholds block a release, who owns each baseline, and who may
change them. Evaluation that does not block anything is only a report.

> All measures evaluated here are synthetic demonstrations, not clinical quality measures.
