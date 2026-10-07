# ADR-0005: Provider ports, router and approved read fallback

- Status: Accepted
- Date: 2026-10-07

## Context

Demos and workshops must keep working when Fabric, Foundry or the network is unavailable.
Silently replacing live results with local ones would teach the wrong lesson and could mislead
decisions.

## Options

1. Use the cloud SDKs directly in domain code, and fail when they are unavailable.
2. A mock switch per call site.
3. Provider ports with injected LIVE, LOCAL and fault-injection adapters, behind a router that
   enforces the environment's fallback policy.

## Decision

- Use option 3.
- Domain services depend on async ports (`FabricProvider`).
- `ProviderRouter` (in `fallback/router.py`) applies:
  - a timeout for each capability;
  - bounded retries with exponential backoff and jitter (`tenacity` 9.2.1);
  - a circuit breaker for each capability (CLOSED → OPEN → HALF_OPEN).
- Only **reads** may fall back to the approved LOCAL equivalent. A fallback result keeps the
  `LOCAL` execution label and carries `operating_mode=HYBRID`, `fallback_used` and
  `fallback_reason`.
- Client errors, such as an unknown resource or an invalid request, never trigger a fallback.
- When fallback is not allowed, the result is `UNAVAILABLE` (HTTP 503).

## Rationale

- One place to reason about failure, which is also one place to test.
- Labels keep the audience and the audit trail honest.
- Treating client errors separately stops a typo from looking like an outage.

## Trade-offs

- More indirection than calling SDKs directly.
- Retry budgets are educational defaults. Production values need tenant measurements.

## Security impact

- Fallback cannot widen access, because the LOCAL provider exposes only allow-listed reads over
  synthetic data.
- Writes never use the router's fallback path.

## Operations impact

- Behavior is configured in `config/environments/*.yaml` and `config/policies/fallback.yaml`.
- `/api/v1/runtime/providers` and `ffia demo check` report readiness.

## Offline impact

- `OFFLINE` mode needs no live provider.
- `FFIA_SIMULATE_FABRIC_OUTAGE=1` injects failures for teaching.

## Education impact

- Offline demo act 7 and the L300 and L400 resilience content use this router.

## Revisit trigger

- Live Fabric providers (Phase 5) show throttling or partial-failure modes that the classifier
  does not cover.

## Authoritative references

- `fabric-rest-identity` and `fabric-mcp-servers-list` in `docs/research/sources.yaml`
- [resilience.md](../architecture/resilience.md)
