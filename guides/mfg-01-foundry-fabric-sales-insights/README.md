# Guide MFG-01: Foundry agents + Fabric for sales insights (manufacturing, synthetic)

Foundry agents over governed Fabric sales data: a read-only Fabric data agent, a Foundry agent with
the Fabric tool, cited public context, monthly team briefs and data-quality triage. Synthetic data
only; the manufacturer, customers and products are fictional.

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
| Production gaps | Server-side traces, scheduling/delivery and production identity/network/operations still require verification |

Read [scoped instructions](AGENTS.md), then follow [guide.yaml](guide.yaml) one prompt at a
time. Stop at each checkpoint. The Fabric tool in Foundry is PREVIEW; Claude Code alternate
prompts are documented, not a comparative run.

## Find the implementation assets

| Asset | Where |
|---|---|
| Guide manifest | `guide.yaml` (7 steps; Copilot and Claude Code prompts, checkpoints, offline equivalents) |
| Architecture | `education/architecture/views/mfg-01.yaml` → app `/architecture/mfg-01` |
| Data and baseline | `data/synthetic/raw/mfg-sales-v1/`, `data/synthetic/expected/mfg-sales-v1.json` |
| Offline commands | `ffia mfg brief [--team T-ENC]`, `ffia mfg quality` |
| Code-first samples | `demos/foundry-fabric-agents-workshop/code/` |
| Workshop talk track | `demos/foundry-fabric-agents-workshop/index.html` |

Evidence: **dated live observations** on 2026-10-08 in the presenter's demo tenant: steps 02–04 and the
duplicate check in step 07. Steps 05 and 06 are offline-validated; running them live requires
tenant validation.
These observations do not certify the whole use case or current service health.
See [phase verification](../../docs/operations/phase-verification.md).

## Architecture

![Foundry agents over governed Fabric sales context, exported by draw.io Desktop](../../docs/architecture/diagrams/mfg-01.png)

[Editable draw.io source](../../docs/architecture/diagrams/mfg-01.drawio) /
[interactive architecture](http://localhost:5173/architecture/mfg-01).
This is the intended architecture, not proof that scheduling, delivery or data corrections ran.
Those operations require their own validation and approval. Claude Code remains DOCUMENTED ONLY
in the bake-off.
