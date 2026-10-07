import json
from pathlib import Path

import duckdb
import pytest

from fabric_foundry_accelerator.models.execution import EvidenceCategory, ExecutionLabel
from fabric_foundry_accelerator.recovery.open_mirroring import (
    ROW_MARKER_COLUMN,
    LandingZoneTable,
    Record,
    RowMarker,
    apply_changes,
    content_hash,
    landing_file_name,
    read_parquet_records,
)
from fabric_foundry_accelerator.recovery.scenario import load_scenario, run_recovery_drill
from fabric_foundry_accelerator.recovery.snapshots import (
    SnapshotIntegrityError,
    SnapshotTarget,
    create_snapshot,
    detect_duplicates,
    load_snapshot_manifest,
    restore_snapshot,
    validate_idempotency,
    validate_keys,
    validate_ordering,
)

KEYS = ("id",)


def _row(key: str, value: str) -> Record:
    return {"id": key, "value": value}


# ------------------------------------------------------------------ documented row-marker semantics
def test_insert_does_not_check_for_duplicate_keys() -> None:
    rows = apply_changes([_row("a", "1")], [(RowMarker.INSERT, _row("a", "2"))], KEYS)
    assert len(rows) == 2
    assert detect_duplicates(rows, KEYS)[0].count == 2


@pytest.mark.parametrize("marker", [RowMarker.UPDATE, RowMarker.UPSERT])
def test_update_and_upsert_replace_existing_or_insert_missing(marker: RowMarker) -> None:
    rows = apply_changes(
        [_row("a", "1")], [(marker, _row("a", "2")), (marker, _row("b", "3"))], KEYS
    )
    assert sorted((r["id"], r["value"]) for r in rows) == [("a", "2"), ("b", "3")]


def test_delete_removes_matching_rows_and_ignores_missing_keys() -> None:
    rows = apply_changes(
        [_row("a", "1"), _row("a", "1b"), _row("b", "2")],
        [(RowMarker.DELETE, {"id": "a"}), (RowMarker.DELETE, {"id": "zzz"})],
        KEYS,
    )
    assert rows == [_row("b", "2")]


def test_changes_apply_in_file_order() -> None:
    rows = apply_changes(
        [],
        [
            (RowMarker.INSERT, _row("a", "1")),
            (RowMarker.UPDATE, _row("a", "2")),
            (RowMarker.UPDATE, _row("a", "3")),
        ],
        KEYS,
    )
    assert rows == [_row("a", "3")]


def test_content_hash_is_order_independent_and_content_sensitive() -> None:
    assert content_hash([_row("a", "1"), _row("b", "2")]) == content_hash(
        [_row("b", "2"), _row("a", "1")]
    )
    assert content_hash([_row("a", "1")]) != content_hash([_row("a", "2")])


# ------------------------------------------------------------------ landing-zone format
def test_landing_file_names_use_20_digits() -> None:
    assert landing_file_name(1) == "00000000000000000001.parquet"
    with pytest.raises(ValueError, match="start at 1"):
        landing_file_name(0)


def test_landing_zone_metadata_markers_and_retention(tmp_path: Path) -> None:
    landing = LandingZoneTable(tmp_path, "orders", ["id", "value"], KEYS)
    metadata = landing.initialize()
    assert json.loads(metadata.read_text(encoding="utf-8")) == {"keyColumns": ["id"]}
    initial = landing.write_initial_load([_row("a", "1")])
    _, _, markers = read_parquet_records(initial.path)
    assert markers is None  # initial load: no __rowMarker__, treated as INSERT
    assert landing.read(initial) == [(RowMarker.INSERT, _row("a", "1"))]

    change = landing.write_changes(
        [(RowMarker.UPSERT, _row("a", "2")), (RowMarker.DELETE, {"id": "b"})]
    )
    columns, records, markers = read_parquet_records(change.path)
    assert change.path.name == "00000000000000000002.parquet"
    assert columns == ["id", "value"] and markers == [4, 2]
    assert records[1]["value"] is None
    with duckdb.connect() as con:
        names = [
            d[0]
            for d in con.execute("SELECT * FROM read_parquet(?)", [str(change.path)]).description
            or ()
        ]
    assert names[-1] == ROW_MARKER_COLUMN

    landing.mark_processed(initial, day=0)
    processed = landing.mark_processed(change, day=3)
    assert processed.processed and [f.sequence for f in landing.files()] == [1, 2]
    assert landing.purge_expired(day=6) == []
    assert landing.purge_expired(day=7) == [1]
    assert landing.purge_expired(day=10) == [2]
    assert landing.files() == []


def test_landing_zone_rejects_unsafe_table_names(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        LandingZoneTable(tmp_path, "../escape", ["id"], KEYS)


# ------------------------------------------------------------------ snapshots and validators
def test_snapshot_round_trip_and_integrity_check(tmp_path: Path) -> None:
    rows = [_row("a", "1"), _row("b", "2")]
    target = SnapshotTarget(tmp_path, "orders", ("id", "value"), KEYS)
    manifest = create_snapshot(rows, target, day=7, watermark_sequence=8)
    assert manifest.snapshot_id == "orders-day007-seq00008"
    assert load_snapshot_manifest(tmp_path / f"{manifest.snapshot_id}.json") == manifest
    assert content_hash(restore_snapshot(manifest, tmp_path)) == content_hash(rows)
    tampered = manifest.model_copy(update={"content_hash": "0" * 64})
    with pytest.raises(SnapshotIntegrityError):
        restore_snapshot(tampered, tmp_path)


def test_validators() -> None:
    assert validate_ordering([5, 6, 7], 4, last_sequence=7).passed
    gap = validate_ordering([7], 4, last_sequence=7)
    assert not gap.passed and "[5, 6]" in gap.detail
    assert validate_keys([_row("a", "1")], KEYS, label="t").passed
    assert not validate_keys([_row("a", "1"), _row("a", "2"), {"id": None}], KEYS, label="t").passed
    assert validate_idempotency([], [(RowMarker.UPSERT, _row("a", "1"))], KEYS, label="t").passed
    assert not validate_idempotency(
        [], [(RowMarker.INSERT, _row("a", "1"))], KEYS, label="t"
    ).passed


# ------------------------------------------------------------------ full drill
def test_recovery_drill(tmp_path: Path, data_root: Path) -> None:
    envelope = run_recovery_drill(
        load_scenario(data_root / "recovery" / "scenario.yaml"),
        data_root=data_root,
        work_dir=tmp_path,
    )
    assert envelope.execution_label is ExecutionLabel.SIMULATED
    assert envelope.cloud_operation_performed is False
    report = envelope.data
    assert report.recovered is True
    assert report.counterfactual_recoverable is False
    assert report.duplicates_detected == 2
    categories = {step.category for step in report.steps}
    assert {
        EvidenceCategory.DOCUMENTED_FABRIC_BEHAVIOR,
        EvidenceCategory.SIMULATED_LOCALLY,
        EvidenceCategory.ASSUMPTION,
        EvidenceCategory.REQUIRES_TENANT_VALIDATION,
        EvidenceCategory.PRODUCTION_RECOMMENDATION,
    } <= categories
    restore = next(s for s in report.steps if s.name.startswith("Restore weekly"))
    assert all(c.passed for c in restore.checks)
    idempotency = next(s for s in report.steps if s.name == "Replay idempotency")
    assert {c.passed for c in idempotency.checks} == {True, False}
    assert report.scale.conceptual_rows == 100_000_000
    assert (tmp_path / "landing" / "LandingZone" / "claims" / "_metadata.json").is_file()


def test_scenario_must_reach_snapshot_day(tmp_path: Path, data_root: Path) -> None:
    scenario = load_scenario(data_root / "recovery" / "scenario.yaml").model_copy(
        update={"snapshot_day": 99}
    )
    with pytest.raises(ValueError, match="snapshot_day"):
        run_recovery_drill(scenario, data_root=data_root, work_dir=tmp_path)
