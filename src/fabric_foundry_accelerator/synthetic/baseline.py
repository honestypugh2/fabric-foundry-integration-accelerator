"""Expected baselines: the numbers a correct build (local or Fabric) must reproduce.

A baseline records row counts per layer, Silver data-quality diagnostics, financial
reconciliation totals and every semantic-model measure. The committed baseline lets a live
Fabric run be compared against the local reference — evidence, not appearance.
"""

import json
from datetime import date
from pathlib import Path
from typing import cast

import duckdb
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import EvidenceCategory
from fabric_foundry_accelerator.models.semantic import SemanticModel
from fabric_foundry_accelerator.synthetic.generator import RawManifest
from fabric_foundry_accelerator.synthetic.measures import (
    MeasureScalar,
    evaluate_measures,
    normalize_value,
)
from fabric_foundry_accelerator.synthetic.medallion import (
    lakehouse_tables,
    open_lakehouse,
    silver_diagnostics,
)
from fabric_foundry_accelerator.synthetic.profiles import DatasetProfile, GoldModel

FLOAT_TOLERANCE = 1e-6

_FACT_TABLES: dict[GoldModel, tuple[str, str]] = {
    "hc_lab": ("gold_encounter_summary", "gold_financial"),
    "core_star": ("fact_encounter", "fact_claim"),
}


class Baseline(BaseModel):
    """Expected results for one profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    generator_version: str
    synthetic_notice: str
    observation_cutoff: date
    row_counts: dict[str, dict[str, int]]
    diagnostics: dict[str, int]
    reconciliation: dict[str, MeasureScalar]
    measures: dict[str, MeasureScalar]


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> MeasureScalar:
    row = con.execute(sql).fetchone()
    return normalize_value(row[0] if row else None)


def compute_baseline(
    output_root: Path, profile: DatasetProfile, manifest: RawManifest, model: SemanticModel
) -> Baseline:
    """Compute the baseline from persisted Parquet tables (read-back, not in-memory state)."""
    counts: dict[str, dict[str, int]] = {
        "raw": {f.name.removesuffix(".csv"): f.rows for f in manifest.files}
    }
    encounters, claims = _FACT_TABLES[profile.gold_model]
    with open_lakehouse(output_root, profile.id) as con:
        for layer, table, _ in lakehouse_tables(output_root, profile.id):
            row = con.execute(f'SELECT count(*) FROM "{table}"').fetchone()  # noqa: S608 - table names come from persisted file names validated at build
            counts.setdefault(layer, {})[table] = int(row[0]) if row else 0
        reconciliation = {
            "silver_claim_amount_total": _scalar(
                con, "SELECT sum(claim_amount) FROM silver_claims"
            ),
            "gold_claim_amount_total": _scalar(con, f"SELECT sum(claim_amount) FROM {claims}"),  # noqa: S608 - constant table name
            "silver_paid_amount_total": _scalar(con, "SELECT sum(paid_amount) FROM silver_claims"),
            "gold_paid_amount_total": _scalar(con, f"SELECT sum(paid_amount) FROM {claims}"),  # noqa: S608 - constant table name
            "silver_total_charges": _scalar(
                con, "SELECT sum(total_charges) FROM silver_encounters"
            ),
            "gold_total_charges": _scalar(con, f"SELECT sum(total_charges) FROM {encounters}"),  # noqa: S608 - constant table name
            "claim_amount_minus_recorded_charges": _scalar(
                con,
                "SELECT (SELECT sum(claim_amount) FROM silver_claims) "
                "- (SELECT sum(total_charges) FROM silver_encounters)",
            ),
        }
        return Baseline(
            profile=profile.id,
            generator_version=manifest.generator_version,
            synthetic_notice=manifest.synthetic_notice,
            observation_cutoff=manifest.observation_cutoff,
            row_counts=counts,
            diagnostics=silver_diagnostics(con),
            reconciliation=reconciliation,
            measures=evaluate_measures(con, model),
        )


def quirk_checks(manifest: RawManifest, diagnostics: dict[str, int]) -> list[CheckResult]:
    """Check that Silver diagnostics detect exactly the quirks the generator injected."""
    checks = [
        CheckResult(
            name=f"Silver detects injected quirk: {name}",
            passed=diagnostics.get(name) == expected,
            detail=f"detected {diagnostics.get(name)}, injected {expected}",
        )
        for name, expected in manifest.quirks.items()
    ]
    checks.extend(
        CheckResult(
            name=f"No unexpected issue: {name}",
            passed=diagnostics.get(name, 0) == 0,
            detail=f"detected {diagnostics.get(name, 0)}",
        )
        for name in ("encounter_chronology_violations", "notes_with_embedded_newline")
    )
    return checks


def reconciliation_checks(baseline: Baseline) -> list[CheckResult]:
    """Check that Gold financial totals reconcile with Silver."""
    pairs = (
        ("claim amount", "silver_claim_amount_total", "gold_claim_amount_total"),
        ("paid amount", "silver_paid_amount_total", "gold_paid_amount_total"),
        ("total charges", "silver_total_charges", "gold_total_charges"),
    )
    return [
        CheckResult(
            name=f"Gold reconciles with Silver: {label}",
            passed=baseline.reconciliation[silver] == baseline.reconciliation[gold],
            detail=(
                f"silver {baseline.reconciliation[silver]}, gold {baseline.reconciliation[gold]}"
            ),
            category=EvidenceCategory.SIMULATED_LOCALLY,
        )
        for label, silver, gold in pairs
    ]


def _differs(expected: object, actual: object) -> bool:
    if isinstance(expected, float) or isinstance(actual, float):
        if expected is None or actual is None:
            return expected is not actual
        return abs(float(str(expected)) - float(str(actual))) > FLOAT_TOLERANCE
    return expected != actual


def _as_mapping(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    items = cast("dict[object, object]", value)
    return {str(k): v for k, v in items.items()}


def compare_baselines(expected: Baseline, actual: Baseline) -> list[str]:
    """Return human-readable differences between two baselines (empty when equivalent)."""
    return _compare_section(
        "baseline", expected.model_dump(mode="json"), actual.model_dump(mode="json")
    )


def _compare_section(section: str, left: dict[str, object], right: dict[str, object]) -> list[str]:
    problems: list[str] = []
    for key in sorted(set(left) | set(right)):
        a, b = left.get(key), right.get(key)
        left_map, right_map = _as_mapping(a), _as_mapping(b)
        if left_map is not None and right_map is not None:
            problems.extend(_compare_section(f"{section}.{key}", left_map, right_map))
        elif _differs(a, b):
            problems.append(f"{section}.{key}: expected {a!r}, got {b!r}")
    return problems


def write_baseline(baseline: Baseline, path: Path) -> None:
    """Write a baseline as stable, pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(baseline.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_baseline(path: Path) -> Baseline:
    """Load a baseline JSON file."""
    return Baseline.model_validate_json(path.read_text(encoding="utf-8"))
