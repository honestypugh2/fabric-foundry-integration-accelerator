# Production checklist

Status: **PRODUCTION RECOMMENDATION / REQUIRES TENANT VALIDATION**.
Offline CI is necessary but insufficient for a production release. Record evidence and an owner
for every applicable item; an unchecked item is not an implied pass.

## Identity, access and data

- [ ] Replace presenter/admin identities with least-privilege workload identities.
- [ ] Authenticate/authorize the API and approvers before any network exposure; enforce TLS.
- [ ] Verify RLS/OLS, workspace/item permissions and denial cases with multiple non-admin users.
- [ ] Bind approvals to the authenticated user, exact plan hash/scope, expiry and permitted writer.
- [ ] Keep credentials in managed secret storage; rotate and test revocation.
- [ ] Approve data classification, residency, retention and legal rights for external sources.
- [ ] Prevent prompts/documents/tool responses from crossing into authority or executable commands.

## Quality, reliability and operations

- [ ] Define production baselines, thresholds, representative evaluation and injection test cases.
- [ ] Keep preview capabilities feature-flagged with tested, honestly labeled fallback.
- [ ] Exercise retries, outages, quota exhaustion and no-fallback LIVE failures.
- [ ] Verify client AND server trace ingestion with a new approved synthetic run.
- [ ] Review exporter payloads, retention and access; no prompts or secrets in default traces.
- [ ] Replace local JSONL with protected, durable audit; monitor approvals/writes and alert on abuse.
- [ ] Validate budget alerts, cost ownership and pause/resume runbooks; caps are not spending limits.
- [ ] Rehearse rollback/recovery against an isolated development workspace before authoritative writes.

## Supply chain and release

- [ ] Require quality, privacy, dependency audit and both CodeQL language checks on protected branches.
- [ ] Enable and triage secret/dependency/code-scanning alerts; resolve HIGH/CRITICAL before release.
- [ ] Inspect SBOMs, checksums, license obligations and action/dependency changes.
- [ ] Require a human-reviewed release; do not deploy from arbitrary PR code or inherited cloud secrets.
- [ ] Record exact revision, commands/results, environment and exclusions in the release evidence.
- [ ] Verify both guides, architecture visuals and offline presentation on the presenter device.

Claude Code remains **DOCUMENTED ONLY**. Copilot model runs are not evidence of Claude Code
behavior. Fabric capacity remains paused until an operator separately approves its use.

See [threat model](threat-model.md) and [release validation](../operations/release-validation.md).
