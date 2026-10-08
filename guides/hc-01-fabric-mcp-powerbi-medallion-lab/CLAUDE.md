# CLAUDE.md — Guide HC-01

Claude Code reads this file when the lab folder (or this guide folder) is the working directory.

@AGENTS.md

- MCP servers come from this folder's `.mcp.json` (profile `hc01-lab`): the real Fabric MCP
  server, plus `ffia-local` as the labeled fallback. Approve each write call.
- Use plan mode for every write step; never use `bypassPermissions`.
