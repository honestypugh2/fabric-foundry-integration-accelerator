"""Dataset profiles: the shape, size and deliberate data-quality quirks of each synthetic dataset.

Profiles let one generator serve the baseline accelerator dataset and Use-Case Guides
without forking code. Every number here is synthetic and chosen for teaching.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

GoldModel = Literal["hc_lab", "core_star"]

CORE_TABLES: tuple[str, ...] = (
    "patients",
    "encounters",
    "conditions",
    "claims",
    "vitals",
    "medications",
    "clinical_notes",
)
MASTER_TABLES: tuple[str, ...] = ("facilities", "payers")


@dataclass(frozen=True, slots=True)
class Quirks:
    """Deliberate, documented data-quality issues injected for teaching.

    Each quirk is detected by Silver diagnostics; tests assert the detected counts equal
    the injected counts.
    """

    overlapping_encounters: int = 3
    length_of_stay_mismatches: int = 4
    blank_total_charges: int = 5
    zero_claim_amounts: int = 3
    out_of_range_vitals: int = 6
    medication_chronology_violations: int = 3


@dataclass(frozen=True, slots=True)
class DatasetProfile:
    """A synthetic dataset profile."""

    id: str
    description: str
    seed: int
    patients: int
    encounters: int
    conditions: int
    vitals: int
    medications: int
    clinical_notes: int
    notes_with_literal_newline: int
    reference_masters: bool
    gold_model: GoldModel
    window_start: date = date(2024, 1, 1)
    window_end: date = date(2025, 12, 31)
    quirks: Quirks = field(default_factory=Quirks)

    @property
    def tables(self) -> tuple[str, ...]:
        """Return the raw table names produced for this profile, in dependency order."""
        return (MASTER_TABLES if self.reference_masters else ()) + CORE_TABLES

    @property
    def claims(self) -> int:
        """Return the claim count (exactly one claim per encounter)."""
        return self.encounters


HC_LAB_7FILE_V1 = DatasetProfile(
    id="hc-lab-7file-v1",
    description=(
        "Use-Case Guide HC-01 profile: seven CSV sources whose row counts and structural "
        "quirks match the guide's documented baseline."
    ),
    seed=20261008,
    patients=200,
    encounters=1025,
    conditions=428,
    vitals=4299,
    medications=643,
    clinical_notes=150,
    notes_with_literal_newline=56,
    reference_masters=False,
    gold_model="hc_lab",
)

CORE_HEALTHCARE_V1 = DatasetProfile(
    id="core-healthcare-v1",
    description=(
        "Baseline accelerator profile: nine entities (seven sources plus facility and payer "
        "masters) feeding a star schema with physical role-playing date dimensions."
    ),
    seed=20261005,
    patients=300,
    encounters=1500,
    conditions=640,
    vitals=6000,
    medications=950,
    clinical_notes=220,
    notes_with_literal_newline=80,
    reference_masters=True,
    gold_model="core_star",
)

PROFILES: dict[str, DatasetProfile] = {p.id: p for p in (CORE_HEALTHCARE_V1, HC_LAB_7FILE_V1)}


def get_profile(profile_id: str) -> DatasetProfile:
    """Return a profile by ID or raise ``KeyError`` listing valid IDs."""
    try:
        return PROFILES[profile_id]
    except KeyError:
        valid = ", ".join(sorted(PROFILES))
        raise KeyError(f"unknown dataset profile {profile_id!r}; valid profiles: {valid}") from None
