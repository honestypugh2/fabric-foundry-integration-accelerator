## Why it matters

The Model Context Protocol (MCP) lets one capability — "list the tables in a lakehouse",
"evaluate a measure", "propose a change" — be used by many agents and developer tools without
writing a new integration each time. That reuse is the value. The risk is that teams expose
**broad** tools (run any SQL, call any URL, run a shell command) and treat "the agent can reach
the tool" as "the agent is allowed to do it".

Pattern P09 keeps the reuse and removes the ambiguity:

| Control | What it means for the business |
|---|---|
| Allow-list | Only named, reviewed tools exist |
| Read-only by default | Changes go through the approval flow (P08), not through a tool |
| Owner, version, classification | Someone is accountable for each tool and the data it touches |
| Rate limits and timeouts | A runaway agent cannot overload a system |
| Audit | Every call can be traced to a caller and a correlation ID |
| Revocation | A tool can be switched off with a configuration change |
| Gateway (pattern P15) | One place for authentication, quotas and telemetry when many teams share tools |

**The principle leaders should repeat:** *MCP standardizes capability access; it does not grant
authority.* Authority comes from Entra identity, the server's own permission checks and policy.

## Decisions for leaders

- Which MCP servers are approved for which teams, and who owns each one.
- Whether write-capable or authoring servers are allowed at all, and only in development
  workspaces with approvals switched on.
- Whether tools shared across many applications go through a central gateway.

## Status (as of October 2026)

MCP itself, the local Fabric MCP server, Fabric IQ MCP and APIM MCP support are **GA**. Some
Fabric MCP servers (for example the Data Warehouse SQL server and hosted Power BI authoring)
are **PREVIEW** and belong in separate, opt-in profiles. In this accelerator the governed local
server runs fully offline and is labeled **LOCAL**.
