# Sharing the accelerator

## What is ready to share

Share the **reference implementation, structured learning content, offline demonstrations and
guided build paths**, not a claim that every live or production checkpoint is complete.

- **HC-01:** primary Fabric engineering / Copilot / Power BI learning guide. Reviewed
  notebooks, synthetic data, independent baseline and offline medallion build are available.
  Live source landing was verified; live end-to-end table/model/report acceptance is deferred.
- **MFG-01:** primary Foundry-over-Fabric agent guide. Offline sales briefs and quality
  results are reproducible. Connected observations are dated and limited; later revenue
  timeouts and final-answer gaps remain unresolved.
- **DQ-01:** supporting LOCAL/SIMULATED quality investigation and governed-change rehearsal.
- **Claude Code:** retain setup instructions and alternate prompts. Setup, execution and
  the Copilot-versus-Claude Code comparison are intentionally deferred.

The [resume tracker](resume-later.md) retains the unfinished work. The
[verification record](use-case-authoring-verification.md) separates actual operations from
LOCAL checks, PREVIEW results, historical observations and unavailable outcomes.

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

Open a local HTML file directly in a browser, attach it to a permitted sharing channel, or
send its repository link. These are documentation assets, not a deployed website. Opening
either page invokes no Fabric, Azure, Foundry or Power BI operation.

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

## Repository content placement review

The review used the tracked-file inventory, bounded searches across tracked text/code and
focused inspection of matching files. It is not a claim of line-by-line human review of all
source or a security certification. The privacy scan supplements, but does not replace,
editorial review. No automatic deletion or relocation was warranted by those searches.

| Content | Placement | Why |
|---|---|---|
| Root/scoped READMEs and instructions, guides, synthetic contracts, tests, code explanations | Tracked | Required for onboarding, reproduction, maintainability and safe extension |
| Structured education, prompts, diagrams and synthetic interface images | Tracked | Teaching assets; interface captures are not cloud execution proof |
| Dated sanitized verification records | Tracked | Show honest outcomes and limitations without real identifiers |
| New audience playbooks | Tracked generated HTML plus structured source | Intentionally distributable docs with reproducible rendering |
| Customer documents, real identifiers, credentials and raw tool responses | Outside repository or explicitly ignored private storage | Never part of the sharing package |
| Session scripts, operational receipts, draft bindings and personal walkthroughs | Local/ignored | Presenter-specific state is not portable implementation |
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

## Release boundary

No live work is required or authorized by this sharing pass. Keep connected previews optional,
run the applicable existing validation commands and privacy scan, and inspect the reviewed
commit/workflow evidence before declaring a released version. Local validation, committing,
pushing and observing GitHub workflows are separate outcomes.

### LOCAL validation snapshot: 2026-10-14

| Check | Result |
|---|---|
| `make validate` | PASSED: 650 backend tests, 1 opt-in live test skipped, backend coverage above 96%; 100 frontend tests with 98.86% statement / 86.58% branch coverage |
| Focused `pytest tests/unit/test_field_playbooks.py --cov=fabric_foundry_accelerator.education.field_playbooks --cov-report=term-missing` | PASSED: 11 tests, 98.45% renderer coverage |
| `make playbooks-check` | PASSED: both generated pages, source IDs and repository links validated |
| `ffia privacy scan` | PASSED: 782 files, zero findings |
| Source, education, talk-track, notebook and prompt drift checks | PASSED; Claude remains documented-only |
| Browser checks for both HTML pages | Rendered successfully; at 390px viewport, no horizontal overflow; customer skip-link keyboard focus and developer navigation/command expansion verified |
| Dependency audits, builds, SBOM checks and offline agent/demo gates in `make validate` | PASSED |

The existing Power BI tool-catalog warnings remain: connected model operations still require
validation when HC-01 resumes. These checks did not execute cloud notebooks, create models,
publish reports, set up Claude or certify production readiness. GitHub CI results are a
separate later check, not inferred from the local gate.
