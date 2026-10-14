# DQ-01: Investigate synthetic data quality with GitHub Copilot

<!-- Generated from education and guide YAML; run ffia prompts render. -->

Recorded bake-off results describe GitHub Copilot CLI only, not every GitHub Copilot surface.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/dq-01-synthetic-quality-investigation/guide.yaml).

Dataset: `mfg-sales-v1`. Guide status: validated-offline.

## 01-define-contract: Define the quality contract

Provider: Local editor; server: not applicable; tools: none.

Skills: spec-driven-delivery. Human approval required: no.

```text
Read this guide, the manufacturing profile and its committed expected baseline. Explain the order-line grain, nine quality categories and the separation between explanation and proof. Read the governed-data-foundations lesson at your chosen depth. No cloud calls or edits.
```

Checkpoint: The learner names the baseline, grain and authority boundary.

Offline equivalent: Read the existing five-level foundations and research brief.

## 02-reconcile-findings: Reconcile all quality findings

Provider: Local synthetic DuckDB CLI; server: not applicable; tools: ffia mfg quality --check --json.

Skills: none required. Human approval required: no.

```text
Run ffia mfg quality --check --json locally. Report the LOCAL label, baseline_passed and nine observed counts. On any mismatch, stop and inspect the check or input; do not rewrite expected values. No Fabric or Foundry call.
```

Checkpoint: All nine counts match exactly and the command exits zero.

Offline equivalent: The same deterministic quality reconciliation.

## 03-break-and-recover: Challenge the baseline in a scratch copy

Provider: Local pytest runner; server: not applicable; tools: pytest tests/offline/test_use_case_authoring.py --no-cov.

Skills: none required. Human approval required: no.

```text
Run the offline authoring regression in tests/offline/test_use_case_authoring.py. Explain its scratch baseline mutation and failed reconciliation. Keep committed data unchanged. State that detecting a controlled discrepancy is not production-scale validation.
```

Checkpoint: The adverse-case test observes a failed baseline gate; the original baseline still passes.

Offline equivalent: Network-blocked pytest with isolated synthetic files.

## 04-inspect-connected-option: Compare optional Fabric MCP context

Provider: Microsoft Fabric; server: fabric-mcp; tools: core_search-catalog.

Skills: ffia-governed-fabric-change. Human approval required: no.

```text
For the connected option, first state Microsoft Fabric / fabric-mcp / core_search-catalog. Perform only read-only catalogue inspection against the approved demo scope. If unavailable, report the error and use only ffia-local list_fabric_items as LOCAL. Do not publish identifiers. Metadata cannot prove the nine quality counts. Skip cloud calls for the offline acceptance path.
```

Checkpoint: The learner separates optional item visibility from deterministic quality evidence.

Offline equivalent: Explain the primary and fallback using the fabric-mcp-landscape lesson without calling cloud tools.

Fallback: LOCAL, ffia-local, list_fabric_items. Disclose primary unavailability; this does not satisfy live verification.

## 05-rehearse-notebook-proposal: Rehearse a governed notebook proposal

Provider: Local governed API; server: not applicable; tools: plan, validate, approve, simulate, audit.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
In the offline workshop, draft a create_notebook plan for dq_review_notebook, destination LOCAL. Review the exact target and explain that creation does not execute a correction. Use a separate approver, execute the SIMULATED rehearsal, and inspect verification and audit.
```

Checkpoint: SIMULATED verification and audit exist; duplicate execution and self-approval are refused.

Offline equivalent: Use the step's existing shared rehearsal panel.

## 06-converge: Verify outcomes and record limits

Provider: Local review; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Compare this guide's acceptance criteria with tests/offline/test_use_case_authoring.py and the authoring verification record. Explain what GitHub Copilot, Skills, MCP, deterministic checks and approval each contributed. Record unavailable live evidence and production gaps.
```

Checkpoint: The learner can reproduce the baseline and explain which claims remain unverified.

Offline equivalent: Review the existing practical and research teaching lenses.
