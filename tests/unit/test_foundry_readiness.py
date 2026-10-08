"""Foundry readiness: every HTTP call goes to an httpx.MockTransport (no tenant)."""

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml

from fabric_foundry_accelerator.cli import main
from fabric_foundry_accelerator.config.bindings import FoundryBinding
from fabric_foundry_accelerator.services import foundry_commands
from fabric_foundry_accelerator.services.foundry_readiness import (
    FoundryReadiness,
    project_endpoint,
    run_sync,
)

SUB = "00000000-0000-0000-0000-000000000011"
BINDING = FoundryBinding(
    subscription_id=SUB,
    resource_group="rg-demo",
    account="foundry-demo",
    project="agents",
    model_deployments=("model-a",),
    agents=("sales-insights-agent",),
    fabric_connection="fabric-conn",
)


class Tokens:
    def __init__(self) -> None:
        self.scopes: list[str] = []

    async def token(self, scope: str) -> str:
        self.scopes.append(scope)
        return "fake"


def _routes(**overrides: Any) -> httpx.MockTransport:
    table: dict[str, Any] = {
        "account": {
            "kind": "AIServices",
            "properties": {"provisioningState": "Succeeded", "allowProjectManagement": True},
        },
        "project": {"properties": {"provisioningState": "Succeeded"}},
        "deployments": {
            "value": [
                {
                    "name": "model-a",
                    "sku": {"name": "DataZoneStandard"},
                    "properties": {"provisioningState": "Succeeded"},
                }
            ]
        },
        "agents": {"data": [{"name": "sales-insights-agent"}]},
        "connections": {"value": [{"name": "fabric-conn", "type": "CustomKeys"}]},
        **overrides,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        key = (
            "deployments"
            if path.endswith("/deployments")
            else "project"
            if "/projects/" in path and "management.azure.com" in str(request.url)
            else "agents"
            if path.endswith("/agents")
            else "connections"
            if path.endswith("/connections")
            else "account"
        )
        entry = table[key]
        return entry if isinstance(entry, httpx.Response) else httpx.Response(200, json=entry)

    return httpx.MockTransport(handler)


def _checker(**overrides: Any) -> tuple[FoundryReadiness, Tokens]:
    tokens = Tokens()
    return FoundryReadiness(tokens, http=httpx.AsyncClient(transport=_routes(**overrides))), tokens


async def test_ready_project_passes_and_uses_both_scopes() -> None:
    checker, tokens = _checker()
    report = await checker.run(BINDING)
    assert report.ready, report.checks
    assert [c.status for c in report.checks] == ["PASS"] * 6
    assert {"https://management.azure.com/.default", "https://ai.azure.com/.default"} <= set(
        tokens.scopes
    )
    assert (
        project_endpoint(BINDING)
        == "https://foundry-demo.services.ai.azure.com/api/projects/agents"
    )


@pytest.mark.parametrize(
    ("overrides", "name", "status"),
    [
        ({"deployments": {"value": []}}, "Model deployments", "FAIL"),
        ({"agents": {"data": []}}, "Agent sales-insights-agent", "WARN"),
        ({"connections": {"value": []}}, "Fabric data agent connection", "FAIL"),
        ({"project": httpx.Response(404, json={})}, "Foundry project", "FAIL"),
        ({"agents": httpx.Response(403, json={})}, "Project data-plane access", "FAIL"),
        ({"agents": httpx.Response(500, text="boom")}, "Project data-plane access", "FAIL"),
        (
            {"account": {"kind": "OpenAI", "properties": {"provisioningState": "Succeeded"}}},
            "Foundry resource",
            "FAIL",
        ),
    ],
)
async def test_failures_are_reported_with_remediation(
    overrides: dict[str, Any], name: str, status: str
) -> None:
    checker, _ = _checker(**overrides)
    report = await checker.run(BINDING)
    check = next(c for c in report.checks if c.name == name)
    assert check.status == status
    assert report.ready is (status == "WARN")


async def test_unreadable_account_stops_early_and_transport_errors_are_handled() -> None:
    checker, _ = _checker(account=httpx.Response(401, json={}))
    report = await checker.run(BINDING)
    assert [c.name for c in report.checks] == ["Foundry resource"] and not report.ready

    def boom(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    failing = FoundryReadiness(
        Tokens(), http=httpx.AsyncClient(transport=httpx.MockTransport(boom))
    )
    assert not (await failing.run(BINDING)).ready


def test_cli_without_binding_and_with_binding(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    config = tmp_path / "config"
    (config / "customers").mkdir(parents=True)
    monkeypatch.setenv("FFIA_CONFIG_ROOT", str(config))
    assert main(["foundry", "readiness"]) == 2
    assert "No Foundry binding" in capsys.readouterr().err
    bindings = {
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "foundry": json.loads(BINDING.model_dump_json()),
    }
    (config / "customers" / "example-healthcare.local.yaml").write_text(
        yaml.safe_dump(bindings), encoding="utf-8"
    )

    def fake(tokens: object) -> FoundryReadiness:
        return FoundryReadiness(Tokens(), http=httpx.AsyncClient(transport=_routes()))

    monkeypatch.setattr(foundry_commands, "FoundryReadiness", fake)
    assert main(["foundry", "readiness"]) == 0
    assert "Foundry ready for agent demos: YES" in capsys.readouterr().out
    assert main(["foundry", "readiness", "--json"]) == 0
    assert '"ready": true' in capsys.readouterr().out
    assert run_sync(fake(None), BINDING).ready
