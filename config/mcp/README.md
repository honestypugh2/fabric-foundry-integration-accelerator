# MCP configuration profiles

[`profiles.yaml`](profiles.yaml) is the single source for MCP client configuration. MCP access is
not authorization: each profile is the narrowest server and tool set for one job.

| Profile | Label | Servers and tools | Writes |
|---|---|---|---|
| `offline` (default) | LOCAL | Microsoft Learn, `ffia-local` | No |
| `fabric-docs` | LOCAL | `@microsoft/fabric-mcp@1.4.0`, 6 docs tools, `--read-only` | No |
| `fabric-readonly` | LIVE | Fabric MCP, 16 tenant-metadata read tools, `--read-only` | No |
| `fabric-authoring-gated` | LIVE | Fabric MCP, `core_search-catalog` + `core_create-item` | Yes, opt-in, per-call approval |
| `powerbi-modeling-sandbox` | LOCAL | `@microsoft/powerbi-modeling-mcp@1.0.0`, local PBIP copies only | Yes, opt-in, per-call approval |

```bash
ffia mcp profiles
ffia mcp render fabric-readonly --client vscode        # or claude, copilot-cli; --output FILE
ffia mcp check                                          # runs in make validate and CI
```

- [`catalog/fabric-mcp-1.4.0.yaml`](catalog/fabric-mcp-1.4.0.yaml) lists every tool of the pinned
  server (48 tools; 19 write, 6 destructive), captured with the server's own `tools list`.
  Re-capture it whenever the pin changes.
- Read-only profiles never include `datafactory_execute-query` (arbitrary M queries) or
  `onelake_download-file` (copies data out), even though the server marks them read-only.
- Destructive tools are never exposed. The default profile is the committed `.mcp.json`.
- The Power BI Modeling MCP EULA is accepted by a person, never by configuration.
- Preview MCP servers (Fabric IQ ontology, Data Warehouse, hosted Power BI authoring) have no
  profile; they stay behind `preview_feature_flags`.

Evidence: starting the rendered `fabric-docs` and `fabric-readonly` profiles and calling MCP
`tools/list` returned exactly 6 and 16 tools, all `readOnlyHint: true` (LOCAL; no tenant call).
Calling the tenant tools REQUIRES TENANT VALIDATION.
