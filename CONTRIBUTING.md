# Contributing

Thank you for improving the Fabric Foundry Integration Accelerator.

## Ground rules

1. **Synthetic data only.**
   - Never commit customer names, abbreviations, people, domains, URLs, tenant, workspace or
     capacity identifiers, e-mail addresses, PHI, PII, credentials or secrets.
   - Run `make privacy-scan` before every commit.
2. **Customer-derived content becomes a sanitized Use-Case Guide.**
   - Keep source documents outside the repository.
   - Re-express their content in your own words.
   - Hash identifying terms into `config/privacy/denylist.yaml` with
     `uv run ffia privacy add-terms`, which reads from stdin and never writes plaintext.
3. **Latest stable, exact-pinned dependencies only**, added in the change that first uses them.
   - Python: activate `.venv`, then `uv add <pkg>==<version>`.
   - Frontend: `npm install --save-exact`.
   - Commit both lockfiles.
4. **Never perform live cloud mutations** from tests, scripts or agents without the documented
   approval flow.
5. **Label execution honestly**: `LIVE`, `HYBRID`, `LOCAL`, `SIMULATED`, `MOCKED`, `PREVIEW` or
   `UNAVAILABLE`.

## Workflow

```bash
uv venv --python 3.14 .venv && source .venv/bin/activate && uv sync --frozen
cd frontend && npm ci && cd ..
make validate
```

- Add or update tests with every behavior change. Backend and frontend coverage must stay at or
  above 85%.
- Record significant decisions as ADRs in `docs/decisions/` using the template sections listed in
  that folder's README.
- When you rely on a new authoritative source, add it to `docs/research/sources.yaml` and run
  `make sources`.
- Keep `AGENTS.md` authoritative. Client-specific files (`CLAUDE.md`,
  `.github/copilot-instructions.md`) stay thin.
