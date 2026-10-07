from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from fabric_foundry_accelerator.api.app import CORRELATION_HEADER, create_app
from fabric_foundry_accelerator.services.container import Container

LAKEHOUSE = "local-lh-hc-lab-7file-v1"
MODEL = "local-sm-hc-lab-7file-v1"
GUIDE = "hc-01-fabric-mcp-powerbi-medallion-lab"


@pytest.fixture
def client(make_container: Callable[..., Container]) -> Iterator[TestClient]:
    with TestClient(create_app(make_container())) as test_client:
        yield test_client


def _target(destination: str = "LOCAL", name: str = "api_lake") -> dict[str, str]:
    return {
        "workspace_alias": "demo-dev",
        "item_type": "Lakehouse",
        "item_name": name,
        "destination": destination,
    }


def _plan(client: TestClient, destination: str = "LOCAL") -> dict[str, object]:
    response = client.post(
        "/api/v1/plans",
        json={
            "operation": "create_lakehouse",
            "target": _target(destination),
            "reason": "API test plan",
            "requested_by": "alice",
        },
    )
    assert response.status_code == 200
    plan: dict[str, object] = response.json()
    return plan


def test_health_ready_and_correlation(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    ready = client.get("/ready")
    assert ready.status_code == 200 and ready.json()["ready"] is True
    generated = ready.headers[CORRELATION_HEADER]
    assert len(generated) == 32
    echoed = client.get("/health", headers={CORRELATION_HEADER: "e" * 32})
    assert echoed.headers[CORRELATION_HEADER] == "e" * 32
    replaced = client.get("/health", headers={CORRELATION_HEADER: "not valid"})
    assert replaced.headers[CORRELATION_HEADER] != "not valid"


def test_runtime_providers_capabilities_profiles(client: TestClient) -> None:
    status = client.get("/api/v1/runtime/status").json()
    assert status["operating_mode"] == "OFFLINE" and status["preview_features"] == []
    assert "LIVE writes disabled" in status["write_mode"]
    kinds = {p["kind"] for p in client.get("/api/v1/runtime/providers").json()}
    assert {"LOCAL", "NOT AVAILABLE"} <= kinds
    assert {c["name"] for c in client.get("/api/v1/capabilities").json()} >= {
        "fabric_read",
        "change_plans",
        "mcp",
    }
    assert client.get("/api/v1/profiles").json() == ["core-healthcare-v1", "hc-lab-7file-v1"]


def test_patterns_and_guides(client: TestClient) -> None:
    assert len(client.get("/api/v1/patterns").json()) == 24
    assert client.get("/api/v1/patterns/P08").json()["name"].startswith("Human-in-the-loop")
    assert client.get("/api/v1/patterns/P99").status_code == 404
    ranked = client.post(
        "/api/v1/patterns/recommend", json={"needs": ["medallion-foundation"]}
    ).json()
    assert ranked[0]["pattern_id"] == "P10"
    assert client.post("/api/v1/patterns/recommend", json={"needs": ["nope"]}).status_code == 422
    assert client.post("/api/v1/patterns/recommend", json={"needs": []}).status_code == 422
    assert client.get("/api/v1/guides").json()[0]["id"] == GUIDE
    assert client.get(f"/api/v1/guides/{GUIDE}").json()["dataset_profile"] == "hc-lab-7file-v1"
    assert client.get(f"/api/v1/guides/{GUIDE}/steps/05-upload-data").json()["writes"] is True
    missing = client.get("/api/v1/guides/nope")
    assert missing.status_code == 404 and missing.json()["detail"] == "nope"


@pytest.mark.parametrize(
    "body",
    [
        {"operation": "list_workspaces"},
        {"operation": "list_items", "workspace_id": "local-ws-synthetic"},
        {"operation": "list_tables", "lakehouse_id": LAKEHOUSE},
        {
            "operation": "read_table",
            "lakehouse_id": LAKEHOUSE,
            "table": "gold_financial",
            "limit": 3,
        },
        {"operation": "get_semantic_model", "semantic_model_id": MODEL},
        {"operation": "evaluate_measures", "semantic_model_id": MODEL, "measures": ["claim_count"]},
    ],
)
def test_fabric_reads_are_labeled_local(client: TestClient, body: dict[str, object]) -> None:
    response = client.post("/api/v1/fabric/read", json=body)
    assert response.status_code == 200
    envelope = response.json()
    assert envelope["execution_label"] == "LOCAL" and envelope["cloud_operation_performed"] is False
    assert envelope["correlation_id"] == response.headers[CORRELATION_HEADER]


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({"operation": "run_sql", "sql": "SELECT 1"}, 422),
        (
            {
                "operation": "read_table",
                "lakehouse_id": LAKEHOUSE,
                "table": "gold_financial",
                "limit": 101,
            },
            422,
        ),
        ({"operation": "read_table", "lakehouse_id": LAKEHOUSE, "table": "secrets"}, 404),
        ({"operation": "list_items", "workspace_id": "other"}, 404),
    ],
)
def test_fabric_read_contract_is_enforced(
    client: TestClient, body: dict[str, object], status: int
) -> None:
    response = client.post("/api/v1/fabric/read", json=body)
    assert response.status_code == status
    if status == 404:
        assert response.json()["correlation_id"]


def test_change_flow_over_http(client: TestClient) -> None:
    plan = _plan(client)
    change_id = plan["change_id"]
    assert plan["status"] == "PROPOSED"
    assert client.get(f"/api/v1/plans/{change_id}").json()["change_id"] == change_id
    assert len(client.get("/api/v1/plans").json()) == 1
    self_approval = client.post(
        "/api/v1/approvals",
        json={"change_id": change_id, "approver": "alice", "decision": "APPROVED"},
    )
    assert self_approval.status_code == 409
    approval = client.post(
        "/api/v1/approvals",
        json={"change_id": change_id, "approver": "bob", "decision": "APPROVED"},
    ).json()
    executed = client.post(
        "/api/v1/fabric/change",
        json={
            "change_id": change_id,
            "approval_id": approval["approval_id"],
            "executed_by": "writer",
        },
    )
    body = executed.json()
    assert (
        executed.status_code == 200
        and body["execution_label"] == "SIMULATED"
        and body["data"]["status"] == "VERIFIED"
    )
    again = client.post(
        "/api/v1/fabric/change",
        json={
            "change_id": change_id,
            "approval_id": approval["approval_id"],
            "executed_by": "writer",
        },
    )
    assert again.status_code == 409
    audit = client.get(f"/api/v1/audit/{plan['correlation_id']}").json()
    assert [(r["action"], r["success"]) for r in audit] == [
        ("change:plan", True),
        ("change:approve:APPROVED", False),
        ("change:approve:APPROVED", True),
        ("change:execute", True),
    ]
    assert audit[1]["details"]["refusal"].startswith("separation of duties")
    assert client.get("/api/v1/plans/missing").status_code == 404


def test_live_change_returns_409_and_is_not_redirected(
    make_container: Callable[..., Container],
) -> None:
    with TestClient(create_app(make_container(allow_live_mutation=True))) as client:
        plan = _plan(client, destination="LIVE")
        approval = client.post(
            "/api/v1/approvals",
            json={"change_id": plan["change_id"], "approver": "bob", "decision": "APPROVED"},
        ).json()
        response = client.post(
            "/api/v1/fabric/change",
            json={
                "change_id": plan["change_id"],
                "approval_id": approval["approval_id"],
                "executed_by": "w",
            },
        )
    assert response.status_code == 409
    assert response.json()["redirected_to_local"] is False
    assert "NOT redirected to LOCAL" in response.json()["detail"]


def test_unavailable_capability_returns_503_with_route_decision(
    make_container: Callable[..., Container],
) -> None:
    with TestClient(create_app(make_container(environment="live"))) as client:
        response = client.post("/api/v1/fabric/read", json={"operation": "list_workspaces"})
    assert response.status_code == 503
    assert response.json()["route_decision"]["outcome"] == "UNAVAILABLE"


def test_hybrid_outage_falls_back_visibly(make_container: Callable[..., Container]) -> None:
    with TestClient(
        create_app(make_container(environment="hybrid", simulate_fabric_outage=True))
    ) as client:
        envelope = client.post("/api/v1/fabric/read", json={"operation": "list_workspaces"}).json()
        providers = client.get("/api/v1/runtime/providers").json()
    assert envelope["fallback_used"] is True and envelope["operating_mode"] == "HYBRID"
    assert "simulated outage" in envelope["fallback_reason"]
    assert any(p["kind"] == "FAULT-INJECTION" for p in providers)


def test_recovery_evaluation_and_demo_status(client: TestClient) -> None:
    drill = client.post("/api/v1/recovery/drill").json()
    assert drill["execution_label"] == "SIMULATED" and drill["data"]["recovered"] is True
    evaluation = client.post("/api/v1/evaluations/run", json={"profile": "hc-lab-7file-v1"}).json()
    assert (
        evaluation["data"]["gate_passed"] is True
        and evaluation["data"]["observed_values_source"] == "local-provider"
    )
    wrong = client.post(
        "/api/v1/evaluations/run",
        json={"profile": "hc-lab-7file-v1", "observed": {"denial_rate": 0.5}},
    ).json()
    assert wrong["data"]["gate_passed"] is False
    assert client.post("/api/v1/evaluations/run", json={"profile": "nope"}).status_code == 404
    status = client.get("/api/v1/demo/status").json()
    assert status["recommended_mode"] == "OFFLINE"
    assert {line["component"] for line in status["lines"]} >= {
        "Fabric API",
        "Local Dataset",
        "MCP Server",
    }


def test_education_endpoints(client: TestClient) -> None:
    lessons = client.get("/api/v1/education/lessons").json()
    assert {lesson["id"] for lesson in lessons} >= {"p08-human-in-the-loop"}
    by_pattern = client.get("/api/v1/education/lessons", params={"pattern_id": "P08"}).json()
    assert all("P08" in lesson["pattern_ids"] for lesson in by_pattern)
    lesson = client.get("/api/v1/education/lessons/p08-human-in-the-loop").json()
    assert [level["level"] for level in lesson["levels"]] == [
        "executive",
        "l100",
        "l200",
        "l300",
        "l400",
    ]
    assert all("answer" not in check for check in lesson["checks"])
    check_id = lesson["checks"][0]["id"]
    graded = client.post(
        f"/api/v1/education/lessons/p08-human-in-the-loop/checks/{check_id}", json={"choice": 0}
    ).json()
    assert set(graded) == {"check_id", "correct", "correct_choice", "explanation"}
    assert (
        client.post(
            "/api/v1/education/lessons/p08-human-in-the-loop/checks/nope", json={"choice": 0}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/education/lessons/nope").status_code == 404
    labs = client.get("/api/v1/education/labs").json()
    assert labs and client.get(f"/api/v1/education/labs/{labs[0]['id']}").json()["steps"]
    assert client.get("/api/v1/education/labs/nope").status_code == 404
    architecture = client.get("/api/v1/education/architecture").json()
    assert architecture["layers"] and architecture["components"]
    completeness = client.get("/api/v1/education/completeness").json()
    assert completeness["total"] == 30


def test_selection_signals_and_demo_run(client: TestClient) -> None:
    signals = client.get("/api/v1/patterns/signals").json()
    assert any(signal["id"] == "business-system-write" for signal in signals)
    report = client.post("/api/v1/demo/run").json()
    assert report["passed"] is True and report["cloud_operations"] == 0
