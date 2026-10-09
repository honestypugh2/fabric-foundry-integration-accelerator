# HC-01: Fabric MCP + Power BI medallion lab (healthcare, synthetic)

<!-- Generated from education and guide YAML; run ffia prompts render. -->

Recorded bake-off results describe Copilot CLI only, not every Copilot surface.

Read AGENTS.md first (Claude Code imports it through CLAUDE.md). Use synthetic data only. State the provider, server and tool before cloud calls. Default to read-only; a prompt is not approval for a write. Label execution and fallback honestly.

Source: [guide](../../guides/hc-01-fabric-mcp-powerbi-medallion-lab/guide.yaml).

Dataset: `hc-lab-7file-v1`. Guide status: validated-offline.

## 01-set-up-tools: Set up and verify the tools

Provider: Local workstation; server: not applicable; tools: MCP: List Servers.

Skills: none required. Human approval required: no.

```text
Check my lab prerequisites without changing anything. List which MCP servers are running and which tools each exposes, confirm the Power BI authoring skills are enabled in this chat, and tell me which items in the guide's tool list are missing. Do not call any cloud tool.
```

Checkpoint: Every required tool is installed and the Fabric MCP server is running with callable tools.

Offline equivalent: Run the demo readiness check and export the synthetic data to a separate folder.

Fallback: LOCAL, ffia-local, get_runtime_status. Reports which providers and MCP tools are ready.

## 02-verify-tenant-anchor: Verify the tenant through a real MCP call

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: core_search-catalog, onelake_list-items.

Skills: none required. Human approval required: no.

```text
Call the Fabric MCP core_search-catalog tool directly with search text <WORKSPACE_NAME> and report the returned workspace ID and exact name. Then call onelake_list-items with that workspace ID and confirm the call succeeds. Show both invocations and results. If the workspace is not found or a tool cannot be called, stop. Do not create anything and do not fall back to REST or the CLI.
```

Checkpoint: The known workspace ID appears in the actual MCP response and a workspace-scoped call succeeds.

Offline equivalent: List workspaces from the Local Fabric Provider (labeled LOCAL).

Fallback: LOCAL, ffia-local, list_fabric_workspaces, list_fabric_items. LOCAL offline; LIVE through the router when FFIA_FABRIC_LIVE=1 in hybrid.

## 03-create-workspace: Create the lab workspace (portal)

Provider: Fabric portal (manual); server: not applicable; tools: none.

Skills: none required. Human approval required: yes.

```text
I created a new blank workspace in the portal. Repeat the step 02 read-only check (core_search-catalog, then onelake_list-items) for the new workspace <WORKSPACE_ID> and confirm it appears and is empty. Do not create anything.
```

Checkpoint: The empty workspace exists on the intended capacity and appears in the MCP listing.

Offline equivalent: Not applicable (portal step). The local provider exposes a simulated workspace.

## 04-create-lakehouse: Create and confirm the lakehouse

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: onelake_list-items, core_create-item.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
Using the Fabric MCP core_create-item tool, create a Lakehouse named healthcare_lakehouse in workspace <WORKSPACE_ID>. First check onelake_list-items for an existing item with that name and report it instead of creating a duplicate. Confirm with onelake_list-items and return the lakehouse ID. Stop after confirmation.
```

Checkpoint: Exactly one healthcare_lakehouse exists and its ID is recorded locally.

Offline equivalent: Plan the change, approve it as a different person, execute it in the simulated workspace (labeled SIMULATED).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, validate_change_plan. Rehearsal only; a failed live create stops and is never redirected.

## 05-upload-data: Upload the synthetic CSVs

Provider: Fabric MCP Server (local); server: fabric-mcp; tools: onelake_list-files, onelake_create-directory, onelake_upload-file.

Skills: ffia-governed-fabric-change. Human approval required: yes.

```text
First check the seven CSVs under <PROJECT_PATH>/data/raw. Using Fabric MCP, list Files/raw in lakehouse <LAKEHOUSE_ID> with onelake_list-files; if it already contains any file, stop and report it. Otherwise create Files/raw with onelake_create-directory and upload each CSV with onelake_upload-file using its local-file-path parameter and overwrite set to false. List Files/raw again and compare every remote byte size with the local file. If a call fails or the tool has no local-file-path parameter, stop. Do not create tables.
```

Checkpoint: Files/raw contains exactly the seven CSVs and every remote size matches its local file.

Offline equivalent: Export the CSVs with SHA256SUMS and verify the checksums.

Fallback: SIMULATED, ffia-local, inspect_healthcare_scenario, generate_fabric_change_plan. Profiles the seven source files and rehearses the upload plan; nothing is uploaded.

## 06-profile-data: Profile the source data locally

Provider: Local Python (not a cloud call); server: not applicable; tools: none.

Skills: e2e-medallion-architecture. Human approval required: no.

```text
Read the seven CSVs in data/raw without changing them, using a CSV-aware parser. Report parsed row counts, columns, candidate keys, blank or duplicate keys, and unmatched patient_id and encounter_id values. Check discharge_date in encounters, and distinguish real newlines from the literal two-character sequence \n in clinical notes. Draw an entity-relationship diagram from the joins the data supports. Stop after the profile.
```

Checkpoint: The profile matches the expected baseline and records the date and text quirks.

Offline equivalent: Inspect the scenario and its documented quirks.

Fallback: LOCAL, ffia-local, inspect_healthcare_scenario.

## 07-bronze-draft: Draft the Bronze notebook (no execution)

Provider: Local editor; server: not applicable; tools: none.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: no.

```text
Create only a local draft at notebooks/MCP_01_Bronze.ipynb for workspace <WORKSPACE_ID> and default lakehouse healthcare_lakehouse (<LAKEHOUSE_ID>) with valid Fabric PySpark metadata. Four cells: explanation, configuration with expected counts, an ingestion function, and a driver. Read all seven CSVs from Files/raw with header, inferSchema, multiLine and a double-quote escape. Keep the literal \n text and the blank condition encounter_id values. Write the seven bronze_ tables as Delta with overwrite and overwriteSchema. Validate parsed counts before writing and read every table back. Show the code. Do not execute, publish or upload.
```

Checkpoint: The draft is reviewed, including output table names and the lakehouse binding.

Offline equivalent: Compare with the local Bronze SQL and build.

Fallback: LOCAL, ffia-local, inspect_medallion_architecture.

## 08-bronze-publish-run: Publish and run Bronze on Fabric Spark

Provider: Fabric Data Engineering extension; server: not applicable; tools: fabricWorkspaceInfo, Microsoft Fabric Runtime kernel.

Skills: spark-cli. Human approval required: yes.

```text
The Bronze draft is reviewed. Check the current Fabric Data Engineering workspace with fabricWorkspaceInfo and require <WORKSPACE_ID>. Publish the reviewed notebook as MCP_01_Bronze with a supported operation and name the tool you used. Confirm the cloud notebook ID, its source and its default lakehouse. Then, with the notebook attached to the Microsoft Fabric Runtime kernel, run it once and report each table's input and persisted counts. Stop on any failure.
```

Checkpoint: Seven Bronze Delta tables exist with persisted counts equal to the baseline.

Offline equivalent: Bronze row counts in the local build and expected baseline.

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan. Rehearses publishing the notebook; the local Bronze build is `ffia data build`.

## 09-silver: Design, draft, publish and run Silver

Provider: Fabric Data Engineering extension; server: not applicable; tools: Microsoft Fabric Runtime kernel.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: yes.

```text
Inspect the Bronze schema and propose the Silver rules: exact types, date parsing, age, risk and LOS thresholds, condition category mapping with an explicit unmapped category, null handling and diagnostics. Keep all seven row counts. Stop for review. After I approve, draft notebooks/MCP_02_Silver.ipynb, then publish and run it in a separate prompt.
```

Checkpoint: Seven typed Silver tables preserve the baseline counts, and parsing and range issues are explained.

Offline equivalent: Local Silver SQL and diagnostics (counts must match the expected baseline).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, detect_duplicate_records, preview_table. Diagnostics read the local Silver tables; publishing is rehearsed.

## 10-gold: Design, draft, publish and run Gold

Provider: Fabric Data Engineering extension; server: not applicable; tools: Microsoft Fabric Runtime kernel.

Skills: e2e-medallion-architecture, spark-cli. Human approval required: yes.

```text
Propose the Gold logic and dimension keys: one row per index inpatient encounter using the actual discharge_date and the next inpatient admission strictly after it (1 to 30 days inclusive), with a follow-up eligibility rule; patient-year ED utilization; diagnosis-facility ALOS keeping counts and totals; encounter and claim grain facts; population health including zero-condition patients; and dim_date, dim_patient, dim_facility, dim_payer. Include checks for duplicate keys, row multiplication and missing dimension keys. Stop for review. Then draft, publish and run MCP_03_Gold.
```

Checkpoint: Twenty-four lab tables exist (7 Bronze, 7 Silver, 6 Gold, 4 dimensions) and reconciliation totals are captured.

Offline equivalent: Local Gold build and expected baseline (the live totals must match).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, inspect_medallion_architecture, evaluate_measures. Reads the local Gold tables; publishing is rehearsed.

## 11-semantic-model: Bootstrap and connect the Direct Lake semantic model

Provider: Power BI Authoring MCP (local); server: powerbi-modeling-mcp; tools: connection, model inspection.

Skills: semantic-model-authoring. Human approval required: yes.

```text
Using Power BI Authoring MCP connection tools and the semantic-model-authoring skill, connect to model <MODEL_ID> in workspace <WORKSPACE_ID> at <XMLA_ENDPOINT>. Confirm the connected model identity and inspect its seven tables, columns, storage modes and relationships. Report the tools used. Do not change the model.
```

Checkpoint: The exact model is connected and its seven tables use Direct Lake.

Offline equivalent: The semantic model contract (tables, grains and roles).

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, evaluate_measures. Rehearses the model creation; measures evaluate locally.

## 12-relationships-and-measures: Apply relationships and measures, then reconcile DAX

Provider: Power BI Authoring MCP (local); server: powerbi-modeling-mcp; tools: relationships, measures, DAX query.

Skills: semantic-model-authoring. Human approval required: yes.

```text
Propose the relationships (one-to-many, single direction, dimension to fact, one active date role per fact), friendly names, hidden keys and descriptions, then the measures with formats and zero-denominator behavior. Do not add a bed occupancy measure (no denominator exists). Stop for review. After approval, apply through Power BI Authoring MCP and run DAX checks for encounters, ED visits, inpatient count and LOS, paid and denied amounts, denial rate, patient counts and the readmission numerator, denominator and rate. Compare with the Gold totals and report mismatches.
```

Checkpoint: Relationships are verified and every DAX check equals the expected baseline.

Offline equivalent: Evaluate the measure contracts locally and compare observed values with the baseline.

Fallback: SIMULATED, ffia-local, generate_fabric_change_plan, evaluate_against_baseline. Rehearses the model change; the baseline check runs locally.

## 13-model-review: Review the model (read-only)

Provider: Power BI authoring skills + Power BI Authoring MCP; server: powerbi-modeling-mcp; tools: model inspection.

Skills: semantic-model-authoring. Human approval required: no.

```text
Use the semantic-model-authoring workflow to review <MODEL_ID> for best practices and AI readiness: relationship ambiguity, grain, date roles, hidden keys, descriptions, synonyms, measure definitions and unsupported clinical interpretations. Group findings by severity. Do not change the model.
```

Checkpoint: Findings are recorded; only explicitly approved fixes are applied and re-checked.

Offline equivalent: Compare the live model with the semantic model contract and vocabulary.

Fallback: LOCAL, ffia-local, evaluate_against_baseline, evaluate_measures.

## 14-report: Plan, build, preview and publish the report

Provider: Power BI authoring skills; server: not applicable; tools: report planner, report authoring.

Skills: powerbi-report-cli. Human approval required: yes.

```text
Using the report planning skill, propose a two-page report on <MODEL_ID>: an executive overview (readmission rate, inpatient ALOS, ED visits and denial rate cards, a monthly encounter trend and a facility breakdown with clear date-role labels) and a population page from dim_patient with patient-attribute slicers. Do not author yet. After review, build it as a PBIP/PBIR project bound to the existing model, validate the definition and stop before publication.
```

Checkpoint: The report renders in preview, cards reconcile with DAX checks, and it is published as a separate step.

Offline equivalent: Report plan review against the measure contracts.

## 15-final-validation: Final read-only validation

Provider: Mixed: Fabric MCP, Power BI Authoring MCP and the Fabric portal; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Perform a read-only final validation for workspace <WORKSPACE_ID>, lakehouse <LAKEHOUSE_ID> and model <MODEL_ID>: workspace and capacity, raw files, Bronze, Silver, Gold and dimension counts, notebook bindings, model storage mode and relationships, DAX reconciliation, review findings and the published report. Name the provider and tool for each check, report pass, fail or not verified with concrete evidence, and do not repair or rerun anything.
```

Checkpoint: Every required check passes; unavailable checks are resolved before calling the lab complete.

Offline equivalent: Run the offline demo, which prints LIVE versus SIMULATED evidence.

Fallback: LOCAL, ffia-local, get_runtime_status, evaluate_against_baseline.

## 16-troubleshooting: Troubleshoot credentials and tooling

Provider: Local workstation; server: not applicable; tools: none.

Skills: none required. Human approval required: no.

```text
Diagnose why <FAILING_STEP> failed without changing authentication or server settings. Check, in order, agent mode and enabled tools, the MCP server log, the Azure CLI account and tenant, the credential selector inherited by VS Code, the Data Engineering workspace selection and the Spark kernel. Never print tokens.
```

Checkpoint: The governing control is identified and the failed step's checkpoint passes on retry.

Offline equivalent: Inject a Fabric outage and watch the circuit breaker and fallback.

Fallback: LOCAL, ffia-local, get_runtime_status, get_audit_record.
