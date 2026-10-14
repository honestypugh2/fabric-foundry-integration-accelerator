# Use-case readiness gates

**LOCAL acceptance contract.** Check what a guide's status actually covers. It does not certify
every service the guide mentions. A reviewed specification is not cloud-write approval.

| Gate | Acceptance evidence | Responsible role | Exclusions |
|---|---|---|---|
| Authoring ready | A third registered synthetic guide passes content checks, baseline reconciliation, real offline API tests, UI tests and an isolated contributor rehearsal | Repository maintainer | No live certification, model-performance claim or deployment |
| Connected workshop ready | Exact provider/server/tool calls, dated results, independent output checks and approval/audit for every mutation in the selected path | Facilitator and authorized operator | Metadata visibility is not notebook execution or publication |
| Production ready | Applicable identity, access, persistence, recovery, monitoring and release controls have evidence and owners | Deployment owner | Presenter-admin access and local JSONL are not production controls |

## Authoring acceptance criteria

1. Add a guide through the template and registries without branching frontend code by scenario.
2. Reuse existing patterns, lessons, diagrams and datasets when their contracts fit.
3. Supply outcome, audience, exclusions, theory, hypothesis, baseline and failure/recovery steps.
4. Resolve every baseline, diagram, lesson, presenter, skill and named MCP tool reference.
5. Validate malformed content, missing assets and unknown references as explicit failures.
6. Reconcile all nine synthetic quality counts exactly against the committed manufacturing
   baseline; a mismatch exits nonzero.
7. Exercise plan, separate approval, SIMULATED execution and audit through the real offline API.
   Reject self-approval and duplicate execution; do not claim a data correction occurred.
8. Discover and navigate the new guide in the shared workshop, including its review checkpoint.
9. Run without cloud configuration and with network access blocked in offline tests.
10. Record exact commands/results, revision and unresolved live/production gates.

The proof scenario is [DQ-01](../../guides/dq-01-synthetic-quality-investigation/README.md).
Requirements map to tests in the [authoring verification record](use-case-authoring-verification.md).
For delivery, follow [onboarding](use-case-onboarding.md), then the
[release gates](release-validation.md). Connected and production work follows its own approval
boundary and the [production checklist](../security/production-checklist.md).
