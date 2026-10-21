# Sharing the accelerator

## What is ready to share

Share the **reference implementation, learning content, offline demos and guided build
paths**. Do not present unfinished live work as complete.

- **HC-01:** primary Fabric engineering / GitHub Copilot / Power BI learning guide. Reviewed
  notebooks, synthetic data, independent baseline and offline medallion build are available.
  Live source landing was verified; live end-to-end table/model/report acceptance is deferred.
- **MFG-01:** primary Foundry-over-Fabric agent guide. Offline sales briefs and quality
  results are reproducible. Connected observations are dated and limited; later revenue
  timeouts and final-answer gaps remain unresolved.
- **DQ-01:** supporting LOCAL/SIMULATED quality investigation and governed-change rehearsal.
- **Claude Code:** retain setup instructions and alternate prompts. Setup, execution and
  the GitHub Copilot-versus-Claude Code comparison are deferred.

Keep personal backlogs, session progress and environment-specific verification records
in ignored local storage, not in the project's tracked documentation.

## Audience entry points

| Audience | Start | Next |
|---|---|---|
| Customer / business stakeholder | [Customer playbook](../field-playbooks/customer.html) | Choose HC-01 or MFG-01 and discuss the outcome and authority boundary |
| SE / developer / presenter | [SE/developer playbook](../field-playbooks/se-developer.html) | Install locked dependencies; run `make demo-offline`; choose an explicit OFFLINE app launch |
| Contributor adding a use case | [Use-case onboarding](use-case-onboarding.md) | Use the existing template, independent checks and registry/readiness gates |

Each audience HTML file is a **complete offline bundle** containing both audience playbooks
and the full Fabric engineering and Foundry agents workshop handouts, including diagrams,
prompts, commands and Q&A, plus an architecture library for every canonical view. Diagrams
are selectable SVGs with component drilldowns, learning-depth selection, build layers and
hop-by-hop request traces—not images. The customer edition starts on the customer page; the SE/developer
edition starts on its technical page. Navigation and cross-document search use a small
embedded script, with no CDN, analytics, network request, local storage or app server.
With JavaScript disabled, all five documents are displayed with textual component and trace
alternatives, but without search, switching or diagram interaction.

**Share either HTML file directly as an attachment.** Save it anywhere and open it in a
browser; do not distribute a set of folders or require readers to download another HTML.
Embedded handout and audience links stay inside the file. Optional online implementation
and product references are labeled and open separately; they require network access and any
repository permissions. This is documentation, not an embedded copy of the React app or live
services. Opening either file runs no Fabric, Azure, Foundry or Power BI operation.
Talk tracks remain presentation documents separate from the React learning workspace.

Use the Markdown guides for reading directly on GitHub. Hosting requires separate setup
and approval; a checked-in HTML file is not a deployed website.

Content lives in `education/field-playbooks/release.yaml` and the two demo `talk-track.yaml`
sources. The renderer validates references and renders the complete handouts directly from
those sources, rather than bundling potentially stale generated HTML:

```bash
make playbooks
make playbooks-check
```

Edit structured sources, not generated HTML. The drift check is part of `make validate`.
Product claims cite existing authoritative source records, including
`fabric-mcp-local`, `skills-for-fabric`, `copilot-cli-ga`, `github-copilot-on-github`,
`foundry-fabric-tool`, `fabric-direct-lake`, `powerbi-authoring-mcp` and `claude-code-memory`.
Product documentation is not tenant execution evidence.

## Repository content boundaries

| Content | Placement | Why |
|---|---|---|
| Root/scoped READMEs and instructions, guides, synthetic contracts, tests, code explanations | Tracked | Required for onboarding, reproduction, maintainability and safe extension |
| Structured education, prompts, diagrams and synthetic interface images | Tracked | Teaching assets; interface captures are not cloud execution proof |
| New audience playbooks | Tracked generated HTML plus structured source | Intentionally distributable docs with reproducible rendering |
| Customer documents, real identifiers, credentials and raw tool responses | Outside repository or explicitly ignored private storage | Never part of the sharing package |
| Session progress, personal backlogs, verification records, operational receipts, draft bindings and personal walkthroughs | Local/ignored | Presenter-specific state is not portable implementation |
| Dependencies, builds, caches and generated native workspace downloads | Ignored | Reinstall/rebuild; native downloads contain private target metadata |

### Every tracked HTML entry point has a purpose

| File | Decision | Purpose |
|---|---|---|
| `frontend/index.html` | Keep tracked | Required Vite application entry |
| `demos/fabric-copilot-level-up/index.html` | Keep tracked | Standalone generated HC engineering presenter handout |
| `demos/foundry-fabric-agents-workshop/index.html` | Keep tracked | Standalone generated MFG agent presenter handout |
| `frontend/public/talktracks/fabric-copilot-level-up.html` | Keep tracked | Standalone HC handout at the existing compatibility URL |
| `frontend/public/talktracks/foundry-fabric-agents-workshop.html` | Keep tracked | Standalone MFG handout at the existing compatibility URL |
| `docs/field-playbooks/customer.html` | Keep tracked | Complete offline bundle, customer-first |
| `docs/field-playbooks/se-developer.html` | Keep tracked | Complete offline bundle, technical-first |

The talk-track pairs are intentional byte-identical publication/deployment copies. The React
workspace does not embed a presenter talk track. Existing standalone URLs and authoring checks
still use the public copies. Edit their YAML sources and use `ffia talktracks render`;
deleting a public copy breaks that compatibility URL and the authoring contract.
Private HTML walkthroughs under ignored local documentation folders are not part of
this release and need not be promoted.

**Recommendation:** use the two audience bundles as the primary shareable deliverables.
Keep `frontend/index.html`: it is the Vite app entry point, not a handout.
Keep the demo `index.html` files for now because existing documentation and standalone
handout workflows link to them; keep the public copies for compatibility and authoring checks.
If reducing generated files later, migrate every link and app route and update the talk-track
renderer/drift tests in one change before deleting the demo outputs. Keep their structured
YAML and the audience-bundle renderer regardless; the bundles need no checked-in demo HTML.

Existing ignore rules already cover private `.local` bindings, source-private material,
local documentation, native workspace caches and dependency/build artifacts. Do not hide
useful public documentation merely because a related live action is unfinished.

### What belongs in the README, public docs and local notes

- **README:** what the repo does, where to start and a short readiness statement.
- **Public docs:** reusable setup and validation procedures, design decisions, API contracts
  and product limitations needed to build, test or use the project.
- **Local only:** resume trackers, implementation diaries, personal backlogs, validation
  records, presenter notes, raw logs, tool responses and tenant-specific receipts. Use
  ignored `docs/local/maintainer/`, or keep them outside the repository. Existing `.local`
  binding rules still apply.

Keep reproducible tests and synthetic expected baselines in the project, not session diaries.
Adding a tracked file to `.gitignore` does not remove it from Git history.

## Release boundary

Sharing documentation does not authorize live work. Keep connected previews optional,
run the applicable existing validation commands and privacy scan, and inspect the reviewed
commit/workflow evidence before declaring a released version. Local validation, committing,
pushing and observing GitHub workflows are separate outcomes.
