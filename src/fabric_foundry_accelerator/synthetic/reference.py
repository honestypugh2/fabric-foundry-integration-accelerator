"""Fictional reference vocabularies for the synthetic healthcare generator.

Names, places, facilities, payers and providers are invented. Diagnosis codes use the
public ICD-10-CM vocabulary purely as realistic labels; nothing here is clinical guidance.
"""

from dataclasses import dataclass

FIRST_NAMES: tuple[str, ...] = (
    "Avery",
    "Blake",
    "Casey",
    "Devon",
    "Emery",
    "Finley",
    "Harper",
    "Jordan",
    "Kendall",
    "Logan",
    "Morgan",
    "Parker",
    "Quinn",
    "Reese",
    "Riley",
    "Rowan",
    "Sage",
    "Skyler",
    "Taylor",
    "Jamie",
    "Arden",
    "Bellamy",
    "Cameron",
    "Dakota",
    "Ellis",
    "Hollis",
)
LAST_NAMES: tuple[str, ...] = (
    "Ashgrove",
    "Brookmere",
    "Cindervale",
    "Dunmore",
    "Elmsworth",
    "Fernhollow",
    "Glenbrook",
    "Hollowell",
    "Ironwood",
    "Juniperra",
    "Kestrelton",
    "Larchmont",
    "Maplecrest",
    "Northvale",
    "Oakhurst",
    "Pinecrest",
    "Quarrystone",
    "Ravensmere",
    "Stonebridge",
    "Thornfield",
)
CITIES: tuple[str, ...] = (
    "Northbrook Vale",
    "Riverbend Hollow",
    "Cedar Mesa",
    "Harbor Point",
    "Maple Ridge",
    "Stonefield",
)
STATE_CODE = "ZZ"  # Deliberately not a real state code.
GENDERS: tuple[tuple[str, float], ...] = (("Female", 0.51), ("Male", 0.47), ("Unknown", 0.02))
RACES: tuple[tuple[str, float], ...] = (
    ("White", 0.45),
    ("Black or African American", 0.18),
    ("Hispanic or Latino", 0.18),
    ("Asian", 0.10),
    ("Two or More Races", 0.05),
    ("Other", 0.04),
)


@dataclass(frozen=True, slots=True)
class Facility:
    """A fictional facility."""

    facility_id: str
    name: str
    facility_type: str
    region: str
    inpatient: bool


FACILITIES: tuple[Facility, ...] = (
    Facility("FAC-01", "Synthetic Regional Medical Center", "Acute Care Hospital", "Central", True),
    Facility("FAC-02", "Synthetic Community Hospital East", "Community Hospital", "East", True),
    Facility("FAC-03", "Synthetic Community Hospital West", "Community Hospital", "West", True),
    Facility("FAC-04", "Synthetic Outpatient Center", "Outpatient Center", "Central", False),
    Facility("FAC-05", "Synthetic Specialty Clinic", "Specialty Clinic", "East", False),
)


@dataclass(frozen=True, slots=True)
class Payer:
    """A fictional payer."""

    payer_id: str
    name: str
    payer_type: str


PAYERS: tuple[Payer, ...] = (
    Payer("PYR-01", "Synthetic Commercial Plan A", "Commercial"),
    Payer("PYR-02", "Synthetic Commercial Plan B", "Commercial"),
    Payer("PYR-03", "Synthetic Medicare Advantage Plan", "Medicare"),
    Payer("PYR-04", "Synthetic Medicaid Managed Care", "Medicaid"),
    Payer("PYR-05", "Self-Pay", "Self-Pay"),
)


@dataclass(frozen=True, slots=True)
class ConditionCode:
    """A condition vocabulary entry."""

    code: str
    description: str
    condition_type: str  # Chronic | Acute


CHRONIC_CONDITIONS: tuple[ConditionCode, ...] = (
    ConditionCode("E11.9", "Type 2 diabetes mellitus without complications", "Chronic"),
    ConditionCode("I10", "Essential (primary) hypertension", "Chronic"),
    ConditionCode("I50.9", "Heart failure, unspecified", "Chronic"),
    ConditionCode("J44.9", "Chronic obstructive pulmonary disease, unspecified", "Chronic"),
    ConditionCode("N18.30", "Chronic kidney disease, stage 3 unspecified", "Chronic"),
    ConditionCode("E78.5", "Hyperlipidemia, unspecified", "Chronic"),
    ConditionCode("J45.909", "Unspecified asthma, uncomplicated", "Chronic"),
    ConditionCode("E66.9", "Obesity, unspecified", "Chronic"),
    ConditionCode("M17.9", "Osteoarthritis of knee, unspecified", "Chronic"),
)
ACUTE_CONDITIONS: tuple[ConditionCode, ...] = (
    ConditionCode("J06.9", "Acute upper respiratory infection, unspecified", "Acute"),
    ConditionCode("N39.0", "Urinary tract infection, site not specified", "Acute"),
    ConditionCode(
        "S93.401A", "Sprain of unspecified ligament of ankle, initial encounter", "Acute"
    ),
)


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """A primary diagnosis label with the departments that typically record it."""

    code: str
    description: str
    departments: tuple[str, ...]


INPATIENT_DIAGNOSES: tuple[Diagnosis, ...] = (
    Diagnosis("I50.9", "Heart failure, unspecified", ("Cardiology",)),
    Diagnosis(
        "J44.1", "Chronic obstructive pulmonary disease with acute exacerbation", ("Pulmonology",)
    ),
    Diagnosis("J18.9", "Pneumonia, unspecified organism", ("Pulmonology", "Internal Medicine")),
    Diagnosis("I48.91", "Unspecified atrial fibrillation", ("Cardiology",)),
    Diagnosis("N17.9", "Acute kidney failure, unspecified", ("Nephrology",)),
    Diagnosis("S72.002A", "Fracture of unspecified part of neck of left femur", ("Orthopedics",)),
    Diagnosis("I63.9", "Cerebral infarction, unspecified", ("Neurology",)),
    Diagnosis("E11.65", "Type 2 diabetes mellitus with hyperglycemia", ("Internal Medicine",)),
)
ED_DIAGNOSES: tuple[Diagnosis, ...] = (
    Diagnosis("R07.9", "Chest pain, unspecified", ("Emergency",)),
    Diagnosis("R10.9", "Unspecified abdominal pain", ("Emergency",)),
    Diagnosis(
        "S93.401A", "Sprain of unspecified ligament of ankle, initial encounter", ("Emergency",)
    ),
    Diagnosis("R51.9", "Headache, unspecified", ("Emergency",)),
    Diagnosis("J45.901", "Unspecified asthma with (acute) exacerbation", ("Emergency",)),
)
OUTPATIENT_DIAGNOSES: tuple[Diagnosis, ...] = (
    Diagnosis("Z00.00", "Encounter for general adult medical examination", ("Primary Care",)),
    Diagnosis(
        "E11.9", "Type 2 diabetes mellitus without complications", ("Endocrinology", "Primary Care")
    ),
    Diagnosis("I10", "Essential (primary) hypertension", ("Primary Care", "Cardiology")),
    Diagnosis("M17.9", "Osteoarthritis of knee, unspecified", ("Orthopedics",)),
    Diagnosis("J44.9", "Chronic obstructive pulmonary disease, unspecified", ("Pulmonology",)),
)
OBSERVATION_DIAGNOSES: tuple[Diagnosis, ...] = (
    Diagnosis("R07.9", "Chest pain, unspecified", ("Cardiology",)),
    Diagnosis("R55", "Syncope and collapse", ("Internal Medicine",)),
)

DISPOSITIONS: dict[str, tuple[tuple[str, float], ...]] = {
    "Inpatient": (
        ("Home", 0.60),
        ("Home with Services", 0.20),
        ("Skilled Nursing Facility", 0.15),
        ("Transferred", 0.05),
    ),
    "ED": (("Home", 0.85), ("Transferred", 0.10), ("Left Before Completion", 0.05)),
    "Observation": (("Home", 0.90), ("Home with Services", 0.10)),
    "Outpatient": (("Home", 1.0),),
}

CLAIM_STATUSES: tuple[tuple[str, float], ...] = (
    ("Paid", 0.70),
    ("Denied", 0.10),
    ("Partially Paid", 0.08),
    ("Pending", 0.07),
    ("Paid on Appeal", 0.05),
)
DENIAL_REASONS: tuple[str, ...] = (
    "Missing documentation",
    "Authorization not on file",
    "Coding mismatch",
    "Eligibility not verified",
    "Duplicate submission",
)


@dataclass(frozen=True, slots=True)
class Medication:
    """A medication vocabulary entry (generic names used as labels only)."""

    name: str
    medication_class: str
    dosage: str
    frequency: str


MEDICATIONS: tuple[Medication, ...] = (
    Medication("metformin", "Biguanide", "500 mg", "Twice daily"),
    Medication("lisinopril", "ACE inhibitor", "10 mg", "Once daily"),
    Medication("atorvastatin", "Statin", "20 mg", "Once daily"),
    Medication("furosemide", "Loop diuretic", "40 mg", "Once daily"),
    Medication("albuterol", "Bronchodilator", "2 puffs", "As needed"),
    Medication("amlodipine", "Calcium channel blocker", "5 mg", "Once daily"),
    Medication("apixaban", "Anticoagulant", "5 mg", "Twice daily"),
    Medication("ceftriaxone", "Antibiotic", "1 g", "Once daily"),
    Medication("acetaminophen", "Analgesic", "650 mg", "Every 6 hours as needed"),
    Medication("insulin glargine", "Insulin", "10 units", "Once daily"),
    Medication("prednisone", "Corticosteroid", "20 mg", "Once daily"),
    Medication("ondansetron", "Antiemetic", "4 mg", "Every 8 hours as needed"),
)
MEDICATION_STATUSES: tuple[tuple[str, float], ...] = (
    ("Completed", 0.50),
    ("Active", 0.35),
    ("Discontinued", 0.15),
)

NOTE_TYPES: dict[str, tuple[str, ...]] = {
    "Inpatient": ("Progress Note", "Discharge Summary", "Consult Note"),
    "ED": ("ED Note",),
    "Observation": ("Progress Note",),
}

# Note sentences are deliberately non-clinical. Some contain commas and double quotes so
# that correct CSV quoting matters.
NOTE_SENTENCES: tuple[str, ...] = (
    "SYNTHETIC TRAINING NOTE ({note_type}) for analytics practice in {department}.",
    "This record is fictional, generated for a data engineering workshop.",
    'Workflow steps "intake, review, handoff" were documented, with no clinical guidance implied.',
    "Follow-up scheduling, documentation completeness, and coding status were reviewed.",
    'Status recorded as "complete" for training purposes only.',
)
