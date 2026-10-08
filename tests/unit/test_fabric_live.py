"""Offline tests for the live Fabric integration: every HTTP call goes to an ``httpx.MockTransport``.

No test reaches a tenant. IDs use the synthetic ``00000000-0000-0000-0000-`` prefix.
"""

import base64
import json
import shutil
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from tests.conftest import CONFIG_ROOT

from fabric_foundry_accelerator.audit.store import InMemoryAuditStore
from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.config.bindings import (
    BindingsError,
    TenantBindings,
    bindings_path,
    load_bindings,
)
from fabric_foundry_accelerator.config.overlay import load_overlay
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.models.changes import (
    ApprovalDecision,
    ApprovalRequest,
    ChangeRequest,
    ChangeStatus,
    ExecuteRequest,
    FabricTarget,
    ProposedChange,
)
from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import (
    EvidenceCategory,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.policies.engine import load_write_policy
from fabric_foundry_accelerator.providers.errors import (
    InvalidRequestError,
    ProviderUnavailableError,
    UnknownResourceError,
)
from fabric_foundry_accelerator.providers.fabric import auth as auth_module
from fabric_foundry_accelerator.providers.fabric.auth import (
    FABRIC_SCOPE,
    POWER_BI_SCOPE,
    AzureCliTokenProvider,
)
from fabric_foundry_accelerator.providers.fabric.live import LiveFabricProvider
from fabric_foundry_accelerator.providers.fabric.rest import (
    MAX_PAGES,
    MAX_RETRY_AFTER_SECONDS,
    FabricApiError,
    FabricRestClient,
)
from fabric_foundry_accelerator.providers.fabric.writer import (
    FabricScopedWriter,
    notebook_definition_dir,
)
from fabric_foundry_accelerator.services import fabric_commands
from fabric_foundry_accelerator.services.changes import (
    ApprovalError,
    ChangeService,
    LiveWriteUnavailableError,
)
from fabric_foundry_accelerator.services.container import build_container
from fabric_foundry_accelerator.services.fabric_readiness import run_readiness, run_readiness_sync

TENANT = "00000000-0000-0000-0000-000000000001"
WORKSPACE = "00000000-0000-0000-0000-000000000002"
LAKEHOUSE = "00000000-0000-0000-0000-000000000003"
MODEL = "00000000-0000-0000-0000-000000000004"
CAPACITY = "00000000-0000-0000-0000-000000000005"
FABRIC = "https://api.fabric.microsoft.com/v1"
POWER_BI = "https://api.powerbi.com/v1.0/myorg"

Handler = Callable[[httpx.Request], httpx.Response]


class FakeTokens:
    """Returns fixed fake tokens and records requested scopes."""

    def __init__(self, *, fail: Exception | None = None) -> None:
        self.scopes: list[str] = []
        self._fail = fail

    async def token(self, scope: str) -> str:
        if self._fail is not None:
            raise self._fail
        self.scopes.append(scope)
        return "fake-token"


class Sleeps:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


def _client(
    handler: Handler, *, tokens: FakeTokens | None = None
) -> tuple[FabricRestClient, Sleeps]:
    sleeps = Sleeps()
    client = FabricRestClient(
        tokens or FakeTokens(),
        http=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        sleep=sleeps,
    )
    return client, sleeps


def _routes(table: dict[tuple[str, str], Any]) -> Handler:
    """Map (method, path-with-query) to a response, a JSON body, or a list of responses (in order)."""

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.raw_path.decode())
        if key not in table:
            key = (request.method, request.url.path)
        entry = table.get(key)
        if entry is None:
            return httpx.Response(404, json={"errorCode": "EntityNotFound", "message": str(key)})
        if isinstance(entry, list):
            queue = cast("list[Any]", entry)
            entry = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(entry, httpx.Response):
            return entry
        return httpx.Response(200, json=entry)

    return handler


def _bindings() -> TenantBindings:
    return TenantBindings.model_validate(
        {
            "tenant_id": TENANT,
            "workspaces": {
                "demo-dev": {
                    "workspace_id": WORKSPACE,
                    "semantic_models": {"core-healthcare-v1": MODEL},
                }
            },
        }
    )


# ------------------------------------------------------------------ REST client
async def test_get_all_follows_continuation_tokens_with_bearer_token() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "continuationToken" in request.url.params:
            return httpx.Response(200, json={"value": [{"id": "b"}]})
        return httpx.Response(200, json={"value": [{"id": "a"}], "continuationToken": "next"})

    tokens = FakeTokens()
    client, _ = _client(handler, tokens=tokens)
    assert [r["id"] for r in await client.get_all("/workspaces")] == ["a", "b"]
    assert seen[0].headers["Authorization"] == "Bearer fake-token"
    assert seen[1].url.params["continuationToken"] == "next"
    assert tokens.scopes == [FABRIC_SCOPE, FABRIC_SCOPE]
    await client.aclose()


async def test_get_all_is_bounded() -> None:
    client, _ = _client(lambda _: httpx.Response(200, json={"value": [], "continuationToken": "x"}))
    with pytest.raises(ProviderUnavailableError, match=f"more than {MAX_PAGES} pages"):
        await client.get_all("/workspaces")


async def test_throttling_retries_with_capped_retry_after() -> None:
    responses = [
        httpx.Response(429, headers={"Retry-After": "999"}),
        httpx.Response(429, headers={"Retry-After": "1"}),
        httpx.Response(200, json={"value": [{"id": "a"}]}),
    ]
    client, sleeps = _client(lambda _: responses.pop(0))
    assert len(await client.get_all("/workspaces")) == 1
    assert sleeps.calls == [MAX_RETRY_AFTER_SECONDS, 1.0]


async def test_throttling_gives_up_after_bounded_retries() -> None:
    client, sleeps = _client(lambda _: httpx.Response(429, json={"errorCode": "TooManyRequests"}))
    with pytest.raises(FabricApiError, match="429 TooManyRequests"):
        await client.get_all("/workspaces")
    assert len(sleeps.calls) == 2


@pytest.mark.parametrize(
    ("response", "error", "fragment"),
    [
        (
            httpx.Response(404, json={"errorCode": "ItemNotFound", "message": "gone"}),
            UnknownResourceError,
            "ItemNotFound",
        ),
        (
            httpx.Response(403, json={"errorCode": "Forbidden", "message": "no"}),
            InvalidRequestError,
            "403 Forbidden",
        ),
        (
            httpx.Response(409, json={"errorCode": "ItemDisplayNameAlreadyInUse"}),
            InvalidRequestError,
            "409",
        ),
        (httpx.Response(500, text="not json"), FabricApiError, "HTTP500"),
        (
            httpx.Response(400, json={"error": {"code": "DaxError", "message": "bad"}}),
            InvalidRequestError,
            "DaxError",
        ),
    ],
)
async def test_error_mapping(
    response: httpx.Response, error: type[Exception], fragment: str
) -> None:
    client, _ = _client(lambda _: response)
    with pytest.raises(error, match=fragment):
        await client.get_json(f"{FABRIC}/workspaces", scope=FABRIC_SCOPE)


async def test_user_not_licensed_carries_code_request_id_and_guidance() -> None:
    body = {"errorCode": "UserNotLicensed", "message": "not licensed", "requestId": "r-1"}
    client, _ = _client(lambda _: httpx.Response(401, json=body))
    with pytest.raises(FabricApiError) as caught:
        await client.get_all("/workspaces")
    assert caught.value.code == "UserNotLicensed" and caught.value.status == 401
    assert caught.value.request_id == "r-1"
    assert "ffia fabric readiness" in str(caught.value)
    assert isinstance(caught.value, ProviderUnavailableError)  # reads may fall back in HYBRID


@pytest.mark.parametrize(
    ("exc", "fragment"),
    [(httpx.ReadTimeout("slow"), "timed out"), (httpx.ConnectError("down"), "ConnectError")],
)
async def test_transport_failures_are_unavailable(exc: Exception, fragment: str) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise exc

    client, _ = _client(handler)
    with pytest.raises(ProviderUnavailableError, match=fragment):
        await client.get_all("/workspaces")


async def test_post_returns_body_or_empty() -> None:
    responses = [httpx.Response(201, json={"id": "new"}), httpx.Response(200)]
    client, _ = _client(lambda _: responses.pop(0))
    assert await client.post_fabric("/x", {}) == {"id": "new"}
    assert await client.post_fabric("/x", {}) == {}


async def test_long_running_operation_is_polled_to_its_result() -> None:
    op = "https://api.fabric.microsoft.com/v1/operations/op-1"
    handler = _routes(
        {
            ("POST", "/v1/workspaces/w/notebooks"): httpx.Response(
                202, headers={"Location": op, "Retry-After": "3"}
            ),
            ("GET", "/v1/operations/op-1"): [{"status": "Running"}, {"status": "Succeeded"}],
            ("GET", "/v1/operations/op-1/result"): {"id": "nb"},
        }
    )
    client, sleeps = _client(handler)
    assert await client.post_fabric("/workspaces/w/notebooks", {}) == {"id": "nb"}
    assert sleeps.calls == [3.0, 3.0]


async def test_long_running_operation_failures() -> None:
    accepted = httpx.Response(202, headers={"Location": f"{FABRIC}/operations/op"})
    failed = _routes(
        {
            ("POST", "/v1/x"): accepted,
            ("GET", "/v1/operations/op"): {
                "status": "Failed",
                "error": {"errorCode": "Boom", "message": "m"},
            },
        }
    )
    client, _ = _client(failed)
    with pytest.raises(FabricApiError, match="Boom"):
        await client.post_fabric("/x", {})

    client, _ = _client(lambda _: httpx.Response(202))
    with pytest.raises(ProviderUnavailableError, match="without a Location"):
        await client.post_fabric("/x", {})

    running = _routes(
        {("POST", "/v1/x"): accepted, ("GET", "/v1/operations/op"): {"status": "Running"}}
    )
    client, _ = _client(running)
    with pytest.raises(ProviderUnavailableError, match="did not finish"):
        await client.post_fabric("/x", {})


async def test_execute_dax_reads_first_table_rows_with_power_bi_scope() -> None:
    bodies: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        assert request.url.path.endswith(f"/groups/{WORKSPACE}/datasets/{MODEL}/executeQueries")
        return httpx.Response(200, json={"results": [{"tables": [{"rows": [{"[v]": 7}]}]}]})

    tokens = FakeTokens()
    client, _ = _client(handler, tokens=tokens)
    assert await client.execute_dax(WORKSPACE, MODEL, 'EVALUATE ROW("v", 7)') == [{"[v]": 7}]
    assert bodies[0]["queries"] == [{"query": 'EVALUATE ROW("v", 7)'}]
    assert tokens.scopes == [POWER_BI_SCOPE]

    client, _ = _client(lambda _: httpx.Response(200, json={"results": []}))
    assert await client.execute_dax(WORKSPACE, MODEL, "q") == []


# ------------------------------------------------------------------ live provider
def _live(handler: Handler, data_root: Path) -> LiveFabricProvider:
    client, _ = _client(handler)
    return LiveFabricProvider(client, _bindings(), data_root=data_root, mode=OperatingMode.HYBRID)


def test_live_provider_refuses_offline_mode(data_root: Path) -> None:
    client, _ = _client(lambda _: httpx.Response(200))
    with pytest.raises(ValueError, match="OFFLINE"):
        LiveFabricProvider(client, _bindings(), data_root=data_root, mode=OperatingMode.OFFLINE)


async def test_live_reads_are_labeled_live(data_root: Path) -> None:
    items = {
        "value": [
            {"id": LAKEHOUSE, "type": "Lakehouse", "displayName": "lh_hc"},
            {"id": MODEL, "type": "SemanticModel", "displayName": "sm_hc"},
            {"id": "n", "type": "Notebook", "displayName": "nb"},
        ]
    }
    tables = {
        "data": [{"name": n} for n in ("bronze_x", "silver_x", "gold_x", "dim_x", "fact_x", "misc")]
    }
    provider = _live(
        _routes(
            {
                ("GET", "/v1/workspaces"): {"value": [{"id": WORKSPACE, "displayName": "dev"}]},
                ("GET", f"/v1/workspaces/{WORKSPACE}/items"): items,
                ("GET", f"/v1/workspaces/{WORKSPACE}/lakehouses/{LAKEHOUSE}/tables"): tables,
            }
        ),
        data_root,
    )
    assert provider.name == "Fabric REST API (live)"
    workspaces = await provider.list_workspaces(correlation_id="a" * 32)
    assert (
        workspaces.execution_label is ExecutionLabel.LIVE and workspaces.cloud_operation_performed
    )
    assert workspaces.correlation_id == "a" * 32 and workspaces.data[0].display_name == "dev"
    listed = await provider.list_items(WORKSPACE)
    assert [i.type for i in listed.data] == ["Lakehouse", "SemanticModel"]
    result = await provider.list_tables(LAKEHOUSE)
    assert result.execution_label is ExecutionLabel.PREVIEW and result.cloud_operation_performed
    assert [t.layer for t in result.data] == [
        "bronze",
        "silver",
        "gold",
        "gold",
        "gold",
        "unclassified",
    ]
    assert all(t.row_count is None for t in result.data)


async def test_live_tables_resolve_workspace_through_bindings(data_root: Path) -> None:
    provider = _live(
        _routes(
            {
                ("GET", f"/v1/workspaces/{WORKSPACE}/items"): {"value": [{"id": LAKEHOUSE}]},
                ("GET", f"/v1/workspaces/{WORKSPACE}/lakehouses/{LAKEHOUSE}/tables"): {"data": []},
            }
        ),
        data_root,
    )
    assert (await provider.list_tables(LAKEHOUSE)).data == ()
    with pytest.raises(UnknownResourceError, match="not in any bound workspace"):
        await provider.list_tables("00000000-0000-0000-0000-000000000099")


async def test_live_provider_does_not_fake_unsupported_reads(data_root: Path) -> None:
    provider = _live(lambda _: httpx.Response(500), data_root)
    with pytest.raises(InvalidRequestError, match="Row previews"):
        await provider.read_table(LAKEHOUSE, "gold_x")
    with pytest.raises(InvalidRequestError, match="semantic model definitions"):
        await provider.get_semantic_model(MODEL)


async def test_live_measures_use_dax_by_display_name(data_root: Path) -> None:
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        query = json.loads(request.content)["queries"][0]["query"]
        queries.append(query)
        if "Total Encounters" in query:
            return httpx.Response(200, json={"results": [{"tables": [{"rows": [{"[v]": 1200}]}]}]})
        if "ED Visit Count" in query:
            return httpx.Response(400, json={"error": {"code": "DaxError", "message": "missing"}})
        return httpx.Response(200, json={"results": [{"tables": [{"rows": [{"[v]": "text"}]}]}]})

    provider = _live(handler, data_root)
    wanted = ["total_encounters", "ed_visit_count", "inpatient_encounters"]
    result = await provider.evaluate_measures(MODEL, wanted)
    assert result.execution_label is ExecutionLabel.LIVE
    assert [m.value for m in result.data] == [1200, None, None]
    assert 'EVALUATE ROW("v", [Total Encounters])' in queries
    with pytest.raises(UnknownResourceError, match="unknown measures"):
        await provider.evaluate_measures(MODEL, ["nope"])
    with pytest.raises(UnknownResourceError, match="not bound"):
        await provider.evaluate_measures("00000000-0000-0000-0000-000000000099")


# ------------------------------------------------------------------ scoped writer
def _plan(
    operation: str = "create_lakehouse", item_type: str = "Lakehouse", name: str = "lh_hc"
) -> ProposedChange:
    target = FabricTarget.model_validate(
        {
            "workspace_alias": "demo-dev",
            "item_type": item_type,
            "item_name": name,
            "destination": "LIVE",
        }
    )
    return ProposedChange(
        change_id="chg-1",
        correlation_id="c" * 32,
        operation=operation,
        target=target,
        provider="test",
        reason="unit test",
        requested_by="alice",
        risk="low",
        reversible=True,
        expected_impact="one new item",
        validation=("exists once",),
        rollback="delete the item",
        approval_required=True,
        policy_allowed=True,
        policy_reasons=(),
        precondition=CheckResult(name="p", passed=True, detail="d"),
        destination_hash=target.destination_hash(),
        status=ChangeStatus.APPROVED,
        created_at=datetime(2026, 10, 7, tzinfo=UTC),
    )


def _writer(handler: Handler, root: Path) -> FabricScopedWriter:
    client, _ = _client(handler)
    return FabricScopedWriter(client, _bindings(), definitions_root=root)


async def test_writer_prechecks_duplicates_case_insensitively(tmp_path: Path) -> None:
    rows = {"value": [{"id": LAKEHOUSE, "displayName": "LH_HC"}]}
    writer = _writer(
        _routes({("GET", f"/v1/workspaces/{WORKSPACE}/items?type=Lakehouse"): rows}), tmp_path
    )
    assert writer.supports("create_lakehouse") and not writer.supports("delete_item")
    check = await writer.precheck(_plan())
    assert not check.passed and "already exists" in check.detail
    assert check.category is EvidenceCategory.VERIFIED_LIVE
    assert (await writer.precheck(_plan(name="other"))).passed


async def test_writer_creates_lakehouse_and_verifies(tmp_path: Path) -> None:
    posted: list[dict[str, Any]] = []
    created = {"done": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posted.append(json.loads(request.content))
            created["done"] = True
            return httpx.Response(201, json={"id": LAKEHOUSE})
        rows = [{"id": LAKEHOUSE, "displayName": "lh_hc"}] if created["done"] else []
        return httpx.Response(200, json={"value": rows})

    writer = _writer(handler, tmp_path)
    item_id = await writer.execute(_plan())
    assert item_id == LAKEHOUSE
    assert posted[0]["displayName"] == "lh_hc" and "definition" not in posted[0]
    assert (await writer.verify(_plan(), item_id)).passed
    assert not (await writer.verify(_plan(), "00000000-0000-0000-0000-000000000099")).passed


async def test_writer_creates_notebook_only_from_a_committed_definition(tmp_path: Path) -> None:
    posted: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posted.append(json.loads(request.content))
            return httpx.Response(200)  # no body: the writer looks the item up by name
        return httpx.Response(200, json={"value": [{"id": "nb-1", "displayName": "nb_hc"}]})

    writer = _writer(handler, tmp_path)
    plan = _plan("create_notebook", "Notebook", "nb_hc")
    with pytest.raises(BindingsError, match="no reviewed notebook definition"):
        await writer.execute(plan)
    folder = notebook_definition_dir(tmp_path, "nb_hc")
    folder.mkdir()
    (folder / "notebook-content.py").write_text("# Fabric notebook source\n", encoding="utf-8")
    (folder / ".platform").write_text("{}", encoding="utf-8")
    assert await writer.execute(plan) == "nb-1"
    definition = posted[0]["definition"]
    assert definition["format"] == "fabricGitSource"
    assert [p["path"] for p in definition["parts"]] == ["notebook-content.py", ".platform"]
    assert base64.b64decode(definition["parts"][0]["payload"]) == b"# Fabric notebook source\n"


async def test_writer_refuses_unbound_or_unsupported(tmp_path: Path) -> None:
    writer = _writer(lambda _: httpx.Response(200, json={"value": []}), tmp_path)
    unbound = _plan().model_copy(
        update={
            "target": FabricTarget.model_validate(
                {**_plan().target.model_dump(), "workspace_alias": "other"}
            )
        }
    )
    with pytest.raises(BindingsError, match="not bound"):
        await writer.precheck(unbound)
    with pytest.raises(BindingsError, match="not supported"):
        await writer.execute(_plan("delete_item"))


# ------------------------------------------------------------------ ChangeService live path
class FakeWriter:
    def __init__(
        self,
        *,
        precheck: bool = True,
        verify: bool = True,
        fail: Exception | None = None,
        supported: bool = True,
    ) -> None:
        self._precheck, self._verify, self._fail = precheck, verify, fail
        self._supported = supported
        self.executed: list[str] = []

    @property
    def name(self) -> str:
        return "fake live writer"

    def supports(self, operation: str) -> bool:
        return self._supported and operation == "create_lakehouse"

    async def precheck(self, plan: ProposedChange) -> CheckResult:
        return CheckResult(
            name="dup",
            passed=self._precheck,
            detail="dup check",
            category=EvidenceCategory.VERIFIED_LIVE,
        )

    async def execute(self, plan: ProposedChange) -> str:
        if self._fail is not None:
            raise self._fail
        self.executed.append(plan.change_id)
        return LAKEHOUSE

    async def verify(self, plan: ProposedChange, item_id: str) -> CheckResult:
        return CheckResult(
            name="v", passed=self._verify, detail=item_id, category=EvidenceCategory.VERIFIED_LIVE
        )


def _live_service(writer: FakeWriter) -> tuple[ChangeService, InMemoryAuditStore]:
    audit = InMemoryAuditStore()
    service = ChangeService(
        policy=load_write_policy(CONFIG_ROOT),
        overlay=load_overlay(CONFIG_ROOT, "example-healthcare"),
        audit=audit,
        mode=OperatingMode.LIVE,
        allow_live_mutation=True,
        live_writer=writer,
    )
    return service, audit


async def _approved_live(
    service: ChangeService, operation: str = "create_lakehouse"
) -> ExecuteRequest:
    target = FabricTarget.model_validate(
        {
            "workspace_alias": "demo-dev",
            "item_type": "Lakehouse",
            "item_name": "lh_hc",
            "destination": "LIVE",
        }
    )
    plan = service.plan(
        ChangeRequest(operation=operation, target=target, reason="live test", requested_by="alice")
    )
    assert plan.status is ChangeStatus.PROPOSED, plan.policy_reasons
    approval = service.approve(
        ApprovalRequest(
            change_id=plan.change_id, approver="bob", decision=ApprovalDecision.APPROVED
        )
    )
    return ExecuteRequest(
        change_id=plan.change_id, approval_id=approval.approval_id, executed_by="writer"
    )


async def test_live_change_executes_through_the_writer_and_is_audited() -> None:
    writer = FakeWriter()
    service, audit = _live_service(writer)
    assert service.live_writer is writer
    request = await _approved_live(service)
    envelope = await service.execute(request)
    assert envelope.execution_label is ExecutionLabel.LIVE and envelope.cloud_operation_performed
    assert envelope.selected_provider == "fake live writer"
    assert envelope.data.status is ChangeStatus.VERIFIED and writer.executed == [request.change_id]
    record = audit.for_correlation(envelope.correlation_id)[-1]
    assert record.action == "change:execute" and record.success
    assert record.details["item_id"] == "[REDACTED-ID]"  # audit never stores real item IDs


async def test_failed_live_verification_marks_the_change_failed() -> None:
    service, _ = _live_service(FakeWriter(verify=False))
    envelope = await service.execute(await _approved_live(service))
    assert envelope.data.status is ChangeStatus.FAILED


async def test_live_precheck_failure_stops_before_writing() -> None:
    writer = FakeWriter(precheck=False)
    service, audit = _live_service(writer)
    request = await _approved_live(service)
    with pytest.raises(ApprovalError, match="live precondition failed"):
        await service.execute(request)
    assert writer.executed == []
    assert service.get_plan(request.change_id).status is ChangeStatus.FAILED
    assert not audit.for_correlation(service.get_plan(request.change_id).correlation_id)[-1].success


async def test_live_write_errors_are_audited_and_re_raised() -> None:
    service, audit = _live_service(FakeWriter(fail=ProviderUnavailableError("tenant down")))
    request = await _approved_live(service)
    with pytest.raises(ProviderUnavailableError, match="tenant down"):
        await service.execute(request)
    plan = service.get_plan(request.change_id)
    assert plan.status is ChangeStatus.FAILED
    record = audit.for_correlation(plan.correlation_id)[-1]
    assert not record.success and "ProviderUnavailableError" in str(record.details["outcome"])


async def test_unsupported_live_operation_is_never_redirected_to_local() -> None:
    service, _ = _live_service(FakeWriter(supported=False))
    with pytest.raises(LiveWriteUnavailableError, match="NOT redirected"):
        await service.execute(await _approved_live(service))


# ------------------------------------------------------------------ container wiring
def _config_with_bindings(tmp_path: Path) -> Path:
    root = tmp_path / "config"
    shutil.copytree(CONFIG_ROOT, root)
    bindings_path(root, "example-healthcare").write_text(
        json.dumps(_bindings().model_dump()), encoding="utf-8"
    )
    return root


def test_live_client_requires_explicit_opt_in_mode_and_bindings(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> None:
    assert build_container(make_settings()).bindings is None
    with pytest.raises(BindingsError, match="FFIA_ENVIRONMENT"):
        build_container(make_settings(fabric_live=True))
    with pytest.raises(BindingsError, match=r"local\.yaml"):
        build_container(make_settings(fabric_live=True, environment="hybrid"))


def test_container_wires_live_provider_and_writer_from_bindings(
    make_settings: Callable[..., Settings], tmp_path: Path
) -> None:
    client, _ = _client(lambda _: httpx.Response(200, json={"value": []}))
    root = _config_with_bindings(tmp_path)
    read_only = build_container(
        make_settings(fabric_live=True, environment="hybrid", config_root=root),
        fabric_client=client,
    )
    assert read_only.bindings is not None and read_only.bindings.tenant_id == TENANT
    assert read_only.changes.live_writer is None
    writable = build_container(
        make_settings(
            fabric_live=True, environment="hybrid", config_root=root, allow_live_mutation=True
        ),
        fabric_client=client,
    )
    assert isinstance(writable.changes.live_writer, FabricScopedWriter)


# ------------------------------------------------------------------ readiness
def _ready_routes(**overrides: Any) -> Handler:
    table: dict[tuple[str, str], Any] = {
        ("GET", "/v1/workspaces"): {"value": [{"id": WORKSPACE, "capacityId": CAPACITY}]},
        ("GET", "/v1/capacities"): {"value": [{"id": CAPACITY, "state": "Active", "sku": "F2"}]},
        ("GET", "/v1/admin/tenantsettings"): {
            "value": [
                {"settingName": "FabricGAWorkloads", "enabled": True},
                {"settingName": "AllowXMLAEndpoints", "enabled": True},
                {
                    "settingName": "S1",
                    "title": "Semantic Model Execute Queries REST API",
                    "enabled": True,
                },
                {
                    "settingName": "S2",
                    "title": "Users can synchronize workspace items with their Git repositories",
                    "enabled": True,
                },
                {
                    "settingName": "S3",
                    "title": "Users can create and share data agent item types",
                    "enabled": False,
                },
            ]
        },
    }
    table.update({("GET", k): v for k, v in overrides.items()})
    return _routes(table)


async def test_readiness_passes_on_a_ready_tenant() -> None:
    client, _ = _client(_ready_routes())
    report = await run_readiness(client, _bindings(), TENANT)
    assert report.ready, report.checks
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Fabric capacity"] == "PASS" and statuses["Workspace demo-dev"] == "PASS"
    assert statuses["Tenant setting: Fabric data agent items (preview features)"] == "WARN"
    assert statuses["Tenant setting: Copilot and Azure OpenAI features"] == "SKIPPED"


async def test_readiness_reports_unlicensed_account_with_remediation() -> None:
    body = {"errorCode": "UserNotLicensed", "message": "not licensed"}
    client, _ = _client(lambda _: httpx.Response(401, json=body))
    report = await run_readiness(client, None, TENANT)
    assert not report.ready
    access = next(c for c in report.checks if c.name == "Fabric API access")
    assert access.status == "FAIL" and "app.fabric.microsoft.com" in access.remediation
    assert report.checks[0].status == "WARN"  # no bindings file


async def test_readiness_stops_when_no_token() -> None:
    client, _ = _client(
        lambda _: httpx.Response(200), tokens=FakeTokens(fail=ProviderUnavailableError("az\nmore"))
    )
    report = await run_readiness(client, _bindings(), TENANT)
    assert [c.status for c in report.checks] == ["PASS", "FAIL"]
    assert (
        "az login --tenant" in report.checks[-1].remediation
        and "\n" not in report.checks[-1].detail
    )


async def test_readiness_flags_missing_capacity_workspace_and_settings() -> None:
    client, _ = _client(
        _ready_routes(
            **{
                "/v1/workspaces": {"value": [{"id": WORKSPACE}]},
                "/v1/capacities": {"value": [{"id": CAPACITY, "state": "Inactive"}]},
                "/v1/admin/tenantsettings": httpx.Response(403, json={"errorCode": "Forbidden"}),
            }
        )
    )
    report = await run_readiness(client, _bindings(), TENANT)
    statuses = {c.name: c.status for c in report.checks}
    assert not report.ready
    assert statuses["Fabric capacity"] == "FAIL" and statuses["Workspace demo-dev"] == "FAIL"
    assert statuses["Tenant settings"] == "SKIPPED"


async def test_readiness_flags_unknown_workspace_disabled_settings_and_no_alias() -> None:
    settings = {"value": [{"settingName": "FabricGAWorkloads", "enabled": False}]}
    client, _ = _client(
        _ready_routes(**{"/v1/workspaces": {"value": []}, "/v1/admin/tenantsettings": settings})
    )
    report = await run_readiness(client, _bindings(), TENANT)
    statuses = {c.name: c.status for c in report.checks}
    assert statuses["Workspace demo-dev"] == "FAIL"
    assert statuses["Tenant setting: Users can create Fabric items"] == "FAIL"
    assert statuses["Tenant setting: Git integration for workspaces"] == "WARN"


def test_readiness_sync_warns_without_bound_workspaces() -> None:
    empty = TenantBindings(tenant_id=TENANT)
    client, _ = _client(_ready_routes())
    report = run_readiness_sync(client, empty, TENANT)
    assert {c.name: c.status for c in report.checks}["Bound dev workspace"] == "WARN"


def test_readiness_cli(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(tmp_path))
    assert main(["fabric", "readiness"]) == 2
    assert "Pass --tenant" in capsys.readouterr().err

    def fake_client(_: object) -> FabricRestClient:
        return _client(_ready_routes())[0]

    monkeypatch.setattr(fabric_commands, "FabricRestClient", fake_client)
    assert main(["fabric", "readiness", "--tenant", TENANT]) == 0
    out = capsys.readouterr().out
    assert "Fabric ready for live labs: YES" in out and "-> Create the git-ignored" in out
    assert main(["fabric", "readiness", "--tenant", TENANT, "--json"]) == 0
    assert '"ready": true' in capsys.readouterr().out


# ------------------------------------------------------------------ auth and bindings
async def test_azure_cli_token_provider_pins_tenant_and_bounds_the_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[dict[str, object]] = []

    class FakeCredential:
        def __init__(self, **kwargs: object) -> None:
            created.append(kwargs)

        def get_token(self, scope: str) -> object:
            return type("Token", (), {"token": f"token-for-{scope}"})()

    import azure.identity  # noqa: PLC0415

    monkeypatch.setattr(azure.identity, "AzureCliCredential", FakeCredential)
    provider = AzureCliTokenProvider(TENANT, process_timeout=5)
    assert await provider.token(FABRIC_SCOPE) == f"token-for-{FABRIC_SCOPE}"
    assert created == [{"tenant_id": TENANT, "process_timeout": 5}]
    assert auth_module.FABRIC_SCOPE.endswith("/.default")


def test_bindings_load_validate_and_resolve(tmp_path: Path) -> None:
    assert load_bindings(tmp_path, "example-healthcare") is None
    (tmp_path / "customers").mkdir()
    bindings_path(tmp_path, "example-healthcare").write_text(
        json.dumps(_bindings().model_dump()), encoding="utf-8"
    )
    loaded = load_bindings(tmp_path, "example-healthcare")
    assert loaded is not None and loaded.workspace_id("demo-dev") == WORKSPACE
    assert loaded.workspace_id("prod") is None
    with pytest.raises(ValueError, match="must be GUIDs"):
        TenantBindings.model_validate(
            {
                "tenant_id": TENANT,
                "workspaces": {"a": {"workspace_id": WORKSPACE, "semantic_models": {"p": "x"}}},
            }
        )


def test_example_bindings_file_is_a_placeholder_template() -> None:
    example = CONFIG_ROOT / "customers" / "example-healthcare.local.example.yaml"
    text = example.read_text(encoding="utf-8")
    assert "tenant_id" in text and "workspace_id" in text


async def test_writer_packages_the_committed_reference_notebook() -> None:
    from tests.conftest import REPO_ROOT  # noqa: PLC0415

    posted: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posted.append(json.loads(request.content))
            return httpx.Response(201, json={"id": "nb-1"})
        return httpx.Response(200, json={"value": []})

    writer = _writer(handler, REPO_ROOT / "fabric" / "workspace")
    assert await writer.execute(_plan("create_notebook", "Notebook", "MCP_01_Bronze")) == "nb-1"
    parts = {
        p["path"]: base64.b64decode(p["payload"]).decode() for p in posted[0]["definition"]["parts"]
    }
    assert parts["notebook-content.py"].startswith("# Fabric notebook source")
    assert json.loads(parts[".platform"])["metadata"]["displayName"] == "MCP_01_Bronze"
