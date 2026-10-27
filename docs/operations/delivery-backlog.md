# Learning-repo completion and backlog

Status recorded on 2026-10-26. All data and demonstration metrics are synthetic.
This is a solution accelerator and learning repository, not a production workload.
Deferred work is not completed or passed work.

## Current completion scope

The user confirmed that the four operational items below were already completed
and instructed that they must not be reopened as repository-completion gates.
This records user-confirmed completion, not a new independent tenant verification
or a claim that every historical automated check is now green.

Preserve the existing React/backend architecture and personal settings. Finish the
repository documentation and reviewed commit/push without repeating live runs,
inferences, browser-outage checks, or settings changes.

Report rendering remains deferred by user decision; do not install a Chromium
runtime to unblock it. For production adaptation, follow Microsoft's
[Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
and [Microsoft Fabric workload guidance](https://learn.microsoft.com/azure/well-architected/microsoft-fabric/overview),
also linked in the [main README](../../README.md).

Report rendering and its dependent publication are not gates for the current
repository/demo handoff. This scope exception does not certify the report or the
complete published Power BI workflow.

## User-confirmed completed scope

- [x] Authorized LIVE writer and six-measure correction work.
- [x] Manufacturing answer-gap work on existing resources.
- [x] Settings-portability work while preserving personal skill access.
- [x] Visible-browser backend-unavailable feedback work.

These items are closed for this learning-repo handoff based on the user's
confirmation. Earlier receipts retain the outcomes of their specific attempts;
they are not being rewritten as evidence of new operations. Do not automatically
repeat these steps to obtain production-style certification.

## Repository closeout

- Add the main README's explicit not-for-production disclaimer and Microsoft
  Well-Architected references.
- Keep report rendering/publication in the deferred backlog below.
- Reuse existing test evidence; check source-registry freshness, privacy, links,
  and whitespace for this documentation closeout.
- Commit and push the reviewed repository scope. Exclude private bindings,
  screenshots, and unrelated personal settings. This is a learning-repo
  checkpoint, not production acceptance.

## Deferred Power BI work

- [ ] **Report rendering and screenshot review -- DEFERRED BY USER.**
  - **LOCAL evidence:** the two-page, 34-visual draft passed Microsoft report CLI
    0.5.0 validation with zero errors and zero warnings. Saved geometry checks
    passed. These checks do not prove actual rendering.
  - **Observed blocker:** service preview open returned `HOST_UNAVAILABLE` with
    `browser_not_installed`. No report was rendered and no screenshots or
    workflow-owned screenshot directory were created.
  - **Constraint:** do not install Chromium or silently change preview hosts.
  - **Future route:** assess an existing Windows Power BI Desktop environment
    with supported preview tooling. This is a candidate route, not a verified
    available host. Confirm the host and screenshot destination before resuming.
  - **Completion:** validate the latest PBIR, load it in the agreed supported
    host, capture and review both pages, and verify slicers and population
    semantics after the persisted measure correction. Clean up only the exact
    workflow-owned validation screenshot directory.
- [ ] **Report publication and published readback -- DEPENDENT / DEFERRED.**
  Rendering review and model acceptance must pass first. Then perform duplicate
  checks, present the exact publication plan, obtain separate human approval,
  publish, and verify exactly one report with the intended model binding.
  A local PBIP or an existing semantic model is not publication evidence.

## Explicitly out of scope

The actual Copilot-versus-Claude bake-off and live Claude demonstrations are
excluded, not pending delivery gates. Existing alternative-pattern documentation
remains. Optional integrations are not default acceptance prerequisites.

See the [Power BI build area](../../powerbi/README.md),
[phase verification](phase-verification.md), and
[release gates](release-validation.md).
