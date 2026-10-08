"""Local educational MCP server (FastMCP).

Only tools listed and enabled in ``config/policies/tools.yaml`` are registered. Each tool is
typed, bounded, rate limited, audited and returns an execution envelope. There is no shell,
SQL, filesystem, URL-fetch or REST-proxy tool, and no tool can approve or execute a change:
MCP standardizes access to capabilities; it does not grant authority.
"""

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fabric_foundry_accelerator.audit.store import AuditRecord, audit_from_envelope
from fabric_foundry_accelerator.models.changes import ChangeRequest, FabricTarget
from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.policies.engine import ToolManifestEntry
from fabric_foundry_accelerator.providers.errors import ProviderError
from fabric_foundry_accelerator.recovery.scenario import (
    DEFAULT_SCENARIO_PATH,
    load_scenario,
    run_recovery_drill,
)
from fabric_foundry_accelerator.services.changes import ChangeError
from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.evaluation import EvaluationRequest
from fabric_foundry_accelerator.services.runtime import runtime_status
from fabric_foundry_accelerator.synthetic.generator import load_manifest
from fabric_foundry_accelerator.synthetic.medallion import (
    GOLD_SPECS,
    SILVER_MASTER_SPECS,
    SILVER_SPECS,
    open_lakehouse,
)
from fabric_foundry_accelerator.synthetic.paths import raw_dir
from fabric_foundry_accelerator.synthetic.profiles import PROFILES
from fabric_foundry_accelerator.synthetic.sqlutil import quote_ident

JsonDict = dict[str, Any]
MAX_MCP_PREVIEW_ROWS = 20
CONTENT_NOTICE = "LOCAL content from the accelerator repository. No cloud operation was performed."


class RateLimiter:
    """Sliding one-minute window per tool."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        """Create the limiter."""
        self._calls: dict[str, deque[float]] = {}
        self._clock = clock

    def check(self, tool: str, limit_per_minute: int) -> None:
        """Raise ``ToolError`` when the tool exceeds its per-minute limit."""
        now = self._clock()
        window = self._calls.setdefault(tool, deque())
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= limit_per_minute:
            raise ToolError(f"rate limit exceeded for {tool} ({limit_per_minute} calls per minute)")
        window.append(now)


def _content_envelope[T](
    mode: OperatingMode, data: T, *, service: str, objective: str
) -> ExecutionEnvelope[T]:
    return ExecutionEnvelope[T](
        operating_mode=mode,
        execution_label=ExecutionLabel.LOCAL,
        requested_provider="Local MCP server",
        selected_provider="Local MCP server",
        cloud_operation_performed=False,
        equivalent_fabric_service=service,
        teaching_objective=objective,
        simulation_notice=CONTENT_NOTICE,
        data=data,
    )


def _profile(profile: str) -> str:
    if profile not in PROFILES:
        raise ToolError(f"unknown profile {profile!r}; valid: {sorted(PROFILES)}")
    return profile


def _table_keys(profile: str) -> dict[str, tuple[str, ...]]:
    spec = PROFILES[profile]
    keys = {
        s.name: s.keys
        for s in (*SILVER_SPECS, *SILVER_MASTER_SPECS, *GOLD_SPECS[spec.gold_model])
        if not s.staging
    }
    for name, columns in list(keys.items()):
        if name.startswith("silver_"):
            keys[name.replace("silver_", "bronze_", 1)] = columns
    return keys


def build_tools(container: Container) -> dict[str, Callable[..., Awaitable[JsonDict]]]:  # noqa: PLR0915 - one closure per tool keeps each tool small and explicit
    """Return the tool implementations keyed by manifest name."""
    fabric = container.fabric

    async def get_demo_capabilities() -> JsonDict:
        """Summarize what this server can demonstrate and how results are labeled."""
        data = {
            "labels": [label.value for label in ExecutionLabel],
            "tools": sorted(container.tool_manifest.enabled()),
            "cannot_do": [
                "approve changes",
                "execute changes",
                "run arbitrary SQL, shell, filesystem or URL access",
            ],
            "principle": "MCP standardizes capability access; identity and policy determine authority.",
        }
        return _content_envelope(
            container.mode,
            data,
            service="MCP tool discovery",
            objective="Know what a tool can and cannot do.",
        ).model_dump(mode="json")

    async def get_runtime_status() -> JsonDict:
        """Report operating mode, providers, preview flags, write mode and breaker state."""
        status = runtime_status(container)
        return _content_envelope(
            container.mode,
            status,
            service="Runtime status",
            objective="Always make execution state visible.",
        ).model_dump(mode="json")

    async def get_architecture_pattern(pattern_id: str) -> JsonDict:
        """Return one architecture pattern (P01-P24)."""
        try:
            pattern = container.catalog.get(pattern_id)
        except KeyError:
            raise ToolError(f"unknown pattern {pattern_id!r}") from None
        return _content_envelope(
            container.mode,
            pattern,
            service="Architecture pattern catalog",
            objective="Compare patterns before building.",
        ).model_dump(mode="json")

    async def recommend_architecture_pattern(needs: list[str]) -> JsonDict:
        """Recommend patterns for declared needs from the selection vocabulary."""
        from fabric_foundry_accelerator.patterns.catalog import (  # noqa: PLC0415
            UnknownNeedError,
            recommend,
        )

        try:
            ranked = recommend(container.catalog, needs)
        except UnknownNeedError as error:
            raise ToolError(str(error)) from None
        return _content_envelope(
            container.mode,
            ranked,
            service="Architecture selection guide",
            objective="Explain why a pattern fits.",
        ).model_dump(mode="json")

    async def inspect_healthcare_scenario(profile: str = "hc-lab-7file-v1") -> JsonDict:
        """Describe a synthetic dataset profile: sources, row counts and deliberate quirks."""
        manifest = load_manifest(raw_dir(container.settings.data_root, _profile(profile)))
        data = {
            "profile": profile,
            "description": PROFILES[profile].description,
            "synthetic_notice": manifest.synthetic_notice,
            "observation_cutoff": manifest.observation_cutoff.isoformat(),
            "sources": {f.name: f.rows for f in manifest.files},
            "quirks": manifest.quirks,
        }
        return _content_envelope(
            container.mode,
            data,
            service="Source system profiling",
            objective="Profile before transforming.",
        ).model_dump(mode="json")

    async def inspect_medallion_architecture(profile: str = "hc-lab-7file-v1") -> JsonDict:
        """List Bronze, Silver and Gold tables with row counts."""
        envelope = await fabric.list_tables(f"local-lh-{_profile(profile)}")
        layers: dict[str, dict[str, int | None]] = {}
        for table in envelope.data:
            layers.setdefault(table.layer, {})[table.name] = table.row_count
        summary = envelope.model_copy(update={"data": layers})
        return summary.model_dump(mode="json")

    async def preview_table(profile: str, table: str, limit: int = 10) -> JsonDict:
        """Return at most 20 rows of a catalogued table."""
        if not 1 <= limit <= MAX_MCP_PREVIEW_ROWS:
            raise ToolError(f"limit must be between 1 and {MAX_MCP_PREVIEW_ROWS}")
        envelope = await fabric.read_table(f"local-lh-{_profile(profile)}", table, limit=limit)
        return envelope.model_dump(mode="json")

    async def evaluate_measures(
        profile: str = "hc-lab-7file-v1", measures: list[str] | None = None
    ) -> JsonDict:
        """Evaluate declared measures by name."""
        envelope = await fabric.evaluate_measures(f"local-sm-{_profile(profile)}", measures)
        return envelope.model_dump(mode="json")

    async def get_guide_step(guide_id: str, step_id: str) -> JsonDict:
        """Return a Use-Case Guide step with prompts, checkpoint and evidence."""
        guide = container.guides.get(guide_id)
        if guide is None:
            raise ToolError(f"unknown guide {guide_id!r}; available: {sorted(container.guides)}")
        try:
            step = guide.step(step_id)
        except KeyError:
            raise ToolError(
                f"unknown step {step_id!r}; available: {[s.id for s in guide.steps]}"
            ) from None
        return _content_envelope(
            container.mode,
            step,
            service="Use-Case Guide",
            objective="One prompt at a time; stop at each checkpoint.",
        ).model_dump(mode="json")

    async def generate_fabric_change_plan(
        operation: str,
        item_type: Literal["Lakehouse", "Notebook", "SemanticModel", "Report"],
        item_name: str,
        reason: str,
        workspace_alias: str = "demo-dev",
        destination: Literal["LOCAL", "LIVE"] = "LOCAL",
        requested_by: str = "mcp-client",
    ) -> JsonDict:
        """Create a change PLAN. This tool never approves or executes anything."""
        request = ChangeRequest(
            operation=operation,
            target=FabricTarget(
                workspace_alias=workspace_alias,
                item_type=item_type,
                item_name=item_name,
                destination=destination,
            ),
            reason=reason,
            requested_by=requested_by,
        )
        plan = container.changes.plan(request)
        data = {
            "plan": plan.model_dump(mode="json"),
            "next_step": "A human approves or rejects this plan via POST /api/v1/approvals. MCP cannot approve it.",
        }
        return _content_envelope(
            container.mode,
            data,
            service="Fabric change plan (no execution)",
            objective="Models propose; humans approve.",
        ).model_dump(mode="json")

    async def validate_change_plan(change_id: str) -> JsonDict:
        """Re-validate a plan against policy and preconditions."""
        plan = container.changes.revalidate(change_id)
        return _content_envelope(
            container.mode,
            plan,
            service="Fabric change plan validation",
            objective="Validate deterministically.",
        ).model_dump(mode="json")

    async def simulate_recovery_drill() -> JsonDict:
        """Run the Open Mirroring snapshot + incremental + restore drill (SIMULATED)."""
        settings = container.settings
        scenario = load_scenario(settings.data_root / "recovery" / DEFAULT_SCENARIO_PATH.name)
        work = settings.data_root / "recovery" / "runs" / f"mcp-{new_correlation_id()}"
        envelope = await asyncio.to_thread(
            run_recovery_drill, scenario, data_root=settings.data_root, work_dir=work
        )
        return envelope.model_dump(mode="json")

    async def detect_duplicate_records(profile: str, table: str) -> JsonDict:
        """Count duplicated keys in a catalogued table."""
        keys = _table_keys(_profile(profile)).get(table)
        if keys is None:
            raise ToolError(f"table {table!r} has no declared key in profile {profile!r}")

        def count() -> tuple[int, int]:
            columns = ", ".join(quote_ident(k) for k in keys)
            query = (
                f"SELECT count(*), coalesce(sum(n), 0) FROM (SELECT {columns}, count(*) AS n "  # noqa: S608 - validated identifiers
                f"FROM {quote_ident(table)} GROUP BY {columns} HAVING count(*) > 1)"
            )
            with open_lakehouse(container.settings.lakehouse_root, profile) as con:
                row = con.execute(query).fetchone()
            return (int(row[0]), int(row[1])) if row else (0, 0)

        duplicated_keys, rows = await asyncio.to_thread(count)
        data = {
            "table": table,
            "key_columns": list(keys),
            "duplicated_keys": duplicated_keys,
            "rows_in_duplicated_keys": rows,
        }
        return _content_envelope(
            container.mode,
            data,
            service="Lakehouse data-quality check",
            objective="Treat duplicates as a data-quality finding.",
        ).model_dump(mode="json")

    async def evaluate_against_baseline(
        profile: str = "hc-lab-7file-v1",
        observed: dict[str, float | int | None] | None = None,
        observed_label: Literal["LIVE", "HYBRID", "LOCAL", "MOCKED"] = "LIVE",
    ) -> JsonDict:
        """Compare observed (or local) measure values with the committed expected baseline."""
        request = EvaluationRequest(
            profile=_profile(profile), observed=observed, observed_label=observed_label
        )
        envelope = await container.evaluation.run(request)
        return envelope.model_dump(mode="json")

    async def get_audit_record(correlation_id: str) -> JsonDict:
        """Return redacted audit records for a correlation ID."""
        records = container.audit.for_correlation(correlation_id)
        return _content_envelope(
            container.mode, records, service="Audit log", objective="Evidence of what ran and why."
        ).model_dump(mode="json")

    return {
        "get_demo_capabilities": get_demo_capabilities,
        "get_runtime_status": get_runtime_status,
        "get_architecture_pattern": get_architecture_pattern,
        "recommend_architecture_pattern": recommend_architecture_pattern,
        "inspect_healthcare_scenario": inspect_healthcare_scenario,
        "inspect_medallion_architecture": inspect_medallion_architecture,
        "preview_table": preview_table,
        "evaluate_measures": evaluate_measures,
        "get_guide_step": get_guide_step,
        "generate_fabric_change_plan": generate_fabric_change_plan,
        "validate_change_plan": validate_change_plan,
        "simulate_recovery_drill": simulate_recovery_drill,
        "detect_duplicate_records": detect_duplicate_records,
        "evaluate_against_baseline": evaluate_against_baseline,
        "get_audit_record": get_audit_record,
    }


def _governed(
    container: Container,
    entry: ToolManifestEntry,
    implementation: Callable[..., Awaitable[JsonDict]],
    limiter: RateLimiter,
) -> Callable[..., Awaitable[JsonDict]]:
    """Wrap a tool with rate limiting, error translation and auditing (signature preserved)."""
    import functools  # noqa: PLC0415

    @functools.wraps(implementation)
    async def governed(*args: object, **kwargs: object) -> JsonDict:
        limiter.check(entry.name, entry.rate_limit_per_minute)
        try:
            result = await implementation(*args, **kwargs)
        except ToolError:
            _audit_tool(container, entry, success=False)
            raise
        except (ProviderError, ChangeError, ValueError) as error:
            _audit_tool(container, entry, success=False)
            raise ToolError(f"{type(error).__name__}: {error}") from None
        _audit_tool(container, entry, success=True, result=result)
        return result

    return governed


def _audit_tool(
    container: Container, entry: ToolManifestEntry, *, success: bool, result: JsonDict | None = None
) -> None:
    if not entry.audit:
        return
    if result is not None and "execution_label" in result:
        envelope = ExecutionEnvelope[object].model_validate(result)
        record = audit_from_envelope(
            envelope,
            actor="mcp-client",
            action=f"mcp:{entry.name}",
            capability="mcp",
            tool=entry.name,
            success=success,
        )
    else:
        record = AuditRecord(
            correlation_id=new_correlation_id(),
            actor="mcp-client",
            action=f"mcp:{entry.name}",
            capability="mcp",
            requested_provider="Local MCP server",
            selected_provider="Local MCP server",
            operating_mode=container.mode,
            execution_label=ExecutionLabel.LOCAL,
            cloud_operation_performed=False,
            success=success,
            tool=entry.name,
        )
    container.audit.record(record)


def build_mcp_server(container: Container, *, limiter: RateLimiter | None = None) -> FastMCP:
    """Build the allow-listed MCP server.

    Raises:
        ValueError: when the manifest enables a tool that has no implementation.
    """
    manifest = container.tool_manifest
    implementations = build_tools(container)
    unknown = sorted(set(manifest.enabled()) - set(implementations))
    if unknown:
        raise ValueError(f"manifest enables tools without an implementation: {unknown}")
    server = FastMCP(
        name=manifest.server.name,
        instructions=(
            f"{manifest.server.description} Every result carries an execution label; LOCAL and "
            "SIMULATED results never represent a real Fabric, Foundry or Power BI operation."
        ),
    )
    rate_limiter = limiter or RateLimiter()
    for name, entry in manifest.enabled().items():
        server.tool(
            _governed(container, entry, implementations[name], rate_limiter),
            name=name,
            description=entry.description,
            tags={entry.classification},
            timeout=entry.timeout_seconds,
            annotations=ToolAnnotations(
                read_only_hint=entry.read_only,
                destructive_hint=False,
                idempotent_hint=entry.read_only,
                open_world_hint=False,
            ),
        )
    return server
