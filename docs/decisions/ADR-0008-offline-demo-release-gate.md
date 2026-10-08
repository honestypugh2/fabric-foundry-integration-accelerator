# ADR-0008: The offline demo is a release gate

- Status: Accepted
- Date: 2026-10-07

## Context

The accelerator is presented live, sometimes without a working tenant or network. A demo that
breaks at the moment it is presented costs credibility. A demo that hides simulation costs
trust.

## Options

1. Do manual dry runs before each event.
2. Use a recorded video as the fallback.
3. Use an automated ten-act offline demo that must pass in CI and `make validate`.

## Decision

Use option 3. `ffia demo offline` (in `services/demo.py`) runs the ten acts against the real
services in `OFFLINE` mode. It fails when any of these happen:

- a required act fails;
- any act reports a LIVE or cloud operation;
- a label is dishonest.

Acts that depend on later phases, such as Foundry in act 6, are reported as `UNAVAILABLE` and
are optional. They are never simulated as the real service. `make validate` runs the gate, and
`tests/offline` runs it with sockets blocked.

## Rationale

- It catches regressions in the story as well as in the code.
- Honesty is tested: the gate checks the labels as well as success.

## Trade-offs

- It adds about 10 s to validation.
- Act content must change when phases add capabilities.

## Security impact

- None. The demo is offline and uses only synthetic data.

## Operations impact

- Run `make demo-check` and then `make demo-offline` before every session. See
  [demo-continuity.md](../operations/demo-continuity.md).

## Offline impact

- This is the definition of the offline guarantee.

## Education impact

- The ten acts follow the Executive story and link to the L100–L400 content.

## Revisit trigger

- ~~Phase 6 makes act 6 available locally through an offline Foundry simulation.~~ Done in Phase 6,
  without simulating Foundry: act 6 runs the deterministic LOCAL agent, labeled LOCAL, and is
  required ([ADR-0013](ADR-0013-foundry-agents-evaluation-tracing.md)).

## Authoritative references

- [demo-continuity.md](../operations/demo-continuity.md)
