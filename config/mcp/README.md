# MCP configuration profiles

[`profiles.yaml`](profiles.yaml) is the single source for MCP client configuration. MCP access is
not authorization: each profile is the narrowest server and tool set for one job.

| Profile | Label | Servers and tools | Writes |
|---|---|---|---|
| `fabric-first` (default) | LIVE reads or explicit LOCAL fallback | Microsoft Learn, narrow Fabric metadata tools, `ffia-local` | No |
| `offline` | LOCAL | Microsoft Learn, `ffia-local` | No |
| `fabric-docs` | LOCAL | `@microsoft/fabric-mcp@1.4.0`, 6 docs tools, `--read-only` | No |
| `fabric-readonly` | LIVE | Fabric MCP, 16 tenant-metadata read tools, `--read-only` | No |
| `fabric-authoring-gated` | LIVE | Fabric MCP, `core_search-catalog` + `core_create-item` | Yes, opt-in, per-call approval |
| `powerbi-modeling-readonly` | LOCAL server; LIVE only when a live model is actually inspected | `@microsoft/powerbi-modeling-mcp@1.0.0`, `--read-only` | No |
| `powerbi-modeling-sandbox` | LOCAL | Same pinned package, local PBIP copies only, `--require-confirmation` | Yes, opt-in, per-call approval |
| `hc01-lab` | LIVE | Fabric metadata plus lakehouse creation, directory creation and upload; `ffia-local` rehearsal fallback | Yes, opt-in, per-call approval |

```bash
ffia mcp profiles
ffia mcp render fabric-readonly --client vscode        # or claude, copilot-cli; --output FILE
ffia mcp check                                          # runs in make validate and CI
```

- [`catalog/fabric-mcp-1.4.0.yaml`](catalog/fabric-mcp-1.4.0.yaml) lists every tool of the pinned
  server (48 tools; 22 write, 5 destructive), captured with the server's own `tools list`.
  Re-capture it whenever the pin changes.
- Read-only profiles never include `datafactory_execute-query` (arbitrary M queries) or
  `onelake_download-file` (copies data out), even though the server marks them read-only.
- Destructive tools are excluded unless an opt-in profile documents its explicit exception and
  guard. HC-01 permits upload only after the empty-folder check, with overwrite disabled.
  The default profile is the committed `.mcp.json`.
- The Power BI Modeling MCP EULA is accepted by a person, never by configuration.
- Preview MCP servers (Fabric IQ ontology, Data Warehouse, hosted Power BI authoring) have no
  profile; they stay behind `preview_feature_flags`.

The Power BI extension registers its own server separately from rendered profiles. Its upstream
default arguments accept the EULA and enable writes. The repository's VS Code settings override
them with `--start --read-only --require-confirmation`; reload/restart the server to apply them.
This does not revoke a license acceptance already made. Grouped Power BI tools retain
write-capable annotations in read-only mode; server mode, selected target and operation matter.
See [notebook and Power BI tooling](../../docs/operations/notebook-powerbi-tooling.md) for client
activation, the separate Fabric Notebook MCP server and the publication/kernel boundary.

Evidence: starting the rendered `fabric-docs` and `fabric-readonly` profiles and calling MCP
`tools/list` returned exactly 6 and 16 tools, all `readOnlyHint: true` (LOCAL; no tenant call).
In the presenter's demo tenant (VERIFIED LIVE, 2026-10-07):

- `core_search-catalog` found the dev workspace;
- `onelake_list-workspaces` returned an empty list for a new, empty workspace;
- calling the non-allow-listed `core_create-item` was refused by the server.
