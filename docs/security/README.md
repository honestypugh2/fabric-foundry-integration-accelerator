# Security and production readiness

This is a synthetic, local-first teaching application, not an internet-facing production
control plane. Passing its offline gates does not certify a tenant or authorize cloud writes.

- [Threat model](threat-model.md): assets, trust boundaries, abuse cases, controls and residual risks.
- [Production checklist](production-checklist.md): tenant-specific work before go-live.
- [Release operations](../operations/release-validation.md): CI, SBOMs, evaluation gates and evidence.
- [Harness policy](../../config/harness/policy.yaml): client safeguards and approvals.

**LOCAL checks:** `make validate` and `make sbom`. **DOCUMENTED BEHAVIOR:** CodeQL and release
workflows are defined in Git; a workflow definition is not evidence of a successful GitHub run.
Live validation remains opt-in and requires its own scope, identity and approval.
