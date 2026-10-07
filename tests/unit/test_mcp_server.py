from collections.abc import Callable
from typing import Any

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from fabric_foundry_accelerator.mcp.server import RateLimiter, build_mcp_server
from fabric_foundry_accelerator.services.container import Container

HC = "hc-lab-7file-v1"
GUIDE = "hc-01-fabric-mcp-powerbi-medallion-lab"


async def _call(
    container: Container, tool: str, arguments: dict[str, Any] | None = None
) -> dict[str, Any]:
    async with Client(build_mcp_server(container)) as client:
        result = await client.call_tool(tool, arguments or {})
    assert result.structured_content is not None
    return result.structured_content


async def test_only_manifest_tools_are_exposed_and_none_can_authorize(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    async with Client(build_mcp_server(container)) as client:
        tools = await client.list_tools()
    names = {t.name for t in tools}
    assert names == set(container.tool_manifest.enabled())
    assert not {n for n in names if "approve" in n or "execute" in n or "sql" in n or "shell" in n}
    plan_tool = next(t for t in tools if t.name == "generate_fabric_change_plan")
    assert plan_tool.annotations is not None and plan_tool.annotations.read_only_hint is False
    assert all(t.annotations and t.annotations.open_world_hint is False for t in tools)


async def test_disabled_tools_are_not_registered(make_container: Callable[..., Container]) -> None:
    container = make_container()
    manifest = container.tool_manifest
    disabled = tuple(
        t.model_copy(update={"enabled": t.name != "preview_table"}) for t in manifest.tools
    )
    container.tool_manifest = manifest.model_copy(update={"tools": disabled})
    async with Client(build_mcp_server(container)) as client:
        names = {t.name for t in await client.list_tools()}
    assert "preview_table" not in names


def test_manifest_tools_without_implementation_fail_fast(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    extra = container.tool_manifest.tools[0].model_copy(update={"name": "run_shell"})
    container.tool_manifest = container.tool_manifest.model_copy(
        update={"tools": (*container.tool_manifest.tools, extra)}
    )
    with pytest.raises(ValueError, match="without an implementation"):
        build_mcp_server(container)


def test_rate_limiter() -> None:
    now = [0.0]
    limiter = RateLimiter(clock=lambda: now[0])
    limiter.check("t", 2)
    limiter.check("t", 2)
    with pytest.raises(ToolError, match="rate limit"):
        limiter.check("t", 2)
    now[0] = 61
    limiter.check("t", 2)


async def test_rate_limit_is_enforced_through_the_server(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    manifest = container.tool_manifest
    tools = tuple(
        t.model_copy(update={"rate_limit_per_minute": 1})
        if t.name == "get_demo_capabilities"
        else t
        for t in manifest.tools
    )
    container.tool_manifest = manifest.model_copy(update={"tools": tools})
    async with Client(build_mcp_server(container)) as client:
        await client.call_tool("get_demo_capabilities", {})
        with pytest.raises(ToolError, match="rate limit"):
            await client.call_tool("get_demo_capabilities", {})


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("get_demo_capabilities", {}),
        ("get_runtime_status", {}),
        ("get_architecture_pattern", {"pattern_id": "P08"}),
        ("recommend_architecture_pattern", {"needs": ["business-system-write"]}),
        ("inspect_healthcare_scenario", {"profile": HC}),
        ("inspect_medallion_architecture", {"profile": HC}),
        ("preview_table", {"profile": HC, "table": "dim_facility", "limit": 2}),
        ("evaluate_measures", {"profile": HC, "measures": ["patient_count"]}),
        ("get_guide_step", {"guide_id": GUIDE, "step_id": "04-create-lakehouse"}),
        ("detect_duplicate_records", {"profile": HC, "table": "bronze_claims"}),
        ("evaluate_against_baseline", {"profile": HC}),
    ],
)
async def test_tools_return_honestly_labeled_envelopes(
    make_container: Callable[..., Container], tool: str, arguments: dict[str, Any]
) -> None:
    payload = await _call(make_container(), tool, arguments)
    assert payload["execution_label"] == "LOCAL"
    assert payload["cloud_operation_performed"] is False
    assert payload["simulation_notice"]


async def test_specific_tool_results(make_container: Callable[..., Container]) -> None:
    container = make_container()
    medallion = await _call(container, "inspect_medallion_architecture", {"profile": HC})
    assert {layer: len(tables) for layer, tables in medallion["data"].items()} == {
        "bronze": 7,
        "silver": 7,
        "gold": 10,
    }
    scenario = await _call(container, "inspect_healthcare_scenario", {"profile": HC})
    assert scenario["data"]["sources"]["vitals.csv"] == 4299
    duplicates = await _call(
        container, "detect_duplicate_records", {"profile": HC, "table": "gold_ed_utilization"}
    )
    assert duplicates["data"]["duplicated_keys"] == 0 and duplicates["data"]["key_columns"] == [
        "patient_id",
        "year",
    ]
    evaluation = await _call(
        container, "evaluate_against_baseline", {"profile": HC, "observed": {"patient_count": 200}}
    )
    assert (
        evaluation["data"]["observed_values_source"] == "caller-supplied"
        and evaluation["data"]["passed"] == 1
    )


async def test_plan_tool_proposes_but_never_executes(
    make_container: Callable[..., Container],
) -> None:
    container = make_container()
    payload = await _call(
        container,
        "generate_fabric_change_plan",
        {
            "operation": "create_lakehouse",
            "item_type": "Lakehouse",
            "item_name": "lake",
            "reason": "MCP plan test",
        },
    )
    plan = payload["data"]["plan"]
    assert plan["status"] == "PROPOSED" and "MCP cannot approve" in payload["data"]["next_step"]
    assert container.changes.workspace.items() == []
    revalidated = await _call(container, "validate_change_plan", {"change_id": plan["change_id"]})
    assert revalidated["data"]["change_id"] == plan["change_id"]
    audit = await _call(container, "get_audit_record", {"correlation_id": plan["correlation_id"]})
    assert [r["action"] for r in audit["data"]] == ["change:plan", "change:revalidate"]


async def test_recovery_tool(make_container: Callable[..., Container]) -> None:
    payload = await _call(make_container(), "simulate_recovery_drill")
    assert payload["execution_label"] == "SIMULATED" and payload["data"]["recovered"] is True


@pytest.mark.parametrize(
    ("tool", "arguments", "message"),
    [
        ("get_architecture_pattern", {"pattern_id": "P99"}, "unknown pattern"),
        ("recommend_architecture_pattern", {"needs": ["nope"]}, "unknown needs"),
        ("inspect_healthcare_scenario", {"profile": "nope"}, "unknown profile"),
        ("preview_table", {"profile": HC, "table": "dim_facility", "limit": 50}, "limit must be"),
        ("preview_table", {"profile": HC, "table": "x; DROP TABLE y"}, "unknown table"),
        ("get_guide_step", {"guide_id": "nope", "step_id": "x"}, "unknown guide"),
        ("get_guide_step", {"guide_id": GUIDE, "step_id": "x"}, "unknown step"),
        ("detect_duplicate_records", {"profile": HC, "table": "nope"}, "no declared key"),
        ("validate_change_plan", {"change_id": "missing"}, "unknown change"),
    ],
)
async def test_tool_errors_are_reported_and_audited(
    make_container: Callable[..., Container], tool: str, arguments: dict[str, Any], message: str
) -> None:
    container = make_container()
    with pytest.raises(ToolError, match=message):
        await _call(container, tool, arguments)
    assert container.audit.recent()[-1].success is False
