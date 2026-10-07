"""Open Mirroring landing-zone simulation (documented contract, local files).

Reproduces the documented landing-zone format and change semantics so recovery can be taught
offline. Documented behavior (Microsoft Learn, "Open mirroring landing zone requirements and
format"):

* each table folder has ``_metadata.json`` with ``keyColumns``;
* data files are named with 20 digits in continuous sequence (``00000000000000000001.parquet``);
* the initial load may omit ``__rowMarker__`` and is treated as INSERT;
* incremental files carry ``__rowMarker__`` as the LAST column: 0 insert, 1 update,
  2 delete, 4 upsert. INSERT performs no duplicate-key check; UPDATE/UPSERT insert when the
  key is missing; DELETE of a missing key is a no-op; rows apply in file order;
* processed files move to ``_ProcessedFiles`` and are removed after seven days.

Simulation simplifications are labeled ASSUMPTION in recovery reports.
"""

import hashlib
import json
import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import duckdb

from fabric_foundry_accelerator.synthetic.sqlutil import quote_ident, sql_literal

ROW_MARKER_COLUMN = "__rowMarker__"
FILE_NAME_DIGITS = 20
PROCESSED_DIR = "_ProcessedFiles"
DOCUMENTED_RETENTION_DAYS = 7
_STATE_FILE = "_simulation_state.json"

Record = dict[str, str | None]
Change = tuple["RowMarker", Record]


class RowMarker(IntEnum):
    """Documented ``__rowMarker__`` values."""

    INSERT = 0
    UPDATE = 1
    DELETE = 2
    UPSERT = 4


@dataclass(frozen=True, slots=True)
class LandingFile:
    """A data file in the landing zone (pending or processed)."""

    sequence: int
    path: Path
    processed: bool


def landing_file_name(sequence: int) -> str:
    """Return the documented 20-digit file name for a sequence number."""
    if sequence < 1:
        raise ValueError("landing-zone sequences start at 1")
    return f"{sequence:0{FILE_NAME_DIGITS}d}.parquet"


def key_of(record: Record, key_columns: Sequence[str]) -> tuple[str | None, ...]:
    """Return the key tuple of a record."""
    return tuple(record.get(k) for k in key_columns)


def apply_changes(
    rows: Sequence[Record], changes: Sequence[Change], key_columns: Sequence[str]
) -> list[Record]:
    """Apply changes in order using the documented row-marker semantics.

    ASSUMPTION: when duplicate keys already exist, UPDATE/UPSERT replace every matching row and
    DELETE removes every matching row.
    """
    result = [dict(r) for r in rows]
    for marker, record in changes:
        key = key_of(record, key_columns)
        if marker is RowMarker.INSERT:
            result.append(dict(record))
            continue
        matches = [i for i, r in enumerate(result) if key_of(r, key_columns) == key]
        if marker is RowMarker.DELETE:
            doomed = set(matches)
            result = [r for i, r in enumerate(result) if i not in doomed]
        elif matches:
            for index in matches:
                result[index] = dict(record)
        else:
            result.append(dict(record))
    return result


def content_hash(rows: Sequence[Record]) -> str:
    """Return an order-independent SHA-256 over row contents (a real content hash, not a size)."""
    lines = sorted(json.dumps(r, sort_keys=True) for r in rows)
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_parquet_records(
    path: Path, columns: Sequence[str], records: Sequence[Record], markers: Sequence[int] | None
) -> None:
    """Write VARCHAR records (plus an optional trailing ``__rowMarker__``) to Parquet."""
    definitions = [f"{quote_ident(c)} VARCHAR" for c in columns]
    if markers is not None:
        # The documented marker column must be last; its mixed-case name is a fixed constant.
        definitions.append(f'"{ROW_MARKER_COLUMN}" INTEGER')
    definition = ", ".join(definitions)
    values = [
        [r.get(c) for c in columns] + ([markers[i]] if markers is not None else [])
        for i, r in enumerate(records)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect() as con:
        con.execute(f"CREATE TABLE landing ({definition})")
        if values:
            placeholders = ", ".join("?" for _ in definitions)
            con.executemany(f"INSERT INTO landing VALUES ({placeholders})", values)  # noqa: S608 - placeholders only
        con.execute(f"COPY landing TO {sql_literal(path)} (FORMAT parquet)")


def read_parquet_records(path: Path) -> tuple[list[str], list[Record], list[int] | None]:
    """Read records and, when present, the trailing ``__rowMarker__`` values."""
    with duckdb.connect() as con:
        cursor = con.execute("SELECT * FROM read_parquet(?)", [str(path)])
        names = [str(d[0]) for d in cursor.description or ()]
        raw = cursor.fetchall()
    has_marker = bool(names) and names[-1] == ROW_MARKER_COLUMN
    columns = names[:-1] if has_marker else names
    records: list[Record] = [
        {
            c: (None if v is None else str(v))
            for c, v in zip(columns, row[: len(columns)], strict=True)
        }
        for row in raw
    ]
    markers = [int(row[-1]) for row in raw] if has_marker else None
    return columns, records, markers


class LandingZoneTable:
    """A local folder that behaves like ``Files/LandingZone/<table>`` for one table."""

    def __init__(
        self, root: Path, table: str, columns: Sequence[str], key_columns: Sequence[str]
    ) -> None:
        """Create a landing-zone table handle (call ``initialize`` before writing)."""
        quote_ident(table)  # validates the name
        self.directory = root / "LandingZone" / table
        self.columns = tuple(columns)
        self.key_columns = tuple(key_columns)

    # ------------------------------------------------------------------ state
    def _state(self) -> dict[str, object]:
        path = self.directory / _STATE_FILE
        if not path.is_file():
            return {"last_sequence": 0, "processed_day": {}}
        loaded: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
        return loaded

    def _save_state(self, state: dict[str, object]) -> None:
        (self.directory / _STATE_FILE).write_text(
            json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _processed_days(self) -> dict[str, int]:
        raw = self._state()["processed_day"]
        assert isinstance(raw, dict)  # noqa: S101 - state file is written only by this class
        return {str(k): int(v) for k, v in raw.items()}  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]

    # ------------------------------------------------------------------ operations
    def initialize(self) -> Path:
        """Create the table folder and the documented ``_metadata.json``."""
        if self.directory.exists():
            shutil.rmtree(self.directory)
        self.directory.mkdir(parents=True)
        metadata = self.directory / "_metadata.json"
        metadata.write_text(
            json.dumps({"keyColumns": list(self.key_columns)}, indent=2), encoding="utf-8"
        )
        self._save_state({"last_sequence": 0, "processed_day": {}})
        return metadata

    def _next_path(self) -> tuple[int, Path]:
        state = self._state()
        sequence = int(str(state["last_sequence"])) + 1
        state["last_sequence"] = sequence
        self._save_state(state)
        return sequence, self.directory / landing_file_name(sequence)

    def write_initial_load(self, records: Sequence[Record]) -> LandingFile:
        """Write the initial load without ``__rowMarker__`` (treated as INSERT)."""
        sequence, path = self._next_path()
        write_parquet_records(path, self.columns, records, None)
        return LandingFile(sequence, path, processed=False)

    def write_changes(self, changes: Sequence[Change]) -> LandingFile:
        """Write an incremental file with ``__rowMarker__`` as the last column."""
        sequence, path = self._next_path()
        records = [{c: r.get(c) for c in self.columns} for _, r in changes]
        write_parquet_records(path, self.columns, records, [int(m) for m, _ in changes])
        return LandingFile(sequence, path, processed=False)

    def files(self) -> list[LandingFile]:
        """Return pending and retained processed files, ordered by sequence."""
        pending = [LandingFile(int(p.stem), p, False) for p in self.directory.glob("*.parquet")]
        processed = [
            LandingFile(int(p.stem), p, True)
            for p in (self.directory / PROCESSED_DIR).glob("*.parquet")
        ]
        return sorted(pending + processed, key=lambda f: f.sequence)

    def read(self, landing_file: LandingFile) -> list[Change]:
        """Read a file as ordered changes (initial loads become INSERTs)."""
        _, records, markers = read_parquet_records(landing_file.path)
        if markers is None:
            return [(RowMarker.INSERT, r) for r in records]
        return [(RowMarker(m), r) for m, r in zip(markers, records, strict=True)]

    def mark_processed(self, landing_file: LandingFile, day: int) -> LandingFile:
        """Move a file to ``_ProcessedFiles`` and record the day it was processed."""
        target = self.directory / PROCESSED_DIR / landing_file.path.name
        target.parent.mkdir(exist_ok=True)
        shutil.move(landing_file.path, target)
        state = self._state()
        days = self._processed_days()
        days[str(landing_file.sequence)] = day
        state["processed_day"] = days
        self._save_state(state)
        return LandingFile(landing_file.sequence, target, processed=True)

    def purge_expired(self, day: int, retention_days: int = DOCUMENTED_RETENTION_DAYS) -> list[int]:
        """Remove processed files older than the retention window; return purged sequences."""
        purged: list[int] = []
        for sequence, processed_day in sorted(
            self._processed_days().items(), key=lambda kv: int(kv[0])
        ):
            path = self.directory / PROCESSED_DIR / landing_file_name(int(sequence))
            if day - processed_day >= retention_days and path.exists():
                path.unlink()
                purged.append(int(sequence))
        return purged
