"""Local medallion pipeline: raw CSV -> Bronze -> Silver -> Gold Parquet, using DuckDB.

This is the *Local Fabric Educational Provider* data path. It is not a Fabric emulator: it
reproduces the medallion logic so the architecture can be taught and demonstrated offline.
The Fabric equivalent is a Lakehouse with Delta tables built by Spark notebooks.
"""

import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

import duckdb

from fabric_foundry_accelerator.models.checks import CheckResult, failed
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.synthetic.generator import load_manifest
from fabric_foundry_accelerator.synthetic.profiles import DatasetProfile, GoldModel
from fabric_foundry_accelerator.synthetic.sqlutil import quote_ident, sql_literal

LAYERS: tuple[str, ...] = ("bronze", "silver", "gold")


class DataValidationError(RuntimeError):
    """Raised when a layer fails a blocking validation (counts, keys, row preservation)."""

    def __init__(self, message: str, checks: Sequence[CheckResult] = ()) -> None:
        """Create the error with the failed checks attached."""
        super().__init__(message)
        self.checks = tuple(checks)


class DataNotBuiltError(FileNotFoundError):
    """Raised when local lakehouse tables have not been built yet."""


@dataclass(frozen=True, slots=True)
class TableSpec:
    """An output table produced from one SQL file."""

    name: str
    sql_file: str
    keys: tuple[str, ...] = ()

    @property
    def staging(self) -> bool:
        """Return True for staging tables (not written to Parquet)."""
        return self.name.startswith("_")


SILVER_SPECS: tuple[TableSpec, ...] = (
    TableSpec("silver_patients", "silver/silver_patients.sql", ("patient_id",)),
    TableSpec("silver_encounters", "silver/silver_encounters.sql", ("encounter_id",)),
    TableSpec("silver_conditions", "silver/silver_conditions.sql", ("condition_id",)),
    TableSpec("silver_claims", "silver/silver_claims.sql", ("claim_id",)),
    TableSpec("silver_vitals", "silver/silver_vitals.sql", ("vital_id",)),
    TableSpec("silver_medications", "silver/silver_medications.sql", ("medication_id",)),
    TableSpec("silver_clinical_notes", "silver/silver_clinical_notes.sql", ("note_id",)),
)
SILVER_MASTER_SPECS: tuple[TableSpec, ...] = (
    TableSpec("silver_facilities", "silver/silver_facilities.sql", ("facility_id",)),
    TableSpec("silver_payers", "silver/silver_payers.sql", ("payer_id",)),
)

GOLD_SPECS: dict[GoldModel, tuple[TableSpec, ...]] = {
    "hc_lab": (
        TableSpec("dim_date", "gold_shared/date_spine.sql", ("date",)),
        TableSpec("dim_facility", "gold_hc_lab/dim_facility.sql", ("facility_id",)),
        TableSpec("dim_payer", "gold_hc_lab/dim_payer.sql", ("payer_key",)),
        TableSpec("gold_population_health", "gold_shared/population_health.sql", ("patient_id",)),
        TableSpec("dim_patient", "gold_shared/dim_patient.sql", ("patient_id",)),
        TableSpec("gold_encounter_summary", "gold_shared/encounter_summary.sql", ("encounter_id",)),
        TableSpec("gold_financial", "gold_hc_lab/gold_financial.sql", ("claim_id",)),
        TableSpec("gold_readmissions", "gold_shared/readmissions.sql", ("index_encounter_id",)),
        TableSpec(
            "gold_ed_utilization", "gold_hc_lab/gold_ed_utilization.sql", ("patient_id", "year")
        ),
        TableSpec(
            "gold_alos", "gold_hc_lab/gold_alos.sql", ("primary_diagnosis_code", "facility_id")
        ),
    ),
    "core_star": (
        TableSpec("_date_spine", "gold_shared/date_spine.sql", ("date",)),
        TableSpec(
            "dim_date_admission", "gold_core_star/dim_date_admission.sql", ("admission_date",)
        ),
        TableSpec(
            "dim_date_discharge", "gold_core_star/dim_date_discharge.sql", ("discharge_date",)
        ),
        TableSpec("dim_date_claim", "gold_core_star/dim_date_claim.sql", ("claim_date",)),
        TableSpec("dim_facility", "gold_core_star/dim_facility.sql", ("facility_id",)),
        TableSpec("dim_payer", "gold_core_star/dim_payer.sql", ("payer_key",)),
        TableSpec("gold_population_health", "gold_shared/population_health.sql", ("patient_id",)),
        TableSpec("dim_patient", "gold_shared/dim_patient.sql", ("patient_id",)),
        TableSpec("fact_encounter", "gold_shared/encounter_summary.sql", ("encounter_id",)),
        TableSpec("fact_claim", "gold_core_star/fact_claim.sql", ("claim_id",)),
        TableSpec("gold_readmission_demo", "gold_shared/readmissions.sql", ("index_encounter_id",)),
    ),
}

# Gold tables whose row count must equal a Silver table (no row multiplication or loss).
ROW_PRESERVATION: dict[GoldModel, tuple[tuple[str, str], ...]] = {
    "hc_lab": (
        ("gold_encounter_summary", "silver_encounters"),
        ("gold_financial", "silver_claims"),
        ("gold_population_health", "silver_patients"),
        ("dim_patient", "silver_patients"),
    ),
    "core_star": (
        ("fact_encounter", "silver_encounters"),
        ("fact_claim", "silver_claims"),
        ("gold_population_health", "silver_patients"),
        ("dim_patient", "silver_patients"),
    ),
}


@dataclass(frozen=True, slots=True)
class BuildResult:
    """Summary of a local medallion build."""

    profile: str
    output_root: Path
    row_counts: dict[str, dict[str, int]]
    checks: tuple[CheckResult, ...]


def read_sql(relative: str) -> str:
    """Return the text of a packaged SQL file."""
    resource = files("fabric_foundry_accelerator.synthetic").joinpath("sql", *relative.split("/"))
    return resource.read_text(encoding="utf-8")


def layer_dir(output_root: Path, layer: str, profile_id: str) -> Path:
    """Return the Parquet directory for a layer and profile."""
    return output_root / layer / profile_id


def _count(con: duckdb.DuckDBPyConnection, table: str) -> int:
    row = con.execute(f"SELECT count(*) FROM {quote_ident(table)}").fetchone()  # noqa: S608 - validated identifier
    return int(row[0]) if row else 0


def _write_parquet(con: duckdb.DuckDBPyConnection, table: str, directory: Path) -> int:
    path = directory / f"{table}.parquet"
    con.execute(
        f"COPY {quote_ident(table)} TO {sql_literal(path)} (FORMAT parquet, COMPRESSION zstd)"
    )
    persisted = con.execute("SELECT count(*) FROM read_parquet(?)", [str(path)]).fetchone()
    return int(persisted[0]) if persisted else 0


def _reset(directory: Path) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def _load_bronze(
    con: duckdb.DuckDBPyConnection, profile: DatasetProfile, raw_dir: Path, ingested_at: datetime
) -> list[CheckResult]:
    manifest = load_manifest(raw_dir)
    checks: list[CheckResult] = []
    for table in profile.tables:
        name = f"bronze_{table}"
        con.execute(
            f"CREATE TABLE {quote_ident(name)} AS "  # noqa: S608 - validated identifier
            "SELECT *, ? AS _source_file, CAST(? AS TIMESTAMPTZ) AS _ingested_at "
            "FROM read_csv(?, header = true, all_varchar = true, quote = '\"', escape = '\"', "
            "delim = ',', strict_mode = true)",
            [f"raw/{profile.id}/{table}.csv", ingested_at, str(raw_dir / f"{table}.csv")],
        )
        expected, actual = manifest.entry(table).rows, _count(con, name)
        checks.append(
            CheckResult(
                name=f"{name}: parsed rows equal source baseline",
                passed=actual == expected,
                detail=f"parsed {actual}, expected {expected}",
            )
        )
    return checks


def _create(con: duckdb.DuckDBPyConnection, spec: TableSpec) -> None:
    con.execute(f"CREATE TABLE {quote_ident(spec.name)} AS {read_sql(spec.sql_file)}")


def key_check(con: duckdb.DuckDBPyConnection, table: str, keys: Sequence[str]) -> CheckResult:
    """Check that ``keys`` are populated and unique in ``table``."""
    cols = ", ".join(quote_ident(k) for k in keys)
    not_null = " AND ".join(f"{quote_ident(k)} IS NOT NULL" for k in keys)
    row = con.execute(
        f"SELECT count(*), count(DISTINCT ({cols})), count(*) FILTER (WHERE {not_null}) "  # noqa: S608 - validated identifiers
        f"FROM {quote_ident(table)}"
    ).fetchone()
    total, distinct, populated = (int(v) for v in row) if row else (0, 0, 0)
    return CheckResult(
        name=f"{table}: key ({', '.join(keys)}) populated and unique",
        passed=total == distinct == populated,
        detail=f"rows {total}, distinct keys {distinct}, populated keys {populated}",
    )


def foreign_key_check(
    con: duckdb.DuckDBPyConnection,
    fact: str,
    fact_column: str,
    dimension: str,
    dimension_column: str,
) -> CheckResult:
    """Check that every non-null fact key exists in the dimension (no missing dimension keys)."""
    f_col, d_col = f"f.{quote_ident(fact_column)}", f"d.{quote_ident(dimension_column)}"
    query = (
        f"SELECT count(*) FROM {quote_ident(fact)} AS f "  # noqa: S608 - validated identifiers
        f"LEFT JOIN {quote_ident(dimension)} AS d ON {f_col} = {d_col} "
        f"WHERE {f_col} IS NOT NULL AND {d_col} IS NULL"
    )
    row = con.execute(query).fetchone()
    missing = int(row[0]) if row else 0
    return CheckResult(
        name=f"{fact}.{fact_column} -> {dimension}.{dimension_column}: no missing dimension keys",
        passed=missing == 0,
        detail=f"{missing} fact rows reference a missing dimension key",
    )


def gold_checks(
    con: duckdb.DuckDBPyConnection, gold_model: GoldModel, semantic_model: SemanticModel | None
) -> list[CheckResult]:
    """Return grain, row-preservation and relationship checks for Gold."""
    checks = [key_check(con, s.name, s.keys) for s in GOLD_SPECS[gold_model] if not s.staging]
    for gold, silver in ROW_PRESERVATION[gold_model]:
        gold_rows, silver_rows = _count(con, gold), _count(con, silver)
        checks.append(
            CheckResult(
                name=f"{gold}: row count equals {silver} (no multiplication or loss)",
                passed=gold_rows == silver_rows,
                detail=f"{gold} {gold_rows}, {silver} {silver_rows}",
            )
        )
    if semantic_model is not None:
        checks.extend(
            foreign_key_check(con, r.to_table, r.to_column, r.from_table, r.from_column)
            for r in semantic_model.relationships
        )
    return checks


def build_profile(
    profile: DatasetProfile,
    *,
    raw_dir: Path,
    output_root: Path,
    semantic_model: SemanticModel | None = None,
    ingested_at: datetime | None = None,
) -> BuildResult:
    """Build Bronze, Silver and Gold Parquet tables for a profile and validate them.

    Raises:
        DataValidationError: when any blocking check fails. Nothing is reported as built.
    """
    timestamp = ingested_at or datetime.now(UTC)
    counts: dict[str, dict[str, int]] = {layer: {} for layer in LAYERS}
    with duckdb.connect() as con:
        checks = _load_bronze(con, profile, raw_dir, timestamp)
        _raise_if_failed("Bronze", checks)
        silver_specs = (SILVER_MASTER_SPECS if profile.reference_masters else ()) + SILVER_SPECS
        for spec in silver_specs:
            _create(con, spec)
        silver_checks = [key_check(con, s.name, s.keys) for s in silver_specs]
        silver_checks += [
            CheckResult(
                name=f"silver_{t}: row count preserved from bronze_{t}",
                passed=_count(con, f"silver_{t}") == _count(con, f"bronze_{t}"),
                detail=f"silver {_count(con, f'silver_{t}')}, bronze {_count(con, f'bronze_{t}')}",
            )
            for t in profile.tables
        ]
        _raise_if_failed("Silver", silver_checks)
        for spec in GOLD_SPECS[profile.gold_model]:
            _create(con, spec)
        g_checks = gold_checks(con, profile.gold_model, semantic_model)
        _raise_if_failed("Gold", g_checks)
        checks += silver_checks + g_checks

        layer_tables = {
            "bronze": [f"bronze_{t}" for t in profile.tables],
            "silver": [s.name for s in silver_specs],
            "gold": [s.name for s in GOLD_SPECS[profile.gold_model] if not s.staging],
        }
        for layer, tables in layer_tables.items():
            directory = layer_dir(output_root, layer, profile.id)
            _reset(directory)
            for table in tables:
                persisted = _write_parquet(con, table, directory)
                if persisted != _count(con, table):
                    raise DataValidationError(
                        f"{table}: persisted row count differs from built table"
                    )
                counts[layer][table] = persisted
    return BuildResult(profile.id, output_root, counts, tuple(checks))


def _raise_if_failed(layer: str, checks: Sequence[CheckResult]) -> None:
    problems = failed(list(checks))
    if problems:
        details = "; ".join(f"{c.name} ({c.detail})" for c in problems)
        raise DataValidationError(f"{layer} validation failed: {details}", problems)


def lakehouse_tables(output_root: Path, profile_id: str) -> list[tuple[str, str, Path]]:
    """Return ``(layer, table, path)`` for every built Parquet table of a profile."""
    found: list[tuple[str, str, Path]] = []
    for layer in LAYERS:
        directory = layer_dir(output_root, layer, profile_id)
        found.extend((layer, p.stem, p) for p in sorted(directory.glob("*.parquet")))
    return found


def open_lakehouse(output_root: Path, profile_id: str) -> duckdb.DuckDBPyConnection:
    """Open an in-memory DuckDB connection with a view per persisted table of a profile."""
    tables = lakehouse_tables(output_root, profile_id)
    if not tables:
        raise DataNotBuiltError(
            f"no local tables for profile {profile_id!r} under {output_root}; run `ffia data build`"
        )
    con = duckdb.connect()
    for _, table, path in tables:
        source = f"read_parquet({sql_literal(path)})"
        con.execute(f"CREATE VIEW {quote_ident(table)} AS SELECT * FROM {source}")  # noqa: S608 - validated
    return con


# Diagnostic name -> (Silver table, predicate). Counts rows matching the predicate.
DIAGNOSTICS: dict[str, tuple[str, str]] = {
    "overlapping_encounters": ("silver_encounters", "overlaps_prior_encounter"),
    "length_of_stay_mismatches": ("silver_encounters", "NOT is_los_consistent"),
    "encounter_chronology_violations": ("silver_encounters", "NOT is_chronology_valid"),
    "blank_total_charges": ("silver_encounters", "total_charges IS NULL"),
    "zero_claim_amounts": ("silver_claims", "claim_amount = 0"),
    "out_of_range_vitals": ("silver_vitals", "is_out_of_range"),
    "medication_chronology_violations": ("silver_medications", "NOT is_chronology_valid"),
    "notes_with_literal_newline": ("silver_clinical_notes", "has_literal_newline_sequence"),
    "notes_with_embedded_newline": ("silver_clinical_notes", "has_embedded_newline"),
    "conditions_with_blank_encounter_id": ("silver_conditions", "encounter_id IS NULL"),
}


def silver_diagnostics(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Return data-quality diagnostic counts computed from Silver."""
    result: dict[str, int] = {}
    for name, (table, predicate) in DIAGNOSTICS.items():
        query = f"SELECT count(*) FROM {quote_ident(table)} WHERE {predicate}"  # noqa: S608 - constants
        row = con.execute(query).fetchone()
        result[name] = int(row[0]) if row else 0
    return result
