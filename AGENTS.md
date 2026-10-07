# AGENTS.md — Fabric Foundry Integration Accelerator

This is the single source of truth for every coding agent working in this repository
(GitHub Copilot in VS Code, Copilot CLI, the Copilot app, the Copilot cloud agent, and
Claude Code). `CLAUDE.md` imports this file; `.github/copilot-instructions.md` summarizes it.

## 1. What this repository is

A reusable, customer-neutral reference implementation and teaching platform for
**Microsoft Fabric + Microsoft Foundry** integration. It covers:

- Fabric MCP, Fabric Skills, Fabric IQ and Fabric Data Agents
- Agent Framework
- GitHub Copilot and Claude Code
- medallion architecture and Open Mirroring recovery
- human-in-the-loop actions and evaluation
- offline-first demos and Executive-to-L400 education

Central lesson:

- Fabric provides governed business context.
- Foundry turns that context into reasoning, orchestration, evaluation and action.
- **MCP standardizes capability access; it does not grant authority.**
- Entra identity and policy determine authority.
- Business systems remain the authority for transactional writes.

## 2. Repository map

| Path | Purpose |
|---|---|
| `src/fabric_foundry_accelerator/` | Python package (`ffia` CLI, providers, API, MCP server, …) |
| `tests/` | `unit/`, `contract/`, `offline/`, `security/`, `evaluation/`, `integration/` (opt-in live) |
| `frontend/` | React + TypeScript + Vite educational application |
| `config/` | Customer overlays, environments, MCP profiles, policies, providers, privacy denylist |
| `data/synthetic/` | Synthetic medallion data (raw → bronze → silver → gold → semantic → recovery) |
| `education/`, `docs/`, `demos/`, `prompts/` | Structured learning content, documentation, demos, prompt packs |
| `guides/` | Customer-neutral Use-Case Guides (e.g., `hc-01-…`); each guide has its own scoped `AGENTS.md` |
| `notebooks/`, `powerbi/`, `fabric/workspace/` | Fabric notebooks, PBIP/TMDL, Fabric Git-format items |
| `docs/research/sources.yaml` | Authoritative source registry → rendered `source-validation.md` |

## 3. Build, test and validate

Python uses **uv**. Always create and **activate** the virtual environment before installing:

```bash
uv venv --python 3.14 .venv
source .venv/bin/activate
uv sync --frozen            # install exactly what uv.lock specifies
```

| Task | Command |
|---|---|
| Everything (CI equivalent) | `make validate` |
| Python lint / format | `ruff check src tests` · `ruff format src tests` |
| Python types (strict) | `pyright` |
| Python tests + coverage (≥85%) | `pytest --cov` |
| Frontend | `cd frontend && npm ci && npm run lint && npm run typecheck && npm run test:coverage && npm run build` |
| Privacy scan | `ffia privacy scan` |
| Demo | `ffia demo check` · `ffia demo offline` (release gate) |
| Control plane | `ffia serve api` · `ffia serve mcp` (stdio) |
| JSON Schemas, OpenAPI, frontend API types | `ffia schemas export` (after model changes) · `ffia schemas check` |
| Education content | `ffia education check` · frontend fixtures: `make fixtures` (after API model changes) |
| Run the app | `make run` (API on :8000 + frontend on :5173) |
| Source registry | `ffia sources render` (after editing `sources.yaml`) · `ffia sources check` |
| Synthetic data | `ffia data generate --check` · `ffia data build` (Bronze → Silver → Gold + baseline) · `ffia data export --profile <id> --dest <dir>` |
| Recovery drill | `ffia recovery run` (Open Mirroring snapshot + replay, SIMULATED) |

## 4. Dependency rules

- Latest **stable** releases only. No preview, beta, alpha or RC packages for core functionality. No deprecated packages.
- **Exact pins** (`==` in `pyproject.toml`, `--save-exact` in npm). No wildcards, no ranges. Commit `uv.lock` and `frontend/package-lock.json`.
- Add a dependency **only in the change that first uses it**, after checking:
  - latest stable version
  - supported runtime (Python 3.14 / Node 24+)
  - maintenance status
  - known HIGH/CRITICAL vulnerabilities (none allowed)
- Add Python packages with `uv add <pkg>==<version>` inside the activated venv. Add npm packages with `npm install --save-exact`.
- Documented exception: TypeScript is pinned to 6.0.3 because `typescript-eslint` 8.71.x supports `<6.1.0`.

## 5. Code conventions

**Python**

- `src` layout; full type annotations; Pyright strict; Ruff (Google docstrings).
- Pydantic models at external boundaries; `pathlib`; UTC-aware datetimes.
- Explicit exceptions; dependency injection.
- No business logic in route handlers; no global cloud clients; no import side effects.
- No broad `except Exception` outside controlled translation boundaries.
- No hard-coded IDs or endpoints.
- Comments explain *why*.

**TypeScript/React**

- Strict mode; typed API contracts; feature-oriented folders; accessible semantic HTML; keyboard navigation; explicit loading, error and offline states.
- No `any`; no `dangerouslySetInnerHTML`; no secrets or credentials in the browser; no business rules duplicated from the backend.

## 6. Safety and authority rules (non-negotiable)

1. Models propose. Deterministic logic validates. Policy constrains.
2. Humans approve any of the following:
   - high-impact actions
   - destructive actions
   - regulated actions
   - financially material actions
   - difficult-to-reverse actions
3. Only a narrowly scoped, authorized service performs authoritative writes.
4. **MCP access is not authorization. Model intent is not proof of user authorization.**
5. Default to **read-only**. Every mutation follows: PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT → (ROLLBACK).
6. Check for duplicates before creating any resource. Confirm the exact tenant, workspace and item IDs before any write.
7. **Never** silently redirect an approved LIVE write to LOCAL simulation.
8. **Never perform live Fabric/Azure/Foundry mutations automatically** while building this repository.
9. Never expose arbitrary shell, SQL, filesystem, URL fetch or REST-proxy tools through MCP.

## 7. Evidence rules

- Label every result with an execution mode: `LIVE`, `HYBRID`, `LOCAL`, `SIMULATED`, `MOCKED`, `PREVIEW` or `UNAVAILABLE`.
- Before each cloud operation, state the **provider, server and actual tool** used.
- These are not evidence:
  - a configured MCP server is not evidence of a call;
  - a tool description is not evidence of invocation;
  - an item's existence is not evidence of execution;
  - matching byte size is not a content hash;
  - a local PBIR file is not publication;
  - an editor or portal run is not an MCP job.
- If a required tool is unavailable, report the limitation and stop. Do not silently substitute REST, CLI or a different tool for a step assigned to a specific tool.
- Never print tokens or secrets. Never enable token-bearing debug output.

## 8. Provider and MCP selection

- Domain logic depends on provider **ports**; LIVE/LOCAL/MOCK adapters are injected.
- The router probes, applies timeouts, bounded retries and circuit breakers, then applies the approved fallback policy.
- Pick the **narrowest** MCP server and tool set for the job:
  - local Fabric MCP docs tools for *how*;
  - read-only remote tools for *what is*;
  - Git/PR or the approved change flow for *change it*.
- Do not conflate different Fabric MCP servers. Pin external server versions.

## 9. Privacy (absolute)

- **Synthetic data only.** No PHI, no PII, no credentials, no secrets.
- **No customer identity:** no names, abbreviations, employee names, domains, URLs, tenant/workspace/capacity IDs, screenshots, emails, customer-unique source-system names, or customer source-document titles.
- Real environment identifiers live only in git-ignored files (`.env*`, `*.local.yaml`, `*.local.json`).
- Customer source material stays outside the repository. Use-Case Guides are sanitized re-expressions.
- Run `ffia privacy scan` before committing. It checks a salted, hashed denylist, GUIDs, secret patterns and e-mail addresses.
- No clinical diagnosis, treatment advice or real clinical quality measures. Label demonstration metrics as synthetic.

## 10. Live environment

- Live work targets the presenter's Microsoft demo tenant, signed in as its admin account (`az login`, VS Code sign-in).
- Identifiers are never committed.
- Admin rights do not change the rules above: every write still requires an explicit plan and approval.
- Prefer a dedicated **dev** workspace for labs.
- `make demo-check` verifies each service rather than assuming it is available.

## 11. Preview features

Preview features (for example Fabric IQ, ontology, the Foundry Fabric data agent tool, Data Warehouse MCP and hosted Power BI authoring MCP):

- stay behind `preview_feature_flags`;
- are labeled `PREVIEW` in the UI and in results;
- have an offline simulation;
- are **never required** by the default demo.

## 12. Education

- Every major capability and pattern teaches **Executive, L100, L200, L300 and L400** levels.
- Labs follow LEARN → SEE → BUILD → INSPECT → BREAK IT → RECOVER → VERIFY → GO DEEPER → TRY WITH COPILOT → TRY WITH CLAUDE CODE → PRODUCTION NOTES.
- Learning content is structured data under `education/`, not hard-coded UI copy.
