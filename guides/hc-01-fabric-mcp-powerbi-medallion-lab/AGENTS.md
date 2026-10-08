# AGENTS.md — Guide HC-01 (Fabric MCP + Power BI medallion lab)

Scoped instructions for agents working on this guide or in a lab folder created from it. The
repository's root `AGENTS.md` still applies; this file adds the lab's rules. Synthetic data only.

## Run one step at a time

- Read the step from `guide.yaml` (or the `get_guide_step` tool on `ffia-local`). Submit one
  prompt, stop at its checkpoint, and show the evidence the step requires.
- Propose first, wait for review, then apply. Authoring and execution are separate prompts.
- Before every cloud call, say the **provider, server and exact tool**.

## Tools for this lab

| Need | Use | Not |
|---|---|---|
| Find the workspace (step 02) | Fabric MCP `core_search-catalog`, then `onelake_list-items` | `onelake_list-workspaces` (can return an empty list) |
| List lakehouse tables | Fabric MCP `onelake_list-tables` with `namespace: dbo` | Omitting the namespace (returns 400) |
| Create lakehouse, `Files/raw`, upload (04–05) | Fabric MCP `core_create-item`, `onelake_create-directory`, `onelake_upload-file` (overwrite **false**) | REST, Azure CLI or a skill calling APIs |
| Notebooks (07–10) | Draft locally; compare with `fabric/workspace/MCP_0x_*.Notebook`; publish and run with the Fabric Data Engineering extension | Running local Python and calling it Fabric |
| Semantic model and report (11–14) | Power BI Modeling MCP with the `semantic-model-authoring` and `powerbi-report-cli` skills | Editing a shared model outside the dev workspace |

The MCP profile is `hc01-lab` (this folder's `.mcp.json`; for VS Code run
`ffia mcp render hc01-lab --client vscode --output <LAB_PATH>/.vscode/mcp.json`). It starts the
real Fabric MCP server and `ffia-local` as the fallback. Install the pinned Fabric Skills with
`ffia skills install`; each step's `skills` field names the ones to load. Skills run `az rest`
outside MCP; every such command needs approval.

## Fabric MCP first, `ffia-local` as the fallback

1. Use the step's Fabric MCP tool (`tool_path.tools`).
2. If it is unavailable (not signed in, no capacity, server not running, tool error), **say so**,
   with the error. Do not retry with REST, the Azure CLI or a different tool.
3. Offer the step's fallback (`tool_path.fallback`): the named `ffia-local` tools, labeled with
   the fallback's label. Use it only after saying the primary tool failed.
4. **Reads** fall back to `LOCAL` reads (`list_fabric_workspaces`, `list_fabric_items`, …).
   **Writes never fall back to a write**: a failed create or upload stops, and the fallback is a
   `SIMULATED` rehearsal (`generate_fabric_change_plan`, `validate_change_plan`). Nothing is
   created, and you never present the rehearsal as the real change.
5. In the summary, list which results came from Fabric MCP (`LIVE`) and which from the fallback.

## Writes

- Every write step is `approval_required: true`. Check for an existing item (or a non-empty
  `Files/raw`) first; if one exists, stop and report it. Never retry a create without checking.
- Use exact IDs from your local notes. Never paste tenant, workspace, lakehouse or model IDs into
  committed files or chat summaries.
- Use the `ffia-governed-fabric-change` skill to wrap any change in PLAN → VALIDATE → APPROVE →
  EXECUTE → VERIFY → AUDIT.

## Evidence

- Compare counts with `data/synthetic/expected/hc-lab-7file-v1.json` (200 / 1,025 / 428 / 1,025 /
  4,299 / 643 / 150 raw rows; 35 of 211 readmissions).
- Not evidence: a configured server, a tool description, an item's existence, a matching byte size,
  a Spark application status, or a portal run presented as an MCP job.
- Label results `LIVE`, `PREVIEW`, `LOCAL` or `SIMULATED`. All metrics are synthetic
  demonstrations, not clinical measures.
