# ADR-0015: Offline-first security and evaluated release artifacts

- Status: Accepted
- Date: 2026-10-09

## Context

A demo's successful live call does not establish production readiness. Releases need
deterministic correctness, privacy and supply-chain checks without tenant secrets.

## Options

Publish automatically after a build; require live services for CI; or gate artifacts on
offline quality, evaluation, dependency/privacy checks and CodeQL.

## Decision

Reuse quality CI for docs and offline gates. Add two-language CodeQL and a gated artifact
workflow. Generate CycloneDX SBOMs/checksums; leave publication/deployment to human operators.

## Rationale

Offline CI is reproducible and does not incur cloud operations. The agent's five-case baseline
gate rejects wrong/ungrounded/fallback answers. Separate tenant checks remain mandatory.

## Trade-offs

Passing analysis is not proof of zero CodeQL alerts; branch protection and triage are operator
responsibilities. SBOMs describe dependencies, not security certification or signed provenance.

## Security impact

Immutable action SHAs, non-persisted checkout credentials and scoped permissions.
Only CodeQL jobs receive security-events write; release jobs cannot publish or deploy.

## Operations impact

Run `make validate` and `make sbom`. Review gated artifacts, licenses and checksums before
publication; preserve actual CI results and residual risks.

## Offline impact

Quality/evaluation/demo gates require no tenant. Dependency audits need public vulnerability
feeds, not Azure access.

## Education impact

Teach the distinction between tested LOCAL behavior, dated LIVE evidence and production checks.

## Revisit trigger

Production hosting, authenticated multi-user approvals, signed provenance, regulated data,
or automated authoritative delivery.

## Authoritative references

Registry entries `github-codeql-configuration`, `foundry-evaluators`, `fabric-waf`,
`foundry-mcp-governance`; ADR-0006, ADR-0008 and ADR-0013.
