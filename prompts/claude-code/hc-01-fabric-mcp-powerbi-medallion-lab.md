# HC-01: Fabric MCP + Power BI medallion lab (healthcare, synthetic)

<!-- Generated from education and guide YAML; run ffia prompts render. -->

DOCUMENTED ONLY: no Claude Code runs were recorded. Claude models inside Copilot are not Claude Code.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/hc-01-fabric-mcp-powerbi-medallion-lab/guide.yaml).

Dataset: `hc-lab-7file-v1`. Guide status: validated-offline.

## 01-set-up-tools: Set up and verify the tools

Provider: Local workstation; server: not applicable; tools: MCP: List Servers.

Skills: none required. Human approval required: no.

```text
Run `claude mcp list` and report which servers from .mcp.json are connected and which tools they expose. Confirm the Power BI authoring skills are available. Do not call any cloud tool.
```

Checkpoint: Every required tool is installed and the Fabric MCP server is running with callable tools.

Offline equivalent: Run the demo readiness check and export the synthetic data to a separate folder.

Fallback: LOCAL, ffia-local, get_runtime_status. Reports which providers and MCP tools are ready.

## 02-verify-tenant-anchor: Verify the tenant through a real MCP call

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: core_search-catalog, onelake_list-items.

Skills: none required. Human approval required: no.

```text
Using the fabric-mcp server from this guide's .mcp.json, call core_search-catalog for <WORKSPACE_NAME>, then onelake_list-items with the returned workspace ID. Show the raw tool calls and results. Stop if the workspace is missing. No REST or CLI fallback.
```

Checkpoint: The known workspace ID appears in the actual MCP response and a workspace-scoped call succeeds.

Offline equivalent: List workspaces from the Local Fabric Provider (labeled LOCAL).

Fallback: LOCAL, ffia-local, list_fabric_workspaces, list_fabric_items. LOCAL offline; LIVE through the router when FFIA_FABRIC_LIVE=1 in hybrid.

## 03-create-workspace: Create the lab workspace (portal)

Provider: Fabric portal (manual); server: not applicable; tools: none.

Skills: none required. Human approval required: yes.

```text
Repeat the step 02 check (core_search-catalog, then onelake_list-items) for <WORKSPACE_ID>. Read-only.
```

Checkpoint: The empty workspace exists on the intended capacity and appears in the MCP listing.

Offline equivalent: Not applicable (portal step). The local provider exposes a simulated workspace.

## 04-create-lakehouse: Create and confirm the lakehouse

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: onelake_list-items, core_create-item.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
Check for an existing healthcare_lakehouse with onelake_list-items in <WORKSPACE_ID>; if absent, create it with core_create-item and confirm with onelake_list-items. Return the lakehouse ID. Stop.
```

Checkpoint: Exactly one healthcare_lakehouse exists and its ID is recorded locally.

Offline equivalent: Plan the change, approve it as a different person, execute it in the simulated workspace (labeled SIMULATED).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, validate_change_plan. Rehearsal only; a failed live create stops and is never redirected.

## 05-upload-data: Upload the synthetic CSVs

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: onelake_list-files, onelake_create-directory, onelake_upload-file.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
List Files/raw in <LAKEHOUSE_ID> and stop if it is not empty; then upload the seven CSVs with onelake_upload-file (overwrite false), list them with onelake_list-files and compare sizes. Stop on any failure. No tables.
```

Checkpoint: Files/raw contains exactly the seven CSVs and every remote size matches its local file.

Offline equivalent: Export the CSVs with SHA256SUMS and verify the checksums.

Fallback: SIMULATED, ffia-local, inspect_healthcare_scenario, generate_fabric_change_plan. Profiles the seven source files and rehearses the upload plan; nothing is uploaded.

## 06-profile-data: Profile the source data locally

Provider: Local Python (not a cloud call); server: not applicable; tools: none.

Skills: e2e-medallion-architecture. Human approval required: no.

```text
Profile data/raw/*.csv with a CSV-aware parser (no edits): row counts, keys, orphans, discharge_date, literal \n versus real newlines, and an ER diagram of supported joins. Stop after the profile.
```

Checkpoint: The profile matches the expected baseline and records the date and text quirks.

Offline equivalent: Inspect the scenario and its documented quirks.

Fallback: LOCAL, ffia-local, inspect_healthcare_scenario.

## 07-bronze-draft: Draft the Bronze notebook (no execution)

Provider: Local editor; server: not applicable; tools: none.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: no.

```text
Draft notebooks/MCP_01_Bronze.ipynb (local only) with the same four-cell structure, count validation before write, read-back after write, and Delta overwrite of the seven bronze_ tables. Do not run or publish.
```

Checkpoint: The draft is reviewed, including output table names and the lakehouse binding.

Offline equivalent: Compare with the local Bronze SQL and build.

Fallback: LOCAL, ffia-local, inspect_medallion_architecture.

## 08-bronze-publish-run: Publish and run Bronze on Fabric Spark

Provider: Fabric Data Engineering extension; server: not applicable; tools: fabricWorkspaceInfo, Microsoft Fabric Runtime kernel.

Skills: spark-cli. Human approval required: yes.

```text
In VS Code (Claude harness) or the Fabric portal, publish the reviewed notebook, confirm its cloud ID and lakehouse binding, run it once on Fabric Spark, and report per-table counts. Name the provider.
```

Checkpoint: Seven Bronze Delta tables exist with persisted counts equal to the baseline.

Offline equivalent: Bronze row counts in the local build and expected baseline.

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan. Rehearses publishing the notebook; the local Bronze build is `ffia data build`.

## 09-silver: Design, draft, publish and run Silver

Provider: Fabric Data Engineering extension; server: not applicable; tools: Microsoft Fabric Runtime kernel.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: yes.

```text
Propose Silver rules (types, dates, bands, mappings, nulls, diagnostics) and stop. After approval, draft MCP_02_Silver.ipynb; publishing and running is a separate step.
```

Checkpoint: Seven typed Silver tables preserve the baseline counts, and parsing and range issues are explained.

Offline equivalent: Local Silver SQL and diagnostics (counts must match the expected baseline).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, detect_duplicate_records, preview_table. Diagnostics read the local Silver tables; publishing is rehearsed.

## 10-gold: Design, draft, publish and run Gold

Provider: Fabric Data Engineering extension; server: not applicable; tools: Microsoft Fabric Runtime kernel.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: yes.

```text
Propose the Gold grains, readmission and eligibility rule, and key checks; stop for review; then draft and separately run MCP_03_Gold with reconciliation totals printed.
```

Checkpoint: Twenty-four lab tables exist (7 Bronze, 7 Silver, 6 Gold, 4 dimensions) and reconciliation totals are captured.

Offline equivalent: Local Gold build and expected baseline (the live totals must match).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, inspect_medallion_architecture, evaluate_measures. Reads the local Gold tables; publishing is rehearsed.

## 11-semantic-model: Bootstrap and connect the Direct Lake semantic model

Provider: Power BI Authoring MCP (local); server: powerbi-modeling-mcp; tools: connection, model inspection.

Skills: semantic-model-authoring. Human approval required: yes.

```text
Connect to <MODEL_ID> with the Power BI Authoring MCP server and report tables, storage modes and relationships. Read-only.
```

Checkpoint: The exact model is connected and its seven tables use Direct Lake.

Offline equivalent: The semantic model contract (tables, grains and roles).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, evaluate_measures. Rehearses the model creation; measures evaluate locally.

## 12-relationships-and-measures: Apply relationships and measures, then reconcile DAX

Provider: Power BI Authoring MCP (local); server: powerbi-modeling-mcp; tools: relationships, measures, DAX query.

Skills: semantic-model-authoring. Human approval required: yes.

```text
Propose relationships and measures; stop for review; then apply through Power BI Authoring MCP and reconcile DAX results with the Gold totals.
```

Checkpoint: Relationships are verified and every DAX check equals the expected baseline.

Offline equivalent: Evaluate the measure contracts locally and compare observed values with the baseline.

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, evaluate_against_baseline. Rehearses the model change; the baseline check runs locally.

## 13-model-review: Review the model (read-only)

Provider: Power BI authoring skills + Power BI Authoring MCP; server: powerbi-modeling-mcp; tools: model inspection.

Skills: semantic-model-authoring. Human approval required: no.

```text
Review <MODEL_ID> read-only for best practices and AI readiness; group findings by severity.
```

Checkpoint: Findings are recorded; only explicitly approved fixes are applied and re-checked.

Offline equivalent: Compare the live model with the semantic model contract and vocabulary.

Fallback: LOCAL, ffia-local, evaluate_against_baseline, evaluate_measures.

## 14-report: Plan, build, preview and publish the report

Provider: Power BI authoring skills; server: not applicable; tools: report planner, report authoring.

Skills: powerbi-report-cli. Human approval required: yes.

```text
Plan the two-page report, stop for review, then build the PBIR project bound to <MODEL_ID> and stop before publishing.
```

Checkpoint: The report renders in preview, cards reconcile with DAX checks, and it is published as a separate step.

Offline equivalent: Report plan review against the measure contracts.

## 15-final-validation: Final read-only validation

Provider: Mixed: Fabric MCP, Power BI Authoring MCP and the Fabric portal; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Run the same read-only acceptance checks; report pass, fail or not verified with evidence and tools used.
```

Checkpoint: Every required check passes; unavailable checks are resolved before calling the lab complete.

Offline equivalent: Run the offline demo, which prints LIVE versus SIMULATED evidence.

Fallback: LOCAL, ffia-local, get_runtime_status, evaluate_against_baseline.

## 16-troubleshooting: Troubleshoot credentials and tooling

Provider: Local workstation; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Diagnose <FAILING_STEP> read-only: MCP server status, Azure CLI account and tenant, credential selection and notebook binding. Never print tokens.
```

Checkpoint: The governing control is identified and the failed step's checkpoint passes on retry.

Offline equivalent: Inject a Fabric outage and watch the circuit breaker and fallback.

Fallback: LOCAL, ffia-local, get_runtime_status, get_audit_record.
