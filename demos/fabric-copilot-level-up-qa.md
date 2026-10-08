# Talk track companion: anticipated questions and answers

These go with [the run of show](fabric-copilot-level-up.md). Answers are short enough to say out
loud. "Show" points to something on screen. Labels follow the repository's evidence rules:

- **VERIFIED LIVE:** observed in the demo tenant;
- **LOCAL:** observed on the laptop;
- **DOCUMENTED:** Microsoft or GitHub documentation; see `docs/research/sources.yaml`;
- **CHECK:** confirm in the customer's own tenant or organization.

## Strategy and value

**Q: In one sentence, what does GitHub Copilot add to Fabric data engineering?**
It takes on the code and procedure work: explaining, drafting, grounding and validating
notebooks, SQL, DAX and item definitions. Governed access to Fabric through MCP and skills means it
works against real context, and your identity and approvals still decide what changes.

**Q: How much faster will our team be?**
We don't quote a number. It depends on the team, the codebase and the maturity level. Instead,
measure it: pick one pipeline, time a reference task at L1, then again at L3 and L4 using the lab's
scorecard (`/labs/lab-copilot-maturity-ladder`). Track cycle time, rework and defects caught by
validation.

**Q: Where should we start?**
Climb L1 → L4 in a dev workspace with one team:

- **L1:** Copilot in the editor, with Fabric items in Git.
- **L2:** repository instructions plus documentation MCP.
- **L3:** pinned skills.
- **L4:** read-only Fabric MCP.

Pilot L5 (governed change through pull requests and pipelines) only after that. Show:
`/architecture/agentic-de`.

**Q: Is this a product?**
No. It's a reference implementation and teaching platform. It shows patterns built on GA
products: Fabric, GitHub Copilot, the Fabric MCP server and Power BI Modeling MCP. Preview pieces
are flagged and are off by default.

## Fabric MCP

**Q: What is Fabric MCP, and is it GA?**
It's a family of MCP servers:

- **Local Fabric MCP server** (GA, version 1.4.0 pinned here): docs, OneLake, item and Data
  Factory tools.
- **Fabric IQ MCP** (GA): read-only.
- **Data Warehouse MCP** (preview).
- **Power BI Modeling MCP** (GA as a local server; the hosted version is preview).

Pick the narrowest one for the job. DOCUMENTED. Show: `/learn/fabric-mcp-landscape`.

**Q: Does the agent get access to all our data?**
No. The servers act with the signed-in user's identity and Fabric permissions. If you can't see a
workspace, the agent can't either. We saw this live: the agent found only the workspace our
account can see. VERIFIED LIVE.

**Q: Can the agent delete things?**
The local server has destructive tools: 5 of its 48, plus 22 that can write. That's why we never
expose the full server:

- Read-only profiles start it with `--read-only` and an explicit tool allow-list.
- Write tools appear only in opt-in profiles with per-call approval.
- `ffia mcp check` fails CI if anyone breaks those rules.

The server itself refused a write tool that wasn't allow-listed. VERIFIED LIVE.

**Q: Isn't the approval prompt just a click-through?**
Approval is one control out of several:

- the allow-list removes tools entirely;
- the profile is pinned to a dev workspace;
- duplicate and empty-folder checks run before writes;
- for production, changes land through pull requests and deployment pipelines, not chat.

The approval itself must come from a different person than the requester. MCP can't approve
anything. LOCAL: the plan comes back BLOCKED.

**Q: Why not just use the Fabric REST API?**
You can, and our control plane does for its live reads. MCP standardizes how *agents* discover
and call capabilities across tools. Either way, authority comes from Entra identity and policy,
not the protocol.

**Q: We saw an empty workspace list. Is something broken?**
In our demo tenant, Fabric MCP 1.4.0's `onelake_list-workspaces` returned an empty list, while
catalog search and workspace-scoped calls worked. The guide uses `core_search-catalog` for this
reason. VERIFIED LIVE (observed); the cause is unverified.

**Q: How do we govern MCP across many teams?**
Start direct, with pinned profiles. When several teams share servers, add a gateway such as Azure
API Management for central sign-in, quotas and logging (pattern P15). The caller's Fabric
permissions still decide access.

## Fabric Skills

**Q: What's the difference between a skill and MCP?**
MCP gives the agent tools, its hands. A skill gives it a procedure, its know-how: Markdown
instructions such as "how to build a medallion architecture in Fabric". Microsoft publishes them
open source as `microsoft/skills-for-fabric` (MIT, 25 skills).

**Q: Are skills safe?**
Treat them like code you install:

- **They run with your permissions.** Skills tell the agent to call Fabric's REST API directly with
  `az rest`, which bypasses MCP allow-lists and can include POST and DELETE.
- **We pin a release** (v0.3.18) and verify its archive hash.
- **We install a curated four**, not all 25.
- **We drop the bundled MCP configuration**, which grants every tool and runs `@latest`.
- **We require approval** for every `az rest` command in VS Code and Claude Code.

Also note that skill-driven calls add an `x-ms-fabric-skill` telemetry header, as the skills
instruct.

**Q: Are skills supported like a product?**
They're Microsoft-authored open source with frequent releases (pre-1.0 versioning). Review changes
before you move the pin. DOCUMENTED.

**Q: Can we write our own skills?**
Yes. This repository ships one, `ffia-governed-fabric-change`, which wraps every Fabric change in
PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT. Your conventions belong in your own skills
and in `AGENTS.md`.

## GitHub Copilot

**Q: What exactly is GitHub Copilot doing in the demo?**
In VS Code agent mode it reads the repository instructions (`AGENTS.md`,
`.github/copilot-instructions.md`), plans, edits files, runs commands, and calls MCP tools. You
approve tool calls and commands. In the demo it explains a transform, reads the medallion layers
through MCP, uses a skill to plan, and proposes a governed change that comes back blocked pending
approval.

**Q: Which Copilot surfaces matter for data engineers?**

- VS Code agent mode and Copilot CLI (GA) for interactive work under your identity.
- The cloud agent for well-scoped issues that end in a pull request.
- Code review on pull requests.
- The Copilot SDK to embed the agent in your own tools.

Show: `/learn/copilot-surfaces`.

**Q: Is the cloud agent safe to point at Fabric?**
Give it read-only or offline tools only. Its configured MCP tools run without per-call approval, so
the pull request is the control. Route every Fabric change through review and a deployment
pipeline. DOCUMENTED.

**Q: How is GitHub Copilot different from Copilot in Fabric?**
They work in different places and complement each other:

- **Copilot in Fabric** works inside the Fabric portal (notebooks, Data Factory, Power BI) and runs
  on your Fabric capacity.
- **GitHub Copilot** works in developer tools on code and Git-synced Fabric items, with MCP and
  skills.

Fabric Git integration connects the two worlds.

**Q: What do admins need to enable?**
CHECK. Things to confirm:

- the Copilot plan, and the organization policies that allow MCP servers and agent features;
- VS Code settings for tool approval (we commit ours in `.vscode/settings.json`);
- in Fabric:
  - "Users can create Fabric items";
  - XMLA endpoints;
  - the semantic model Execute Queries REST API;
  - Git integration, plus GitHub sync if you use GitHub.

Run `ffia fabric readiness` to check your tenant read-only.

**Q: Where do our prompts and data go?**
Prompts, the code in context, and any tool results are sent to the model service under your
GitHub Copilot plan's data terms. CHECK them with your GitHub admin. Our practices:

- synthetic data in labs;
- read metadata, not rows;
- never put IDs or secrets in chat;
- keep regulated data out of prompts.

**Q: Can Copilot write to production?**
Not in this design:

- Agents work against a dev workspace.
- Production changes arrive as pull requests and deployment pipelines.
- Live writes need a scoped writer, two flags, policy approval and a second person.
- An approved live write is never silently replaced with a simulation.

## Power BI

**Q: Where does Power BI fit?**
Business definitions live in the semantic model:

- Copilot edits the model through Power BI Modeling MCP, with the `semantic-model-authoring` skill.
- It plans and builds reports with the `powerbi-report-cli` skill.
- DAX checks reconcile every measure with a governed baseline.

LOCAL: 23 of 23 measures match. Against a live model, the same check runs through the Execute
Queries API; that requires tenant validation.

**Q: Do we need Power BI Desktop?**
For local preview and publishing in the guide, yes, on Windows. Modeling through the local
Power BI Modeling MCP server and PBIP/TMDL files works from VS Code.

**Q: Can the agent break a shared semantic model?**
In this design it edits a local PBIP copy (the `powerbi-modeling-sandbox` profile), and the change
reaches the workspace only through review. The Power BI Modeling MCP licence is accepted by a
person, never by configuration.

## Data engineering specifics

**Q: How do we know the agent's notebook is right?**
Compare it with the reviewed reference and the baseline:

- The reference Bronze, Silver and Gold notebooks are generated from the same SQL as the local
  build, and passed 85 of 85 checks on Spark 3.5 locally.
- Counts, keys, missing dimension keys, reconciliation to the cent, and readmissions of 35 out of
  211 are all checked.

Running them on Fabric Spark is the next validation. LOCAL.

**Q: What about preview features like Fabric IQ ontology or Data Warehouse MCP?**
They sit behind feature flags that are off by default, carry a PREVIEW label, and have an offline
simulation. The default demo never depends on them. Show: `/learn/preview-isolation`.

**Q: What if Fabric is unavailable during the day?**
In HYBRID mode, reads fall back to local data with a visible "fallback" label. Writes never fall
back. Show: `/architecture/live-vs-offline`.

**Q: How do changes get to test and production?**
Through Git:

- Fabric Git integration syncs workspace items.
- Pull requests are reviewed, with Copilot code review as well.
- Deployment pipelines promote the changes.

The full promotion flow is the next phase of this accelerator.

## Claude Code (if asked)

**Q: How does this compare with Claude Code?**
Both read the same repository files: `CLAUDE.md` imports `AGENTS.md`, and the project `.mcp.json`
and `.claude/skills` are shared. They differ in permission modes, hooks and admin controls. A
same-task evaluation scored against the same rubric is scheduled as a follow-up session. Show:
`/learn/copilot-vs-claude-code`.

## Cost

**Q: What does the demo environment cost?**
Pay-as-you-go prices as of 2026-10-07:

- **F8 Fabric capacity:** about $1.44 per hour in Central US while running, $0 while paused.
- **Fabric Skills and the MCP servers:** free open-source packages.
- **Copilot:** per-seat licensing under your GitHub plan. CHECK.

Copilot in Fabric consumes capacity units when it's used.
