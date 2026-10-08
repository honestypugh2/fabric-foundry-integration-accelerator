# LIVE, HYBRID and OFFLINE

How a request is served when services are healthy, slow or unavailable:

- reads may fall back to an approved local equivalent, with a visible label and reason;
- writes never fall back;
- client errors never trigger a fallback.

The configuration and mechanics are described in [resilience.md](resilience.md).

## Architecture

<!-- BEGIN GENERATED DIAGRAM: run `ffia diagrams render`; do not edit by hand -->

> Generated from [`education/architecture/views/live-vs-offline.yaml`](../../education/architecture/views/live-vs-offline.yaml). Edit the YAML, then run `ffia diagrams render`.

- **draw.io:** [diagrams/live-vs-offline.drawio](diagrams/live-vs-offline.drawio). Open it in draw.io desktop, diagrams.net or the VS Code Draw.io Integration extension. Page 1 is the full architecture; the next pages build it up one step at a time.
- **Interactive:** run `make run`, then open `http://localhost:5173/architecture/live-vs-offline` to build it step by step, trace requests, switch Executive to L400 and see live runtime state.

```mermaid
flowchart LR
  subgraph reads["Reads"]
    caller["Caller<br/><small>App, MCP tool or demo</small>"]
    router["Provider router<br/><small>Per-capability policy</small>"]
    breaker["Circuit breaker<br/><small>CLOSED, OPEN, HALF_OPEN</small>"]
    live["LIVE Fabric provider · tenant<br/><small>Timeout + bounded retries</small>"]
    fallback_policy["Fallback policy<br/><small>config/environments</small>"]
    local["Local Fabric provider<br/><small>Approved equivalent</small>"]
    envelope["Labeled result<br/><small>LIVE / LOCAL in HYBRID mode / UNAVAILABLE</small>"]
    audit["Audit and route decisions"]
  end
  subgraph writes["Writes - never fall back"]
    write_request["Approved LIVE write<br/><small>Plan + approval</small>"]
    live_writer["Live writer · tenant<br/><small>Authorized, narrowly scoped</small>"]
    simulated_workspace["Simulated workspace<br/><small>LOCAL rehearsals only</small>"]
    unavailable["UNAVAILABLE (HTTP 409)<br/><small>Plan again - nothing redirected</small>"]
  end
  caller -->|Typed read| router
  router -->|Allowed?| breaker
  breaker -->|Try LIVE| live
  router -.->|On failure| fallback_policy
  fallback_policy -.->|Approved fallback| local
  live -->|LIVE| envelope
  local -->|LOCAL (HYBRID mode, reason)| envelope
  envelope --> audit
  write_request -->|Execute| live_writer
  live_writer -->|Writer not available| unavailable
  class caller,router,breaker,fallback_policy,local,envelope,audit,write_request,simulated_workspace,unavailable implemented
  class live,live_writer tenant_validation
  classDef implemented stroke-width:2px
  classDef planned stroke-dasharray: 6 4
  classDef preview stroke-dasharray: 2 3
  classDef optional stroke-dasharray: 8 4
  classDef documented stroke-width:1px
  classDef tenant_validation stroke-dasharray: 3 3
```

Solid boxes are implemented here or documented by Microsoft; dashed boxes are planned, preview or optional.

### Workflow

*LOCAL.* Reads during a simulated outage - three failures open the breaker, the approved LOCAL equivalent answers with an honest label. Offline demo act 7.

1. The caller asks for the lakehouse tables.
2. The router applies the HYBRID policy for fabric_data.
3. The breaker is CLOSED, so the live call is allowed.
4. The live provider times out; a bounded retry fails too. In training the outage is injected with FFIA_SIMULATE_FABRIC_OUTAGE=1.
5. Reads may fall back in HYBRID; this is a provider failure, not a client error.
6. The approved LOCAL equivalent answers.
7. The result says LOCAL, mode HYBRID, fallback_used true, with the reason.
8. After three failures the breaker opens and later reads skip the live call until the reset timeout.

### Flow: Approved LIVE write, no writer

*SIMULATED.* Approval is not enough - without an authorized live writer the result is UNAVAILABLE and nothing runs locally instead. Offline demo act 5.

1. A LIVE plan was approved by a second person.
2. Execution needs an authorized, narrowly scoped live writer. None exists yet.
3. The result is UNAVAILABLE (HTTP 409) with redirected_to_local false.
4. The simulated workspace is untouched - the demo asserts it.

### Components

| Component | Status | Role | In this repository |
|---|---|---|---|
| Caller | Implemented in this repository | Any consumer of the control plane - the web app, an ffia-local tool or the offline demo. | - |
| Provider router | Implemented in this repository | Timeouts, retries and a circuit breaker per capability; writes never fall back. | `src/fabric_foundry_accelerator/fallback/router.py` |
| Circuit breaker | Implemented in this repository | Opens after three consecutive failures and skips the live call; after the reset timeout one trial call decides whether it closes again. | `src/fabric_foundry_accelerator/fallback/circuit_breaker.py` |
| LIVE Fabric provider | Requires tenant validation | Pick the narrowest server; they run with the caller's Fabric permissions; status differs by server. | `src/fabric_foundry_accelerator/providers/fabric/live.py` |
| Fallback policy | Implemented in this repository | Which capabilities may fall back in each environment. Unknown resources and invalid requests are client errors and never fall back. | `config/policies/fallback.yaml` |
| Local Fabric provider | Implemented in this repository | Read-only, allow-listed operations over synthetic Parquet; never presented as Fabric. | - |
| Labeled result | Implemented in this repository | Every result is an execution envelope with a label, the requested and selected provider, fallback_used and the reason. Non-cloud labels cannot claim a cloud operation. | `src/fabric_foundry_accelerator/models/execution.py` |
| Audit and route decisions | Implemented in this repository | Records share a correlation ID across plan, approval, execution and tool calls. | - |
| Approved LIVE write | Implemented in this repository | Separation of duties, expiry and destination binding protect the decision. | - |
| Live writer | Requires tenant validation | Least-privilege identity bound to specific targets; LIVE writes are never redirected to LOCAL. | `src/fabric_foundry_accelerator/providers/fabric/writer.py` |
| Simulated workspace | Implemented in this repository | Where LOCAL plans execute, labeled SIMULATED. An approved LIVE change is never redirected here. | `src/fabric_foundry_accelerator/services/changes.py` |
| UNAVAILABLE (HTTP 409) | Implemented in this repository | When no authorized live writer exists the result is UNAVAILABLE with redirected_to_local false, and the attempt is audited. | - |

### Aligned to

- [Azure Well-Architected Framework service guide for Microsoft Fabric](https://learn.microsoft.com/azure/well-architected/microsoft-fabric/overview) (GUIDANCE)
- [Baseline Microsoft Foundry chat reference architecture](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat) (GUIDANCE)

<!-- END GENERATED DIAGRAM -->
