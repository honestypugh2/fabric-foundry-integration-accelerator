## Why it matters

Teams ask "Copilot or Claude Code?" as if one must win. For Fabric data engineering the better
questions are: **where does governance live, how are changes reviewed, and can the same
repository assets serve both?** In this accelerator they can — the same rules, skills, MCP
configuration, prompts and labs work in either harness.

## Where each fits

| Situation | Usually a better fit | Why |
|---|---|---|
| GitHub-centric enterprise, PR-driven delivery | GitHub Copilot | Native issues → PR flow, code review, org policies and MCP allow-list in the same admin plane as repositories |
| Fabric Skills as the main knowledge source | GitHub Copilot | Skills for Fabric targets Copilot CLI first; Claude Code is also supported |
| Teams wanting fine-grained permission modes and enforced blocks | Claude Code | Named permission modes and hooks that can block actions |
| CI outside GitHub | Claude Code | Headless runs and an Agent SDK usable in any CI |
| Claude models with GitHub governance | Copilot with Claude models, or Agent HQ | Keeps one admin plane |

These are **fit observations**, not rankings. Both harnesses are generally available; the Copilot
app (parallel worktree sessions) is a **technical preview** as of October 2026.

## Risk and governance

- Both act with the identity of whoever runs them. Neither grants authority over Fabric.
- Using both means **two admin planes** — GitHub enterprise policy and Claude managed settings —
  that do not share configuration.
- Autonomous modes (Copilot app Autopilot, Claude Code bypass) belong only in sandboxes.

## How we will decide with evidence

A bake-off arrives in Phase 7: the **same five data-engineering tasks** on synthetic data in both
harnesses, scored on time, steps, approvals requested, checks passed, unsafe actions blocked and
evidence completeness. Results will be published as dated **observations about this
repository**, with model and versions recorded — not as product claims.

**Decision for leaders:** pick a default harness for your operating model, keep assets portable,
and let measured results — not marketing — drive any change.
