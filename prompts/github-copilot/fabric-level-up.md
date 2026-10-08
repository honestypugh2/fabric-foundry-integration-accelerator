# Prompt pack: Leveling up Fabric data engineering with GitHub Copilot

Prompts used in [the run of show](../../demos/fabric-copilot-level-up.md). Each prompt is shown with
the window it runs in, its maturity level and what to expect. Use VS Code Chat in **agent mode**.
Approve tool calls only after reading them.

- **Repo window:** this repository; MCP servers come from `.mcp.json` (`ffia-local`,
  `microsoft-learn`).
- **Lab window:** a scratch folder whose `.vscode/mcp.json` is rendered from `fabric-readonly`.

The HC-01 step prompts (all 16 steps, for Copilot and Claude Code) live in
[`guide.yaml`](../../guides/hc-01-fabric-mcp-powerbi-medallion-lab/guide.yaml) and in the app's
guide runner.

## Fabric MCP

### P-MCP-1: find the workspace (L4, LIVE, read-only)

Window: lab.

```text
Using the Fabric MCP server, call core_search-catalog with the search text "ffia-dev". Before
calling, state the provider, server and tool. Report the item type, display name and description
that come back, but do not print any IDs. Do not call any other tool.
```

Expect a Workspace named `ffia-dev`, labeled LIVE.

### P-MCP-2: try to write through a read-only profile (governance)

Window: lab.

```text
Create a Lakehouse named demo_lakehouse in the ffia-dev workspace using the Fabric MCP server.
```

Expect the agent to report that no create tool is available. The profile starts the server with
`--read-only` and an allow-list, and the server refuses unlisted tools. Point out that this is not
a failure: it's the control working.

### P-MCP-3: propose the change instead (L5, LOCAL)

Window: repo.

```text
Use the ffia-local MCP tool generate_fabric_change_plan to propose creating a Lakehouse named
healthcare_lakehouse in workspace alias demo-dev with destination LIVE, requested by
copilot-agent. Show the plan's status, policy reasons, risk, rollback and next step. Do not try to
approve it.
```

Expect status `BLOCKED` with "Live mutation is disabled", `approval_required: true`, and the next
step "A human approves… MCP cannot approve it." Labeled LOCAL.

## Fabric Skills

### P-SKILL-1: plan with a Microsoft skill, no Fabric calls (L3)

Window: repo.

```text
Using the e2e-medallion-architecture skill, plan a Bronze/Silver/Gold design for the
hc-lab-7file-v1 synthetic dataset in data/synthetic/raw/hc-lab-7file-v1. Do not call any Fabric API
and do not run az rest. Then compare your plan with the ffia-local inspect_medallion_architecture
result for the same profile and list the differences.
```

Expect a layered plan from the skill's procedure, compared against the 24 local tables (7 Bronze, 7
Silver, 10 Gold and dimension tables). Any `az rest` the agent proposes needs approval.

### P-SKILL-2: which skill, which tool? (L3, governance)

Window: repo.

```text
Use the ffia-governed-fabric-change skill. I want to upload seven CSVs to Files/raw in our dev
lakehouse. Classify the request, tell me which MCP profile and tool you would use and what you
must check first, and stop before any cloud call.
```

Expect: a change; profile `hc01-lab`; tool `onelake_upload-file` with overwrite false; check that
`Files/raw` is empty first; approval required.

## GitHub Copilot level-up

### P-COP-1: explain a transform (L1–L2)

Window: repo.

```text
Explain src/fabric_foundry_accelerator/synthetic/sql/silver/silver_encounters.sql to a data
engineer: what each data-quality flag catches, and why discharge is never approximated as
encounter date plus length of stay. Then show the Spark SQL form of the same query from
fabric/workspace/MCP_02_Silver.Notebook/notebook-content.py.
```

### P-COP-2: see the data through MCP (L4, LOCAL)

Window: repo.

```text
Call the ffia-local inspect_medallion_architecture tool for profile hc-lab-7file-v1. Summarize
each layer's tables and row counts, and tell me the execution label and whether a cloud
operation was performed.
```

Expect 24 tables. Label LOCAL, `cloud_operation_performed: false`.

### P-COP-3: governed change (L5)

Same as P-MCP-3. Then, in the app, open the HC-01 guide, step 04. In **Rehearse this write**,
click **1. Plan and validate**, then **2. Approve as** a different person, then **3. Execute with
the scoped writer** (SIMULATED). Open the **Audit trail**.

## Power BI

### P-PBI-1: reconcile the measures (LOCAL)

Window: repo.

```text
Call the ffia-local evaluate_against_baseline tool for profile hc-lab-7file-v1. Report how many
measures were compared and passed, the readmission rate and count, and the execution label. Remind
me that these are synthetic demonstration metrics.
```

Expect 23 of 23 passed; 30-day readmissions 35 of 211 (0.165877). Label LOCAL.
