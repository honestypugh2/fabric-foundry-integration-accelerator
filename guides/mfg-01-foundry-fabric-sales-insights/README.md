# Guide MFG-01: Foundry agents + Fabric for sales insights (manufacturing, synthetic)

Build and learn how a Foundry agent uses governed Fabric sales data.
The guide covers read-only data access, public sources, team briefs and quality investigation.
The manufacturer, customers and products are fictional.

## Start this use case

| Question | Answer |
|---|---|
| Outcome | Governed sales answers, reviewed team briefs and data-quality proposals over Fabric context |
| Audience | Agent builders and business teams |
| Prerequisites | [Root installation](../../README.md#quick-start); connected Fabric/Foundry requirements and preview limitations in [guide.yaml](guide.yaml) |
| Effort | The linked business-agent learning journey estimates 75 minutes; provisioning and the full live workflow take additional environment-dependent time |
| Offline path | Run `ffia mfg brief` and `ffia mfg quality`; launch `make run API_ARGS=--offline` and open Use Cases → MFG-01 |
| Connected path | Configure [private bindings](../../docs/operations/environment-configuration.md), inspect readiness, then follow the guide's portal/code-first steps with separate write approval |
| First checkpoint | Step `01-explore-architecture`: explain Fabric's read-only context, Foundry reasoning and human authority without cloud calls |
| Completion evidence | Baseline-reconciled answers, citations, review gates and per-step evidence; a draft is not scheduled/delivered |
| Production gaps | Revenue and final-answer reconciliation, scheduling/delivery and production identity/network/operations still require verification; bounded server-side traces have been observed |

Read [scoped instructions](AGENTS.md), then follow [guide.yaml](guide.yaml) one prompt at a
time. Stop at each checkpoint. The Foundry Fabric tool is PREVIEW.
Claude Code prompts are available as instructions, not as a completed comparison.

## Find the implementation assets

| Asset | Where |
|---|---|
| Guide manifest | `guide.yaml` (7 steps; GitHub Copilot and Claude Code prompts, checkpoints, offline equivalents) |
| Architecture | `education/architecture/views/mfg-01.yaml` → app `/architecture/mfg-01` |
| Data and baseline | `data/synthetic/raw/mfg-sales-v1/`, `data/synthetic/expected/mfg-sales-v1.json` |
| Offline commands | `ffia mfg brief [--team T-ENC]`, `ffia mfg quality` |
| Code-first samples | `demos/foundry-fabric-agents-workshop/code/` |
| Workshop talk track | `demos/foundry-fabric-agents-workshop/index.html` |

Evidence: **dated live observations** on 2026-10-08 in the presenter's demo tenant: steps 02 to 04 and the
duplicate check in step 07. Steps 05 and 06 are offline-validated; running them live requires
tenant validation.
These observations do not certify the whole use case or current service health.
See [phase verification](../../docs/operations/phase-verification.md).
Later bounded invocations timed out; a recovered PREVIEW duplicate-count tool payload matched
12, but no final assistant answer was verified. This limits the current sharing claim to the
offline implementation and dated connected observations. See the
[current verification record](../../docs/operations/use-case-authoring-verification.md) and
[resume-later tracker](../../docs/operations/resume-later.md).

## Architecture

![Foundry agents over governed Fabric sales context, exported by draw.io Desktop](../../docs/architecture/diagrams/mfg-01.png)

[Editable draw.io source](../../docs/architecture/diagrams/mfg-01.drawio) /
[interactive architecture](http://localhost:5173/architecture/mfg-01).
This is the intended architecture, not proof that scheduling, delivery or data corrections ran.
Those operations require their own validation and approval. Claude Code remains DOCUMENTED ONLY
in the bake-off.
