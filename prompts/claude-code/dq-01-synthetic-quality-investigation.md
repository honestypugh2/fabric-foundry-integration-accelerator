# DQ-01: Investigate synthetic data quality with GitHub Copilot

<!-- Generated from education and guide YAML; run ffia prompts render. -->

DOCUMENTED ONLY: no Claude Code runs were recorded. Claude models inside GitHub Copilot are not Claude Code.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/dq-01-synthetic-quality-investigation/guide.yaml).

Dataset: `mfg-sales-v1`. Guide status: validated-offline.

## 01-define-contract: Define the quality contract

Provider: Local editor; server: not applicable; tools: none.

Skills: spec-driven-delivery. Human approval required: no.

```text
Read this guide and governed-data-foundations. Explain order-line grain, the nine committed quality categories and why fluent model output does not establish correctness. No cloud calls.
```

Checkpoint: The learner names the baseline, grain and authority boundary.

Offline equivalent: Read the existing five-level foundations and research brief.

## 02-reconcile-findings: Reconcile all quality findings

Provider: Local synthetic DuckDB CLI; server: not applicable; tools: ffia mfg quality --check --json.

Skills: none required. Human approval required: no.

```text
Run ffia mfg quality --check --json and report the nine counts and independent baseline result as LOCAL. Stop on mismatch without regenerating the baseline.
```

Checkpoint: All nine counts match exactly and the command exits zero.

Offline equivalent: The same deterministic quality reconciliation.

## 03-break-and-recover: Challenge the baseline in a scratch copy

Provider: Local pytest runner; server: not applicable; tools: pytest tests/offline/test_use_case_authoring.py --no-cov.

Skills: none required. Human approval required: no.

```text
Run tests/offline/test_use_case_authoring.py and explain how a scratch baseline mismatch exits nonzero. Do not edit committed data or claim production validation.
```

Checkpoint: The adverse-case test observes a failed baseline gate; the original baseline still passes.

Offline equivalent: Network-blocked pytest with isolated synthetic files.

## 04-inspect-connected-option: Compare optional Fabric MCP context

Provider: Microsoft Fabric; server: fabric-mcp; tools: core_search-catalog.

Skills: ffia-governed-fabric-change. Human approval required: no.

```text
Explain the optional Fabric MCP read-only catalogue path and named LOCAL fallback. Do not invoke a cloud tool without confirming the target scope. Metadata is not quality validation.
```

Checkpoint: The learner separates optional item visibility from deterministic quality evidence.

Offline equivalent: Explain the primary and fallback using the fabric-mcp-landscape lesson without calling cloud tools.

Fallback: LOCAL, ffia-local, list_fabric_items. Disclose primary unavailability; this does not satisfy live verification.

## 05-rehearse-notebook-proposal: Rehearse a governed notebook proposal

Provider: Local governed API; server: not applicable; tools: plan, validate, approve, simulate, audit.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
Explain and rehearse LOCAL create_notebook for dq_review_notebook through the offline API. Require separate approval and inspect SIMULATED verification and audit. Do not run a notebook or correct data.
```

Checkpoint: SIMULATED verification and audit exist; duplicate execution and self-approval are refused.

Offline equivalent: Use the step's existing shared rehearsal panel.

## 06-converge: Verify outcomes and record limits

Provider: Local review; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Map requirements to observed tests, distinguish LOCAL and SIMULATED outcomes, and list live and production gaps. Keep Claude Code execution DOCUMENTED ONLY unless actually run.
```

Checkpoint: The learner can reproduce the baseline and explain which claims remain unverified.

Offline equivalent: Review the existing practical and research teaching lenses.
