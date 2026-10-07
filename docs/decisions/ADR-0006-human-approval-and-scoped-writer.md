# ADR-0006: Human approval, scoped writer, and no silent LIVE → LOCAL redirect

- Status: Accepted
- Date: 2026-10-07

## Context

Agents can propose Fabric changes such as creating lakehouses and notebooks, uploading files,
editing semantic models and publishing reports. Model intent is not proof of user
authorization. An approved live change that silently ran against a simulation would report
success for something that never happened.

## Options

1. Let agents call write tools directly.
2. Approval prompts inside the agent harness only.
3. A deterministic change service: PLAN → VALIDATE → APPROVE → EXECUTE → VERIFY → AUDIT, with
   policy files, separation of duties and a narrowly scoped writer per destination.

## Decision

Use option 3 (`services/changes.py`).

- **PLAN** records:
  - risk, reversibility, expected impact, validation and rollback;
  - policy reasons;
  - a duplicate or existence precondition;
  - a destination hash.

  Policy violations and duplicates are `BLOCKED`.
- **APPROVE**:
  - the requester cannot approve their own change;
  - approvals expire after `approval_ttl_minutes`;
  - rejections are recorded.
- **EXECUTE** rechecks:
  - the approval matches the plan;
  - the destination hash is unchanged;
  - the precondition still holds.
- **LOCAL** destinations execute in a simulated workspace and are labeled `SIMULATED`.
- **LIVE** destinations need `FFIA_ALLOW_LIVE_MUTATION=1`, an approval and an authorized live
  writer.
  - No live writer exists before Phase 5, so an approved LIVE change returns `UNAVAILABLE`.
  - An approved LIVE change is **never** redirected to LOCAL.
- No MCP tool can approve or execute a change.

## Rationale

- Models propose, deterministic logic validates, policy constrains and humans approve.
- The destination hash and the precondition recheck catch target swaps and races between
  approval and execution.

## Trade-offs

- There are more steps than calling a tool directly. The demo shows that the extra friction is
  the point.

## Security impact

- Separation of duties, expiring approvals and tamper checks are enforced in code and covered by
  tests (`tests/unit/test_config_policy_changes.py`).
- The audit trail is redacted.

## Operations impact

- Policies live in `config/policies/writes.yaml`. Overlays can narrow `allowed_writes`, but they
  cannot remove approval.

## Offline impact

- The whole flow runs offline against the simulated workspace (offline demo act 5).

## Education impact

- L200 shows the flow, L300 breaks it (self-approval, duplicates, tampering), and L400 maps it
  to production identity.

## Revisit trigger

- Adding the Phase 5 live writer. It needs an Entra-scoped identity, an exact item-ID check and a
  verify step against the live item.

## Authoritative references

- `fabric-rest-identity`, `fabric-mcp-local` and `foundry-agent-service` in `docs/research/sources.yaml`
- [control-plane.md](../architecture/control-plane.md)
