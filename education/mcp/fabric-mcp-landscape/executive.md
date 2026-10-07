## Not one server - a family

When someone says "connect the agent to Fabric MCP", the right response is "which one?".
Microsoft publishes several Fabric-related MCP servers. They differ in where they run, what
they can change and how mature they are.

| Server | What it is for | Can it change things? | Status (October 2026) |
|---|---|---|---|
| Fabric MCP Server (local) | API docs, item schemas, best practices; OneLake and item operations | Docs: no. OneLake/items: yes | GA |
| Fabric IQ MCP | Ask questions of semantic models (DAX) | No, read-only | GA |
| Power BI Authoring MCP | Edit semantic models | Yes | Local GA, hosted PREVIEW |
| Data Warehouse MCP | Run T-SQL against a warehouse or SQL endpoint | Yes, any SQL your rights allow | PREVIEW |
| Ontology MCP | Query a business ontology | No | PREVIEW |
| Data agent MCP | Ask a published Fabric data agent | No | Needs validation |
| Real-Time Intelligence MCP | Eventhouse, KQL, Activator | Yes | Needs validation |

## The rule we teach

- **"How do I…?"** → local documentation tools. Safe, no tenant needed.
- **"What is…?"** → read-only remote tools under your own identity.
- **"Change it."** → Git and pull requests, or the approved change flow. Not a chat window.

## Risk in one line

The servers inherit the caller's permissions. Connecting a write-capable or arbitrary-SQL
server under an administrator identity gives an AI assistant administrator reach. The
accelerator's default is read-only, with writes in a separate, opt-in, approval-gated profile.

## What leaders should decide

- Which servers are allowed in which environments (dev, test, production).
- Which identities may use write-capable servers, and who approves their use.
- How preview servers are evaluated before anyone depends on them.

## A note on this accelerator

The accelerator ships its own small MCP server, `ffia-local`, for offline teaching. It is
**not** a Fabric MCP server and never touches Fabric. Fabric MCP profiles arrive in Phase 5.
