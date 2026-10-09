# Foundry observability

[main.bicep](main.bicep) provisions workspace-based Application Insights, Log Analytics,
Foundry account/project connections, diagnostic settings and project reader roles.
Check for existing resources before deployment; use the governed approval flow.
The template is committed (it was already included in the live bake-off commit).

## Verified evidence

On 2026-10-09, read-only Azure checks observed existing monitoring resources with
`Succeeded` provisioning state, 30-day retention and a one GB/day ingestion cap.
Foundry had AppInsights connections and diagnostic settings for logs and metrics.
No deployment was performed by the assistant in this verification session.

With explicit approval, a synthetic client span was exported through the pinned Azure Monitor
OpenTelemetry exporter. An Application Insights query observed two matching synthetic records
after ingestion delay; successful query verification was recorded in the local audit.
This verifies **LIVE client telemetry ingestion**, not a new Foundry agent execution.
F8 remained paused. Server-side `sales-insights-agent` traces still require a new, approved live
agent run and a query verifying those traces.

## Operator walkthrough

1. In Azure, open Application Insights and its linked Log Analytics workspace.
2. In Foundry, open the project, Agents, then Traces; inspect the connected monitoring resource.
3. Query `dependencies`, `requests`, `traces` and `exceptions` over a bounded time range.
   Filter by synthetic span name or a run correlation ID before expanding details.
4. For application export, supply `FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING` through an
   ignored local environment file or secret manager. Never put it in a browser, transcript or Git.
5. Run an explicitly approved synthetic question, then verify its trace and audit correlation.

Connecting resources is not evidence that a trace arrived. Export completion is not ingestion
confirmation. Allow for ingestion delay and query actual records before claiming success.
An ingestion cap is not a guaranteed spending limit.
