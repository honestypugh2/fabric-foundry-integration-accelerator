# MFG-01: Foundry agents + Fabric for sales insights (manufacturing, synthetic)

<!-- Generated from education and guide YAML; run ffia prompts render. -->

Recorded bake-off results describe Copilot CLI only, not every Copilot surface.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/mfg-01-foundry-fabric-sales-insights/guide.yaml).

Dataset: `mfg-sales-v1`. Guide status: validated-live.

## 01-explore-architecture: Explore the architecture

Provider: Local editor; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Read education/architecture/views/mfg-01.yaml and explain, in plain language, what Fabric owns, what Foundry owns, and where authority and evidence come from. Do not call any cloud tool.
```

Checkpoint: The learner can state the three boundaries and the five steps of the diagram.

Offline equivalent: Step through the diagram in the app.

## 02-land-data: Land the synthetic sales data in a lakehouse

Provider: Fabric REST API and OneLake (or the Fabric portal); server: not applicable; tools: create lakehouse, OneLake upload, Load Table.

Skills: none required. Human approval required: yes.

```text
Check the six CSVs in data/synthetic/raw/mfg-sales-v1 against SHA256SUMS. Then propose (do not run) the steps to create lakehouse mfg_lakehouse in workspace <WORKSPACE_NAME>, upload the CSVs to Files/raw after confirming it is empty, and load each as a Delta table. Name the provider and tool for each step.
```

Checkpoint: Six Delta tables exist with the row counts in the expected baseline.

Offline equivalent: Build the local tables and see the counts.

## 03-data-agent: Create and publish the Fabric data agent

Provider: Fabric portal (manual); server: not applicable; tools: Data agent.

Skills: none required. Human approval required: yes.

```text
Draft data agent instructions for the mfg-sales-v1 tables: the booked revenue definition, product line codes, team focus areas, and an instruction to report data-quality problems. Keep it under 150 words.
```

Checkpoint: The data agent answers "booked revenue by product line in September 2026" and is published.

Offline equivalent: Read the same numbers locally.

## 04-foundry-agent: Build the Foundry agent with the Fabric tool (portal and code)

Provider: Foundry Agent Service; server: not applicable; tools: agents.create_version, responses.create, fabric_dataagent_preview.

Skills: none required. Human approval required: yes.

```text
Open demos/foundry-fabric-agents-workshop/code/fabric_sales_agent.py. Explain what the agent can and cannot do, where its identity comes from, and why it must not estimate numbers. Then run it with the question "Which product line grew fastest last month?" and report the tools used. Do not print IDs.
```

Checkpoint: The answer names Enclosures, +55.78% ($56,623.73 → $88,207.09), with a Fabric tool call in the run.

Offline equivalent: Show the governed numbers locally.

## 05-web-context: Add cited public context, safely

Provider: Foundry Agent Service; server: not applicable; tools: web search (Grounding with Bing).

Skills: none required. Human approval required: no.

```text
Read demos/foundry-fabric-agents-workshop/code/market_context_agent.py. List the security concerns of web grounding (compliance boundary, prompt injection, query leakage, site terms) and the control for each. Do not run it unless web search is enabled in the project.
```

Checkpoint: Every web-grounded answer shows citations, and no internal data appears in queries.

Offline equivalent: Review the boundary band in the MFG-01 diagram and the Q&A answer.

## 06-monthly-brief: Generate monthly briefs per business team

Provider: Foundry Agent Service; server: not applicable; tools: responses.create, fabric_dataagent_preview.

Skills: none required. Human approval required: no.

```text
Run demos/foundry-fabric-agents-workshop/code/monthly_brief.py and compare each team's numbers with ffia mfg brief --json. Then propose a schedule (Logic Apps Recurrence or Azure Functions timer) and Teams delivery, naming preview pieces.
```

Checkpoint: Every brief's revenue, attainment and margin match the baseline.

Offline equivalent: Print all four briefs locally.

## 07-data-quality: Triage data quality and propose fixes

Provider: Local CLI and Foundry Agent Service; server: not applicable; tools: ffia mfg quality, fabric_dataagent_preview.

Skills: none required. Human approval required: no.

```text
Run ffia mfg quality. For each finding, explain the business impact on booked revenue and propose a Silver-layer correction for a data steward. Ask the live agent how many duplicate order lines exist and compare. Do not change any data.
```

Checkpoint: All nine injected issue types are detected with exact counts; the agent's duplicate count is 12.

Offline equivalent: The data-quality report is offline by design.
