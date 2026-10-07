## Why it matters

Fabric data engineering is mostly *correct procedure*: the right item format, the right Spark or
SQL pattern, the right workspace, the right review. GitHub Copilot's role is to be an **agent
harness that turns intent into correct, reviewable Fabric artifacts and operations** — grounded
by Skills, executed through MCP, CLI and Git, constrained by permissions and policy, and
evidenced by pull requests and audit records.

Copilot does not grant authority. Entra identity, Fabric roles, policy and human approval do.

## The maturity ladder

| Level | What changes | Value | Control you need |
|---|---|---|---|
| L0 Manual | Nothing | Baseline | — |
| L1 Assisted | Copilot completes and explains code in files | Speed | Code review |
| L2 Grounded | Instructions plus documentation tools | Correctness | Pinned tool versions |
| L3 Skilled | Microsoft-authored Fabric Skills | Consistent expert procedures | Hardened MCP overlay, dev workspace |
| L4 Connected | Read-only access to real workspace context | Real context | Read-only allow-list, pinned target |
| L5 Governed change | Changes arrive as plans and pull requests | Safe velocity | Approvals, branch protection |
| L6 Parallel | Many agent sessions at once | Throughput | Sandboxes, budgets, allow-lists |

Most teams should aim for **L5 as the production default**. L6 is preview-heavy and belongs in
controlled experiments.

## What is GA and what is not (as of October 2026)

- **GA:** Copilot CLI, VS Code agent mode, Copilot cloud agent, Fabric Git integration, the
  Fabric MCP Server (local).
- **Pre-1.0 open source:** Skills for Fabric (official, MIT); its persona agents are experimental.
- **Technical preview:** the Copilot app (worktrees, Autopilot) that L6 relies on.

## Decisions for leaders

1. Which level is the target for each team, and by when.
2. Who approves changes at L5 — and which changes never go through an agent.
3. How you will **measure** the climb: the scorecard records time, steps, approvals requested,
   checks passed, evidence completeness and errors caught. Results are observations on synthetic
   work, not product benchmarks.
