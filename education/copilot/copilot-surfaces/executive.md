## Why it matters

Data engineers do not use one tool all day. They explore in a terminal, write transforms in an
editor, hand routine tasks to a backlog and promote changes through pull requests. GitHub Copilot
now meets them in each of those places with **one agent runtime** — so the same rules, skills and
tools apply everywhere.

## The surfaces

| Surface | Where it runs | Best for | Status (October 2026) |
|---|---|---|---|
| VS Code agent mode | Developer's editor | Writing and reviewing notebooks, SQL, TMDL | GA |
| Copilot CLI | Developer's terminal | Exploration, triage, scripted checks | GA since 2026-02-25 |
| Copilot app | Desktop, parallel worktrees | Parallel migrations and refactors | Technical preview |
| Copilot cloud agent | GitHub Actions sandbox | Issue → pull request for well-scoped tasks | GA |
| Copilot SDK | Your own application | Embedded data-engineering assistants | GA |

## Risk and governance

- Local surfaces act as **the developer**, with per-tool approval prompts.
- The cloud agent works **without per-call approval**; the pull request is its approval point, so
  it should only have read-only or offline tools.
- The Copilot app's Autopilot mode removes the human gate; keep it in sandboxed experiments.
- An organization MCP allow-list limits which tool servers any surface can use.

None of these surfaces grants authority over Fabric. Identity, workspace roles, policy and human
approval do.

## One rulebook

`AGENTS.md`, instruction files, skills and `.mcp.json` steer every surface — and Claude Code reads
the same rules through `CLAUDE.md`. Writing rules once lowers the cost of governance and makes a
fair comparison between tools possible.

## Decisions for leaders

1. Which surfaces are approved for which teams and data.
2. Whether the cloud agent may work on data-engineering repositories, and with which tools.
3. When preview surfaces (the Copilot app, sandboxes) may move from experiment to standard
   practice.
