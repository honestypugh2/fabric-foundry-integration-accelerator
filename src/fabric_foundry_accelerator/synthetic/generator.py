"""Deterministic, seeded synthetic healthcare data generator.

Produces obviously fictional CSV sources for a dataset profile, including the documented
data-quality quirks Silver must detect. The same profile and seed always produce
byte-identical files (verified by ``ffia data generate --check``).

Randomness here is ``random.Random`` on purpose: reproducible pseudo-randomness for teaching
data, never for security.
"""

import csv
import hashlib
import io
import json
import random
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from itertools import pairwise
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.synthetic import reference as ref
from fabric_foundry_accelerator.synthetic.profiles import DatasetProfile

GENERATOR_VERSION = "1"
SYNTHETIC_NOTICE = (
    "SYNTHETIC DATA. Fictional people, places, providers, facilities and payers generated for "
    "analytics education. Not PHI, not PII, and not clinical guidance."
)

COLUMNS: dict[str, tuple[str, ...]] = {
    "facilities": ("facility_id", "facility_name", "facility_type", "region", "city", "state"),
    "payers": ("payer_id", "payer_name", "payer_type"),
    "patients": (
        "patient_id",
        "first_name",
        "last_name",
        "date_of_birth",
        "age",
        "gender",
        "race",
        "zip_code",
        "city",
        "state",
        "insurance_type",
        "primary_care_provider",
        "risk_score",
    ),
    "encounters": (
        "encounter_id",
        "patient_id",
        "encounter_date",
        "encounter_time",
        "discharge_date",
        "encounter_type",
        "facility_id",
        "facility_name",
        "department",
        "primary_diagnosis_code",
        "primary_diagnosis_description",
        "attending_provider",
        "discharge_disposition",
        "length_of_stay_days",
        "total_charges",
    ),
    "conditions": (
        "condition_id",
        "patient_id",
        "encounter_id",
        "condition_code",
        "condition_description",
        "condition_type",
        "date_diagnosed",
        "status",
    ),
    "claims": (
        "claim_id",
        "patient_id",
        "encounter_id",
        "claim_date",
        "payer",
        "payer_type",
        "claim_amount",
        "paid_amount",
        "denied_amount",
        "patient_responsibility",
        "denial_reason",
        "claim_status",
        "days_to_payment",
    ),
    "vitals": (
        "vital_id",
        "patient_id",
        "encounter_id",
        "facility_name",
        "department",
        "timestamp",
        "heart_rate",
        "systolic_bp",
        "diastolic_bp",
        "temperature_f",
        "respiratory_rate",
        "spo2_percent",
        "pain_level",
    ),
    "medications": (
        "medication_id",
        "patient_id",
        "encounter_id",
        "medication_name",
        "medication_class",
        "dosage",
        "frequency",
        "prescriber",
        "start_date",
        "end_date",
        "status",
    ),
    "clinical_notes": (
        "note_id",
        "patient_id",
        "encounter_id",
        "note_date",
        "note_type",
        "provider",
        "note_text",
    ),
}

ENCOUNTER_TYPES = ("Inpatient", "ED", "Observation", "Outpatient")
MAX_CONDITIONS_PER_PATIENT = len(ref.CHRONIC_CONDITIONS) + len(ref.ACUTE_CONDITIONS)
MAX_ENCOUNTERS_PER_PATIENT = 30

Row = dict[str, str]


class GenerationError(RuntimeError):
    """Raised when a profile's exact counts or quirks cannot be satisfied."""


@dataclass(slots=True)
class _Patient:
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    gender: str
    race: str
    city: str
    zip_code: str
    payer: ref.Payer
    pcp: str
    home_facility: ref.Facility
    conditions: list[ref.ConditionCode] = field(default_factory=list[ref.ConditionCode])
    risk_score: float = 0.0


@dataclass(slots=True)
class _Encounter:
    patient: _Patient
    encounter_type: str
    admit: date
    discharge: date
    time: str
    facility: ref.Facility
    department: str
    diagnosis: ref.Diagnosis
    disposition: str
    recorded_los: int
    charges_cents: int
    charges_blank: bool = False
    encounter_id: str = ""


@dataclass(frozen=True, slots=True)
class GeneratedTable:
    """One generated table."""

    name: str
    columns: tuple[str, ...]
    rows: tuple[Row, ...]

    def render_csv(self) -> str:
        """Render the table as CSV text (header first, minimal quoting, LF line endings)."""
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(self.columns)
        for row in self.rows:
            writer.writerow([row[c] for c in self.columns])
        return buffer.getvalue()


@dataclass(frozen=True, slots=True)
class GeneratedDataset:
    """A complete generated dataset for one profile."""

    profile: DatasetProfile
    tables: tuple[GeneratedTable, ...]
    quirks: dict[str, int]
    observation_cutoff: date

    def table(self, name: str) -> GeneratedTable:
        """Return a table by name."""
        for candidate in self.tables:
            if candidate.name == name:
                return candidate
        raise KeyError(name)


class RawFileEntry(BaseModel):
    """Manifest entry for one raw CSV file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    rows: int
    columns: tuple[str, ...]
    sha256: str


class RawManifest(BaseModel):
    """Manifest written next to the raw CSV files of a profile."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile: str
    generator_version: str
    seed: int
    synthetic_notice: str
    observation_cutoff: date
    files: tuple[RawFileEntry, ...]
    quirks: dict[str, int]

    def entry(self, table: str) -> RawFileEntry:
        """Return the manifest entry for a table."""
        for candidate in self.files:
            if candidate.name == f"{table}.csv":
                return candidate
        raise KeyError(table)


def _money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def _weighted[T](rng: random.Random, options: Sequence[tuple[T, float]]) -> T:
    values = [o[0] for o in options]
    weights = [o[1] for o in options]
    return rng.choices(values, weights=weights, k=1)[0]


class _Generator:
    """Stateful generator: one seeded RNG consumed in a fixed order for determinism."""

    def __init__(self, profile: DatasetProfile) -> None:
        self.profile = profile
        self.rng = random.Random(profile.seed)
        self.quirks: dict[str, int] = {}

    # ------------------------------------------------------------------ patients
    def patients(self) -> list[_Patient]:
        rng, as_of = self.rng, self.profile.window_end
        patients: list[_Patient] = []
        for index in range(1, self.profile.patients + 1):
            age = round(rng.triangular(1, 95, 68))
            dob = as_of - timedelta(days=age * 365 + age // 4 + rng.randint(0, 360))
            exact_age = as_of.year - dob.year - ((as_of.month, as_of.day) < (dob.month, dob.day))
            payer_type = self._insurance_type(exact_age)
            payer = rng.choice([p for p in ref.PAYERS if p.payer_type == payer_type])
            patients.append(
                _Patient(
                    patient_id=f"SYN-P-{index:05d}",
                    first_name=rng.choice(ref.FIRST_NAMES),
                    last_name=rng.choice(ref.LAST_NAMES),
                    date_of_birth=dob,
                    age=exact_age,
                    gender=_weighted(rng, ref.GENDERS),
                    race=_weighted(rng, ref.RACES),
                    city=rng.choice(ref.CITIES),
                    zip_code=f"000{rng.randint(1, 99):02d}",
                    payer=payer,
                    pcp=f"Provider SYN-{rng.randint(1, 40):02d}",
                    home_facility=rng.choice(ref.FACILITIES),
                )
            )
        self._assign_conditions(patients)
        for patient in patients:
            chronic = sum(1 for c in patient.conditions if c.condition_type == "Chronic")
            score = 0.08 + 0.09 * chronic + patient.age / 400 + rng.uniform(-0.08, 0.08)
            patient.risk_score = round(min(0.99, max(0.01, score)), 2)
        return patients

    def _insurance_type(self, age: int) -> str:
        if age >= 65:
            return _weighted(self.rng, (("Medicare", 0.75), ("Commercial", 0.25)))
        return _weighted(self.rng, (("Commercial", 0.60), ("Medicaid", 0.28), ("Self-Pay", 0.12)))

    def _assign_conditions(self, patients: list[_Patient]) -> None:
        rng = self.rng
        weights = {p.patient_id: (p.age / 95) ** 1.5 + 0.05 for p in patients}
        eligible = [p for p in patients if rng.random() >= 0.35 * (1 - weights[p.patient_id])]
        counts = dict.fromkeys((p.patient_id for p in eligible), 0)
        for _ in range(self.profile.conditions):
            open_patients = [
                p for p in eligible if counts[p.patient_id] < MAX_CONDITIONS_PER_PATIENT
            ]
            if not open_patients:
                raise GenerationError("not enough patients to hold the requested conditions")
            chosen = rng.choices(
                open_patients, weights=[weights[p.patient_id] for p in open_patients]
            )[0]
            counts[chosen.patient_id] += 1
        for patient in eligible:
            patient.conditions = self._pick_conditions(counts[patient.patient_id])

    def _pick_conditions(self, count: int) -> list[ref.ConditionCode]:
        pool = [(c, 4.0) for c in ref.CHRONIC_CONDITIONS] + [(c, 1.0) for c in ref.ACUTE_CONDITIONS]
        picked: list[ref.ConditionCode] = []
        for _ in range(count):
            choice = _weighted(self.rng, pool)
            picked.append(choice)
            pool = [item for item in pool if item[0] != choice]
        return picked

    # ------------------------------------------------------------------ encounters
    def encounters(self, patients: list[_Patient]) -> list[_Encounter]:
        rng = self.rng
        counts = dict.fromkeys((p.patient_id for p in patients), 1)
        extra = self.profile.encounters - len(patients)
        if extra < 0:
            raise GenerationError("encounters must be at least the number of patients")
        for _ in range(extra):
            open_patients = [
                p for p in patients if counts[p.patient_id] < MAX_ENCOUNTERS_PER_PATIENT
            ]
            chosen = rng.choices(
                open_patients, weights=[0.5 + 3 * p.risk_score for p in open_patients]
            )[0]
            counts[chosen.patient_id] += 1
        encounters: list[_Encounter] = []
        for patient in patients:
            encounters.extend(self._patient_encounters(patient, counts[patient.patient_id]))
        encounters.sort(key=lambda e: (e.admit, e.time, e.patient.patient_id))
        for index, encounter in enumerate(encounters, start=1):
            encounter.encounter_id = f"SYN-E-{index:06d}"
        self._inject_encounter_quirks(encounters)
        return encounters

    def _plan(self, patient: _Patient, count: int) -> list[tuple[str, int, int, bool]]:
        rng = self.rng
        plan: list[tuple[str, int, int, bool]] = []
        previous = ""
        for _ in range(count):
            if previous == "Inpatient" and rng.random() < 0.08 + 0.25 * patient.risk_score:
                gap = rng.randint(1, 30) if rng.random() < 0.85 else rng.randint(31, 45)
                encounter_type, readmit = "Inpatient", True
            else:
                inpatient = 0.10 + 0.20 * patient.risk_score
                encounter_type = _weighted(
                    rng,
                    (
                        ("Inpatient", inpatient),
                        ("ED", 0.20),
                        ("Observation", 0.06),
                        ("Outpatient", 1.0 - inpatient - 0.26),
                    ),
                )
                gap, readmit = rng.randint(14, 160), False
            plan.append((encounter_type, self._length_of_stay(encounter_type), gap, readmit))
            previous = encounter_type
        return plan

    def _length_of_stay(self, encounter_type: str) -> int:
        if encounter_type == "Inpatient":
            return _weighted(
                self.rng,
                (
                    (1, 0.12),
                    (2, 0.2),
                    (3, 0.2),
                    (4, 0.15),
                    (5, 0.12),
                    (6, 0.08),
                    (7, 0.06),
                    (9, 0.04),
                    (12, 0.03),
                ),
            )
        if encounter_type == "Observation":
            return self.rng.choice((0, 1))
        return 0

    def _fit_gaps(self, plan: list[tuple[str, int, int, bool]]) -> tuple[list[int], int]:
        window = (self.profile.window_end - self.profile.window_start).days
        gaps = [0] + [step[2] for step in plan[1:]]
        flexible = [i for i in range(1, len(plan)) if not plan[i][3]]

        def span() -> int:
            return sum(step[1] for step in plan) + sum(gaps)

        while span() > window:
            target = max(flexible or range(1, len(plan)), key=lambda i: gaps[i])
            if gaps[target] <= 1:
                raise GenerationError("encounter plan cannot fit in the profile window")
            gaps[target] = max(1, gaps[target] // 2)
        return gaps, self.rng.randint(0, window - span())

    def _patient_encounters(self, patient: _Patient, count: int) -> list[_Encounter]:
        plan = self._plan(patient, count)
        gaps, offset = self._fit_gaps(plan)
        admit = self.profile.window_start + timedelta(days=offset)
        result: list[_Encounter] = []
        for (encounter_type, los, _, _), gap in zip(plan, gaps, strict=True):
            if result:
                # The next encounter starts strictly after the previous discharge (gap >= 1).
                admit = result[-1].discharge + timedelta(days=gap)
            result.append(self._encounter(patient, encounter_type, admit, los))
        return result

    def _encounter(
        self, patient: _Patient, encounter_type: str, admit: date, los: int
    ) -> _Encounter:
        rng = self.rng
        facility = self._facility(patient, encounter_type)
        diagnosis = self._diagnosis(patient, encounter_type)
        charges = {
            "Outpatient": rng.randint(15_000, 90_000),
            "ED": rng.randint(80_000, 400_000),
            "Observation": rng.randint(200_000, 600_000),
        }.get(encounter_type, 600_000 + los * 250_000 + rng.randint(0, 300_000))
        return _Encounter(
            patient=patient,
            encounter_type=encounter_type,
            admit=admit,
            discharge=admit + timedelta(days=los),
            time=f"{rng.randint(0, 23):02d}:{rng.choice((0, 15, 30, 45)):02d}",
            facility=facility,
            department=rng.choice(diagnosis.departments),
            diagnosis=diagnosis,
            disposition=_weighted(rng, ref.DISPOSITIONS[encounter_type]),
            recorded_los=los,
            charges_cents=charges,
        )

    def _facility(self, patient: _Patient, encounter_type: str) -> ref.Facility:
        if encounter_type == "Outpatient":
            return self.rng.choice(
                [f for f in ref.FACILITIES if not f.inpatient] + [patient.home_facility]
            )
        if patient.home_facility.inpatient:
            return patient.home_facility
        return self.rng.choice([f for f in ref.FACILITIES if f.inpatient])

    def _diagnosis(self, patient: _Patient, encounter_type: str) -> ref.Diagnosis:
        options = {
            "Inpatient": ref.INPATIENT_DIAGNOSES,
            "ED": ref.ED_DIAGNOSES,
            "Observation": ref.OBSERVATION_DIAGNOSES,
            "Outpatient": ref.OUTPATIENT_DIAGNOSES,
        }[encounter_type]
        prefixes = {c.code.split(".")[0] for c in patient.conditions}
        weights = [3.0 if d.code.split(".")[0] in prefixes else 1.0 for d in options]
        return self.rng.choices(options, weights=weights)[0]

    def _inject_encounter_quirks(self, encounters: list[_Encounter]) -> None:
        quirks, rng = self.profile.quirks, self.rng
        by_patient: dict[str, list[_Encounter]] = {}
        for encounter in sorted(encounters, key=lambda e: (e.admit, e.encounter_id)):
            by_patient.setdefault(encounter.patient.patient_id, []).append(encounter)
        candidates = [
            (current, following)
            for history in by_patient.values()
            for current, following in pairwise(history)
            if current.encounter_type == "Inpatient"
            and current.recorded_los >= 2
            and following.encounter_type in ("ED", "Outpatient")
        ]
        if len(candidates) < quirks.overlapping_encounters:
            raise GenerationError("not enough candidates for overlapping encounters")
        touched: set[str] = set()
        for current, following in rng.sample(candidates, quirks.overlapping_encounters):
            following.admit = current.discharge - timedelta(days=1)
            following.discharge = following.admit
            touched.update((current.encounter_id, following.encounter_id))
        self.quirks["overlapping_encounters"] = quirks.overlapping_encounters

        inpatient = [
            e
            for e in encounters
            if e.encounter_type == "Inpatient" and e.encounter_id not in touched
        ]
        for encounter in rng.sample(inpatient, quirks.length_of_stay_mismatches):
            encounter.recorded_los += 1
        self.quirks["length_of_stay_mismatches"] = quirks.length_of_stay_mismatches

        outpatient = [
            e
            for e in encounters
            if e.encounter_type == "Outpatient" and e.encounter_id not in touched
        ]
        chosen = rng.sample(outpatient, quirks.zero_claim_amounts + quirks.blank_total_charges)
        for encounter in chosen[: quirks.zero_claim_amounts]:
            encounter.charges_cents = 0
        for encounter in chosen[quirks.zero_claim_amounts :]:
            encounter.charges_blank = True
        self.quirks["zero_claim_amounts"] = quirks.zero_claim_amounts
        self.quirks["blank_total_charges"] = quirks.blank_total_charges

    # ------------------------------------------------------------------ child tables
    def claims(self, encounters: list[_Encounter]) -> list[Row]:
        rows: list[Row] = []
        for index, encounter in enumerate(encounters, start=1):
            amount = encounter.charges_cents
            status = "Paid" if amount == 0 else _weighted(self.rng, ref.CLAIM_STATUSES)
            paid, denied, responsibility, reason, days = self._adjudicate(status, amount)
            rows.append(
                {
                    "claim_id": f"SYN-C-{index:06d}",
                    "patient_id": encounter.patient.patient_id,
                    "encounter_id": encounter.encounter_id,
                    "claim_date": (
                        encounter.discharge + timedelta(days=self.rng.randint(1, 14))
                    ).isoformat(),
                    "payer": encounter.patient.payer.name,
                    "payer_type": encounter.patient.payer.payer_type,
                    "claim_amount": _money(amount),
                    "paid_amount": _money(paid),
                    "denied_amount": _money(denied),
                    "patient_responsibility": _money(responsibility),
                    "denial_reason": reason,
                    "claim_status": status,
                    "days_to_payment": days,
                }
            )
        return rows

    def _adjudicate(self, status: str, amount: int) -> tuple[int, int, int, str, str]:
        rng = self.rng

        def part(low: float, high: float) -> int:
            return int(amount * rng.uniform(low, high))

        if status == "Denied":
            return 0, amount, 0, rng.choice(ref.DENIAL_REASONS), ""
        if status == "Pending":
            return 0, 0, 0, "", ""
        if status == "Partially Paid":
            return (
                part(0.3, 0.6),
                part(0.1, 0.3),
                part(0.0, 0.05),
                rng.choice(ref.DENIAL_REASONS),
                str(rng.randint(20, 75)),
            )
        if status == "Paid on Appeal":
            return (
                part(0.55, 0.85),
                0,
                part(0.0, 0.05),
                rng.choice(ref.DENIAL_REASONS),
                str(rng.randint(45, 120)),
            )
        return part(0.62, 0.92), 0, part(0.0, 0.08), "", str(rng.randint(7, 60))

    def vitals(self, encounters: list[_Encounter]) -> list[Row]:
        rng = self.rng
        weights = [
            {"Inpatient": 3 + 2 * e.recorded_los, "Observation": 4, "ED": 3}.get(
                e.encounter_type, 1
            )
            for e in encounters
        ]
        picks = rng.choices(encounters, weights=weights, k=self.profile.vitals)
        drafts: list[tuple[str, datetime, _Encounter, Row]] = []
        for encounter in picks:
            hour, minute = (int(x) for x in encounter.time.split(":"))
            start = datetime.combine(encounter.admit, time(hour, minute))
            span_minutes = ((encounter.discharge - encounter.admit).days * 24 + 4) * 60
            moment = start + timedelta(minutes=rng.randint(0, span_minutes))
            drafts.append(
                (
                    encounter.encounter_id,
                    moment,
                    encounter,
                    {
                        "heart_rate": str(rng.randint(55, 110)),
                        "systolic_bp": str(rng.randint(100, 160)),
                        "diastolic_bp": str(rng.randint(60, 95)),
                        "temperature_f": f"{rng.uniform(97.0, 99.8):.1f}",
                        "respiratory_rate": str(rng.randint(12, 22)),
                        "spo2_percent": str(rng.randint(92, 100)),
                        "pain_level": "" if rng.random() < 0.05 else str(rng.randint(0, 8)),
                    },
                )
            )
        drafts.sort(key=lambda d: (d[0], d[1]))
        out_of_range = (
            ("heart_rate", "0"),
            ("spo2_percent", "104"),
            ("temperature_f", "120.5"),
            ("systolic_bp", "310"),
            ("respiratory_rate", "75"),
            ("diastolic_bp", "200"),
        )
        targets = rng.sample(range(len(drafts)), self.profile.quirks.out_of_range_vitals)
        for slot, index in enumerate(targets):
            column, value = out_of_range[slot % len(out_of_range)]
            drafts[index][3][column] = value
        self.quirks["out_of_range_vitals"] = len(targets)
        return [
            {
                "vital_id": f"SYN-V-{index:06d}",
                "patient_id": encounter.patient.patient_id,
                "encounter_id": encounter.encounter_id,
                "facility_name": encounter.facility.name,
                "department": encounter.department,
                "timestamp": moment.strftime("%Y-%m-%d %H:%M:%S"),
                **values,
            }
            for index, (_, moment, encounter, values) in enumerate(drafts, start=1)
        ]

    def medications(self, encounters: list[_Encounter]) -> list[Row]:
        rng = self.rng
        weights = [
            {"Inpatient": 3.0, "Observation": 1.5, "ED": 1.0}.get(e.encounter_type, 0.8)
            for e in encounters
        ]
        drafts: list[tuple[str, date, _Encounter, ref.Medication, str, date | None]] = []
        for encounter in rng.choices(encounters, weights=weights, k=self.profile.medications):
            medication = rng.choice(ref.MEDICATIONS)
            start = encounter.admit + timedelta(days=rng.randint(0, encounter.recorded_los))
            status = _weighted(rng, ref.MEDICATION_STATUSES)
            end = None if status == "Active" else start + timedelta(days=rng.randint(3, 90))
            drafts.append((encounter.encounter_id, start, encounter, medication, status, end))
        drafts.sort(key=lambda d: (d[0], d[1], d[3].name))
        closed = [i for i, d in enumerate(drafts) if d[5] is not None]
        for index in rng.sample(closed, self.profile.quirks.medication_chronology_violations):
            item = drafts[index]
            drafts[index] = (*item[:5], item[1] - timedelta(days=rng.randint(1, 5)))
        self.quirks["medication_chronology_violations"] = (
            self.profile.quirks.medication_chronology_violations
        )
        return [
            {
                "medication_id": f"SYN-M-{index:06d}",
                "patient_id": encounter.patient.patient_id,
                "encounter_id": encounter.encounter_id,
                "medication_name": medication.name,
                "medication_class": medication.medication_class,
                "dosage": medication.dosage,
                "frequency": medication.frequency,
                "prescriber": f"Provider SYN-{rng.randint(1, 60):02d}",
                "start_date": start.isoformat(),
                "end_date": "" if end is None else end.isoformat(),
                "status": status,
            }
            for index, (_, start, encounter, medication, status, end) in enumerate(drafts, start=1)
        ]

    def clinical_notes(self, encounters: list[_Encounter]) -> list[Row]:
        rng = self.rng
        eligible = [e for e in encounters if e.encounter_type in ref.NOTE_TYPES]
        weights = [{"Inpatient": 3.0, "ED": 1.5}.get(e.encounter_type, 1.0) for e in eligible]
        drafts: list[tuple[str, date, str, _Encounter]] = []
        for encounter in rng.choices(eligible, weights=weights, k=self.profile.clinical_notes):
            note_type = rng.choice(ref.NOTE_TYPES[encounter.encounter_type])
            note_date = encounter.discharge if note_type == "Discharge Summary" else encounter.admit
            drafts.append((encounter.encounter_id, note_date, note_type, encounter))
        drafts.sort(key=lambda d: (d[0], d[1], d[2]))
        literal = set(rng.sample(range(len(drafts)), self.profile.notes_with_literal_newline))
        self.quirks["notes_with_literal_newline"] = len(literal)
        rows: list[Row] = []
        for index, (_, note_date, note_type, encounter) in enumerate(drafts, start=1):
            sentences = [ref.NOTE_SENTENCES[0], *rng.sample(ref.NOTE_SENTENCES[1:], 2)]
            separator = "\\n" if index - 1 in literal else " "
            text = separator.join(sentences).format(
                note_type=note_type, department=encounter.department
            )
            rows.append(
                {
                    "note_id": f"SYN-N-{index:05d}",
                    "patient_id": encounter.patient.patient_id,
                    "encounter_id": encounter.encounter_id,
                    "note_date": note_date.isoformat(),
                    "note_type": note_type,
                    "provider": f"Provider SYN-{rng.randint(1, 60):02d}",
                    "note_text": text,
                }
            )
        return rows

    def condition_rows(self, patients: list[_Patient]) -> list[Row]:
        rng, window_end = self.rng, self.profile.window_end
        drafts: list[tuple[str, date, ref.ConditionCode, str]] = []
        for patient in patients:
            for condition in patient.conditions:
                if condition.condition_type == "Chronic":
                    earliest = max(
                        patient.date_of_birth + timedelta(days=5 * 365), date(2010, 1, 1)
                    )
                    status = "Active" if rng.random() < 0.92 else "Resolved"
                else:
                    earliest = self.profile.window_start
                    status = "Resolved" if rng.random() < 0.85 else "Active"
                earliest = min(earliest, window_end)
                diagnosed = earliest + timedelta(days=rng.randint(0, (window_end - earliest).days))
                drafts.append((patient.patient_id, diagnosed, condition, status))
        drafts.sort(key=lambda d: (d[0], d[1], d[2].code))
        self.quirks["conditions_with_blank_encounter_id"] = len(drafts)
        return [
            {
                "condition_id": f"SYN-CN-{index:05d}",
                "patient_id": patient_id,
                "encounter_id": "",
                "condition_code": condition.code,
                "condition_description": condition.description,
                "condition_type": condition.condition_type,
                "date_diagnosed": diagnosed.isoformat(),
                "status": status,
            }
            for index, (patient_id, diagnosed, condition, status) in enumerate(drafts, start=1)
        ]


def _patient_rows(patients: list[_Patient]) -> list[Row]:
    return [
        {
            "patient_id": p.patient_id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "date_of_birth": p.date_of_birth.isoformat(),
            "age": str(p.age),
            "gender": p.gender,
            "race": p.race,
            "zip_code": p.zip_code,
            "city": p.city,
            "state": ref.STATE_CODE,
            "insurance_type": p.payer.payer_type,
            "primary_care_provider": p.pcp,
            "risk_score": f"{p.risk_score:.2f}",
        }
        for p in patients
    ]


def _encounter_rows(encounters: list[_Encounter]) -> list[Row]:
    return [
        {
            "encounter_id": e.encounter_id,
            "patient_id": e.patient.patient_id,
            "encounter_date": e.admit.isoformat(),
            "encounter_time": e.time,
            "discharge_date": e.discharge.isoformat(),
            "encounter_type": e.encounter_type,
            "facility_id": e.facility.facility_id,
            "facility_name": e.facility.name,
            "department": e.department,
            "primary_diagnosis_code": e.diagnosis.code,
            "primary_diagnosis_description": e.diagnosis.description,
            "attending_provider": f"Provider SYN-{int(e.encounter_id[-6:]) % 60 + 1:02d}",
            "discharge_disposition": e.disposition,
            "length_of_stay_days": str(e.recorded_los),
            "total_charges": "" if e.charges_blank else _money(e.charges_cents),
        }
        for e in encounters
    ]


def _master_rows() -> dict[str, list[Row]]:
    return {
        "facilities": [
            {
                "facility_id": f.facility_id,
                "facility_name": f.name,
                "facility_type": f.facility_type,
                "region": f.region,
                "city": ref.CITIES[i % len(ref.CITIES)],
                "state": ref.STATE_CODE,
            }
            for i, f in enumerate(ref.FACILITIES)
        ],
        "payers": [
            {"payer_id": p.payer_id, "payer_name": p.name, "payer_type": p.payer_type}
            for p in ref.PAYERS
        ],
    }


def generate(profile: DatasetProfile) -> GeneratedDataset:
    """Generate the complete dataset for a profile."""
    generator = _Generator(profile)
    patients = generator.patients()
    encounters = generator.encounters(patients)
    encounters.sort(key=lambda e: e.encounter_id)
    rows: dict[str, list[Row]] = {
        "patients": _patient_rows(patients),
        "encounters": _encounter_rows(encounters),
        "conditions": generator.condition_rows(patients),
        "claims": generator.claims(encounters),
        "vitals": generator.vitals(encounters),
        "medications": generator.medications(encounters),
        "clinical_notes": generator.clinical_notes(encounters),
    }
    if profile.reference_masters:
        rows.update(_master_rows())
    tables = tuple(
        GeneratedTable(name, COLUMNS[name], tuple(rows[name])) for name in profile.tables
    )
    _assert_counts(profile, tables)
    cutoff = max(e.admit for e in encounters)
    return GeneratedDataset(profile, tables, dict(sorted(generator.quirks.items())), cutoff)


def _assert_counts(profile: DatasetProfile, tables: tuple[GeneratedTable, ...]) -> None:
    expected = {
        "patients": profile.patients,
        "encounters": profile.encounters,
        "conditions": profile.conditions,
        "claims": profile.claims,
        "vitals": profile.vitals,
        "medications": profile.medications,
        "clinical_notes": profile.clinical_notes,
    }
    for table in tables:
        if table.name in expected and len(table.rows) != expected[table.name]:
            raise GenerationError(
                f"{table.name}: generated {len(table.rows)} rows, expected {expected[table.name]}"
            )


def build_manifest(dataset: GeneratedDataset) -> RawManifest:
    """Build the manifest describing a generated dataset."""
    files = tuple(
        RawFileEntry(
            name=f"{table.name}.csv",
            rows=len(table.rows),
            columns=table.columns,
            sha256=hashlib.sha256(table.render_csv().encode("utf-8")).hexdigest(),
        )
        for table in dataset.tables
    )
    return RawManifest(
        profile=dataset.profile.id,
        generator_version=GENERATOR_VERSION,
        seed=dataset.profile.seed,
        synthetic_notice=SYNTHETIC_NOTICE,
        observation_cutoff=dataset.observation_cutoff,
        files=files,
        quirks=dataset.quirks,
    )


def _manifest_text(manifest: RawManifest) -> str:
    return json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n"


def write_raw(dataset: GeneratedDataset, directory: Path) -> RawManifest:
    """Write CSV files and ``manifest.json`` for a dataset; return the manifest."""
    directory.mkdir(parents=True, exist_ok=True)
    for table in dataset.tables:
        (directory / f"{table.name}.csv").write_text(
            table.render_csv(), encoding="utf-8", newline=""
        )
    manifest = build_manifest(dataset)
    (directory / "manifest.json").write_text(_manifest_text(manifest), encoding="utf-8")
    return manifest


def check_raw(dataset: GeneratedDataset, directory: Path) -> list[str]:
    """Return differences between a regenerated dataset and files on disk (empty if identical)."""
    problems: list[str] = []
    for table in dataset.tables:
        path = directory / f"{table.name}.csv"
        if not path.is_file():
            problems.append(f"missing {path.name}")
        elif path.read_text(encoding="utf-8") != table.render_csv():
            problems.append(f"{path.name} differs from the generator output")
    manifest_path = directory / "manifest.json"
    if not manifest_path.is_file() or manifest_path.read_text(encoding="utf-8") != _manifest_text(
        build_manifest(dataset)
    ):
        problems.append("manifest.json differs from the generator output")
    return problems


def load_manifest(directory: Path) -> RawManifest:
    """Load the raw manifest from a profile directory."""
    return RawManifest.model_validate_json(
        (directory / "manifest.json").read_text(encoding="utf-8")
    )
