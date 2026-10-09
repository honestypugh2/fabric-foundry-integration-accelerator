# Release validation

Status: **DOCUMENTED BEHAVIOR** for CI; run results are separate evidence.
The workflows never deploy Azure/Fabric resources or publish a package automatically.

## Gates

| Surface | Gate |
|---|---|
| Python/frontend | Strict types, lint/format, tests with >=85% coverage, distribution/bundle build |
| Documentation and demos | Sources, education (30/30 completeness), diagrams, schemas, notebooks, MCP, skills, talk tracks, prompts, bake-off and harness drift checks; offline demo |
| Evaluation | `ffia agents eval --suite sales-insights-agent`: 100% of five baseline cases; expected grounding and out-of-scope refusal; fallbacks fail |
| Privacy/dependencies | Privacy scan; pip-audit fails on any reported vulnerability; npm audit fails on HIGH/CRITICAL |
| Static security | CodeQL Python and JavaScript/TypeScript, security-extended queries, push/PR/weekly/manual |
| Release | Reuses quality and CodeQL; only then builds Python/frontend artifacts, CycloneDX SBOMs and SHA-256 checksums |

The existing [quality workflow](../../.github/workflows/quality.yml) owns docs and offline-demo
gates; separate duplicate workflows are unnecessary.
[CodeQL](../../.github/workflows/codeql.yml) needs GitHub code-scanning availability.
Successful analysis/upload does not mean zero alerts: enable branch code-scanning protection
and review alerts before publication.
[Release artifacts](../../.github/workflows/release.yml) run on version tags or manual dispatch.
They have no package/release publishing or cloud deployment authority. Artifacts expire after
14 days; a human reviews them and publishes a release separately.

## Local verification

Activate the existing virtual environment; restore dependencies only if missing:

```bash
source .venv/bin/activate
make validate
make sbom
```

For a fresh environment, use the setup in `AGENTS.md`. Live credentials are not required.
The evaluation gate explicitly selects offline providers. CI has no Azure configuration.
Default offline tests reject live execution; tenant tests remain opt-in.

`sbom/python.cdx.json` describes the installed Python environment (including developer tools).
`sbom/frontend.cdx.json` describes frontend runtime and developer dependencies. The full
inventory avoids npm production-only filtering omitting shared runtime/peer packages.
`make sbom` validates both CycloneDX schemas and checks every exact runtime manifest pin.
The verifier canonicalizes npm's GitHub SCP-style VCS references to SSH URIs, preserving
other metadata; npm otherwise emits references rejected by the strict CycloneDX schema.
Neither is a security attestation: review scanner findings and license obligations independently. Keep generated
SBOMs/builds ignored locally; the release workflow uploads only builds, SBOMs and checksums,
never bindings, runtime traces, audit files or private source material.

## Publishing checklist

1. Select a reviewed revision and confirm required quality/CodeQL checks actually succeeded.
2. Run local validation when feasible; record exact commands, results and remaining gaps.
3. Inspect SBOM format/components and verify `sha256sum -c release-SHA256SUMS.txt` from the
   extracted artifact root.
4. Verify both guides in offline mode; do not represent recorded LIVE replays as new cloud calls.
5. Get release-owner approval, publish reviewed artifacts, and preserve evidence.
6. Before live use, complete the [production checklist](../security/production-checklist.md).

Failure in an evaluation, privacy scan or security gate blocks release. Do not bypass a hook,
downgrade a threshold or silently substitute simulated results to make the pipeline green.

## Verified LOCAL results (2026-10-09)

In the activated virtual environment:

```bash
FFIA_ENVIRONMENT=offline FFIA_FABRIC_LIVE=0 FFIA_FOUNDRY_LIVE=0 \
  FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING='' make validate
```

**PASSED**, including:

- Python: 581 passed, one opt-in live integration test skipped; 96.10% coverage.
- Frontend: 81 passed; 98.74% statement and 86.19% branch coverage.
- Python/TypeScript strict checks, lint/format and both builds passed.
- Privacy: zero findings. pip-audit: no known vulnerabilities. npm audit: zero vulnerabilities.
- Education: 16 lessons at five levels, 100 checks; 30/30 completeness.
- LOCAL agent evaluation: 5/5, no fallback. Offline demo: passed.
- All generated source/schema/diagram/MCP/notebook/skill/talk-track/prompt/harness checks passed.
- Bake-off: five tasks, ten recorded runs valid; Claude Code remains documented-only.
- `make sbom`: passed; valid schemas and runtime pins, 163 Python and 345 frontend components.

Workflow syntax also passed with checksum-verified actionlint 1.7.12:

```bash
actionlint -shellcheck= .github/workflows/quality.yml .github/workflows/codeql.yml .github/workflows/release.yml
```

ShellCheck was disabled for this syntax check. This is not an actual GitHub workflow run or
CodeQL analysis. The first GitHub quality/CodeQL/release executions, production checklist and
new server-side Foundry trace verification remain outstanding. No new deployment, capacity
resume, package publication or cloud write was performed during final LOCAL validation.
