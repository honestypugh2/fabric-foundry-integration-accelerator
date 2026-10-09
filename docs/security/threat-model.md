# Threat model

Status: **PRODUCTION RECOMMENDATION**, with repository controls tested **LOCAL**.
Scope: the local frontend, API, typed MCP server, provider router, approval/audit flow,
Fabric/Foundry adapters, agent workflows, skills and build pipeline. This is a design model,
not a penetration test or a claim of production certification.

## Assets and trust boundaries

Assets: tenant credentials, governed context and permissions, model/tool outputs, change-plan
integrity, approval identity, audit/trace evidence, source/lockfiles and release artifacts.
Only synthetic data belongs here; customer material and bindings stay outside committed files.

```text
Presenter/browser -> loopback educational API -> domain services -> provider ports
                                                |                  |
                                                |                  +-> Entra -> Fabric/Foundry
                                                +-> plan/validate -> human -> scoped writer
Coding assistant -> reviewed skills/instructions -> allow-listed MCP tools
                         (untrusted outputs are data, not approval)
Domain services -> local audit + opt-in telemetry
Source/lockfiles -> read-only CI -> quality/security gates -> SBOMs + artifacts
```

Each arrow crosses a trust boundary. MCP grants capability access, not authority.
An administrator's session is not an appropriate production workload identity.

## Abuse cases, controls and proof

| Risk | Implemented control | Repository evidence | Remaining production work |
|---|---|---|---|
| Prompt injection through documents, websites or tool output | Narrow typed tools; model proposals cannot approve/execute; deterministic validation | `tests/unit/test_mcp_server.py`, `tests/unit/test_harness.py` | Content isolation, adversarial testing, safe external-data retrieval and egress policy |
| Unauthorized or confused-deputy writes | Read-only defaults, explicit mutation opt-in, approval and scoped writer; no silent LIVE write fallback | ADR-0006, ADR-0012, harness policy and change-flow tests | Authenticate approvers, bind identity/scope/expiry, independent writer identity and audit sink |
| Privilege escalation or RLS bypass | Live identity passthrough and authorization remain Fabric's responsibility; no model-granted rights | `fabric-rest-identity`, `foundry-fabric-tool` source entries | Test positive AND negative access with distinct non-admin users; verify RLS/OLS for each source |
| Token, customer or prompt leakage | Ignored bindings, secret settings, privacy scan; agent spans omit question text | `tests/unit/test_tracing.py`, privacy CI job | Secret rotation, log/exporter review, retention, private networking and DLP |
| Evidence spoofing or simulation mistaken for LIVE | Execution envelopes expose label/provider/fallback; graders reject fallbacks; recorded runs preserve provenance | `tests/unit/test_router.py`, `tests/unit/test_agent_eval.py`, `tests/unit/test_bakeoff.py` | Durable tamper-evident audit; signing and access controls for evidence |
| Incorrect business numbers or automatic remediation | Exact baseline/grounding gates; monthly workflow produces drafts and holds mismatches; no delivery | `tests/unit/test_agent_eval.py`, `tests/unit/test_agent_workflows.py` | Customer-approved baselines, drift monitoring, rollback and transaction reconciliation |
| Arbitrary SQL/shell/filesystem access | Local MCP manifest has no generic shell, SQL, fetch or proxy tool; harness denies dangerous commands | `tests/unit/test_mcp_server.py`, `tests/unit/test_harness.py` | Process/container sandbox, filesystem isolation; client guards are not a security sandbox |
| Malicious dependency, skill or CI action | Exact dependencies/locks, immutable action SHAs, reviewed pinned skills, audits and CodeQL | quality/CodeQL workflows, `tests/unit/test_ci_workflows.py`, `tests/unit/test_mcp_profiles.py` | Registry controls, provenance verification, branch protection and alert triage |
| Denial of service or runaway cost | MCP rate limits, bounded retries/timeouts/circuit breakers; live agent serialization | `tests/unit/test_mcp_server.py`, `tests/unit/test_router.py` | Service quotas, admission control, budget alerts and load tests; an ingestion cap is not a cost ceiling |
| Exposed demo API or forged local approval | Loopback use documented; no cloud credentials in browser | Runtime settings and ADR-0006 | API authentication/authorization, CSRF/session protection, TLS and gateway BEFORE remote exposure |

## Explicit exclusions and residual risks

- The local API is **not** a production-authenticated authorization service. Do not expose it
  publicly or treat its approval fields as proof of a real user's identity.
- Local append-only JSONL is useful teaching evidence, not immutable regulated audit storage.
- Shell/client hooks are defense in depth, not isolation against a malicious local process.
- Preview Fabric data-agent/knowledge paths need tenant-specific access and availability tests.
- Client telemetry ingestion was verified on 2026-10-09. New server-side agent tracing was not.
- Publicly accessible web content is not automatically licensed for reuse; review terms,
  copyright, robots guidance and privacy. No generic web scraper is exposed by this repository.

## Review and response

Revisit on a new provider/tool, write capability, identity flow, data class or deployment boundary.
If a leak or unauthorized action is suspected: stop the affected workload, disable its access,
preserve bounded evidence without copying secrets, involve the security owner, rotate credentials
and reconcile actual resource state before restarting. Do not erase audit evidence.

References: registry entries `mcp-specification`, `foundry-mcp-governance`,
`foundry-agent-identity`, `fabric-rest-identity`, `foundry-fabric-tool`, `fabric-waf`,
`github-codeql-configuration`; [authority ADR](../decisions/ADR-0007-mcp-access-is-not-authority.md).
