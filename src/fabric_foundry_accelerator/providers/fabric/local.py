"""Local Fabric Educational Provider.

A realistic *educational analog* of a Fabric workspace, lakehouse and semantic model, backed
by synthetic Parquet files and DuckDB. It is not a Fabric emulator. Every result is labeled
``LOCAL`` with ``cloud_operation_performed=False`` and names the Fabric service it stands in for.
"""

import asyncio
from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from fabric_foundry_accelerator.models.execution import (
    Evidence,
    EvidenceCategory,
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
)
from fabric_foundry_accelerator.models.semantic import SemanticModel, load_semantic_model
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError
from fabric_foundry_accelerator.providers.fabric.port import (
    MAX_PREVIEW_ROWS,
    ColumnInfo,
    ItemInfo,
    JsonScalar,
    MeasureValue,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)
from fabric_foundry_accelerator.synthetic.measures import evaluate_measures
from fabric_foundry_accelerator.synthetic.medallion import lakehouse_tables, open_lakehouse
from fabric_foundry_accelerator.synthetic.paths import semantic_model_path
from fabric_foundry_accelerator.synthetic.profiles import PROFILES
from fabric_foundry_accelerator.synthetic.sqlutil import quote_ident

PROVIDER_NAME = "Local Fabric Educational Provider"
WORKSPACE_ID = "local-ws-synthetic"
SIMULATION_NOTICE = (
    "LOCAL educational analog over synthetic Parquet data. No Microsoft Fabric, OneLake or "
    "Power BI operation was performed."
)
_LAKEHOUSE_PREFIX = "local-lh-"
_SEMANTIC_PREFIX = "local-sm-"


def _json_scalar(value: object) -> JsonScalar:
    if value is None or isinstance(value, str | bool | int | float):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    return str(value)


class LocalFabricProvider:
    """Read-only local implementation of the ``FabricProvider`` port."""

    def __init__(
        self,
        data_root: Path,
        *,
        output_root: Path | None = None,
        mode: OperatingMode = OperatingMode.OFFLINE,
    ) -> None:
        """Create a provider over built local data.

        Args:
            data_root: Root containing ``semantic/`` models.
            output_root: Root containing built ``bronze/``, ``silver/`` and ``gold/`` Parquet
                (defaults to ``data_root``).
            mode: Operating mode recorded on every envelope (OFFLINE or HYBRID).
        """
        if mode is OperatingMode.LIVE:
            raise ValueError("the local provider cannot run in LIVE mode")
        self._data_root = data_root
        self._output_root = output_root or data_root
        self._mode = mode

    @property
    def name(self) -> str:
        """Return the provider name."""
        return PROVIDER_NAME

    # ------------------------------------------------------------------ helpers
    def _built_profiles(self) -> list[str]:
        return [
            p
            for p in sorted(PROFILES)
            if lakehouse_tables(self._output_root, p)
            and semantic_model_path(self._data_root, p).is_file()
        ]

    def _profile_for(self, item_id: str, prefix: str) -> str:
        profile = item_id.removeprefix(prefix)
        if not item_id.startswith(prefix) or profile not in self._built_profiles():
            raise UnknownResourceError(f"unknown item {item_id!r}")
        return profile

    def _envelope[T](
        self,
        data: T,
        *,
        service: str,
        objective: str,
        evidence: str,
        correlation_id: str | None,
    ) -> ExecutionEnvelope[T]:
        return ExecutionEnvelope[T](
            operating_mode=self._mode,
            execution_label=ExecutionLabel.LOCAL,
            requested_provider=PROVIDER_NAME,
            selected_provider=PROVIDER_NAME,
            cloud_operation_performed=False,
            equivalent_fabric_service=service,
            teaching_objective=objective,
            simulation_notice=SIMULATION_NOTICE,
            data=data,
            correlation_id=correlation_id or new_correlation_id(),
            evidence=(Evidence(category=EvidenceCategory.SIMULATED_LOCALLY, statement=evidence),),
        )

    # ------------------------------------------------------------------ port
    async def list_workspaces(
        self, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[WorkspaceInfo, ...]]:
        """List the single local synthetic workspace."""
        workspace = WorkspaceInfo(
            id=WORKSPACE_ID,
            display_name="Synthetic Demo Workspace (LOCAL)",
            description="Local educational workspace: one lakehouse per built dataset profile.",
        )
        return self._envelope(
            (workspace,),
            service="Microsoft Fabric workspace",
            objective="Discover where governed data lives before reading it.",
            evidence="Listed the local synthetic workspace.",
            correlation_id=correlation_id,
        )

    async def list_items(
        self, workspace_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[ItemInfo, ...]]:
        """List lakehouse and semantic model items for every built profile."""
        if workspace_id != WORKSPACE_ID:
            raise UnknownResourceError(f"unknown workspace {workspace_id!r}")
        items: list[ItemInfo] = []
        for profile in self._built_profiles():
            items.append(
                ItemInfo(
                    id=f"{_LAKEHOUSE_PREFIX}{profile}",
                    display_name=f"{profile} lakehouse (LOCAL)",
                    type="Lakehouse",
                    workspace_id=WORKSPACE_ID,
                    description=PROFILES[profile].description,
                )
            )
            items.append(
                ItemInfo(
                    id=f"{_SEMANTIC_PREFIX}{profile}",
                    display_name=f"{profile} semantic model (LOCAL)",
                    type="SemanticModel",
                    workspace_id=WORKSPACE_ID,
                    description="Semantic model contract evaluated locally with DuckDB.",
                )
            )
        return self._envelope(
            tuple(items),
            service="Microsoft Fabric workspace items (Lakehouse, Semantic model)",
            objective="Inventory items before choosing which governed context to use.",
            evidence=f"Listed {len(items)} local items.",
            correlation_id=correlation_id,
        )

    async def list_tables(
        self, lakehouse_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[tuple[TableInfo, ...]]:
        """List Bronze, Silver and Gold tables with row counts and columns."""
        profile = self._profile_for(lakehouse_id, _LAKEHOUSE_PREFIX)
        tables = await asyncio.to_thread(self._describe_tables, profile)
        return self._envelope(
            tables,
            service="Fabric Lakehouse Delta tables (OneLake)",
            objective="See the medallion layers: Bronze preserves, Silver conforms, Gold serves.",
            evidence=f"Described {len(tables)} local Parquet tables.",
            correlation_id=correlation_id,
        )

    def _describe_tables(self, profile: str) -> tuple[TableInfo, ...]:
        result: list[TableInfo] = []
        with open_lakehouse(self._output_root, profile) as con:
            for layer, table, _ in lakehouse_tables(self._output_root, profile):
                ident = quote_ident(table)
                columns = tuple(
                    ColumnInfo(name=str(r[0]), data_type=str(r[1]))
                    for r in con.execute(f"DESCRIBE {ident}").fetchall()
                )
                count = con.execute(f"SELECT count(*) FROM {ident}").fetchone()  # noqa: S608 - validated identifier
                result.append(
                    TableInfo(
                        name=table,
                        layer=layer,
                        row_count=int(count[0]) if count else 0,
                        columns=columns,
                    )
                )
        return tuple(result)

    async def read_table(
        self,
        lakehouse_id: str,
        table: str,
        *,
        limit: int = 20,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[TablePreview]:
        """Return a bounded preview of a catalogued table. Free-form SQL is not accepted."""
        if not 1 <= limit <= MAX_PREVIEW_ROWS:
            raise InvalidRequestError(f"limit must be between 1 and {MAX_PREVIEW_ROWS}")
        profile = self._profile_for(lakehouse_id, _LAKEHOUSE_PREFIX)
        catalog = {name: layer for layer, name, _ in lakehouse_tables(self._output_root, profile)}
        if table not in catalog:
            raise UnknownResourceError(f"unknown table {table!r} in {lakehouse_id!r}")
        preview = await asyncio.to_thread(self._preview, profile, table, catalog[table], limit)
        return self._envelope(
            preview,
            service="Fabric Lakehouse SQL analytics endpoint (read)",
            objective="Inspect governed data safely: bounded, read-only, catalogued tables only.",
            evidence=f"Read {len(preview.rows)} of {preview.total_rows} rows from local {table}.",
            correlation_id=correlation_id,
        )

    def _preview(self, profile: str, table: str, layer: str, limit: int) -> TablePreview:
        ident = quote_ident(table)
        with open_lakehouse(self._output_root, profile) as con:
            cursor = con.execute(f"SELECT * FROM {ident} LIMIT ?", [limit])  # noqa: S608 - validated identifier
            names = [str(d[0]) for d in cursor.description or ()]
            rows = tuple(
                {name: _json_scalar(value) for name, value in zip(names, record, strict=True)}
                for record in cursor.fetchall()
            )
            types = {str(r[0]): str(r[1]) for r in con.execute(f"DESCRIBE {ident}").fetchall()}
            total = con.execute(f"SELECT count(*) FROM {ident}").fetchone()  # noqa: S608 - validated identifier
        total_rows = int(total[0]) if total else 0
        return TablePreview(
            table=table,
            layer=layer,
            columns=tuple(ColumnInfo(name=n, data_type=types[n]) for n in names),
            rows=rows,
            total_rows=total_rows,
            truncated=total_rows > len(rows),
        )

    async def get_semantic_model(
        self, semantic_model_id: str, *, correlation_id: str | None = None
    ) -> ExecutionEnvelope[SemanticModel]:
        """Return the semantic model contract for a profile."""
        profile = self._profile_for(semantic_model_id, _SEMANTIC_PREFIX)
        model = load_semantic_model(semantic_model_path(self._data_root, profile))
        return self._envelope(
            model,
            service="Power BI semantic model (Direct Lake) / Fabric IQ business vocabulary",
            objective="Separate data from semantics: entities, relationships, measures, terms.",
            evidence=f"Loaded local semantic model {model.id}.",
            correlation_id=correlation_id,
        )

    async def evaluate_measures(
        self,
        semantic_model_id: str,
        measures: Sequence[str] | None = None,
        *,
        correlation_id: str | None = None,
    ) -> ExecutionEnvelope[tuple[MeasureValue, ...]]:
        """Evaluate declared measures with no filter context."""
        profile = self._profile_for(semantic_model_id, _SEMANTIC_PREFIX)
        model = load_semantic_model(semantic_model_path(self._data_root, profile))
        names = list(measures) if measures is not None else [m.name for m in model.measures]
        unknown = [n for n in names if n not in {m.name for m in model.measures}]
        if unknown:
            raise UnknownResourceError(f"unknown measure(s): {', '.join(unknown)}")
        values = await asyncio.to_thread(self._evaluate, profile, model, names)
        return self._envelope(
            values,
            service="Power BI semantic model DAX query (Direct Lake)",
            objective="Measures are governed definitions, evaluated the same way every time.",
            evidence=f"Evaluated {len(values)} declared measures locally with DuckDB.",
            correlation_id=correlation_id,
        )

    def _evaluate(
        self, profile: str, model: SemanticModel, names: list[str]
    ) -> tuple[MeasureValue, ...]:
        with open_lakehouse(self._output_root, profile) as con:
            raw = evaluate_measures(con, model, names)
        return tuple(
            MeasureValue(
                name=name,
                display_name=model.measure(name).display_name,
                value=raw[name],
                format=model.measure(name).format,
                synthetic_demonstration=model.measure(name).synthetic_demonstration,
            )
            for name in names
        )
