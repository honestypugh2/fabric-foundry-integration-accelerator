## Why it matters

Agents are only as trustworthy as the data they read. If an agent answers "what is our average
length of stay?" from raw, duplicated or untyped data, it will be confidently wrong. Pattern P10
puts a **refinement pipeline** between source systems and every report or agent, and it is clear
about which jobs AI may speed up and which decisions it may not make.

| Layer | Job | Who consumes it |
|---|---|---|
| Raw / Bronze | Keep exactly what arrived, for replay and audit | Data engineers only |
| Silver | Type, conform, de-duplicate and flag quality issues | Data engineers, data-quality owners |
| Gold | Business-ready facts and dimensions | Semantic models, data agents |
| Semantic model | The governed business vocabulary and measures | Reports, Copilot, Foundry agents |

## Where AI helps, and where it must not decide

| AI accelerates | Deterministic logic decides |
|---|---|
| Profiling new sources and suggesting types | Whether a row passes a quality rule |
| Drafting notebooks and SQL | Whether a change merges (tests + baseline) |
| Explaining a data-quality failure in plain language | Measure definitions and their expected values |
| Enrichment with Fabric AI functions | Anything that overwrites a source fact |

**Decision for leaders:** who owns the expected baseline for each business measure, and the rule
that no pipeline change ships unless it reproduces that baseline.

## Status

Medallion lakehouses, Direct Lake and Fabric AI functions are **GA** as of October 2026. In this
accelerator the medallion runs **SIMULATED LOCALLY** over synthetic data. Reference Fabric
notebooks generated from the same logic reproduce the expected results on a local Spark engine;
running them in Fabric still requires validation in a tenant. All metrics are synthetic
demonstrations, not clinical measures.
