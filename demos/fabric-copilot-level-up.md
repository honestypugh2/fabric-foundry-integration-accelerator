# Run of show: Leveling up Fabric data engineering with GitHub Copilot

**Audience:** data-engineering and platform leads, plus their architects. **Length:** 60 minutes
(a 40-minute cut is marked ✂). **Guide:** [HC-01](../guides/hc-01-fabric-mcp-powerbi-medallion-lab/)
(healthcare, synthetic data). **Companion files:**

- [talk track and Q&A](fabric-copilot-level-up-qa.md);
- [prompt pack](../prompts/github-copilot/fabric-level-up.md).

The demo answers four questions:

1. **Fabric MCP:** what is it, and what can an agent safely do with it?
2. **Fabric Skills:** what are they, how do they differ from MCP, and how are they hardened?
3. **GitHub Copilot:** what is it actually doing for a data engineer, and how does a team level up?
4. **Power BI:** where do semantic models and reports fit?

The Claude Code comparison is scheduled as a separate session. Its lesson is ready if someone
asks (see the Q&A).

## Honesty rules for the presenter

Every result on screen carries a label. Say the label out loud.

| Label | Means | In this demo |
|---|---|---|
| `LOCAL` / `SIMULATED` | Ran on this laptop over synthetic data; no cloud call | Offline app, `ffia-local` MCP, change rehearsal |
| `LIVE` | A real call to the demo tenant, read-only | Fabric readiness, live workspace reads, Fabric MCP read profile |
| `PREVIEW` | Depends on a preview API or feature | Lakehouse table listing; Fabric IQ ontology (not shown) |
| REQUIRES TENANT VALIDATION | Built and tested, not yet run in a tenant | Notebooks on Fabric Spark, live writes, DAX against a live model |

Before any cloud call, name the **provider, server and tool**. Never show IDs or tokens.

## T-30 minutes: setup checklist

```bash
az login --tenant <DEMO_TENANT_ID>        # the demo tenant's admin account
ffia fabric readiness                      # expect "Fabric ready for live labs: YES" (GET only)
# If the F capacity is paused, resume it (docs/operations/fabric-tenant-readiness.md)
make demo-prep                             # clears the dev-server cache and runs every offline check
ffia skills install && ffia skills status  # four pinned skills, v0.3.18
make run                                   # API :8000 + app :5173
```

- In VS Code, open this repository. Confirm in Chat that agent mode is on and that `ffia-local`
  and `microsoft-learn` appear in the tool picker. Confirm the four skills plus
  `ffia-governed-fabric-change` appear in the skills list (Chat → Configure Skills).
- For the live Fabric MCP segment, use a scratch lab folder, not the repository:

  ```bash
  mkdir -p ~/hc-01-lab/.vscode
  ffia mcp render fabric-readonly --client vscode --output ~/hc-01-lab/.vscode/mcp.json
  ```

  Open `~/hc-01-lab` in a second VS Code window and start the server once (MCP: List Servers).
- Browser tabs, in order:
  1. `/architecture/reference`
  2. `/patterns`
  3. `/architecture/mcp-topology`
  4. `/learn/fabric-mcp-landscape`
  5. `/learn/fabric-skills`
  6. `/architecture/agentic-de`
  7. `/labs/lab-copilot-maturity-ladder`
  8. `/guides/hc-01-fabric-mcp-powerbi-medallion-lab`
  9. `/learn/power-bi-agentic-tooling`
  10. `/demo`
- Set the learning level selector (top of the app) to **Executive** for the opening, **L200** for
  the technical segments, and **L300/L400** when an architect asks for depth.

**Fallback:** if the tenant, network or sign-in fails, stay offline. Every segment below has an
offline path, and the labels already tell the truth.

---

## 0. Opening (3 min)

**Screen:** `/architecture/reference`, level **Executive**, "Full picture".

> "Today is about one question: how do we make Fabric data engineering faster *and* safer with
> GitHub Copilot? Three ideas to hold onto:
>
> - Fabric holds the governed business context.
> - Agents, Copilot included, turn that context into work.
> - MCP gives an agent hands, but it doesn't give it authority. Your Entra identity, your policies
>   and a human approval give authority.
>
> Everything you'll see is labeled. LOCAL means it ran on this laptop on synthetic data. LIVE means
> it read our demo tenant. I'll say which is which."

## 1. Reference architecture and patterns (7 min) ✂ to 4 min

**Screen:** `/architecture/reference` → click **Trace a request**. Then `/patterns`.

> "This is the reference architecture, drawn the way the Azure Architecture Center draws them. The
> same picture is generated as draw.io files in `docs/architecture/diagrams`. Watch one request: the
> agent asks Fabric for context, reasons, proposes an action, a person approves, and a narrowly
> scoped writer acts. Then we verify and audit."

Patterns to name (click each):

| Pattern | One line |
|---|---|
| **P09** Governed MCP | Pinned servers, allow-listed tools, approval for writes |
| **P19** Copilot CLI + Fabric Skills + MCP | The developer-harness pattern for today |
| **P10** Medallion + AI | Bronze preserves, Silver conforms, Gold serves; AI works on Gold |
| **P12** Direct Lake + semantic model + AI | Business definitions live in the model, not the prompt |
| **P20** Repo-first | Git is the source of truth for Fabric items; agents work through PRs |
| **P08** Human-in-the-loop | Models propose, humans approve |

> "Each pattern has a status. GA, PREVIEW or MIXED is shown on the card. None of today's default
> path depends on a preview feature."

## 2. Fabric MCP (10 min) ✂ to 6 min

**Screen:** `/architecture/mcp-topology` → **Trace a request** ("Pick the narrowest server").

> "'Fabric MCP' isn't one thing. It's a family:
>
> - the local Fabric MCP server, which we use today;
> - Fabric IQ MCP, which is read-only;
> - the Data Warehouse MCP server, in preview;
> - Power BI Modeling MCP.
>
> The rule is the narrowest server for the job: documentation tools for *how*, read-only tools for
> *what is*, and an approved change flow for *change it*."

**Screen:** `/learn/fabric-mcp-landscape` (L200), then the terminal:

```bash
ffia mcp profiles
```

> "Here's what we found when we pinned version 1.4.0 of the local server. It has **48 tools; 22
> can write and 5 are destructive**. So you don't connect it and hope. These are profiles: a
> docs-only profile, a read-only profile with 16 tools, and an approval-gated lab profile. CI fails
> if anyone adds a write tool to a read-only profile or unpins a version."

**LIVE moment 1: tenant readiness.** Provider: Fabric REST API. Tool: `ffia fabric readiness`,
GET requests only.

```bash
ffia fabric readiness
```

> "This is our demo tenant: an F8 capacity, a dev workspace bound by alias, and the tenant
> settings checked. It's read-only. It also caught that a Premium Per User capacity can't host
> lakehouses."

**LIVE moment 2: Fabric MCP read.** Server: Fabric MCP 1.4.0, profile `fabric-readonly`. Tool:
`core_search-catalog`. Run it in the second VS Code window (agent mode) with prompt **P-MCP-1**
from the prompt pack.

> "Copilot called the real Fabric MCP tool and found our workspace. The result is labeled LIVE,
> and it ran under my identity. If I can't see a workspace, neither can the agent."

**Governance moment.** Use prompt **P-MCP-2**: ask the agent to create a lakehouse while the
read-only profile is loaded.

> "The agent can't, because the server was started with an allow-list and `--read-only`. The write
> tool doesn't exist for it. We verified that the server itself refuses the call."

**Offline equivalent (always works).** In the repository window, use prompt **P-MCP-3** (`ffia-local`
→ `generate_fabric_change_plan`).

> "This plan came back **BLOCKED**: live mutation is disabled, approval is required, and MCP
> cannot approve it. Models propose; people approve."

## 3. Fabric Skills (8 min) ✂ to 5 min

**Screen:** `/learn/fabric-skills` (L200), then the terminal.

> "MCP gives an agent hands. Skills give it know-how: Microsoft-authored procedures for things
> like medallion design, Spark notebooks, semantic models and reports. They're open source, in
> `microsoft/skills-for-fabric`.
>
> Here's the part most teams miss: **skills don't go through MCP.** They tell the agent to call
> Fabric's REST API directly with `az rest`, and that includes POST and DELETE. Your MCP
> allow-list doesn't cover them."

```bash
ffia skills status
cat config/skills/fabric-skills.lock.yaml
```

> "So we harden skills differently:
>
> - **Pinned.** Release v0.3.18, with its archive hash verified.
> - **Curated.** Four skills for this lab instead of all 25.
> - **Bundle MCP config dropped.** The bundle's MCP file grants every tool and runs `@latest`, so we
>   don't install it.
> - **Approval required.** Both VS Code and Claude Code are configured to ask before any `az rest`
>   command."

```bash
grep -A4 autoApprove .vscode/settings.json
```

**Skill moment.** Use prompt **P-SKILL-1** in the repository window: plan a medallion design with
`e2e-medallion-architecture`, with no Fabric calls.

> "Watch the agent pick the skill and follow its procedure. Then compare its plan with our
> reference build: same layers, same row counts. Our own skill, `ffia-governed-fabric-change`,
> decides whether a change may happen at all, and what evidence it needs."

## 4. GitHub Copilot: what it's doing and how to level up (15 min) ✂ to 10 min

This is the centerpiece. **Screen:** `/architecture/agentic-de`, level **L200**, "Full picture".

### What GitHub Copilot is

> "GitHub Copilot is one agent runtime that shows up in several places. They all read the same
> repository files:
>
> - in VS Code as agent mode, which you're watching now;
> - in the terminal as Copilot CLI, which is GA;
> - on GitHub as the cloud agent, which takes an issue and opens a pull request;
> - in pull-request code review;
> - inside your own apps through the Copilot SDK."

**Show** `AGENTS.md` and `.github/copilot-instructions.md`:

> "This is how we teach Copilot *our* rules: synthetic data only, read-only by default, label
> every result, never write without approval. Copilot reads these files on every request."

### What it's doing for data engineering, concretely

| Job | What Copilot does | Where you saw it |
|---|---|---|
| Understand | Explains PySpark, Spark SQL and DAX; profiles source files; finds data quirks | Guide step 06 |
| Author | Drafts notebooks, transforms, measures and tests from a reviewed design | Steps 07–10; compare with `fabric/workspace/*.Notebook` |
| Ground | Looks up real APIs and item formats through docs tools, instead of guessing | Fabric MCP `fabric-docs` profile, Microsoft Learn MCP |
| Follow procedure | Uses Fabric Skills for medallion, Spark and semantic-model work | Segment 3 |
| See reality | Reads workspace metadata through read-only MCP under your identity | Segment 2, LIVE |
| Change safely | Proposes plans and pull requests; never approves its own work | `generate_fabric_change_plan` → BLOCKED |
| Prove it | Checks counts, keys and reconciliation against a baseline | `ffia-local` `evaluate_against_baseline` |

### How to level up: the ladder

Click **L1 → L6** on the diagram, one at a time. Each level fills five columns: knowledge,
harness, execution, authority and evidence.

| Level | What you add | What it unlocks | Control that keeps it safe |
|---|---|---|---|
| **L1 Assisted** | Copilot in the editor; Fabric items synced to Git as files | Explain and complete PySpark, SQL, DAX | Code review of the diff |
| **L2 Grounded** | `AGENTS.md`, instructions, docs MCP (Microsoft Learn, Fabric MCP docs tools) | Correct APIs and item formats instead of plausible guesses | Pinned docs sources |
| **L3 Skilled** | Fabric Skills (pinned, curated) and your own repository skills | Microsoft-authored procedures, your conventions | Approval for `az rest`; no wildcard MCP |
| **L4 Connected** | Read-only Fabric MCP against a dev workspace | The agent checks its assumptions against reality | `--read-only`, allow-list, bound workspace |
| **L5 Governed change** | Plans, approvals, scoped writer, pull requests, evidence | Agents contribute changes that ship | Separation of duties, audit, verification |
| **L6 Parallel** | Many sessions or cloud agents on scoped tasks | Throughput on migrations and backlogs | Budgets, sandboxes, PR review; preview-heavy |

> "Most teams jump straight from L1 to 'connect it to production'. Don't. Climb one level at a
> time, and measure each climb. The lab gives you a scorecard. **Skills make the agent competent,
> MCP makes it capable, the harness makes it productive, identity and approval make it safe, and
> evidence makes it trustworthy.**"

**Screen:** `/labs/lab-copilot-maturity-ladder`. Show the stage list (LEARN → … → PRODUCTION NOTES)
and the scorecard.

**Copilot moments.** Run these prompts from the pack in the repository window:

1. **P-COP-1 (L1–L2):** explain the Silver encounters transform and its data-quality flags.
2. **P-COP-2 (L4, LOCAL):** "inspect the medallion architecture" through `ffia-local`, which returns
   24 tables with counts.
3. **P-COP-3 (L5):** propose the lakehouse change; it comes back BLOCKED pending approval.

> "Same agent, three levels. What changed wasn't the model. It was what we gave it: knowledge,
> tools and rules."

## 5. Power BI (5 min) ✂ to 3 min

**Screen:** `/learn/power-bi-agentic-tooling` (L200), then `/data`.

> "Business meaning belongs in the semantic model, not in prompts. In this lab:
>
> - Copilot connects to the model through **Power BI Modeling MCP** (local server, GA).
> - It uses the `semantic-model-authoring` skill for relationships and measures, and the
>   `powerbi-report-cli` skill for the report.
> - Every measure is reconciled with DAX against a governed baseline."

Use prompt **P-PBI-1** (`ffia-local` → `evaluate_measures` / `evaluate_against_baseline`).

> "These are the 23 governed measures, all labeled synthetic. They're evaluated locally and match
> the baseline. Against a live model, the same comparison runs through the Execute Queries API; it
> requires tenant validation, and it's next on our list. Modeling edits happen on a local PBIP
> copy and reach the workspace only through review."

## 6. Putting it together: the HC-01 guide (5 min) ✂ to 3 min

**Screen:** `/guides/hc-01-fabric-mcp-powerbi-medallion-lab`. Open step 02, then step 05.

> "This is the end-to-end lab: 16 steps from tools to a published report. Each step has:
>
> - a Copilot prompt and a Claude Code prompt;
> - the exact tool path;
> - a checkpoint;
> - the evidence required, and what does *not* count as evidence;
> - an offline equivalent.
>
> Step 05 uploads data. That tool is marked destructive because it can overwrite files, so the lab
> profile allows it only with per-call approval, after checking that the folder is empty, and with
> overwrite turned off."

Show the reference notebooks:

```bash
ls fabric/workspace/
```

> "These three notebooks are generated from the same SQL as our local build. They passed all 85
> checks on Spark 3.5, the version Fabric runs, locally. Running them in Fabric is the next
> tenant validation."

## 7. Options and next steps (5 min)

**Screen:** `/architecture/live-vs-offline`, then `/demo` (optionally run the offline demo).

| Decision | Options | Our default and why |
|---|---|---|
| Harness | VS Code agent mode · Copilot CLI · cloud agent · Claude Code | VS Code or CLI for interactive work under your identity; cloud agent only with read-only tools and PR review |
| MCP topology | Direct to servers · through an APIM gateway (P15) | Direct with pinned profiles; add a gateway when many teams share servers |
| Skills | Upstream plugin install · pinned curated vendor install | Pinned and curated, with approval on `az rest` |
| How changes land | MCP write tool with approval · scoped writer · Git PR + deployment pipeline | PR and pipeline for production; the approval-gated MCP tool for dev labs only |
| Where it runs | LIVE · HYBRID (reads fall back, labeled) · OFFLINE | HYBRID for demos; writes never fall back |

> "Proposed next steps:
>
> 1. Pick one team and one pipeline and climb L1 to L4 in a dev workspace.
> 2. Use the scorecard to measure.
> 3. Then pilot L5 with pull requests and a deployment pipeline."

Then open the floor. The Q&A is in [fabric-copilot-level-up-qa.md](fabric-copilot-level-up-qa.md).

## Reset after the demo

- Close the scratch lab folder. Nothing was written to the tenant.
- Pause the F capacity if it isn't needed (see the runbook).
