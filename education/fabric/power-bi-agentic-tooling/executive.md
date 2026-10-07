## Why this matters

Semantic models hold the business definitions that reports, people and AI agents rely on -
"denial rate", "average length of stay", "readmission rate". AI coding agents can now build and
edit those models and reports quickly. The risk is a **plausible but wrong number** published
with confidence.

The governed approach keeps the speed and adds proof:

| Step | Tooling | Control |
|---|---|---|
| Model and report as files | PBIP, TMDL and PBIR in Git | Every change is a reviewable diff |
| Edit the model | Power BI Authoring MCP + authoring skills | Proposal first, human review, then apply |
| Check the numbers | DAX queries (Fabric IQ MCP, read-only) | Every measure must equal an independent baseline |
| Build the report | Report planning and authoring skills | Bound to the validated model only |
| Publish | Separate, approved step | Evidence: published report, workspace, model binding |

## What is GA and what is preview (October 2026)

| Capability | Status |
|---|---|
| PBIP / TMDL files, Direct Lake, Fabric Git integration | GA |
| Power BI Authoring (Modeling) MCP - local | GA (1.0.0) |
| Power BI Authoring MCP - hosted | PREVIEW |
| Fabric IQ MCP (read-only DAX queries) | GA |
| Semantic-model and report authoring skills | Official open source, pre-1.0 |

That mix is why the lesson is labeled **MIXED**.

## The rule leaders should insist on

**Prove numbers, not appearance.** A report that renders is not a report that is right, and a
report file on a laptop is not a published report. Ask for a reconciliation table that compares
every measure with the expected value, and for evidence of publication.

## In this accelerator

The HC-01 guide walks this flow end to end on synthetic healthcare data. Offline, the same
measure definitions are evaluated locally and compared with a committed baseline, so the
discipline can be rehearsed with no tenant. All metrics are synthetic demonstrations, not
clinical quality measures.
