# Resume later: connected work and release follow-up

**Plan:** share the learning repo now. Complete HC-01 live work and Claude Code setup later.
HC-01 and MFG-01 stay featured. DQ-01 stays as a supporting exercise.

Pick up this list at the next working session. It does not approve a cloud operation.
Recheck the service, target and approval window before resuming.
Do not reuse an earlier approval for a new action.

## Priority 1: finish HC-01 live work later

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

## Priority 2: Claude Code instructions now, execution later

- [ ] Follow the existing client/MCP setup instructions in a private, isolated context.
- [ ] Verify instruction loading, relevant skill discovery and narrow MCP capability access.
- [ ] Run equivalent bounded GitHub Copilot and Claude Code tasks against the same baseline.
- [ ] Compare correctness, evidence, approval behavior, recovery and effort with recorded
  limitations; do not substitute a model comparison inside GitHub Copilot CLI.
- [ ] Update the documented-only labels only after actual client execution is verified.

The [Claude prompt pack](../../prompts/claude-code/patterns.md),
[MCP/client setup](../../config/mcp/README.md) and existing guide-specific alternate prompts
remain available now. No comparative Claude Code run or superiority claim is made.

## Priority 3: finish the connected demonstrations later

- [ ] Diagnose MFG revenue timeout/input-length rejection without accidental duplicate inference.
- [ ] Approve any new bounded inference explicitly; reconcile revenue/growth and recover
  final assistant answers, not just tool payloads.
- [ ] Verify connected quality categories required by the selected demonstration.
- [ ] Verify the actual GitHub Copilot CLI and GitHub.com/app/cloud-agent workflows used
  for the demonstration; distinguish configured tools from executed tasks.

**Boundary:** the recovered PREVIEW duplicate-count tool payload matched 12. This does not
certify the final assistant answer, all nine live quality categories or service health.

## Priority 4: agree the production scope

- [ ] Agree whether recurring scheduling/delivery is required and its approval scope.
- [ ] Verify production identity, permissions, network controls and authoritative write service.
- [ ] Verify monitoring, alerts, failure handling, rollback and recovery evidence.
- [ ] Inspect actual capacity, billing and cost evidence with a separately agreed scope.
- [ ] Review a production acceptance matrix. A teaching demo is not production certification.

## Sharing release follow-up

- [ ] Review the rendered customer and SE/developer playbooks with the intended audiences.
- [ ] Walk the new-use-case authoring path from a clean checkout or disposable environment.
- [ ] Inspect actual GitHub workflow results for that commit; configured CI is not run evidence.

The first sharing package was committed and pushed as `83117e6`. That commit passed LOCAL
validation, and the remote branch matched. Check the current local and remote commits before
releasing another version.

## GitHub-friendly playbooks and hosting

- [ ] Generate Markdown companion pages from the same playbook YAML. These will render
  directly in GitHub and stay consistent with the downloadable HTML.
- [ ] Decide whether to publish the static playbooks through GitHub Pages. Review repo
  visibility, permissions, links and deployment approval before enabling it.
- [ ] If hosting is approved, add a narrow static-site workflow and verify the actual published
  pages. Do not deploy the API or include private files in the site.
- [ ] Set the repo's About website field only after a working site has been verified.

**Use now:** download an HTML file and open it in a browser. GitHub's file view shows source,
not the rendered page. Hosting remains a later task; nothing was deployed by this edit.

See [sharing scope](shareable-release.md), [current verification](use-case-authoring-verification.md)
and [release procedure](release-validation.md). Operational receipts, tenant-specific
bindings, raw tool responses and session notes remain private and ignored.
