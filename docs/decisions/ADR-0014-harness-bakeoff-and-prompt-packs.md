# ADR-0014: Governed harnesses, reproducible prompt packs and scoped bake-off claims

- Status: Accepted
- Date: 2026-10-09

## Context

Both guides must explain Copilot, Fabric MCP/Skills and Claude Code alternatives without
confusing model choice with the assistant harness. Recorded runs exist only for Copilot CLI.

## Options

Duplicate prompts by hand; claim cross-product comparisons from model results; or generate
portable packs and preserve separate harness/model provenance.

## Decision

Generate packs from structured guide/lesson prompts and catalog-grounded read-only planning
prompts. Check drift in CI. Keep instructions, MCP profiles and permissions under existing
render/check flows. Label Claude Code **DOCUMENTED ONLY** until actual runs are approved/recorded.

## Rationale

One source prevents presentation/prompt drift. Same task wording, revision and permissions make
recorded observations reproducible without implying that one model result measures a product.

## Trade-offs

Single-run timing is illustrative, not statistically meaningful. Catalog planning prompts are
not implemented live integrations. Other Copilot entry points remain distinct from CLI runs.

## Security impact

Prompt text never grants approval. Harness policy is defense in depth; no bypass mode.
Live mutations require the governed plan/validation/approval flow.

## Operations impact

Use `ffia prompts render|check`, `ffia bakeoff check`, `ffia harness check`.
Recorded runs remain immutable evidence; new recordings need new provenance.

## Offline impact

All packs and replay viewers work without cloud access.

## Education impact

Both guides expose prompts, skills, checkpoints, authority and labeled fallback.
Teach what Copilot does, what MCP exposes and what policy/identity authorize.

## Revisit trigger

Approved access to Claude Code, additional repeated trials, a new harness or tool-permission model.

## Authoritative references

Registry entries `copilot-cli-ga`, `copilot-instructions-support`, `claude-code-memory`,
`claude-code-skills`, `mcp-specification`; ADR-0007 and ADR-0010.
