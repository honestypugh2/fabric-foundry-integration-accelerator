# Security policy

## Reporting a vulnerability

Report vulnerabilities **privately** through GitHub's private vulnerability reporting: open the
repository's **Security** tab and choose **Report a vulnerability**.

- Do not open public issues for security problems.
- Never include real customer data, credentials or tenant identifiers in a report.

## Security posture

| Control | How it is applied |
|---|---|
| Synthetic data | No PHI, PII or customer identity in the repository |
| Leak scanning | `ffia privacy scan` checks a hashed denylist, GUIDs, secrets and e-mail addresses locally and in CI |
| Dependencies | Exact pins and committed lockfiles; CI fails on HIGH/CRITICAL vulnerabilities (`pip-audit`, `npm audit`) |
| CI hardening | Actions pinned by commit SHA; least-privilege `permissions:` |
| Writes | Read-only by default; live mutations need explicit plan, approval, verification and audit |
| MCP | MCP access is not authorization; tool allow-lists, narrow servers and pinned versions |
| Credentials | Entra ID via `DefaultAzureCredential` or managed identity; no secrets in code or in the browser |

The full threat model is published in `docs/security/threat-model.md` (Phase 8).
