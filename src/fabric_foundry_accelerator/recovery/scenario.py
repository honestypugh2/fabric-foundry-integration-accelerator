"""Open Mirroring recovery drill: snapshot + incrementals + failure + restore + replay.

Every step is labeled with an evidence category so learners can separate what was
SIMULATED LOCALLY from DOCUMENTED FABRIC BEHAVIOR, what REQUIRES TENANT VALIDATION, what is an
ASSUMPTION, and what is a PRODUCTION RECOMMENDATION.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import duckdb
import yaml
from pydantic import BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.checks import CheckResult
from fabric_foundry_accelerator.models.execution import (
    EvidenceCategory,
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
)
from fabric_foundry_accelerator.recovery.open_mirroring import (
    DOCUMENTED_RETENTION_DAYS,
    Change,
    LandingZoneTable,
    Record,
    RowMarker,
    apply_changes,
    content_hash,
    key_of,
)
from fabric_foundry_accelerator.recovery.snapshots import (
    SnapshotManifest,
    SnapshotTarget,
    available_changes,
    create_snapshot,
    detect_duplicates,
    replay_changes,
    restore_snapshot,
    validate_idempotency,
    validate_keys,
    validate_ordering,
    validate_row_counts,
)
from fabric_foundry_accelerator.synthetic.generator import load_manifest
from fabric_foundry_accelerator.synthetic.paths import raw_dir

DEFAULT_SCENARIO_PATH = Path("data/synthetic/recovery/scenario.yaml")
PROVIDER_NAME = "Local Open Mirroring Simulator"
SIMULATION_NOTICE = (
    "SIMULATED LOCALLY. Landing-zone files, mirroring and recovery ran on local files only. "
    "No Fabric mirrored database, OneLake or landing-zone operation was performed."
)


class DaySpec(BaseModel):
    """Change volume for one simulated day."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    day: int = Field(ge=1)
    updates: int = Field(default=0, ge=0)
    inserts: int = Field(default=0, ge=0)
    deletes: int = Field(default=0, ge=0)
    marker: Literal["standard", "upsert"] = "standard"
    resend_previous_inserts: bool = False
    remediate_duplicates: bool = False


class ConceptualScale(BaseModel):
    """Scale metadata: the large fact table we describe but never generate locally."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_rows: int = Field(gt=0)
    note: str


class RecoveryScenario(BaseModel):
    """Recovery drill definition (``data/synthetic/recovery/scenario.yaml``)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal[1]
    name: str
    source_profile: str
    table: str
    key_columns: tuple[str, ...]
    seed: int
    retention_days: int = DOCUMENTED_RETENTION_DAYS
    snapshot_day: int
    failure_day: int
    conceptual_scale: ConceptualScale
    days: tuple[DaySpec, ...]


class RecoveryStep(BaseModel):
    """One narrated step of the drill."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    day: int | None
    summary: str
    category: EvidenceCategory
    checks: tuple[CheckResult, ...] = ()


class ScaleEstimate(BaseModel):
    """Extrapolated sizes for the conceptual table. Estimates, not measurements."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    local_rows: int
    local_snapshot_bytes: int
    conceptual_rows: int
    estimated_snapshot_gib: float
    estimated_daily_change_rows: int
    note: str


class RecoveryReport(BaseModel):
    """Outcome of the recovery drill."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenario: str
    table: str
    steps: tuple[RecoveryStep, ...]
    recovered: bool
    counterfactual_recoverable: bool
    duplicates_detected: int
    snapshot: SnapshotManifest
    scale: ScaleEstimate


def load_scenario(path: Path = DEFAULT_SCENARIO_PATH) -> RecoveryScenario:
    """Load and validate a recovery scenario."""
    return RecoveryScenario.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


class _ChangeFactory:
    """Creates deterministic incremental changes from the current mirrored state."""

    def __init__(self, scenario: RecoveryScenario, columns: Sequence[str]) -> None:
        self.rng = random.Random(scenario.seed)
        self.key_columns = scenario.key_columns
        self.columns = tuple(columns)
        self.next_id = 900_001
        self.previous_inserts: list[Record] = []

    def create_incremental_change(self, state: Sequence[Record], spec: DaySpec) -> list[Change]:
        """Return the ordered changes for one day."""
        changes: list[Change] = []
        if spec.remediate_duplicates:
            changes.extend(self._remediation(state))
        unique = {key_of(r, self.key_columns): r for r in state}
        candidates = sorted(unique.values(), key=lambda r: str(key_of(r, self.key_columns)))
        update_marker = RowMarker.UPSERT if spec.marker == "upsert" else RowMarker.UPDATE
        insert_marker = RowMarker.UPSERT if spec.marker == "upsert" else RowMarker.INSERT
        chosen = self.rng.sample(candidates, spec.updates + spec.deletes)
        for record in chosen[: spec.updates]:
            updated = dict(record)
            updated["claim_status"] = (
                "Paid" if record.get("claim_status") != "Paid" else "Paid on Appeal"
            )
            updated["days_to_payment"] = str(self.rng.randint(5, 60))
            changes.append((update_marker, updated))
        for record in chosen[spec.updates :]:
            changes.append((RowMarker.DELETE, {k: record.get(k) for k in self.key_columns}))
        inserted: list[Record] = []
        for template in self.rng.sample(candidates, spec.inserts):
            new = dict(template)
            new[self.key_columns[0]] = f"SYN-C-{self.next_id:06d}"
            self.next_id += 1
            inserted.append(new)
            changes.append((insert_marker, new))
        if spec.resend_previous_inserts:
            # Source-query defect: yesterday's inserts are re-sent as INSERT (no dedupe).
            changes.extend((RowMarker.INSERT, dict(r)) for r in self.previous_inserts)
        self.previous_inserts = inserted
        return changes

    def _remediation(self, state: Sequence[Record]) -> list[Change]:
        latest: dict[tuple[str | None, ...], Record] = {}
        for record in state:
            latest[key_of(record, self.key_columns)] = record
        fixes: list[Change] = []
        for duplicate in detect_duplicates(state, self.key_columns):
            keys = dict(zip(self.key_columns, duplicate.key, strict=True))
            fixes.append((RowMarker.DELETE, keys))
            fixes.append((RowMarker.UPSERT, dict(latest[duplicate.key])))
        return fixes


def _documented_steps(scenario: RecoveryScenario) -> list[RecoveryStep]:
    return [
        RecoveryStep(
            name="Landing-zone contract",
            day=None,
            summary=(
                "Each table folder has _metadata.json with keyColumns; files use 20-digit "
                "continuous sequence names; __rowMarker__ is the last column (0 insert, "
                "1 update, 2 delete, 4 upsert); INSERT does not check for duplicate keys; "
                "processed files move to _ProcessedFiles and are removed after "
                f"{DOCUMENTED_RETENTION_DAYS} days."
            ),
            category=EvidenceCategory.DOCUMENTED_FABRIC_BEHAVIOR,
        ),
        RecoveryStep(
            name="Git versus data",
            day=None,
            summary=(
                "Fabric Git integration tracks item definitions and metadata only; it never stores "
                "table data. Recovering table contents needs data copies (snapshots) and changes."
            ),
            category=EvidenceCategory.DOCUMENTED_FABRIC_BEHAVIOR,
        ),
        RecoveryStep(
            name="Simulation simplifications",
            day=None,
            summary=(
                "Values are stored as text; the service's 'last file left in place' behavior is "
                "modeled by a sequence counter; UPDATE/UPSERT replace and DELETE removes every row "
                "sharing a duplicated key. Replaying processed files assumes the publisher "
                "retained its own copies."
            ),
            category=EvidenceCategory.ASSUMPTION,
        ),
        RecoveryStep(
            name="What needs tenant validation",
            day=None,
            summary=(
                "Whether processed files remain readable for replay, actual cleanup timing, and "
                f"restore throughput at {scenario.conceptual_scale.fact_rows:,} rows must be "
                "validated in a Fabric tenant. Mirroring is not documented as a backup mechanism."
            ),
            category=EvidenceCategory.REQUIRES_TENANT_VALIDATION,
        ),
    ]


@dataclass(slots=True)
class _Drill:
    """Mutable drill context: the landing zone, snapshot folder and narrated steps."""

    scenario: RecoveryScenario
    columns: tuple[str, ...]
    landing: LandingZoneTable
    snapshots_dir: Path
    steps: list[RecoveryStep]

    @property
    def keys(self) -> tuple[str, ...]:
        return self.scenario.key_columns

    def snapshot(self, rows: Sequence[Record], *, day: int, watermark: int) -> SnapshotManifest:
        target = SnapshotTarget(self.snapshots_dir, self.scenario.table, self.columns, self.keys)
        return create_snapshot(rows, target, day=day, watermark_sequence=watermark)

    def recover(
        self, snapshot: SnapshotManifest, expected: Sequence[Record], last: int, name: str
    ) -> tuple[bool, RecoveryStep]:
        changes = available_changes(self.landing, snapshot.watermark_sequence)
        sequences = [s for s, _ in changes]
        ordering = validate_ordering(sequences, snapshot.watermark_sequence, last_sequence=last)
        if not ordering.passed:
            return False, RecoveryStep(
                name=name,
                day=None,
                summary=(
                    f"Snapshot {snapshot.snapshot_id} cannot be brought current: retained change "
                    "files have a gap. Recovery point objective not met; re-seed the mirror from "
                    "the source."
                ),
                category=EvidenceCategory.SIMULATED_LOCALLY,
                checks=(ordering,),
            )
        restored = restore_snapshot(snapshot, self.snapshots_dir)
        recovered = replay_changes(restored, changes, self.keys)
        matches = content_hash(recovered) == content_hash(expected)
        checks = (
            ordering,
            validate_row_counts(recovered, len(expected), label="Recovered table"),
            validate_keys(recovered, self.keys, label="Recovered table"),
            CheckResult(
                name="Recovered content hash equals pre-failure hash",
                passed=matches,
                detail="match" if matches else "mismatch",
            ),
        )
        return all(c.passed for c in checks), RecoveryStep(
            name=name,
            day=None,
            summary=(
                f"Restored {snapshot.snapshot_id} and replayed {len(changes)} retained change "
                f"files (sequences {sequences})."
            ),
            category=EvidenceCategory.SIMULATED_LOCALLY,
            checks=checks,
        )


def _read_source(
    scenario: RecoveryScenario, data_root: Path
) -> tuple[tuple[str, ...], list[Record]]:
    source = raw_dir(data_root, scenario.source_profile)
    columns = load_manifest(source).entry(scenario.table).columns
    with duckdb.connect() as con:
        cursor = con.execute(
            "SELECT * FROM read_csv(?, header = true, all_varchar = true, "
            "quote = '\"', escape = '\"')",
            [str(source / f"{scenario.table}.csv")],
        )
        rows: list[Record] = [dict(zip(columns, r, strict=True)) for r in cursor.fetchall()]
    return columns, rows


def run_recovery_drill(
    scenario: RecoveryScenario, *, data_root: Path, work_dir: Path
) -> ExecutionEnvelope[RecoveryReport]:
    """Run the drill end to end in ``work_dir`` and return a SIMULATED envelope."""
    columns, initial = _read_source(scenario, data_root)
    landing = LandingZoneTable(work_dir / "landing", scenario.table, columns, scenario.key_columns)
    landing.initialize()
    drill = _Drill(scenario, columns, landing, work_dir / "snapshots", _documented_steps(scenario))
    drill.snapshots_dir.mkdir(parents=True, exist_ok=True)

    first = landing.write_initial_load(initial)
    state = apply_changes([], landing.read(first), drill.keys)
    landing.mark_processed(first, day=0)
    drill.steps.append(
        RecoveryStep(
            name="Initial load",
            day=0,
            summary=(
                f"Sequence {first.sequence} written without __rowMarker__; "
                f"{len(state)} rows mirrored as INSERT."
            ),
            category=EvidenceCategory.SIMULATED_LOCALLY,
            checks=(validate_keys(state, drill.keys, label="After initial load"),),
        )
    )
    day0 = drill.snapshot(state, day=0, watermark=first.sequence)
    state, weekly, duplicates_seen = _run_days(drill, state)

    last_sequence = max(f.sequence for f in landing.files())
    drill.steps.append(
        RecoveryStep(
            name="Failure",
            day=scenario.failure_day,
            summary=(
                f"Mirrored table lost (simulated). Pre-failure state: {len(state)} rows, "
                "content hash recorded."
            ),
            category=EvidenceCategory.SIMULATED_LOCALLY,
        )
    )
    recovered_ok, recovery_step = drill.recover(
        weekly, state, last_sequence, "Restore weekly snapshot + replay retained changes"
    )
    counterfactual_ok, counterfactual_step = drill.recover(
        day0, state, last_sequence, "Counterfactual: weekly snapshot missing"
    )
    restored = restore_snapshot(weekly, drill.snapshots_dir)
    idempotency = tuple(
        validate_idempotency(restored, changes, drill.keys, label=f"Sequence {sequence}")
        for sequence, changes in available_changes(landing, weekly.watermark_sequence)
    )
    scale = _scale(scenario, weekly)
    drill.steps += [
        recovery_step,
        counterfactual_step,
        RecoveryStep(
            name="Replay idempotency",
            day=scenario.failure_day,
            summary=(
                "Files containing INSERT markers are not idempotent; replay each sequence exactly "
                "once after the watermark, or publish UPSERT (4) markers for keyed tables."
            ),
            category=EvidenceCategory.PRODUCTION_RECOMMENDATION,
            checks=idempotency,
        ),
        RecoveryStep(
            name="Scale estimate",
            day=None,
            summary=(
                f"Extrapolated snapshot ~{scale.estimated_snapshot_gib} GiB and "
                f"~{scale.estimated_daily_change_rows:,} changed rows/day for "
                f"{scale.conceptual_rows:,} rows. {scale.note}"
            ),
            category=EvidenceCategory.ASSUMPTION,
        ),
    ]
    report = RecoveryReport(
        scenario=scenario.name,
        table=scenario.table,
        steps=tuple(drill.steps),
        recovered=recovered_ok,
        counterfactual_recoverable=counterfactual_ok,
        duplicates_detected=duplicates_seen,
        snapshot=weekly,
        scale=scale,
    )
    return ExecutionEnvelope[RecoveryReport](
        operating_mode=OperatingMode.OFFLINE,
        execution_label=ExecutionLabel.SIMULATED,
        requested_provider=PROVIDER_NAME,
        selected_provider=PROVIDER_NAME,
        cloud_operation_performed=False,
        equivalent_fabric_service="Fabric Open Mirroring landing zone and mirrored database",
        teaching_objective=(
            "Recover a mirrored table from a snapshot plus retained incrementals, and see when "
            "recovery is impossible."
        ),
        simulation_notice=SIMULATION_NOTICE,
        data=report,
    )


def _run_days(drill: _Drill, state: list[Record]) -> tuple[list[Record], SnapshotManifest, int]:
    factory = _ChangeFactory(drill.scenario, drill.columns)
    weekly: SnapshotManifest | None = None
    duplicates_seen = 0
    for spec in drill.scenario.days:
        changes = factory.create_incremental_change(state, spec)
        written = drill.landing.write_changes(changes)
        state = apply_changes(state, drill.landing.read(written), drill.keys)
        drill.landing.mark_processed(written, day=spec.day)
        purged = drill.landing.purge_expired(spec.day, drill.scenario.retention_days)
        duplicates = len(detect_duplicates(state, drill.keys))
        duplicates_seen = max(duplicates_seen, duplicates)
        outcome = _DayOutcome(written.sequence, len(changes), tuple(purged), duplicates, len(state))
        drill.steps.append(_day_step(spec, outcome))
        if spec.day == drill.scenario.snapshot_day:
            weekly = drill.snapshot(state, day=spec.day, watermark=written.sequence)
            drill.steps.append(
                RecoveryStep(
                    name="Weekly full snapshot",
                    day=spec.day,
                    summary=(
                        f"Snapshot {weekly.snapshot_id}: {weekly.row_count} rows, watermark "
                        f"sequence {weekly.watermark_sequence}, content hash recorded."
                    ),
                    category=EvidenceCategory.PRODUCTION_RECOMMENDATION,
                )
            )
        if spec.day == drill.scenario.failure_day:
            break
    if weekly is None:
        raise ValueError("scenario never reached snapshot_day")
    return state, weekly, duplicates_seen


@dataclass(frozen=True, slots=True)
class _DayOutcome:
    sequence: int
    changes: int
    purged: tuple[int, ...]
    duplicates: int
    rows: int


def _day_step(spec: DaySpec, outcome: _DayOutcome) -> RecoveryStep:
    notes = [f"sequence {outcome.sequence}: {outcome.changes} changes ({spec.marker} markers)"]
    if spec.resend_previous_inserts:
        notes.append("source re-sent yesterday's inserts as INSERT")
    if spec.remediate_duplicates:
        notes.append("duplicates remediated with DELETE + UPSERT")
    if outcome.purged:
        notes.append(f"retention purged sequences {list(outcome.purged)}")
    notes.append(f"{outcome.rows} rows, {outcome.duplicates} duplicated keys")
    category = (
        EvidenceCategory.DOCUMENTED_FABRIC_BEHAVIOR
        if spec.resend_previous_inserts
        else EvidenceCategory.SIMULATED_LOCALLY
    )
    return RecoveryStep(
        name=f"Day {spec.day} incremental",
        day=spec.day,
        summary="; ".join(notes),
        category=category,
    )


def _scale(scenario: RecoveryScenario, snapshot: SnapshotManifest) -> ScaleEstimate:
    per_row = snapshot.size_bytes / max(snapshot.row_count, 1)
    conceptual = scenario.conceptual_scale.fact_rows
    days = scenario.days
    daily = sum(d.updates + d.inserts + d.deletes for d in days) / max(len(days), 1)
    return ScaleEstimate(
        local_rows=snapshot.row_count,
        local_snapshot_bytes=snapshot.size_bytes,
        conceptual_rows=conceptual,
        estimated_snapshot_gib=round(per_row * conceptual / 2**30, 2),
        estimated_daily_change_rows=round(daily / max(snapshot.row_count, 1) * conceptual),
        note=scenario.conceptual_scale.note,
    )
