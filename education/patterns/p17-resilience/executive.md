## Why it matters

Live demos and live operations fail in the same ways: a slow endpoint, an expired sign-in, a
throttled API, a preview feature switched off. Pattern P17 keeps the experience running **without
hiding what actually ran**.

| Mode | What runs | When to use it |
|---|---|---|
| `OFFLINE` | Local, synthetic equivalents only; labeled `LOCAL` or `SIMULATED` | Workshops, laptops, CI, the release gate |
| `HYBRID` | Live services when healthy; **reads** fall back to local equivalents, visibly labeled with a reason | Live demos with a safety net |
| `LIVE` | Live services only; failures show `UNAVAILABLE` | Tenant validation and production |

## The three non-negotiables

1. **Degradation is visible.** A fallback read says so, and says why.
2. **Writes never fall back.** An approved change to a live system is never quietly performed
   against a simulation instead. It fails as `UNAVAILABLE`, and a new plan is required.
3. **Mistakes are not outages.** Asking for a table that does not exist returns an error; it does
   not trigger a fallback that would mask the mistake.

## What keeps it stable

- **Timeouts** stop one slow service from freezing everything.
- **Bounded retries** absorb brief glitches without hammering the service.
- **Circuit breakers** stop calling a service that keeps failing, then test it again later.

**Decision for leaders:** which capabilities may degrade to a labeled local equivalent in which
environment — and the rule that writes and approvals never do.

## Status

The router, breaker and labeled fallback are **SIMULATED LOCALLY** and proven by the offline
release gate (`ffia demo offline`). A live, read-only Fabric connection now exists as an opt-in,
but how real Fabric behaves under failure and throttling still requires validation in a tenant.
