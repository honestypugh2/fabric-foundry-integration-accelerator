# GitHub Copilot instructions

**Read `AGENTS.md` first.** It is the authoritative instruction set for this repository. This
file summarizes the rules that matter most when Copilot generates or changes code here.

- **Architecture:** Fabric provides governed context. Foundry provides reasoning,
  orchestration, evaluation and action. MCP provides capability access, not authority.
  Entra identity and policy provide authority.
- **Python:** Python 3.14 with uv. Create and activate `.venv` before installing anything
  (`uv venv --python 3.14 .venv && source .venv/bin/activate && uv sync --frozen`).
  - Add packages with `uv add <pkg>==<exact-version>`, latest stable only.
  - Pyright strict, Ruff, pytest with at least 85% coverage, Pydantic at boundaries.
  - No business logic in routes.
- **Frontend:** React + TypeScript (strict) + Vite only.
  - Exact npm pins, latest stable, accessible semantic HTML.
  - No `any`, no `dangerouslySetInnerHTML`, no credentials in the browser.
- **Privacy:** synthetic data only.
  - Never write customer names, abbreviations, people, domains, URLs, GUIDs, tenant,
    workspace or capacity identifiers, emails, PHI, PII or secrets.
  - Run `ffia privacy scan` before proposing a commit.
- **Providers:** domain code depends on provider ports. Every result carries an execution label
  (`LIVE`, `HYBRID`, `LOCAL`, `SIMULATED`, `MOCKED`, `PREVIEW`, `UNAVAILABLE`).
  - Never present simulation as a real Fabric, Azure, Foundry, Power BI or MCP operation.
  - Never silently turn a LIVE write into a LOCAL one.
- **MCP:** pick the narrowest server and tools. State the provider, server and tool before
  any cloud operation.
  - A configured server, a tool description or an existing item is not evidence that an
    operation ran.
- **Writes:** read-only by default. Follow PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT.
  - Check for duplicates first.
  - Never perform live cloud mutations automatically.
- **Preview features:** keep them behind feature flags, label them, simulate them offline,
  and never require them for the default demo.
- **Testing:** add or update tests with every behavior change.
  - Offline tests must pass with no Azure configuration.
  - Live tests are opt-in (`-m live`).
- **Documentation:** update the directly related docs. Edit `docs/research/sources.yaml`, then
  run `ffia sources render`.
- **Education:** content lives in `education/` as structured data covering Executive, L100,
  L200, L300 and L400.
