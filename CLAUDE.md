# CLAUDE.md

Claude Code reads `AGENTS.md` only when no `CLAUDE.md` exists, so this file imports it
explicitly. `AGENTS.md` is the single source of truth for every agent in this repository.

@AGENTS.md

## Claude Code specifics

- Project skills live in `.claude/skills/<name>/SKILL.md`. This is the one skill folder read by
  both Claude Code and GitHub Copilot.
- Project MCP servers are defined in the root `.mcp.json`. It is shared with VS Code and
  Copilot CLI. Approve project servers only after reviewing them.
- Use plan mode for anything that would change files outside your current task, and for every
  proposed cloud operation.
- Never use `bypassPermissions` in this repository; `.claude/settings.json` disables it
  (`disableBypassPermissionsMode`) and runs `ffia harness guard` before every Bash call. Live
  cloud writes always require explicit human approval (see AGENTS.md §6). The settings are
  rendered from `config/harness/policy.yaml` (`ffia harness render repo --client claude`).
- Put personal, uncommitted notes in `CLAUDE.local.md` (git-ignored). A `CLAUDE.local.md` also
  stops Claude from reading `AGENTS.md` directly; this file's import keeps it loaded.
