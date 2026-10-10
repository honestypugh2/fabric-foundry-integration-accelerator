# Architecture pattern prompts

<!-- Generated from education and guide YAML; run ffia prompts render. -->

Recorded bake-off results describe Copilot CLI only, not every Copilot surface.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

## P01: Fabric Data Agent + Foundry

Status: MIXED. Offline equivalent: Local deterministic data agent over the semantic model with allow-listed queries.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P01: Fabric Data Agent + Foundry. Explain this scenario: A Foundry agent asks a governed Fabric data agent for answers over structured Fabric data. Trace Fabric's role (Owns governed context, data permissions and the data agent's curated sources.), Foundry's role (Owns reasoning, orchestration, conversation and evaluation.), and MCP's role (Optional transport (data agent MCP endpoint); grants no authority.). Identify the authority boundary: End-user identity through on-behalf-of; Fabric permissions decide what is visible. Plan the offline demonstration: Local deterministic data agent over the semantic model with allow-listed queries. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P02: Multiple Fabric Data Agents via Fabric IQ

Status: PREVIEW. Offline equivalent: Local domain routing over separate semantic subsets.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P02: Multiple Fabric Data Agents via Fabric IQ. Explain this scenario: A coordinating agent routes to bounded, domain-specific data agents through Fabric IQ. Trace Fabric's role (Domain data agents and the shared semantic layer.), Foundry's role (Coordinator agent, routing and evaluation.), and MCP's role (Optional per-domain endpoints.). Identify the authority boundary: Per-domain Fabric permissions under the end user's identity. Plan the offline demonstration: Local domain routing over separate semantic subsets. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P03: Fabric IQ Ontology

Status: PREVIEW. Offline equivalent: Local semantic YAML (entities, relationships, vocabulary).

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P03: Fabric IQ Ontology. Explain this scenario: Business entities, relationships and vocabulary bound to Fabric data without copying it. Trace Fabric's role (Ontology entities, relationships and bindings.), Foundry's role (Uses the ontology to ground reasoning.), and MCP's role (Ontology MCP exposes entities for discovery (preview).). Identify the authority boundary: Bindings inherit the underlying item permissions. Plan the offline demonstration: Local semantic YAML (entities, relationships, vocabulary). Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P04: OneLake as Foundry knowledge

Status: MIXED. Offline equivalent: Local retrieval over synthetic documents with citations.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P04: OneLake as Foundry knowledge. Explain this scenario: Unstructured files in OneLake become cited knowledge for agents through Foundry IQ. Trace Fabric's role (Stores and governs the files.), Foundry's role (Indexes, retrieves and cites; evaluates groundedness.), and MCP's role (None required.). Identify the authority boundary: The search service's managed identity indexes content; plan entitlement trimming explicitly. Plan the offline demonstration: Local retrieval over synthetic documents with citations. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P05: Foundry tools in Fabric (AI in data engineering)

Status: GA. Offline equivalent: Deterministic local enrichment labeled SIMULATED.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P05: Foundry tools in Fabric (AI in data engineering). Explain this scenario: AI functions classify, extract and summarize inside notebooks and pipelines. Trace Fabric's role (Runs the pipeline and stores enriched results.), Foundry's role (Provides models.), and MCP's role (None.). Identify the authority boundary: Workspace identity and tenant settings for AI features. Plan the offline demonstration: Deterministic local enrichment labeled SIMULATED. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P06: Fabric + Foundry enterprise agent (anchor)

Status: MIXED. Offline equivalent: Local providers, deterministic agent, local evaluation and audit.

Source: [lesson](../../education/patterns/p06-enterprise-agent/lesson.yaml).

```text
Using the ffia-local MCP server, call get_architecture_pattern for P06 and get_runtime_status. Then draw a text diagram of the P06 request path (context, reasoning, access, authority, action, evidence) and mark each hop as available offline, available opt-in but requiring tenant validation, arriving in a later phase, or PREVIEW. Do not claim that any Foundry or Fabric call ran.
```

## P07: Real-time Fabric + Foundry agent

Status: MIXED. Offline equivalent: Local event replay.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P07: Real-time Fabric + Foundry agent. Explain this scenario: Operational events feed context to an agent that proposes, never autonomously executes, actions. Trace Fabric's role (Eventstream, Eventhouse and Activator.), Foundry's role (Interprets context and proposes actions.), and MCP's role (Optional event and query tools.). Identify the authority boundary: Policy and human approval before any action. Plan the offline demonstration: Local event replay. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P08: Human-in-the-loop governed action

Status: GA. Offline equivalent: Full plan, approve, simulated execute, verify and audit flow.

Source: [lesson](../../education/patterns/p08-human-in-the-loop/lesson.yaml).

```text
Using the ffia-local MCP server, call generate_fabric_change_plan to propose creating a Lakehouse named bronze_lab in the demo-dev workspace with destination LOCAL. Show the risk, validation, rollback and policy reasons. Do not try to approve or execute it; tell me what a human must do next.
```

## P09: Governed MCP

Status: GA. Offline equivalent: Local FastMCP educational server with an allow-listed manifest.

Source: [lesson](../../education/patterns/p09-governed-mcp/lesson.yaml).

```text
Using the ffia-local MCP server, call get_demo_capabilities and list every tool it exposes with its read-only hint. Then try to find a tool that approves or executes a change or runs SQL, and explain why none exists. Finally call get_audit_record with the correlation_id of your first call.
```

## P10: Medallion + AI

Status: GA. Offline equivalent: Local DuckDB medallion over synthetic data.

Source: [lesson](../../education/patterns/p10-medallion-ai/lesson.yaml).

```text
Using the ffia-local MCP server, call inspect_medallion_architecture for profile hc-lab-7file-v1, then preview_table for silver_encounters and gold_encounter_summary (limit 5). Explain what changed between the layers and which data-quality flags Silver adds. Then call evaluate_measures and evaluate_against_baseline. Label every result with its execution label and do not claim any Fabric operation ran.
```

## P11: Mirroring / Open Mirroring + AI

Status: GA. Offline equivalent: Landing-zone simulation and recovery drill.

Source: [lesson](../../education/patterns/p11-mirroring-ai/lesson.yaml).

```text
Using the ffia-local MCP server, call simulate_recovery_drill. Summarize which day introduced duplicate keys and why, how they were remediated, which snapshot the restore used, and why the counterfactual without the weekly snapshot fails. Keep every statement tagged with its evidence category and say clearly that no Fabric mirrored database was touched.
```

## P12: Direct Lake + semantic model + AI

Status: GA. Offline equivalent: Local semantic model contract evaluated with DuckDB.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P12: Direct Lake + semantic model + AI. Explain this scenario: Semantic models over OneLake tables give agents governed measures and relationships. Trace Fabric's role (Direct Lake semantic model.), Foundry's role (Queries measures, never redefines them.), and MCP's role (Fabric IQ MCP (query) and Power BI Authoring MCP (authoring).). Identify the authority boundary: Model permissions and RLS/OLS. Plan the offline demonstration: Local semantic model contract evaluated with DuckDB. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P13: Multi-domain is not multi-agent

Status: GA. Offline equivalent: Documentation and local routing examples.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P13: Multi-domain is not multi-agent. Explain this scenario: Add agents only where tools, context, policy, ownership or lifecycle truly differ. Trace Fabric's role (Domain boundaries in data.), Foundry's role (Deterministic orchestration first.), and MCP's role (Per-domain tool sets.). Identify the authority boundary: Domain owners. Plan the offline demonstration: Documentation and local routing examples. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P14: Secure enterprise Foundry + Fabric

Status: GA. Offline equivalent: Architecture diagrams and checklists.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P14: Secure enterprise Foundry + Fabric. Explain this scenario: Private networking, managed identity, Key Vault, monitoring and policy around the solution. Trace Fabric's role (Workspace isolation and private links.), Foundry's role (Private endpoints and agent identity.), and MCP's role (Private MCP endpoints where required.). Identify the authority boundary: Entra, RBAC and network controls. Plan the offline demonstration: Architecture diagrams and checklists. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P15: APIM AI, MCP and tool governance

Status: GA. Offline equivalent: Local policy simulation.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P15: APIM AI, MCP and tool governance. Explain this scenario: A central gateway for authentication, quotas, routing, versioning and telemetry. Trace Fabric's role (Upstream data APIs.), Foundry's role (Model and agent endpoints behind the gateway.), and MCP's role (REST APIs exposed as governed MCP tools.). Identify the authority boundary: Gateway policies plus backend authorization. Plan the offline demonstration: Local policy simulation. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P16: Evaluation + observability

Status: MIXED. Offline equivalent: Deterministic local evaluation against committed baselines.

Source: [lesson](../../education/patterns/p16-evaluation-observability/lesson.yaml).

```text
Using the ffia-local MCP server, call evaluate_against_baseline for profile hc-lab-7file-v1 with no observed values, then again with observed set to {"claim_count": 1} and observed_label LIVE. Compare the two results: observed_values_source, the evidence category, compared, passed and gate_passed. Explain why the second run is not proof that anything ran in Fabric.
```

## P17: LIVE / HYBRID / OFFLINE resilience

Status: GA. Offline equivalent: The offline demo itself.

Source: [lesson](../../education/patterns/p17-resilience/lesson.yaml).

```text
Read docs/architecture/resilience.md, config/environments/hybrid.yaml and src/fabric_foundry_accelerator/fallback/router.py. Explain, step by step, what happens to four consecutive read_table requests when FFIA_SIMULATE_FABRIC_OUTAGE=1 in hybrid mode: attempts per request, breaker state after each, and the fallback_reason on the fourth. Then explain why POST /api/v1/fabric/change is never routed through this fallback.
```

## P18: Customer overlay

Status: GA. Offline equivalent: Example overlay with synthetic data.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P18: Customer overlay. Explain this scenario: Configuration controls industry, domains, tools, policy, thresholds and learning modules. Trace Fabric's role (Workspace aliases only.), Foundry's role (Project aliases only.), and MCP's role (Tool allow-lists.). Identify the authority boundary: Overlay owners; real identifiers stay in git-ignored files. Plan the offline demonstration: Example overlay with synthetic data. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P19: Copilot CLI + Fabric Skills + MCP

Status: MIXED. Offline equivalent: Skills read locally plus the local MCP server.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P19: Copilot CLI + Fabric Skills + MCP. Explain this scenario: A terminal agent follows Microsoft-authored Fabric skills and calls Fabric MCP or REST. Trace Fabric's role (Target workspace (dev).), Foundry's role (Not required.), and MCP's role (Fabric MCP servers with hardened allow-lists.). Identify the authority boundary: The developer's identity and workspace role. Plan the offline demonstration: Skills read locally plus the local MCP server. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P20: Repo-first (Git as source of truth)

Status: GA. Offline equivalent: Local definitions and dry-run plans.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P20: Repo-first (Git as source of truth). Explain this scenario: Agents edit notebooks, TMDL and pipeline definitions in Git; CI validates; deployment applies. Trace Fabric's role (Git integration and deployment pipelines.), Foundry's role (Not required.), and MCP's role (Documentation and schema tools.). Identify the authority boundary: Pull-request review and branch protection. Plan the offline demonstration: Local definitions and dry-run plans. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P21: Cloud agent issue to pull request

Status: GA. Offline equivalent: Issue template and recorded replay.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P21: Cloud agent issue to pull request. Explain this scenario: A well-scoped issue becomes a pull request from the Copilot cloud agent with read-only tools. Trace Fabric's role (Item definitions in Git.), Foundry's role (Not required.), and MCP's role (Read-only servers only (no per-call approval in the cloud agent).). Identify the authority boundary: Pull-request reviewers. Plan the offline demonstration: Issue template and recorded replay. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P22: Parallel agentic migration

Status: PREVIEW. Offline equivalent: Synthetic legacy notebooks and replay.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P22: Parallel agentic migration. Explain this scenario: Many isolated agent sessions convert legacy notebooks or pipelines into reviewable pull requests. Trace Fabric's role (Migration target.), Foundry's role (Not required.), and MCP's role (Documentation tools.). Identify the authority boundary: Reviewers and CI gates. Plan the offline demonstration: Synthetic legacy notebooks and replay. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P23: Headless agent review in CI

Status: GA. Offline equivalent: Recorded review transcripts.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P23: Headless agent review in CI. Explain this scenario: A non-interactive agent reviews notebooks and models in pull requests. Trace Fabric's role (Item definitions under review.), Foundry's role (Not required.), and MCP's role (Documentation tools only.). Identify the authority boundary: Human reviewers keep approval authority. Plan the offline demonstration: Recorded review transcripts. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P24: Embedded data-engineering assistant

Status: GA. Offline equivalent: Local providers and deterministic agent.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P24: Embedded data-engineering assistant. Explain this scenario: An internal app embeds an agent runtime that calls Fabric tools under app identity or on behalf of the user. Trace Fabric's role (Governed context and approved write targets.), Foundry's role (Agent runtime, evaluation and tracing.), and MCP's role (Typed tools with allow-lists.). Identify the authority boundary: On-behalf-of user identity plus approvals. Plan the offline demonstration: Local providers and deterministic agent. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```

## P25: Spec-driven Fabric and Foundry delivery

Status: GA. Offline equivalent: Review a synthetic use-case specification, map requirements to tests and run existing offline gates.

Source: [catalog](../../education/patterns/catalog.yaml).

```text
Read the catalog entry for P25: Spec-driven Fabric and Foundry delivery. Explain this scenario: A reviewed specification connects business outcomes, architecture, implementation tasks and measurable verification before a PoC changes a workspace. Trace Fabric's role (Supplies governed data contracts and explicit workspace acceptance criteria.), Foundry's role (Supplies reasoning and evaluation requirements; it does not define deployment authority.), and MCP's role (Tools may collect read-only facts and evidence; no specification grants tool authorization.). Identify the authority boundary: Repository policy, human review and the existing governed change flow remain authoritative. Plan the offline demonstration: Review a synthetic use-case specification, map requirements to tests and run existing offline gates. Name any preview dependencies and propose the smallest validation check. Do not edit files, call cloud tools, or claim an operation ran.
```
