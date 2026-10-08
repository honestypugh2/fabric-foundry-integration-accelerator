# Fabric Foundry Integration Accelerator

A reusable, customer-neutral **reference implementation, pattern catalog, workshop and demo
environment** for integrating **Microsoft Fabric** and **Microsoft Foundry**. It covers:

- **Fabric:** Fabric MCP, Fabric Skills, Fabric IQ, Fabric Data Agents
- **Agents and AI coding tools:** Microsoft Agent Framework, GitHub Copilot, Claude Code
- **Data engineering:** medallion architecture, Open Mirroring recovery
- **Governance and evidence:** human-in-the-loop actions, evaluation and observability

> **Fabric provides governed business context. Foundry turns that context into reasoning,
> orchestration, evaluation, and action. MCP standardizes access to capabilities. Enterprise
> identity and policy determine authority. Deterministic validation and human oversight
> constrain high-impact actions. Observability and evaluation provide evidence. Offline
> resilience ensures the architecture can always be demonstrated and taught.**

Learn it · See it · Build it · Run it · Break it · Recover it · Inspect it · Evaluate it ·
Customize it · Productionize it — in one project, with **synthetic data only**.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Research + architecture | ✅ Complete |
| 1 | Repository foundation: uv/Python, React/TS/Vite, instructions, docs, quality tooling, CI | ✅ Complete |
| 2 | Offline-first data foundation (synthetic medallion, recovery fixtures, Local Fabric Provider, dataset profiles) | ✅ Complete |
| 3 | Application control plane (FastAPI, FastMCP, providers, router, circuit breaker, approvals, audit) | ✅ Complete |
| 4 | Interactive educational application (explorers, learning paths, labs, guides, demo mode) | ✅ Complete |
| 5 | Fabric integration (live read-only provider, gated writer, MCP profiles, skills, reference notebooks) | ✅ Complete |
| 6 | Foundry integration (agent port, LOCAL + Foundry agents, evaluation, tracing, Agent Framework workflow, Foundry IQ knowledge analog behind a preview flag) | ✅ Complete offline; live router path REQUIRES TENANT VALIDATION |
| 7 | GitHub Copilot + Claude Code (skills, prompt packs, bake-off) | Planned |
| 8 | Security, CI/CD and production readiness | Planned |
| 9 | Final validation | Planned |

Use-Case Guides under `guides/`: **HC-01** (Fabric MCP + Power BI medallion lab, healthcare,
synthetic) and **MFG-01** (Foundry + Fabric sales insights, manufacturing, synthetic).

Workshop talk tracks (presenter scripts with portal, VS Code, web app and offline paths, generated
from YAML with `ffia talktracks render`, also linked from the app's Demo page):

- **Guide 1:** [Leveling up Fabric data engineering with GitHub Copilot](demos/fabric-copilot-level-up/index.html)
- **Guide 2:** [Foundry + Fabric agent workshop](demos/foundry-fabric-agents-workshop/index.html)
  (manufacturing, synthetic; offline commands `ffia mfg brief`, `ffia mfg quality`,
  `ffia agents ask|eval|workflow`, and the app's Agent page)
- Morning setup: [demos/MORNING-RUNBOOK.md](demos/MORNING-RUNBOOK.md)

## Quick start

Prerequisites:

| Tool | Version | Notes |
|---|---|---|
| uv | 0.12.23 | Python package manager |
| Python | 3.14 | `uv python install 3.14` |
| Node.js | 24 LTS | Node 26 also tested |
| Git | any recent | |
| GNU Make | any recent | |

```bash
# Backend: always create and activate the virtual environment before installing
uv venv --python 3.14 .venv
source .venv/bin/activate
uv sync --frozen

# Frontend
cd frontend && npm ci && cd ..

# Validate everything (lint, types, tests + coverage, privacy scan, build, dependency audit)
make validate
```

Try the offline data path (no cloud access needed):

```bash
make data            # build Bronze/Silver/Gold for every profile and validate against expected baselines
make recovery-demo   # Open Mirroring snapshot + incremental + restore drill (SIMULATED)
```

Run the control plane and the demo (still offline, labeled LOCAL or SIMULATED):

```bash
make demo-check      # probe Fabric, Foundry, MCP, dataset, API and frontend; recommend a mode
make demo-offline    # ten-act release gate (must print "Release gate: PASSED")
make run-api         # FastAPI control plane on http://127.0.0.1:8000 (OpenAPI at /docs)
make run-mcp         # local educational MCP server (stdio), also registered in .mcp.json as ffia-local
make run             # API + educational app on http://localhost:5173 (Guide HC-01 runner at /guides)
```

Architecture diagrams (draw.io, Azure Architecture Center style, generated from YAML) are in
[`docs/architecture`](docs/architecture/README.md) and interactive in the app at `/architecture`.

See [control plane](docs/architecture/control-plane.md), [frontend](docs/architecture/frontend.md),
[resilience](docs/architecture/resilience.md), [demo continuity](docs/operations/demo-continuity.md)
and [learning paths](docs/education/learning-paths.md).

Run `make help` for every target. Targets for later phases print the phase in which they become
available.

## Repository map

| Path | Contents |
|---|---|
| `src/fabric_foundry_accelerator/` | Python package and `ffia` CLI |
| `tests/` | Unit, contract, offline, security, evaluation and opt-in live tests |
| `frontend/` | React + TypeScript + Vite educational application |
| `config/` | Customer overlays, environments, MCP profiles, policies, providers, privacy denylist |
| `data/synthetic/` | Synthetic data: raw → bronze → silver → gold → semantic → recovery |
| `education/`, `docs/`, `demos/`, `prompts/` | Learning content, documentation, demos, Copilot and Claude Code prompt packs |
| `guides/` | Customer-neutral Use-Case Guides |
| `notebooks/`, `powerbi/`, `fabric/workspace/` | Fabric notebooks, PBIP/TMDL, Fabric Git-format items |
| `docs/research/` | `sources.yaml` → `source-validation.md`, GA/preview matrix |
| `docs/decisions/` | Architecture decision records |

## Agent instructions

- [`AGENTS.md`](AGENTS.md) is the single source of truth for coding agents.
- [`CLAUDE.md`](CLAUDE.md) imports it for Claude Code.
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) summarizes it for GitHub
  Copilot.
- The root [`.mcp.json`](.mcp.json) is the portable MCP configuration shared by VS Code, Copilot
  CLI and Claude Code. It contains the Microsoft Learn documentation server and the local
  educational server `ffia-local`, rendered from the default profile in
  [`config/mcp/profiles.yaml`](config/mcp/profiles.yaml). Opt-in Fabric MCP and Power BI Modeling
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

## License

[MIT](LICENSE)
