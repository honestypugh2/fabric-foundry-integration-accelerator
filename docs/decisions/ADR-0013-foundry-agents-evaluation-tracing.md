# ADR-0013: Foundry agents behind a provider port, deterministic agent evaluation, opt-in tracing, Agent Framework workflows

- Status: Accepted
- Date: 2026-10-08
- Extends ADR-0005 (provider router) and ADR-0008 (offline demo release gate)

## Context

Phase 6 connects the accelerator to Microsoft Foundry without weakening the offline default.
Five facts shaped it:

- **A live Foundry agent exists in the presenter's demo tenant.** `sales-insights-agent` uses the
  Fabric data agent tool (preview) over the synthetic `mfg-sales-v1` lakehouse. Its answers
  matched the baseline when called directly through the SDK during Guide MFG-01 preparation.
- **Live agent calls are slow and metered.** The first call took about 2.5 minutes; later calls
  took 30–60 seconds. The Fabric capacity must be running for the tool to answer.
- **The default demo must stay offline.** Act 6 of the offline demo was UNAVAILABLE because
  nothing may be simulated as Foundry.
- **Agent answers carry business numbers.** A fluent answer with a wrong number is worse than no
  answer, so correctness must be checked against the governed baseline, not judged by a model.
- **Agent Framework packaging.** `agent-framework-core` 1.21.0 is stable with stable
  dependencies. `agent-framework-foundry` 1.14.1 requires `azure-ai-projects<2.8.0` (the project
  pins 2.8.0) and the pre-release `azure-ai-inference` 1.0.0b9. The dependency rules forbid
  pre-release packages for core functionality.

## Options

1. Call Foundry directly from routes and the CLI.
2. Use `agent-framework-foundry` for both agents and orchestration.
3. **An `AgentProvider` port with a deterministic LOCAL agent and a Foundry adapter on
   `azure-ai-projects`, routed by capability. Orchestration on `agent-framework-core` only.**

## Decision

Option 3.

- **Port.** `AgentProvider.ask(AgentQuestion) -> ExecutionEnvelope[AgentAnswer]`. An answer
  records its tool calls and whether a governed data tool grounded it.
- **LOCAL agent.** `LocalSalesAgent` answers allow-listed questions with DuckDB over the synthetic
  data, labeled LOCAL. Unsupported questions get an honest "not answerable offline" reply and the
  supported list. It never imitates a model.
- **Foundry adapter.** `FoundryAgentProvider` calls an existing agent version through the
  project's Responses API (`azure-ai-projects` 2.8.0, imported lazily). The result is labeled
  PREVIEW when a preview tool ran, otherwise LIVE. It is built only when all three hold:
  - `FFIA_FOUNDRY_LIVE=1`;
  - the environment is hybrid or live;
  - the git-ignored overlay has a `foundry:` binding.
- **Routing.** Capability `foundry_agent`:
  - offline: LOCAL;
  - hybrid: live with a 240 s timeout and labeled fallback to LOCAL;
  - live: no fallback.
- **Evaluation.** `config/evaluations/<suite>.yaml` lists questions, expected baseline values and
  whether grounding is expected. `run_suite` checks both and gates on `min_pass_rate`. The same
  suite runs against LOCAL (5/5 in CI) and the live agent (opt-in). Foundry's cloud evaluators
  stay complementary and opt-in (`foundry-evaluators`).
- **Tracing.** Each routed ask runs in an OpenTelemetry span `ffia.agent.ask`. Attributes:
  correlation ID, provider, label, fallback, tools, grounding, agent and question length. **The
  question text is never recorded.** Export to Application Insights through the Azure Monitor
  distro is opt-in through the secret `FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING`.
- **Orchestration.** The `monthly-insights` workflow (`agent-framework-core`):
  1. `select` chooses the teams;
  2. one `draft` executor per team asks the routed agent; the fan-out runs concurrently;
  3. a deterministic `review` gate holds any draft that is ungrounded or missing the team's
     baseline revenue or target attainment.

  **Delivery is not performed.** Sending briefs is a governed write (PLAN → APPROVE → EXECUTE →
  AUDIT).
- **Surfaces.** CLI: `ffia agents ask|eval|workflow`. API:
  - `GET /api/v1/agents/{agent}`;
  - `POST /api/v1/agents/ask`;
  - `POST /api/v1/agents/evaluate`;
  - `POST /api/v1/agents/workflows/monthly-insights`.

  The `/agent` page shows the label, provider, fallback, grounding and tool calls for every
  answer.

## Rationale

- The port keeps domain code, the demo and the UI independent of the SDK. The live path can
  change (SDK, preview tool, Agent Framework adapter) without touching callers.
- Grounding and baseline matching are the checks that matter for business numbers, and both are
  deterministic and fast. CI can gate on them with no cloud access.
- Using only `agent-framework-core` gives real Agent Framework workflows today without a
  pre-release dependency or a downgrade of `azure-ai-projects`.
- A workflow that ends in "ready for approval" teaches the central lesson: models propose,
  deterministic logic validates, humans approve.

## Live verification

- **VERIFIED LIVE (2026-10-08, SDK script outside the repository):** the Foundry agent with the
  Fabric data agent tool reproduced these baseline values:
  - Enclosures +55.78%;
  - 12 duplicate order lines;
  - September booked revenue $509,726.22.
- **REQUIRES TENANT VALIDATION:**
  - `FoundryAgentProvider` through the router (`FFIA_ENVIRONMENT=hybrid FFIA_FOUNDRY_LIVE=1
    ffia agents ask …`);
  - `ffia agents eval` against the live agent;
  - the workflow over the live agent;
  - Application Insights export.

  Each needs the Fabric capacity running, which has a cost.

## Trade-offs

- The LOCAL agent answers only five question shapes. That is deliberate: it is a teaching analog
  of a grounded tool call, not a language model.
- Baseline matching checks values, not prose quality. Fluency, tone and safety belong to
  Foundry's evaluators.
- The Azure Monitor distro pulls beta instrumentation packages transitively. The code uses only
  the stable OpenTelemetry API and SDK directly. Revisit when the distro's instrumentations go
  stable.
- Live drafts run concurrently, but each still takes 30–150 seconds. The talk tracks show one live
  brief and the LOCAL workflow for all teams.

## Security impact

- The Foundry adapter uses a tenant-pinned `AzureCliCredential` (the presenter's Entra sign-in).
  No keys exist in code or config. Production should use a managed identity.
- Agent access to Fabric is the user's identity through the data agent connection
  (on-behalf-of). **MCP and tool access are not authorization.**
- The workflow cannot send anything. Delivery stays a governed write.
- Spans exclude question text. The App Insights connection string lives only in `.env.local`.

## Operations impact

- `ffia foundry readiness` checks the resource, project, agent and connection read-only.
- The router's timeout and fallback make a slow or unavailable Foundry visible (labeled fallback)
  instead of failing the demo.

## Offline impact

- Act 6 of the offline demo now runs the LOCAL agent and is required (10/10 acts).
- With `FFIA_FOUNDRY_LIVE` unset, the container never builds a Foundry client.

## Education impact

Lessons on the enterprise agent (P06), evaluation and observability (P16) and the Fabric/Foundry
boundary now describe the implemented agent, evaluation, tracing and workflow, with honest labels.

## Revisit trigger

- A stable `agent-framework-foundry` compatible with the pinned `azure-ai-projects`. At that point,
  consider replacing the hand-written Foundry adapter.
- The Fabric data agent tool reaching GA.
- Stable Azure Monitor instrumentations.

## Authoritative references

`foundry-agent-service`, `foundry-fabric-tool`, `foundry-evaluators`, `agent-framework`,
`agent-framework-workflows`, `azure-monitor-opentelemetry`, `foundry-human-in-the-loop`
(see `docs/research/sources.yaml`).
