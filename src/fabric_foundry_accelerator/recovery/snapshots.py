"""Snapshot, restore, replay and validation primitives for the recovery lab.

Weekly full Parquet snapshots are a *customer-implemented* pattern evaluated here; they are not
a Fabric feature. Git stores metadata and configuration, never table data, so table recovery
needs data copies such as these snapshots plus retained change files.
"""

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.recovery.open_mirroring import (
    Change,
    LandingZoneTable,
    Record,
    apply_changes,
    content_hash,
    key_of,
    read_parquet_records,
    write_parquet_records,
)


class SnapshotIntegrityError(RuntimeError):
    """Raised when a restored snapshot does not match its manifest."""


class SnapshotManifest(BaseModel):
    """Metadata describing one full snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: str
    table: str
    created_day: int
    watermark_sequence: int
    row_count: int
    content_hash: str
    key_columns: tuple[str, ...]
    columns: tuple[str, ...]
    file: str
    size_bytes: int


class DuplicateKey(BaseModel):
    """A key that appears more than once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: tuple[str | None, ...]
    count: int


@dataclass(frozen=True, slots=True)
class SnapshotTarget:
    """Where and what to snapshot."""

    directory: Path
    table: str
    columns: tuple[str, ...]
    key_columns: tuple[str, ...]


def create_snapshot(
    rows: Sequence[Record], target: SnapshotTarget, *, day: int, watermark_sequence: int
) -> SnapshotManifest:
    """Write a full Parquet snapshot plus manifest; the watermark is the last applied file."""
    snapshot_id = f"{target.table}-day{day:03d}-seq{watermark_sequence:05d}"
    data_path = target.directory / f"{snapshot_id}.parquet"
    write_parquet_records(data_path, target.columns, rows, None)
    manifest = SnapshotManifest(
        snapshot_id=snapshot_id,
        table=target.table,
        created_day=day,
        watermark_sequence=watermark_sequence,
        row_count=len(rows),
        content_hash=content_hash(rows),
        key_columns=target.key_columns,
        columns=target.columns,
        file=data_path.name,
        size_bytes=data_path.stat().st_size,
    )
    manifest_path = target.directory / f"{snapshot_id}.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def restore_snapshot(manifest: SnapshotManifest, directory: Path) -> list[Record]:
    """Restore rows from a snapshot and verify row count and content hash.

    Raises:
        SnapshotIntegrityError: when the restored data does not match the manifest.
    """
    _, rows, _ = read_parquet_records(directory / manifest.file)
    if len(rows) != manifest.row_count or content_hash(rows) != manifest.content_hash:
        raise SnapshotIntegrityError(
            f"snapshot {manifest.snapshot_id} failed integrity verification"
        )
    return rows


def load_snapshot_manifest(path: Path) -> SnapshotManifest:
    """Load a snapshot manifest JSON file."""
    return SnapshotManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


def available_changes(
    landing: LandingZoneTable, after_sequence: int
) -> list[tuple[int, list[Change]]]:
    """Return retained change files with sequence greater than ``after_sequence``."""
    return [(f.sequence, landing.read(f)) for f in landing.files() if f.sequence > after_sequence]


def replay_changes(
    rows: Sequence[Record], changes: Sequence[tuple[int, list[Change]]], key_columns: Sequence[str]
) -> list[Record]:
    """Apply change files in sequence order on top of restored rows."""
    result = list(rows)
    for _, file_changes in sorted(changes, key=lambda item: item[0]):
        result = apply_changes(result, file_changes, key_columns)
    return result


def detect_duplicates(rows: Sequence[Record], key_columns: Sequence[str]) -> list[DuplicateKey]:
    """Return keys that occur more than once."""
    counts = Counter(key_of(r, key_columns) for r in rows)
    return [
        DuplicateKey(key=k, count=c)
        for k, c in sorted(counts.items(), key=lambda kv: str(kv[0]))
        if c > 1
    ]


def validate_row_counts(rows: Sequence[Record], expected: int, *, label: str) -> CheckResult:
    """Check that a row count matches the expected value."""
    return CheckResult(
        name=f"{label}: row count matches",
        passed=len(rows) == expected,
        detail=f"actual {len(rows)}, expected {expected}",
    )


def validate_keys(rows: Sequence[Record], key_columns: Sequence[str], *, label: str) -> CheckResult:
    """Check that keys are populated and unique."""
    missing = sum(1 for r in rows if any(v in (None, "") for v in key_of(r, key_columns)))
    duplicates = detect_duplicates(rows, key_columns)
    return CheckResult(
        name=f"{label}: keys populated and unique",
        passed=missing == 0 and not duplicates,
        detail=f"{missing} missing keys, {len(duplicates)} duplicated keys",
    )


def validate_ordering(
    sequences: Sequence[int], after_sequence: int, *, last_sequence: int
) -> CheckResult:
    """Check that change files after the watermark are contiguous through ``last_sequence``."""
    expected = list(range(after_sequence + 1, last_sequence + 1))
    present = sorted(s for s in sequences if s > after_sequence)
    gaps = sorted(set(expected) - set(present))
    return CheckResult(
        name=f"Change files after watermark {after_sequence} are contiguous",
        passed=present == expected,
        detail="no gaps" if not gaps else f"missing sequences {gaps} (purged or never retained)",
    )


def validate_idempotency(
    rows: Sequence[Record], changes: Sequence[Change], key_columns: Sequence[str], *, label: str
) -> CheckResult:
    """Check whether applying a change file twice yields the same state as applying it once."""
    once = apply_changes(rows, changes, key_columns)
    twice = apply_changes(once, changes, key_columns)
    return CheckResult(
        name=f"{label}: replaying twice equals replaying once",
        passed=content_hash(once) == content_hash(twice),
        detail=(
            "idempotent"
            if content_hash(once) == content_hash(twice)
            else f"not idempotent: {len(twice) - len(once)} extra rows after a second replay"
        ),
    )
