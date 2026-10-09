# Prompt packs

Plain Markdown prompt packs. VS Code `.prompt.md` files are deprecated for Agent Host sessions.

| Pack | Purpose |
|---|---|
| [`github-copilot/fabric-level-up.md`](github-copilot/fabric-level-up.md) | Fabric MCP, Fabric Skills, Copilot level-up (L1–L5) and Power BI prompts used in the demo run of show |

Pattern and guide prompts are generated from existing structured education and guide YAML.
Anchor patterns reuse authored lesson prompts; other patterns get read-only planning prompts
grounded in their catalog entries. Each pack links to its source:

```bash
ffia prompts render
ffia prompts check
```

Both [Copilot](github-copilot/patterns.md) and
[Claude Code](claude-code/patterns.md) packs cover every catalog pattern. Each harness folder also
contains a pack for each guide, with its skills, approval requirement, checkpoint and fallback.
Edit the source YAML, not these generated packs.

**Claude Code is DOCUMENTED ONLY.** The ten recorded bake-off runs compare Claude and GPT models
inside Copilot CLI; they do not compare Copilot with Claude Code. No Claude Code authentication,
execution or results are claimed. The same task wording remains available for a future recording.
