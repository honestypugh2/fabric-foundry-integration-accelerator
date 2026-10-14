# Resume later: connected work and release follow-up

**Operator decision:** share the learning repository now; postpone HC-01 live end-to-end
completion and Claude Code setup/execution. HC-01 and MFG-01 remain the two featured guides.
DQ-01 remains a supporting exercise. Nothing is removed because it is deferred.

Review this tracker at the next working session. It is not approval for any cloud operation.
Refresh service state, exact private bindings and approval windows before resuming; prior
creation, landing and publication approvals must not be reused for new actions.

## Priority 1: HC-01 live completion — intentionally deferred

- [ ] Verify the tool-reported Bronze publication: persisted reviewed code, exact notebook
  identity and default lakehouse binding. Complete the correlated publication receipt/audit.
- [ ] Refresh capacity/readiness and establish the Microsoft Fabric Runtime kernel.
- [ ] Obtain separate approval for one Bronze run; execute once and independently verify
  seven persisted Delta tables against the source baseline.
- [ ] Review Silver rules, author and verify the draft, separately approve publication and
  execution, then reconcile seven typed row-preserving tables and diagnostic counts.
- [ ] Review Gold grains/keys, author and verify the draft, separately approve publication
  and execution, then reconcile six Gold tables and four dimensions.
- [ ] Verify all 24 lab tables, financial totals, key relationships and synthetic readmissions
  against the independent baseline; do not change the baseline to hide a mismatch.
- [ ] Bootstrap and connect the exact Direct Lake semantic model; inspect its seven tables.
- [ ] Review/apply approved relationships and measures, then reconcile DAX results.
- [ ] Record model best-practice/AI-readiness findings; approve and recheck any fixes.
- [ ] Establish the supported report authoring/preview environment (the current guide marks
  Windows required), build the two pages, validate and separately approve publication.
- [ ] Run final read-only acceptance checks and publish a sanitized outcome matrix.

**Starting evidence:** lakehouse creation, seven-file landing and remote hash readbacks were
verified LIVE; profiling and the reference build passed LOCAL. One native Bronze scaffold
was independently verified, its four-cell local draft passed schema/syntax/source checks, and
the native publication tool reported success. Persisted published code/binding and runtime
outputs have not yet been independently verified. No HC Delta output, model or report is
certified as a live outcome.

## Priority 2: Claude Code — instructions now, execution later

- [ ] Follow the existing client/MCP setup instructions in a private, isolated context.
- [ ] Verify instruction loading, relevant skill discovery and narrow MCP capability access.
- [ ] Execute equivalent bounded Copilot and Claude tasks against the same baseline.
- [ ] Compare correctness, evidence, approval behavior, recovery and effort with recorded
  limitations; do not substitute a model comparison inside Copilot CLI.
- [ ] Update the documented-only labels only after actual client execution is verified.

The [Claude prompt pack](../../prompts/claude-code/patterns.md),
[MCP/client setup](../../config/mcp/README.md) and existing guide-specific alternate prompts
remain available now. No comparative Claude Code run or superiority claim is made.

## Priority 3: other connected demonstrations — deferred

- [ ] Diagnose MFG revenue timeout/input-length rejection without accidental duplicate inference.
- [ ] Approve any new bounded inference explicitly; reconcile revenue/growth and recover
  final assistant answers, not just tool payloads.
- [ ] Verify connected quality categories required by the selected demonstration.
- [ ] Verify the actual GitHub Copilot CLI and GitHub.com/app/cloud-agent workflows used
  for the demonstration; distinguish configured tools from executed tasks.

**Boundary:** the recovered PREVIEW duplicate-count tool payload matched 12. This does not
certify the final assistant answer, all nine live quality categories or service health.

## Priority 4: production acceptance — separate scope

- [ ] Agree whether recurring scheduling/delivery is required and its approval scope.
- [ ] Verify production identity, permissions, network controls and authoritative write service.
- [ ] Verify monitoring, alerts, failure handling, rollback and recovery evidence.
- [ ] Inspect actual capacity, billing and cost evidence with a separately agreed scope.
- [ ] Review a production acceptance matrix. A teaching demo is not production certification.

## Sharing release follow-up

- [ ] Review the rendered customer and SE/developer playbooks with the intended audiences.
- [ ] Walk the new-use-case authoring path from a clean checkout or disposable environment.
- [ ] Inspect actual GitHub workflow results for that commit; configured CI is not run evidence.

Commit/push is part of the current sharing pass, approved after LOCAL validation passed.
If that pass is interrupted, compare the local commit, remote branch and worktree before
retrying; do not assume the package is either published or unpublished from this tracker alone.

See [sharing scope](shareable-release.md), [current verification](use-case-authoring-verification.md)
and [release procedure](release-validation.md). Operational receipts, tenant-specific
bindings, raw tool responses and session notes remain private and ignored.
