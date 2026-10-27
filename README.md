# Fabric Foundry Integration Accelerator

![Fabric and Foundry Integration Accelerator. Show and tell. Build and learn.](docs/branding/fabric-foundry-social.png)

**Show and tell. Build and learn.**

> **Not for production.** This repository is a solution accelerator, reference
> implementation, and learning/demo environment using synthetic data. It is not a
> production-ready deployment and must not be deployed as-is for production.
> Before adapting these patterns to a production workload, follow Microsoft's
> [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
> and [Well-Architected guidance for Microsoft Fabric](https://learn.microsoft.com/azure/well-architected/microsoft-fabric/overview).
> Assess reliability, security, cost optimization, operational excellence, and
> performance efficiency for your own workload. Demo results are not production
> readiness, security, compliance, or availability certification.

Use this repo to learn how **Microsoft Fabric**, **Microsoft Foundry** and **GitHub Copilot**
work together. It is a reference implementation and a guided learning app—not a deployed
customer solution. Choose one workflow, build it with synthetic data, and verify the result.
You do not need an Azure account for the offline path.

**Why use it?** Improve repeatable Fabric data-engineering work with coding assistants,
then learn how governed data supports grounded agents. Understand each tool's responsibility
before connecting it to a live service.

**How to start:** follow [Quick start](#quick-start), open **Start here**, choose a **Use Case**,
and work through one checkpoint at a time. Use **Hands-on labs** for focused practice and
**Architecture** to inspect components and trace the flow.

**Development showcase, not production deployment.** Normal app startup is LIVE-first
HYBRID in your configured development environment, with disclosed LOCAL read fallback.
Browse the searchable use-case catalog, inspect a workshop's overview and prerequisites,
then select **Start workshop**. See [Microsoft tooling and workshop alignment](docs/operations/tooling-and-workshop-alignment.md)
for supported integrations, deliberate exclusions and the workshop references behind this flow.

| Fabric | Foundry | GitHub Copilot |
|---|---|---|
| Provides governed data and business context | Uses that context for reasoning, orchestration, evaluation and action | Helps engineers understand the repo, write code, add tests and inspect failures |

**Keep the roles clear:** MCP provides tool access. Skills provide procedures. Neither grants
authority. Identity, policy and human approval control live changes.

**Synthetic data only.** This is a learning repo and reference implementation, not a complete
production deployment. Preview features are optional.

**[Quick start](#quick-start)** · **[Use cases](#choose-a-use-case)** ·
**[Workshop](#build-and-learn-workshop)** ·
**[Reading order](#read-and-follow-the-repository)** ·
**[Directory map](#repository-map)** · **[Module map](#module-map)** ·
**[Reproduce and rebuild](#reproduce-and-build-from-scratch)**

## Choose a use case

| Guide | What you will build and learn | What is ready |
|---|---|---|
| [HC-01: Fabric engineering with GitHub Copilot](guides/hc-01-fabric-mcp-powerbi-medallion-lab/README.md) | Fabric MCP, Fabric Skills, Bronze/Silver/Gold notebooks and a planned Power BI handoff | Guide, reviewed notebooks and offline build. Demo steps confirmed complete by the user; report review/publication deferred. |
| [MFG-01: Foundry agents over Fabric](guides/mfg-01-foundry-fabric-sales-insights/README.md) | Sales insights, team briefs and reviewed quality proposals over synthetic manufacturing data | Offline briefs and quality checks. Demo answer checks confirmed complete by the user; not production certification. |
| [DQ-01: Supporting quality exercise](guides/dq-01-synthetic-quality-investigation/README.md) | Exact quality checks and a governed notebook proposal | LOCAL checks and a SIMULATED change rehearsal. No cloud correction runs. |

HC-01 and MFG-01 are the two featured guides. Both stay in the repo.
Claude Code instructions and alternate prompts are available now; setup and execution come
later. These guides do not certify a production deployment. See the
[learning-repo completion scope and deferred work](docs/operations/delivery-backlog.md).

## Get ready to share or present

| Audience | Start here |
|---|---|
| Customer or business team | [Customer field playbook](docs/field-playbooks/customer.html): value, tool roles and the two use cases |
| SE, developer or presenter | [SE/developer field playbook](docs/field-playbooks/se-developer.html): setup, build paths, checks and approval boundaries |
| New contributor | [Use-case onboarding](docs/operations/use-case-onboarding.md), [template](guides/_template/README.md) and [readiness checks](docs/operations/use-case-readiness.md) |

> **Portable delivery:** share either audience HTML file as an attachment, then open it
> directly in a browser. Each contains both playbooks and both complete demo handouts,
> with offline navigation, search and an interactive explorer for all architecture views.
> No second HTML download or local server is needed.
> Optional online source/code references are labeled and open in a new tab.

Presenter handouts: [Fabric engineering](demos/fabric-copilot-level-up/index.html) and
[Foundry agents](demos/foundry-fabric-agents-workshop/index.html). These are generated from
their YAML sources. They are separate presentation documents aligned with the app's use cases
and architecture—not screens or scripts inside the React learning workspace.
Use the [morning runbook](demos/MORNING-RUNBOOK.md) to prepare.

See [sharing scope](docs/operations/shareable-release.md) for what belongs in the public repo.

## Start here: choose your outcome

| I want to... | First step |
|---|---|
| Understand the architecture | Read the [repo map](docs/architecture/repository-map.md) and choose a [learning level](docs/education/learning-paths.md) |
| Try it without cloud access | Follow [Quick start](#quick-start), launch OFFLINE and open **Learn** or **Use Cases** |
| Build through a guide | Choose [HC-01](guides/hc-01-fabric-mcp-powerbi-medallion-lab/README.md) or [MFG-01](guides/mfg-01-foundry-fabric-sales-insights/README.md), then stop at each checkpoint |
| Add a use case | Follow [onboarding](docs/operations/use-case-onboarding.md) and reuse the existing registries and checks |
| Read or maintain the code | Follow the [code-reading path](docs/architecture/code-reading-path.md), then run the [release checks](docs/operations/release-validation.md) |

## Build-and-learn workshop

Follow **Start here → Use Cases → Hands-on labs → Architecture → Evidence** in the app.
Use `/use-cases` for the guides; existing `/guides` links still work.
Open **Explore** for concepts, patterns, data, the agent sandbox, recorded comparisons and
offline verification. These advanced tools do not compete with the primary build path.

**Do not confuse the connections:** coding assistants use **Fabric MCP tools** to reach
remote Fabric, even when the MCP process runs on the workstation. The **app's backend uses
Fabric REST**, a separate connection. **Offline synthetic data (DuckDB/Parquet)** is teaching
data and an eligible LOCAL read fallback, not a Fabric server. A fallback being available
does not mean it was used. See [connection boundaries](docs/operations/workshop-learning.md#three-connections-not-one).

Labs show one stage at a time with an outline, previous/next controls and browser-local
progress. Architecture diagrams are selectable SVGs, not screenshots: click a component
for its responsibilities and connections, drill into a neighbor, or step through a request
trace. Traces explain the design; they do not perform live operations.

- **Learn:** four journeys, 25 patterns and 21 lessons across Executive and L100-L400.
- **Build:** five labs, 130 knowledge checks and guide checkpoints.
- **Inspect:** source data, transformations, expected results, failure modes and recovery.
- **Test ideas:** compare a clear hypothesis against an independent baseline. Proposed
  experiments are not recorded findings or productivity claims.
- **Check evidence:** distinguish a local result, a simulation, a preview and a live operation.
  Missing labs and live checks stay visible.

Use the generated [GitHub Copilot](prompts/github-copilot/patterns.md) or
[Claude Code](prompts/claude-code/patterns.md) prompt packs.
The recorded comparison uses Claude and GPT models **inside GitHub Copilot CLI**.
It is not a GitHub Copilot versus Claude Code comparison.
Replay it at `/bakeoff` without a new cloud call.

### App preview

Captured on **2026-10-09**. These are **LOCAL screenshots** of synthetic workshop content.
The HYBRID status bar shows configuration, not proof of a live operation.

<details>
<summary>See the workshop and evidence screens</summary>

![Workshop entry and learning journeys](docs/architecture/screenshots/app-current-workshop.png)

![Evidence page with local, live-first and strict-live choices](docs/architecture/screenshots/app-current-evidence.png)

See the [current Learn page image](docs/architecture/screenshots/app-current-learn.png)
and the [documented screenshot gallery](docs/operations/workshop-learning.md#current-app-captures).

</details>

See [workshop learning and research](docs/operations/workshop-learning.md),
[reusable use-case onboarding](docs/operations/use-case-onboarding.md),
[the two integration paths](docs/architecture/integration-paths.md) and
[actual draw.io PNG exports](docs/architecture/diagrams/README.md).
Spec-driven delivery is optional. The repo skill and P25 explain when to use it.
Spec Kit is not installed or required for the default demo.

## Quick start

Prerequisites:

| Tool | Version | Notes |
|---|---|---|
| uv | 0.12.23 | Python package manager |
| Python | 3.14 | `uv python install 3.14` |
| Node.js | 24 LTS | Node 26 also tested |
| Git | any recent | |
| GNU Make | any recent | |

For a fresh clone, start here:

```bash
git clone https://github.com/honestypugh2/fabric-foundry-integration-accelerator.git
cd fabric-foundry-integration-accelerator
```

Then restore the checked-in dependency versions:

```bash
# Backend: always create and activate the virtual environment before installing
uv venv --python 3.14 .venv
source .venv/bin/activate
uv sync --frozen

# Frontend
cd frontend && npm ci && cd ..

# First useful success: no Azure setup required
make demo-offline
```

**Expected result:** `Release gate: PASSED` and zero cloud operations. Resolve errors before
connecting providers. Installation needs package-registry access; offline refers to execution.

### Choose one startup path

These are **alternatives, not commands to run in sequence**.

| Path | Start | Expected result / stop |
|---|---|---|
| **A. Workshop app (recommended)** | `make run API_ARGS=--offline` | Open http://localhost:5173; expect Workshop and OFFLINE status. Choose Learn or Use Cases at `/use-cases`. Ctrl+C stops this launch. |
| **B. Headless offline demo** | `make demo-offline` | Ten-act narrative ending in `Release gate: PASSED`; no browser needed |
| **C. Coding-client MCP** | Follow [MCP profiles](config/mcp/README.md) and the guide's tool setup | The coding client launches approved configured servers. `make run-mcp` starts only synthetic `ffia-local` stdio, not a website or the real Fabric MCP. Ctrl+C stops a manually launched server. |

The app command starts both API (:8000, API reference at http://localhost:8000/docs) and
frontend (:5173). Do not start `make run-api` before `make run`. Optional local exercises:
`make data` builds layers; `make recovery-demo` rehearses recovery (SIMULATED).

### Connect deliberately

For a fresh clone only, create private configuration without overwriting an existing file:

```bash
test -f .env || cp .env.example .env
```

Follow [environment configuration](docs/operations/environment-configuration.md), supply
private bindings and authenticate. Stop the offline app, then run `make run` for live-first
HYBRID. Inspect each result's provider, label and fallback; configuration is not LIVE proof.
Leave optional telemetry unconfigured for an entirely local session.

If ports are occupied, reuse the instance or stop only your owned launch. For remote VS Code,
forward the frontend port. See [startup troubleshooting](docs/operations/environment-configuration.md#startup-troubleshooting).

### Maintainer checks

`make validate` is the full local quality/release gate, **not a prerequisite to view the app**.
Run targeted checks first; see [release validation](docs/operations/release-validation.md).

Architecture diagrams (draw.io, Azure Architecture Center style, generated from YAML) are in
[`docs/architecture`](docs/architecture/README.md) and interactive in the app at `/architecture`.
Start with the [graphical repository map and guide screenshots](docs/architecture/repository-map.md)
and [environment configuration](docs/operations/environment-configuration.md).

See [control plane](docs/architecture/control-plane.md), [frontend](docs/architecture/frontend.md),
[resilience](docs/architecture/resilience.md), [demo continuity](docs/operations/demo-continuity.md)
and [learning paths](docs/education/learning-paths.md).

`make demo-live` and `make demo-hybrid` now run a bounded application Fabric read and one
synthetic Foundry question. They incur model usage, never create Fabric items, and do not
substitute for Guide 1's assigned MCP tools. A fallback cannot pass the live evaluation gate.
Run `make help` for every target.

## Read and follow the repository

**Do not read every file in directory order.** Follow one outcome, then trace one
request through the implementation. The guides explain what to build; contracts
and tests explain what the code must guarantee.

| Pass | Read or do | What you should understand before continuing |
|---|---|---|
| 1. Understand the purpose | This README, then [the runtime map](docs/architecture/repository-map.md) and [the two integration paths](docs/architecture/integration-paths.md) | Fabric supplies context; Foundry reasons; the app's REST/SDK path is separate from the coding assistant's MCP path. |
| 2. Run an example | [Quick start](#quick-start), using the OFFLINE app or headless demo | See a working synthetic example before configuring any cloud service. LOCAL and SIMULATED are not LIVE. |
| 3. Follow a use case | Choose [HC-01](guides/hc-01-fabric-mcp-powerbi-medallion-lab/README.md) or [MFG-01](guides/mfg-01-foundry-fabric-sales-insights/README.md), then its step prompts and checkpoints | Understand the business outcome, required tools, expected evidence and approval boundaries. Do not mix steps from different guides accidentally. |
| 4. Read the implementation | [Contracts-to-tests reading path](docs/architecture/code-reading-path.md), then the [module map](#module-map) below | Find the input/result types, local implementation, service, transport and corresponding tests for one capability. |
| 5. Make one change | Start with a failing focused test; change the owning module or structured content, not every layer | Keep domain rules in Python services/providers and presentation in React. Regenerate derived contracts/content only when their inputs change. |
| 6. Reproduce and extend | [Reproduction and build order](#reproduce-and-build-from-scratch), then [use-case onboarding](docs/operations/use-case-onboarding.md) | Repeat the local result, understand dependency order, and add an optional live adapter without replacing the local path. |

For teaching, choose Executive or L100 first; for implementation, move through
L200-L400 as needed. [Learning paths](docs/education/learning-paths.md) explain the
levels. A learner checkpoint or recorded result is not production certification.

## Repository map

This table covers the tracked top-level directories. Start with the **Read first**
column instead of treating generated files as the source of truth.

| Directory | What it is used for | Read first |
|---|---|---|
| [src/](src/) | Installable Python package: CLI, services, provider adapters, synthetic pipeline and teaching-content loaders | [Module map](#module-map), then [cli.py](src/fabric_foundry_accelerator/cli.py) |
| [frontend/](frontend/) | React + strict TypeScript + Vite demo app; it calls the Python API rather than cloud services directly | [Frontend architecture](docs/architecture/frontend.md), then [App.tsx](frontend/src/app/App.tsx) |
| [tests/](tests/) | Unit, API/fixture contract, offline, security, evaluation and opt-in live tests | [Shared fixtures and offline isolation](tests/conftest.py), then the test for the capability being changed |
| [config/](config/) | Environment/overlay definitions, provider and policy settings, MCP profiles, evaluation suites, harness permissions, skill pins and privacy rules | [Environment configuration](docs/operations/environment-configuration.md) and [MCP profiles](config/mcp/README.md) |
| [data/](data/) | Synthetic source data, expected baselines, layer/reference assets and ignored local runtime outputs | [Synthetic data guide](data/synthetic/README.md) |
| [education/](education/) | Structured lessons, labs, knowledge checks, architecture views, workshop content and field-playbook sources | [workshop.yaml](education/workshop.yaml) and [learning paths](docs/education/learning-paths.md) |
| [guides/](guides/) | Use-case manifests, prompts and ordered build/verify checkpoints; each guide can have scoped agent instructions | [Guide index](#choose-a-use-case) and [onboarding](docs/operations/use-case-onboarding.md) |
| [docs/](docs/) | Architecture explanations, decisions, operations, research registry, privacy/security guidance and generated teaching artifacts | [Repository runtime map](docs/architecture/repository-map.md) and [code-reading path](docs/architecture/code-reading-path.md) |
| [demos/](demos/) | Presenter runbooks, structured talk tracks, generated handouts and recorded comparison assets | [Morning runbook](demos/MORNING-RUNBOOK.md) |
| [prompts/](prompts/) | Reusable GitHub Copilot and Claude Code prompt packs for learning and guided engineering | [Copilot patterns](prompts/github-copilot/patterns.md) or [Claude patterns](prompts/claude-code/patterns.md) |
| [notebooks/](notebooks/) | Fabric reference notebook artifacts used by the engineering guide | [HC-01 guide](guides/hc-01-fabric-mcp-powerbi-medallion-lab/README.md); inspect code before any live run |
| [fabric/](fabric/) | Fabric workspace/Git-format reference items; their presence does not mean they were deployed | [Workspace items](fabric/workspace/) |
| [powerbi/](powerbi/) | Customer-neutral semantic/report build area and population-filter contract | [Power BI README](powerbi/README.md) |
| [schemas/](schemas/) | Generated JSON Schemas and OpenAPI contracts; change Python boundary models, then export | [Schema README](schemas/README.md) |
| [evaluation/](evaluation/) | Evaluation-dataset area and guidance; executable evaluators live in the Python package and configured suites under configuration | [Evaluation README](evaluation/README.md) and [configured suites](config/evaluations/) |
| [infra/](infra/) | Reference Bicep modules and observability setup for adaptation; not an automatic demo deployment | [Infrastructure README](infra/README.md) |
| [scripts/](scripts/) | Development-time wrappers and the optional standalone local Spark notebook check | [Scripts README](scripts/README.md) |
| [.claude/](.claude/) | Shared project skills and Claude Code harness configuration | [Agent instructions](#agent-instructions) and [shared skills](.claude/skills/) |
| [.github/](.github/) | Copilot instructions, scoped coding rules, issue/PR support files and CI workflows | [Copilot instructions](.github/copilot-instructions.md) and [release validation](docs/operations/release-validation.md) |
| [.vscode/](.vscode/) | Workspace editor, Python/TypeScript and coding-assistant settings | [settings.json](.vscode/settings.json); keep personal machine configuration out of shared defaults |

Important root files:

| File | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md) | Repository rules and the Claude Code import of those rules |
| [pyproject.toml](pyproject.toml), [uv.lock](uv.lock) | Python package metadata, exact dependencies, lint/type/test configuration and locked resolution |
| [frontend/package.json](frontend/package.json), [frontend/package-lock.json](frontend/package-lock.json) | Frontend dependencies, lockfile and npm scripts |
| [Makefile](Makefile) | Existing setup, run, generation, test and build commands; use `make help` |
| [.mcp.json](.mcp.json) | Rendered coding-client MCP configuration; not the application's provider configuration |
| [.env.example](.env.example), [.gitignore](.gitignore) | Configuration template and rules excluding private bindings, caches and runtime/build artifacts |

Local directories such as `.venv/`, `node_modules/`, `frontend/dist/`, `dist/` and
`sbom/` are restored or generated outputs, not additional application modules.
Never copy private environment files, tenant exports or runtime receipts into a
new public clone.

## Module map

### Python: where responsibilities live

All paths in this table are under
[src/fabric_foundry_accelerator/](src/fabric_foundry_accelerator/).

| Module | Responsibility and dependencies |
|---|---|
| [models/](src/fabric_foundry_accelerator/models/) | Pydantic request/result, execution-label, semantic-model and change contracts shared across boundaries |
| [config/](src/fabric_foundry_accelerator/config/) | Typed settings, environment/overlay loading and private binding validation; distinct from the root configuration files |
| [synthetic/](src/fabric_foundry_accelerator/synthetic/) | Seeded data generation, profiles, Bronze/Silver/Gold transforms, semantic baselines and notebook rendering |
| [providers/](src/fabric_foundry_accelerator/providers/) | Fabric capability protocols and LOCAL/LIVE/outage/routed adapters; domain services depend on the protocol, not an SDK |
| [fallback/](src/fabric_foundry_accelerator/fallback/) | Read routing, bounded retries, breakers and disclosed fallback decisions; never converts a failed live write to a local write |
| [policies/](src/fabric_foundry_accelerator/policies/) | Deterministic tool, write and fallback policy evaluation |
| [approvals/](src/fabric_foundry_accelerator/approvals/) | Expiring, destination-bound approval records and checks |
| [audit/](src/fabric_foundry_accelerator/audit/) | Correlated operation evidence and in-memory/JSONL stores |
| [services/](src/fabric_foundry_accelerator/services/) | Use-case orchestration, runtime status, education and changes; [container.py](src/fabric_foundry_accelerator/services/container.py) composes settings, ports and implementations |
| [api/](src/fabric_foundry_accelerator/api/) | FastAPI routes, application factory and TypeScript contract export; routes validate and delegate rather than implement business rules |
| [mcp/](src/fabric_foundry_accelerator/mcp/) | Safe, allow-listed `ffia-local` tools and client-profile rendering; not the real Microsoft Fabric MCP server |
| [agents/](src/fabric_foundry_accelerator/agents/) | Agent protocol, deterministic local sales agent, existing-agent Foundry SDK adapter and Agent Framework workflows |
| [evaluation/](src/fabric_foundry_accelerator/evaluation/) | Deterministic baseline and agent-answer checks; a fluent model answer alone does not pass |
| [knowledge/](src/fabric_foundry_accelerator/knowledge/) | Cited synthetic knowledge retrieval and flagged preview analogs |
| [recovery/](src/fabric_foundry_accelerator/recovery/) | LOCAL snapshot/replay logic and SIMULATED Open Mirroring recovery drills |
| [education/](src/fabric_foundry_accelerator/education/) | Load/validate structured lessons, guides and architecture; render diagrams, prompts, talk tracks and field playbooks |
| [patterns/](src/fabric_foundry_accelerator/patterns/) | Architecture-pattern catalog, selection signals and recommendations |
| [research/](src/fabric_foundry_accelerator/research/) | Source-registry validation and generated reference documentation |
| [observability/](src/fabric_foundry_accelerator/observability/) | Redacted logs, correlation and explicitly configured OpenTelemetry |
| [privacy/](src/fabric_foundry_accelerator/privacy/) | Local customer-identity, secret and leakage scans |
| [harness/](src/fabric_foundry_accelerator/harness/) | Rendered coding-client permissions and the command guard |
| [skills/](src/fabric_foundry_accelerator/skills/) | Curated skill catalog, pins, installation and consistency checks |
| [bakeoff/](src/fabric_foundry_accelerator/bakeoff/) | Task definitions, recorded runs/replays and deterministic grading; reading a replay is not a new client comparison |
| [auth/](src/fabric_foundry_accelerator/auth/), [clients/](src/fabric_foundry_accelerator/clients/), [tools/](src/fabric_foundry_accelerator/tools/) | Reserved extension namespaces, currently package markers rather than complete shared implementations. Current Fabric REST/auth implementations are in [providers/fabric/](src/fabric_foundry_accelerator/providers/fabric/); the Foundry adapter is in [agents/](src/fabric_foundry_accelerator/agents/). |
| [cli.py](src/fabric_foundry_accelerator/cli.py), [sbom.py](src/fabric_foundry_accelerator/sbom.py) | CLI entry point/command registration and generated dependency-inventory validation |

### React: how the browser reaches the backend

| Module | Responsibility |
|---|---|
| [src/main.tsx](frontend/src/main.tsx) | React, router and query-client initialization |
| [src/app/](frontend/src/app/) | Routes, shared layout, learning level and browser-local progress |
| [src/features/](frontend/src/features/) | Home/workshop, guides, labs, learning, architecture, patterns, data, agent, demo and recorded-comparison screens |
| [src/api/](frontend/src/api/) | HTTP client, runtime-validated response contracts, generated API types and query/mutation hooks |
| [src/components/](frontend/src/components/) | Reusable accessible UI, error/loading states, provenance badges and safe Markdown |
| [src/content/](frontend/src/content/) | Small shared presentation content; structured lessons and guide content remain in the root content directories |
| [src/test/](frontend/src/test/) | Test setup, rendering helpers and API-derived fixtures |
| [vite.config.ts](frontend/vite.config.ts) | Dev proxy to the local API, build settings and frontend test/coverage configuration |

Two useful traces:

```text
Teaching request:
Browser Evidence page -> frontend API hook/client
  -> GET /api/v1/education/workshop
  -> EducationService -> education/workshop.yaml + validated registries

Data request:
Browser Data page -> POST /api/v1/fabric/read
  -> typed request -> execute_read service -> FabricProvider port/router
  -> LOCAL synthetic tables, or configured Fabric REST adapter
  -> labeled execution envelope -> validated frontend contract -> UI
```

The [composition root](src/fabric_foundry_accelerator/services/container.py) wires
these dependencies. Cloud credentials and authoritative write decisions stay out
of the browser. The coding assistant's separate path is **instructions + skills
→ configured Fabric MCP tool → permitted Fabric operation**; it does not travel
through the React API just because the app is open.

## Reproduce and build from scratch

### Reproduce this checked-in codebase

Use the [fresh-clone setup](#quick-start) to restore the exact Python and npm
lockfiles. Do not copy another machine's virtual environment or install floating
dependency versions. From the repository root, after installation:

```bash
source .venv/bin/activate

# Reproduce synthetic inputs and derived local layers; no tenant configuration
make data-check
make data

# Exercise the existing local capabilities without starting a browser
make demo-offline

# Alternative interactive launch: starts API and React together
make run API_ARGS=--offline
```

Stop the interactive launch with Ctrl+C before starting another instance.
Expected outcomes are matching synthetic baselines, a passing offline demo, and
an OFFLINE workshop at http://localhost:5173. These commands do not deploy
infrastructure, publish reports or create Fabric items. Optional local Spark
verification has separate Java/PySpark prerequisites in
[scripts/README.md](scripts/README.md); it is not required for this starting path.

For an intentional maintainer-quality run, use `make validate`; for distributable
Python/frontend outputs, use `make build`. Validation may access package and
vulnerability feeds even though the default demo/tests need no cloud credentials.
See the [release checks](docs/operations/release-validation.md) for what each gate
does; running a build is not deploying it.

### Rebuild the design incrementally

This is the dependency order for implementing an equivalent learning accelerator,
not a claim that one generator recreates the entire repository. Study and build
one vertical slice at a time; keep a deterministic local path throughout.

| Stage | Implement/read | Checkpoint before adding the next layer |
|---|---|---|
| 1. Foundation | Dependency manifests/locks, [AGENTS.md](AGENTS.md), [models/](src/fabric_foundry_accelerator/models/) and typed [configuration](src/fabric_foundry_accelerator/config/) | Explicit inputs/results, execution labels and configuration rules; strict lint/types and a small passing test |
| 2. Deterministic context | [Synthetic profiles/pipeline](src/fabric_foundry_accelerator/synthetic/), [expected results](data/synthetic/expected/), [semantic contracts](data/synthetic/semantic/) and [local provider](src/fabric_foundry_accelerator/providers/fabric/local.py) | Raw → Bronze → Silver → Gold results and semantic measures reconcile without Fabric |
| 3. Domain and safety | Provider/agent protocols and local implementations, [policies](src/fabric_foundry_accelerator/policies/), [approvals](src/fabric_foundry_accelerator/approvals/), [audit](src/fabric_foundry_accelerator/audit/), [routing](src/fabric_foundry_accelerator/fallback/) and services | Direct Python tests prove allowed reads, explicit failures, labeled fallback and separately approved simulated writes |
| 4. Teaching sources | Minimal [pattern catalog](src/fabric_foundry_accelerator/patterns/), [education loaders](src/fabric_foundry_accelerator/education/), source registry and one structured [guide](guides/) | The guide's content, fields, references, prompts and checkpoints validate; content is not hard-coded into screens |
| 5. Composition and transport | [container.py](src/fabric_foundry_accelerator/services/container.py), thin [CLI](src/fabric_foundry_accelerator/cli.py), [API](src/fabric_foundry_accelerator/api/) and allow-listed [local MCP](src/fabric_foundry_accelerator/mcp/) | `/health`, `/ready`, typed API responses and the CLI work over the same services; contract/offline tests pass |
| 6. Browser | [API client/contracts](frontend/src/api/), shared components and one [feature screen](frontend/src/features/) | A real local API request renders loading, error, data and provenance states; frontend fixtures match API responses |
| 7. Reasoning and evidence | [Local agent/workflows](src/fabric_foundry_accelerator/agents/), [evaluation](src/fabric_foundry_accelerator/evaluation/), knowledge and recovery exercises | Grounded synthetic answers match independent baselines; unsupported questions and failure cases are tested |
| 8. Optional connected adapters | Existing [Fabric REST adapters](src/fabric_foundry_accelerator/providers/fabric/), [Foundry adapter](src/fabric_foundry_accelerator/agents/foundry.py) and separate [coding-client profiles](config/mcp/README.md) | Configure private bindings only when needed; obtain scoped approval for writes and retain actual tool/result evidence without changing the local baseline |

### Source files versus generated files

Change the owning source first. Do not patch generated artifacts to hide a
contract or content mismatch.

| When you change... | Regenerate/check with... |
|---|---|
| Python boundary models or API contracts | `ffia schemas export`, then `ffia schemas check`; refresh browser fixtures with `make fixtures` |
| API-returned structured teaching content | `make fixtures`, then the affected backend/frontend tests and `ffia education check` |
| Architecture-view YAML under [education/architecture/views/](education/architecture/views/) | `ffia diagrams render`, then `ffia diagrams check` |
| Reviewed notebook/SQL sources | `ffia notebooks render`, then `ffia notebooks check`; live notebook runs remain a separate approved operation |
| [Research registry](docs/research/sources.yaml) | `ffia sources render`, then `ffia sources check` |
| Presenter talk tracks or field-playbook sources | `ffia talktracks render` / `ffia talktracks check`; `make playbooks` / `make playbooks-check` |
| MCP or coding-harness policy sources | Follow [MCP profile rendering](config/mcp/README.md) and [agent instructions](#agent-instructions); run `ffia mcp check` / `ffia harness check` |

For a new feature, use this loop: **outcome → failing test → typed contract →
local implementation → service → thin API/CLI surface → UI/teaching → targeted
tests**. Add LIVE connectivity only if the feature needs it. Never treat a local
clone, generated diagram or installed MCP server as proof of a cloud operation.

## Agent instructions

- [`AGENTS.md`](AGENTS.md) is the single source of truth for coding agents.
- [`CLAUDE.md`](CLAUDE.md) imports it for Claude Code.
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) summarizes it for GitHub
  Copilot.
- The root [`.mcp.json`](.mcp.json) is the portable MCP configuration shared by VS Code, GitHub Copilot
  CLI and Claude Code, rendered from the default profile `fabric-first` in
  [`config/mcp/profiles.yaml`](config/mcp/profiles.yaml). It starts the **real Fabric MCP server**
  (`@microsoft/fabric-mcp` 1.4.0, read-only, metadata only; LIVE once you `az login` to your demo
  tenant), Microsoft Learn, and the local educational server **`ffia-local` as the labeled
  fallback** when Fabric MCP is unavailable. Fabric Skills install with `ffia skills install`.
- [`config/harness/policy.yaml`](config/harness/policy.yaml) is one permission policy rendered
  for Claude Code (`.claude/settings.json`, with an enforced `ffia harness guard` hook), GitHub Copilot CLI
  (`--allow-tool`/`--deny-tool`) and VS Code (`chat.tools.terminal.autoApprove`). Opt-in Fabric MCP and Power BI Modeling
  MCP profiles are rendered per client with `ffia mcp render <profile> --client vscode|claude|copilot-cli`.

## Operating modes

`LIVE`, `HYBRID` and `OFFLINE`. Every result is labeled with one of `LIVE`, `HYBRID`, `LOCAL`,
`SIMULATED`, `MOCKED`, `PREVIEW` or `UNAVAILABLE`.

- Simulation is never presented as a real Fabric, Azure, Foundry, Power BI or MCP operation.
- An approved live write is never silently redirected to a local simulation.
- The offline demo is a release gate: `make validate` runs it.

## Privacy and safety

- **Synthetic data only.** No PHI, no PII, no credentials, no customer identity.
- `ffia privacy scan` checks a salted, hashed denylist of customer-identifying terms, GUIDs,
  secret patterns and e-mail addresses. It runs locally and in CI.
- Live cloud mutations are never performed automatically. Writes follow PLAN → VALIDATE →
  APPROVE → EXECUTE → VERIFY → AUDIT.
- Preview capabilities stay behind feature flags and are never required for the default demo.
  See [`docs/research/ga-preview-matrix.md`](docs/research/ga-preview-matrix.md).

## Readiness

- **Ready to build and learn:** HC-01 and MFG-01 guides, synthetic data and offline demos.
- **Learning-repo scope:** the user confirmed the operational demo steps complete;
  they are not recurring production-certification gates.
- **Deferred:** Power BI report rendering/review and publication; see the
  [completion scope and backlog](docs/operations/delivery-backlog.md).
- **Instructions only:** Claude Code setup and the cross-harness comparison.

Offline validation does not prove current cloud health or production readiness.
See the [sharing scope](docs/operations/shareable-release.md) and
[readiness gates](docs/operations/use-case-readiness.md).

## License

[MIT](LICENSE)
