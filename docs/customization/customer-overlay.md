# Customer overlays and Use-Case Guide intake

The baseline accelerator is customer-neutral. Overlays and Use-Case Guides **add** to the
baseline; they never change it.

## Customer overlay (`config/customers/<alias>.yaml`)

An overlay is validated by `CustomerOverlay` (`schemas/customer-overlay.schema.json`). It
declares:

| Field | Purpose |
|---|---|
| `alias`, `industry`, `scenario`, `description`, `synthetic: true` | Fictional identity. Real names never appear. |
| `fabric_workspace_aliases`, `foundry_project_aliases` | Aliases only. Map them to real IDs in a git-ignored `<alias>.local.yaml`. |
| `allowed_reads`, `allowed_writes` | Restrict the global policy. They cannot widen it. |
| `required_approvals` | Approvers and the reason for each write operation |
| `feature_flags`, `preview_feature_flags` | Preview features default to `false` and are labeled `PREVIEW`. `FFIA_PREVIEW_FEATURES=<flag>[,<flag>]` turns flags on for one process without changing the file; unknown names fail at startup. |
| `synthetic_dataset`, `guides`, `learning_modules`, `demo_sequence` | What the demo and education surfaces show |
| `evaluation_thresholds`, `recovery_objectives`, `retention_assumptions`, `compliance_notes` | Evidence gates and assumptions |

Select an overlay with `FFIA_OVERLAY=<alias>`.

- Loading fails for any of these:
  - an overlay that is not marked `synthetic: true`;
  - an unknown dataset profile;
  - malformed aliases;
  - approval rules for operations that are not in `allowed_writes`.
- At plan time, the policy engine blocks:
  - operations that are not in `allowed_writes`;
  - undeclared workspace aliases.
- Every write still requires human approval (`config/policies/writes.yaml`). An overlay can
  narrow what is allowed but can never remove the approval step.

Add an overlay:

1. Copy `config/customers/example-healthcare.yaml` to `config/customers/<new-alias>.yaml`, and
   use a fictional alias.
2. Put real tenant, workspace and capacity identifiers **only** in
   `config/customers/<new-alias>.local.yaml`, which is git-ignored.
3. Run `ffia schemas check`, `pytest` and `ffia privacy scan`.

## Use-Case Guide intake

Guides live in `guides/<industry-code>-<nn>-<slug>/` and are validated by `UseCaseGuide`
(`schemas/use-case-guide.schema.json`).

1. **Receive.** Keep the source material **outside** the repository. Never commit or link it.
2. **Sanitize.** Rewrite the guide in your own words.
   - Remove customer names, abbreviations, people, document titles, URLs, domains, tenant,
     workspace or capacity identifiers, and source-system names.
   - Add new identifying terms to the hashed denylist (`ffia privacy add-terms`, which reads terms from stdin), never in
     plain text.
3. **Map.**
   - Link each step to catalog patterns (`education/patterns/catalog.yaml`) and maturity
     levels.
   - For each step, declare whether it writes, its tool, its approval and its
     `offline_equivalent`.
   - For write steps, add a `rehearsal` (operation, item type, item name) when the policy has a
     matching operation. The guide runner rehearses it against the simulated workspace.
4. **Scaffold.** Copy `guides/_template/guide.yaml`. Add guide-scoped `AGENTS.md`,
   `CLAUDE.md` and `.mcp.json` when the guide needs different tools.
5. **Validate.** The loader rejects:
   - a write step that does not require approval;
   - unknown patterns or dataset profiles;
   - a guide ID that does not match its folder;
   - duplicate step IDs;
   - steps with no `evidence_required` or no `offline_equivalent`.

   Run `pytest tests/unit/test_patterns_guides.py` and `ffia privacy scan`.
6. **Register.** Add the guide ID to the overlays that use it, then update `guides/README.md`.

A guide may add patterns, prompts, data profiles or labs. It must not change baseline behavior,
policies or defaults. If it needs a different behavior, add it as an opt-in option.
