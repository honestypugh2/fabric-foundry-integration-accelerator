# Activate notebook and Power BI tooling

**Recorded 2026-10-13. LOCAL discovery verified; connected execution not certified.**
Installing an extension, starting its server and listing tools are three different checks.
None proves notebook execution, a semantic-model change or report publication.

## Which component does what?

| Component | Observed capability | Execution boundary |
|---|---|---|
| Fabric MCP 1.4.0 (`fabric-mcp`) | The root profile exposes eight documentation/metadata tools | Read-only default; HC-01 opt-in tools handle lakehouse creation and upload |
| Fabric Data Engineering extension 1.26.0 (`SynapseVSCode.synapse`) | Registers notebook tools such as `fabricPublishNotebook` and `fabricWorkspaceInfo` in VS Code | Extension tools, not Fabric MCP 1.4.0 tools; each publish needs approval |
| Extension-managed `fabric-notebook-mcp` | Actual MCP handshake reported server 0.1.0 and 11 tools, including `list_artifacts`, `get_lakehouse_detail` and documentation helpers | Discovery succeeded; this catalogue contains no notebook publish or run tool |
| Microsoft Fabric Runtime kernel | Extension's documented remote Spark execution path | Select and verify the remote kernel; local Python/Jupyter is not Fabric execution |
| Power BI Authoring local server 1.0.0 | Actual stdio handshake and `tools/list` returned 22 tools, including `connection_operations`, `model_operations`, `relationship_operations`, `measure_operations` and `dax_query_operations` | Read-only startup verified on Linux ARM64; authoring requires a separate opt-in plan |

Power BI Desktop remains Windows-only; the local MCP server itself works on Linux ARM64.
Power BI Authoring MCP operates on semantic models, not report visuals. Use the
`powerbi-report-cli` skill for the report lifecycle and the `semantic-model-authoring` skill
for models. Skills supply instructions, not missing execution tools.

## Activate safely in VS Code

1. Install the recommended Fabric Data Engineering, Jupyter and Power BI Authoring extensions
   in the extension host for the open repository. With WSL/remote development, a Windows-side
   installation alone does not establish availability in the Linux host.
2. Reload the VS Code window if needed. Use **MCP: List Servers** to find
   `fabric-notebook-mcp` and `powerbi-authoring-local`, then inspect their status/output.
   These extension-provided servers are separate from the root Fabric-first configuration.
3. Restart Power BI's server with the repository's
   [VS Code settings](../../.vscode/settings.json):
   `--start --read-only --require-confirmation`.
   The extension's configuration key really is `args` at the workspace root; it is not a
   `powerbi.*` key. This overrides upstream automatic EULA acceptance/write mode.
4. Review the [Power BI server EULA](https://go.microsoft.com/fwlink/?LinkId=2381247).
   Accept only through an explicitly authorized `accept_eula` call. Do not add acceptance
   arguments or environment variables to shared configuration. Discovery works before
   acceptance; model operations remain gated.
5. In the VS Code Copilot Agent chat's tool picker, enable the intended extension tools.
   Confirm `fabricPublishNotebook` and `fabricWorkspaceInfo` are actually selectable.
   An existing SDK/CLI conversation can retain an older tool inventory; reconnect or start a
   new session if the tools are still absent. Do not assume extension installation injected
   them into every client.
6. Sign in using **Fabric Data Engineering: Sign In**. Confirm the intended tenant privately
   and select the approved dev workspace. The extension's sign-in/workspace is independent
   of Azure CLI and the application's private bindings.
7. After a reviewed exact-target plan, duplicate checks and separate approval, publish only
   the reviewed notebook through the extension. Select **Microsoft Fabric Runtime** and
   verify the intended lakehouse before running. Running can write Delta tables and consume
   capacity, so publication approval does not automatically approve execution.
8. For Power BI, connect read-only to an explicitly selected synthetic model. A model is not
   selected by merely starting the server. Use the actual grouped tools, inspect their
   operation schemas, and reconcile executed DAX against the independent baseline.
   Use the sandbox profile only on a local PBIP copy; live model writes need their own
   exact-target approval. Report publication is another separate step.

If a native extension tool is unavailable in a CLI/SDK client, stop that assigned step and
use the VS Code client that exposes it. A portal run, REST request or different tool is not
evidence that the assigned extension/MCP tool executed.

## CLI alternatives and scope

```bash
source .venv/bin/activate
ffia mcp render powerbi-modeling-readonly --client copilot-cli
ffia mcp render powerbi-modeling-sandbox --client vscode
ffia mcp check
```

Rendering prints configuration; it neither merges a user's MCP configuration nor starts a
server. Merge deliberately without overwriting other servers. The readonly profile enables
inspection, not cloud-write authority. The sandbox profile adds server confirmation and
per-call approval, but neither automatically routes calls through the accelerator's approval
service. Do not use auto-approval/bypass modes.

The Fabric extension owns its HTTP MCP endpoint and can change its local port. Use its
server-definition provider rather than committing a machine-specific endpoint. Copilot CLI
and Claude can use Power BI's pinned stdio server, but notebook extension tools and remote
kernels are not automatically available in those clients. Claude execution remains unverified.

The extension can generate local `.stubs`, `.vfsmeta`, `.vfscache` and GUID-shaped workspace
folders in the repository root. They are ignored because they contain generated dependencies
or private workspace metadata. Do not commit their contents or copy them into public evidence.
The isolation rules preserve the extension's local state; they do not delete it.

## Evidence and remaining gates

- Both extension installation paths/versions were checked in the Linux VS Code host.
- Actual MCP `initialize` and `tools/list` succeeded for Power BI and the extension-managed
  notebook server. A separate Power BI probe confirmed `Mode=ReadOnly`.
- Power BI tool-group annotations still advertise write capability in read-only mode; they
  do not establish that a write operation is permitted.
- No EULA acceptance, model connection, DAX query, notebook publication, notebook run or
  report publication was executed by these discovery probes.
- After explicit operator authorization, **LOCAL / Power BI Authoring MCP / `accept_eula`**
  completed. `connection_operations` with `ListConnections` returned an empty connection
  array. A fresh server process returned the same result without another acceptance call,
  independently verifying persistence. This is callable-tool evidence, not model verification.
- **LIVE / Microsoft Fabric / extension-managed `fabric-notebook-mcp` / `list_artifacts`**
  succeeded for the privately bound dev workspace and an expected synthetic lakehouse filter.
  Independent comparison verified the exact private workspace binding, one result, and its
  expected name/type. Identifiers and raw responses remain private. No wider inventory was read.
- At the initial tooling check, chat tool search did not expose Power BI operations or native Fabric
  notebook publication tools. The actual MCP servers were invoked through an MCP client for
  the checks above, not through REST/CLI substitutions. Native publication requires the
  VS Code client to expose `fabricPublishNotebook`; server discovery cannot provide that tool.
- After the operator reported enabling tools and reconnecting the chat, discovery was retried
  and still did not expose `fabricWorkspaceInfo` or `fabricPublishNotebook` to this SDK session.
  This was the earlier client-exposure blocker, not an extension installation failure.
- On the subsequent resumed session, native `fabricWorkspaceInfo` and `fabricPublishNotebook`
  became exposed. An actual `fabricWorkspaceInfo` call initially selected a personal workspace
  that did not match the private dev binding. After the operator switched workspaces, another
  call matched the private `demo-dev` binding exactly. Native publication remains unexecuted.
- **LIVE / Microsoft Fabric / Fabric Data Engineering extension / `fabricListNotebook`**
  returned no notebook entries. A separate **LIVE / `fabric-notebook-mcp` / `list_artifacts`**
  call scoped to that same workspace and type `Notebook` confirmed an empty array and count
  zero. This is a dated duplicate check, not future write approval.
- The [Power BI folder](../../powerbi/README.md) currently contains documentation, not a PBIP
  project. No model was connected or created. A selected model and its read-only verification
  remain separate from the successful empty-connection check.

Focused regression results: 99 backend MCP/fixture/authoring tests and 28 shared guide/workshop
UI tests passed; strict Python types, Ruff, MCP profiles, source/prompt drift and harness checks
passed. The UI runner emitted its existing jsdom canvas warnings; no new dependency was added.
The privacy scan at that gate checked 775 files with zero findings. Extension activation then
generated stubs/private workspace caches that the scan flagged. After adding root-scoped ignore
rules and independently checking that public source files remain included, the final scan checked
776 files with zero findings. Generated local state was preserved, not deleted.

Full connected evidence is tracked in [authoring verification](use-case-authoring-verification.md).
See sources `powerbi-authoring-mcp`, `powerbi-authoring-mcp-repository` and
`fabric-vscode-data-engineering` in the [source registry](../research/sources.yaml).
