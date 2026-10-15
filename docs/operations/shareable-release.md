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

Both HTML playbooks are **original, self-contained, script-free** documents. They need no
external font, image, analytics service or app server to display. Their repository and
source hyperlinks need network access and any required repository permissions; sharing a
file does not grant repository access. They do not embed customer source material or private
environment data.

GitHub shows HTML source, not the rendered page. Download the file, then open it in a
browser. You can also attach it to an approved sharing channel. A repository link lets
readers find and download the file; it is not a hosted website.
Opening either page runs no Fabric, Azure, Foundry or Power BI operation.

Use the Markdown guides for reading directly on GitHub. Hosting requires separate setup
and approval; a checked-in HTML file is not a deployed website.

Content lives in `education/field-playbooks/release.yaml`; the renderer escapes content,
validates repository asset links and source IDs, and produces both audience pages:

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
| `frontend/public/talktracks/fabric-copilot-level-up.html` | Keep tracked | Generated app-served copy of the HC handout |
| `frontend/public/talktracks/foundry-fabric-agents-workshop.html` | Keep tracked | Generated app-served copy of the MFG handout |
| `docs/field-playbooks/customer.html` | Keep tracked | New business/customer orientation |
| `docs/field-playbooks/se-developer.html` | Keep tracked | New technical preparation and build path |

The talk-track pairs are intentional byte-identical publication/deployment copies. Edit
their YAML sources and use `ffia talktracks render`; deleting an app copy breaks its handout
route. Private HTML walkthroughs under ignored local documentation folders are not part of
this release and need not be promoted.

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
