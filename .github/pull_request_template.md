## Summary

<!-- What changed and why. -->

## Execution labels

- [ ] Any new results or demo outputs carry LIVE / HYBRID / LOCAL / SIMULATED / MOCKED / PREVIEW / UNAVAILABLE labels
- [ ] No simulation is presented as a real cloud operation

## Checklist

- [ ] `make validate` passes locally
- [ ] `make privacy-scan` passes: no customer identity, GUIDs, secrets, e-mails, PHI or PII
- [ ] Tests added or updated; coverage stays at or above 85%
- [ ] New dependencies are the latest stable versions, pinned exactly, and lockfiles are updated
- [ ] Preview features stay behind feature flags and are not required by the default demo
- [ ] Docs, `sources.yaml` and ADRs are updated where relevant
- [ ] No live cloud mutation was performed without the documented approval flow
