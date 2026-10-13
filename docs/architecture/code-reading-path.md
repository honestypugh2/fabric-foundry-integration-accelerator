# Read the implementation one boundary at a time

**LOCAL code orientation.** This tracked guide is available in every clone.
It does not publish the git-ignored interactive resource or claim cloud execution.
Start with the [quick start](../../README.md#quick-start) and [graphical map](repository-map.md).

## A vertical reading path

| Order | Read | Question |
|---|---|---|
| 1. Contracts | [ExecutionEnvelope](../../src/fabric_foundry_accelerator/models/execution.py), [FabricProvider](../../src/fabric_foundry_accelerator/providers/fabric/port.py) | What enters/exits, and which execution claims are rejected? |
| 2. Local implementation | [LocalFabricProvider](../../src/fabric_foundry_accelerator/providers/fabric/local.py), [pipeline](../../src/fabric_foundry_accelerator/synthetic/pipeline.py) | Does the capability and baseline work without cloud configuration? |
| 3. Composition | [build_container](../../src/fabric_foundry_accelerator/services/container.py), [settings](../../src/fabric_foundry_accelerator/config/settings.py) | Where are clients, stores, policies and clocks injected? |
| 4. Routing/authority | [Read router](../../src/fabric_foundry_accelerator/fallback/router.py), [ChangeService](../../src/fabric_foundry_accelerator/services/changes.py) | Which reads may fall back, and why are writes separate? |
| 5. Transport | [API factory](../../src/fabric_foundry_accelerator/api/app.py), [routes](../../src/fabric_foundry_accelerator/api/routes.py), [local MCP](../../src/fabric_foundry_accelerator/mcp/server.py) | Does the surface validate/delegate rather than duplicate rules? |
| 6. Browser | [Client](../../frontend/src/api/client.ts), [hooks](../../frontend/src/api/hooks.ts), [Evidence page](../../frontend/src/features/workshop/EvidencePage.tsx) | How does unknown JSON become validated data and explicit UI states? |
| 7. Proof | [Envelope tests](../../tests/unit/test_execution_envelope.py), [router tests](../../tests/unit/test_router.py), [API tests](../../tests/unit/test_api.py) | Which passing and failure cases prove the boundary? |

## Trace a teaching request

Evidence page → `useWorkshop` → validated API client →
`GET /api/v1/education/workshop` → `EducationService.workshop` →
validated content and registry-derived coverage.

Read [the service](../../src/fabric_foundry_accelerator/services/education.py) and
[workshop content](../../education/workshop.yaml). Reading historical evidence is LOCAL,
not a fresh tenant probe. See [the separate integration paths](integration-paths.md).

## Choose the code shape

- **Function:** transformation or factory with explicit inputs/outputs; start here.
- **Dataclass:** related trusted internal values; it does not validate external input.
- **Pydantic model:** runtime validation and request/result/configuration invariants.
- **Protocol:** a capability with interchangeable LOCAL/LIVE/fake adapters.
- **Class:** meaningful shared state, dependencies or lifecycle, such as breaker history or
  plans/approvals. Avoid unrelated utility-manager classes.
- **React function/hook:** presentation or browser lifecycle, not cloud authority.

Annotate Python parameters/returns and model fields. Type ambiguous locals such as empty
collections or optional values; infer obvious locals. TypeScript cannot validate received
JSON by annotation alone: use `unknown` and runtime schemas, not `any` or unsafe casts.

## A small build loop

1. State an outcome and a failing acceptance case.
2. Define the typed request/result and invariant.
3. Implement deterministic logic with an injected local/fake adapter.
4. Prove it offline before adding transport/UI.
5. Wire one thin surface; update structured teaching and related documentation.
6. Regenerate schemas/types/fixtures after contract changes and test dependent views.
7. Add LIVE only when needed; verify the exact provider/tool separately.

Reusable logic belongs in the package; scripts/CLI should be thin wrappers.
Run targeted tests first, then [release gates](../operations/release-validation.md).
Local success, diagrams, configured servers and existing items do not certify production.
