# Resilience: LIVE, HYBRID and OFFLINE

The architecture must stay demonstrable when Fabric, Foundry, the network or a preview feature
is unavailable. It must do that **without hiding** what actually ran.

## Operating modes

| Mode | Fabric data | Writes | Typical use |
|---|---|---|---|
| `OFFLINE` | Local Fabric Educational Provider (DuckDB over synthetic Parquet) | LOCAL simulated workspace only | Laptops, workshops, CI and the release gate |
| `HYBRID` | LIVE when healthy; reads fall back to LOCAL data in `HYBRID` mode, with `fallback_used` and a reason | Never fall back | Live demos with a safety net |
| `LIVE` | LIVE only. Failures surface as `UNAVAILABLE`. | Need `FFIA_ALLOW_LIVE_MUTATION=1`, approval and an authorized writer | Tenant validation |

Select a mode with `FFIA_ENVIRONMENT=offline|hybrid|live`. Each capability is configured
separately in `config/environments/*.yaml`, and the rules live in
`config/policies/fallback.yaml`.

## Router behavior (`fallback/router.py`)

1. **Probe.** If the circuit breaker for the capability is `OPEN`, skip the live call.
2. **Call LIVE** with a per-capability timeout (`asyncio.timeout`). Retry with bounded
   exponential backoff and jitter (`tenacity`, `max_retries`, `backoff_seconds`).
3. **Classify the error.**
   - `UnknownResourceError` and invalid requests are **client errors**. They are returned as-is
     and never retried or redirected, because a missing table is not an outage.
   - Timeouts and `ProviderUnavailableError` count against the breaker.
4. **Fallback (reads only).** Use the approved LOCAL equivalent if the environment allows it.
   The envelope keeps `execution_label=LOCAL` (the data really is local) and records
   `operating_mode=HYBRID`, `fallback_used=true`, the `fallback_reason`, and the requested and
   selected providers.
5. **No fallback allowed.** Raise `CapabilityUnavailableError`, which the API returns as
   **503** and the UI shows as `UNAVAILABLE`.
6. **Circuit breaker.**
   - `CLOSED`: the breaker opens after `failure_threshold` consecutive failures.
   - `OPEN`: after `reset_timeout_seconds` the breaker moves to `HALF_OPEN` and allows one
     trial call.
   - A successful trial closes it; a failed trial opens it again.

`RouteDecision` records the outcome (`LIVE`, `FALLBACK` or `UNAVAILABLE`), attempts, latency and
breaker state. The offline demo shows it in act 7. `/api/v1/runtime/providers` reports whether
each provider is ready, including a live provider that the breaker is currently blocking.

## Writes never fall back

A write approved for **LIVE** is never executed against the LOCAL simulation. If the live writer
is unavailable, the result is `UNAVAILABLE` and the requester must create a new plan. See
[ADR-0006](../decisions/ADR-0006-human-approval-and-scoped-writer.md).

## Practicing failure

```bash
FFIA_ENVIRONMENT=hybrid FFIA_SIMULATE_FABRIC_OUTAGE=1 ffia demo offline
```

- `SimulatedOutageFabricProvider` stands in for an unreachable live Fabric endpoint (error and
  timeout variants).
- Act 7 of the offline demo shows reads falling back with labels, the breaker opening after
  three failures, and the last read skipping the live call.

## Evidence categories

| Statement | Category |
|---|---|
| Fallback labeling, the breaker and write refusal | SIMULATED LOCALLY (tests in `tests/unit/test_router.py`, offline demo act 7) |
| Live Fabric REST or MCP failure modes and throttling | REQUIRES TENANT VALIDATION (Phase 5) |
| Retry budgets for production | PRODUCTION RECOMMENDATION: tune per API from observed throttling responses |
