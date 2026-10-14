# Prompt packs

Plain Markdown prompt packs. VS Code `.prompt.md` files are deprecated for Agent Host sessions.

| Pack | Purpose |
|---|---|
| [`github-copilot/fabric-level-up.md`](github-copilot/fabric-level-up.md) | Fabric MCP, Fabric Skills, GitHub Copilot level-up (L1 to L5) and Power BI presenter prompts |

The packs are generated from structured lessons and guide YAML.
Some patterns reuse lesson prompts. Others use read-only planning prompts based on their
catalog entries. Each pack links to its source:

```bash
ffia prompts render
ffia prompts check
```

Both [GitHub Copilot](github-copilot/patterns.md) and
[Claude Code](claude-code/patterns.md) packs cover every catalog pattern. Each harness folder also
contains a pack for each guide, with its skills, approval requirement, checkpoint and fallback.
Edit the source YAML, not these generated packs.

**Claude Code is DOCUMENTED ONLY.** The ten recorded bake-off runs compare Claude and GPT models
inside GitHub Copilot CLI; they do not compare GitHub Copilot with Claude Code. No Claude Code authentication,
execution or results are claimed. The same task wording remains available for a future recording.
