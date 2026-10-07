# ADR-0007: MCP access is not authority; local educational MCP server

- Status: Accepted
- Date: 2026-10-07

## Context

Learners need to see a real MCP protocol exchange offline. MCP servers also tempt teams to
expose broad tools, such as shell, SQL or REST proxies, and to treat "the tool exists" as
permission.

## Options

1. Teach with screenshots of the Fabric MCP server only.
2. A local MCP server that mirrors broad cloud tools.
3. A small, allow-listed local MCP server (`ffia-local`, FastMCP 4.0.11) with read-only and
   proposal-only tools.

## Decision

Use option 3.

- The tools in `config/policies/tools.yaml` are the only tools registered. A manifest entry
  without an implementation stops the server at startup.
- No tool can approve or execute a change, and no shell, SQL, filesystem, URL-fetch or
  REST-proxy tool exists.
- Each call is rate limited and audited, and returns an execution envelope labeled `LOCAL` or
  `SIMULATED`.
- `.mcp.json` registers it as `ffia-local` (stdio) next to Microsoft Learn. VS Code, Copilot CLI
  and Claude Code share that file.

## Rationale

- Learners see the real protocol (offline demo act 3) without a tenant.
- The narrow tool surface shows the principle that **MCP standardizes access; Entra identity and
  policy determine authority.**

## Trade-offs

- `ffia-local` is not the Fabric MCP server, and the docs and envelopes must keep saying so.
  The Fabric MCP servers arrive in Phase 5 as separate, pinned profiles.

## Security impact

- No ambient authority and no arbitrary execution.
- Logs go to stderr, so stdio stays protocol-only.
- Arguments are validated against the built catalog.

## Operations impact

- Start it with `make run-mcp` or `ffia serve mcp`.
- Use `uv run --frozen` so the locked environment is used.

## Offline impact

- Fully offline.

## Education impact

- L100 compares MCP with an API. L200 inspects a tool call. L300 removes a tool from the
  manifest and observes the result. L400 covers MCP authorization and gateways.

## Revisit trigger

- MCP SDK v2 changes that affect tool annotations or transports.
- Adding the Fabric MCP profiles in Phase 5.

## Authoritative references

- `mcp-specification`, `fabric-mcp-servers-list`, `fabric-mcp-local` and `vscode-mcp-servers` in
  `docs/research/sources.yaml`
