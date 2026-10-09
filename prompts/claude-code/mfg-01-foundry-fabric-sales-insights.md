# MFG-01: Foundry agents + Fabric for sales insights (manufacturing, synthetic)

<!-- Generated from education and guide YAML; run ffia prompts render. -->

DOCUMENTED ONLY: no Claude Code runs were recorded. Claude models inside Copilot are not Claude Code.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/mfg-01-foundry-fabric-sales-insights/guide.yaml).

Dataset: `mfg-sales-v1`. Guide status: validated-live.

## 01-explore-architecture: Explore the architecture

Provider: Local editor; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Read education/architecture/views/mfg-01.yaml and summarize the ownership boundaries and the monthly brief trace. No cloud calls.
```

Checkpoint: The learner can state the three boundaries and the five steps of the diagram.

Offline equivalent: Step through the diagram in the app.

## 02-land-data: Land the synthetic sales data in a lakehouse

Provider: Fabric REST API and OneLake (or the Fabric portal); server: not applicable; tools: create lakehouse, OneLake upload, Load Table.

Skills: none required. Human approval required: yes.

```text
Verify the six CSVs with sha256sum -c SHA256SUMS, then propose the create, upload and load steps with provider and tool names. Do not run them.
```

Checkpoint: Six Delta tables exist with the row counts in the expected baseline.

Offline equivalent: Build the local tables and see the counts.

## 03-data-agent: Create and publish the Fabric data agent

Provider: Fabric portal (manual); server: not applicable; tools: Data agent.

Skills: none required. Human approval required: yes.

```text
Draft the same data agent instructions (booked revenue, product lines, focus areas, report data-quality issues).
```

Checkpoint: The data agent answers "booked revenue by product line in September 2026" and is published.

Offline equivalent: Read the same numbers locally.

## 04-foundry-agent: Build the Foundry agent with the Fabric tool (portal and code)

Provider: Foundry Agent Service; server: not applicable; tools: agents.create_version, responses.create, fabric_dataagent_preview.

Skills: none required. Human approval required: yes.

```text
Explain fabric_sales_agent.py (tool, identity, limits), then run it and report the answer and the tool calls. Keep IDs out of the output.
```

Checkpoint: The answer names Enclosures, +55.78% ($56,623.73 → $88,207.09), with a Fabric tool call in the run.

Offline equivalent: Show the governed numbers locally.

## 05-web-context: Add cited public context, safely

Provider: Foundry Agent Service; server: not applicable; tools: web search (Grounding with Bing).

Skills: none required. Human approval required: no.

```text
List the web grounding risks and controls from market_context_agent.py; run only if web search is enabled.
```

Checkpoint: Every web-grounded answer shows citations, and no internal data appears in queries.

Offline equivalent: Review the boundary band in the MFG-01 diagram and the Q&A answer.

## 06-monthly-brief: Generate monthly briefs per business team

Provider: Foundry Agent Service; server: not applicable; tools: responses.create, fabric_dataagent_preview.

Skills: none required. Human approval required: no.

```text
Run monthly_brief.py, reconcile with ffia mfg brief --json, and propose schedule and delivery options.
```

Checkpoint: Every brief's revenue, attainment and margin match the baseline.

Offline equivalent: Print all four briefs locally.

## 07-data-quality: Triage data quality and propose fixes

Provider: Local CLI and Foundry Agent Service; server: not applicable; tools: ffia mfg quality, fabric_dataagent_preview.

Skills: none required. Human approval required: no.

```text
Run ffia mfg quality, explain impact and propose Silver fixes; compare duplicates with the live agent. No changes.
```

Checkpoint: All nine injected issue types are detected with exact counts; the agent's duplicate count is 12.

Offline equivalent: The data-quality report is offline by design.
