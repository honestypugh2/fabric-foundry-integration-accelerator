import csv
import io
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from fabric_foundry_accelerator.synthetic.generator import (
    COLUMNS,
    GeneratedDataset,
    GenerationError,
    build_manifest,
    check_raw,
    generate,
    load_manifest,
    write_raw,
)
from fabric_foundry_accelerator.synthetic.paths import raw_dir
from fabric_foundry_accelerator.synthetic.profiles import (
    HC_LAB_7FILE_V1,
    PROFILES,
    get_profile,
)

HC_COUNTS = {
    "patients": 200,
    "encounters": 1025,
    "conditions": 428,
    "claims": 1025,
    "vitals": 4299,
    "medications": 643,
    "clinical_notes": 150,
}


@pytest.fixture(scope="module")
def hc() -> GeneratedDataset:
    return generate(HC_LAB_7FILE_V1)


def test_hc_profile_reproduces_guide_baseline_counts(hc: GeneratedDataset) -> None:
    assert {t.name: len(t.rows) for t in hc.tables} == HC_COUNTS


def test_keys_are_unique_and_references_resolve(hc: GeneratedDataset) -> None:
    keys = {
        "patients": "patient_id",
        "encounters": "encounter_id",
        "conditions": "condition_id",
        "claims": "claim_id",
        "vitals": "vital_id",
        "medications": "medication_id",
        "clinical_notes": "note_id",
    }
    for table, key in keys.items():
        values = [r[key] for r in hc.table(table).rows]
        assert all(values) and len(set(values)) == len(values), table
    patients = {r["patient_id"] for r in hc.table("patients").rows}
    encounters = {r["encounter_id"] for r in hc.table("encounters").rows}
    for table in ("encounters", "conditions", "claims", "vitals", "medications", "clinical_notes"):
        assert {r["patient_id"] for r in hc.table(table).rows} <= patients
    for table in ("claims", "vitals", "medications", "clinical_notes"):
        assert {r["encounter_id"] for r in hc.table(table).rows} <= encounters


def test_documented_structural_quirks(hc: GeneratedDataset) -> None:
    assert all(r["encounter_id"] == "" for r in hc.table("conditions").rows)
    notes = [r["note_text"] for r in hc.table("clinical_notes").rows]
    assert sum("\\n" in n for n in notes) == 56
    assert not any("\n" in n or "\r" in n for n in notes)
    claims = hc.table("claims").rows
    assert Counter(r["encounter_id"] for r in claims).most_common(1)[0][1] == 1
    assert all(r["denial_reason"] == "" for r in claims if r["claim_status"] == "Paid")
    assert {"Denied", "Paid on Appeal"} <= {r["claim_status"] for r in claims}
    assert all(r["discharge_date"] for r in hc.table("encounters").rows)


def test_patients_without_conditions_exist(hc: GeneratedDataset) -> None:
    with_conditions = {r["patient_id"] for r in hc.table("conditions").rows}
    assert len(with_conditions) < HC_COUNTS["patients"]


def test_generation_is_deterministic() -> None:
    first, second = generate(HC_LAB_7FILE_V1), generate(HC_LAB_7FILE_V1)
    assert [t.render_csv() for t in first.tables] == [t.render_csv() for t in second.tables]


def test_csv_round_trips_with_quotes_and_commas(hc: GeneratedDataset) -> None:
    text = hc.table("clinical_notes").render_csv()
    parsed = list(csv.DictReader(io.StringIO(text)))
    assert len(parsed) == HC_COUNTS["clinical_notes"]
    assert any('"' in r["note_text"] for r in parsed)
    assert tuple(parsed[0]) == COLUMNS["clinical_notes"]


@pytest.mark.parametrize("profile_id", sorted(PROFILES))
def test_committed_raw_files_match_generator(data_root: Path, profile_id: str) -> None:
    profile = PROFILES[profile_id]
    assert check_raw(generate(profile), raw_dir(data_root, profile_id)) == []
    manifest = load_manifest(raw_dir(data_root, profile_id))
    assert manifest.profile == profile_id
    assert "SYNTHETIC" in manifest.synthetic_notice


def test_core_profile_includes_reference_masters() -> None:
    dataset = generate(PROFILES["core-healthcare-v1"])
    names = [t.name for t in dataset.tables]
    assert names[:2] == ["facilities", "payers"]
    facility_ids = {r["facility_id"] for r in dataset.table("facilities").rows}
    assert {r["facility_id"] for r in dataset.table("encounters").rows} <= facility_ids


def test_write_and_check_detect_tampering(tmp_path: Path) -> None:
    dataset = generate(HC_LAB_7FILE_V1)
    manifest = write_raw(dataset, tmp_path)
    assert manifest == build_manifest(dataset)
    assert check_raw(dataset, tmp_path) == []
    (tmp_path / "patients.csv").write_text("tampered\n", encoding="utf-8")
    (tmp_path / "vitals.csv").unlink()
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    problems = check_raw(dataset, tmp_path)
    assert "patients.csv differs from the generator output" in problems
    assert "missing vitals.csv" in problems
    assert "manifest.json differs from the generator output" in problems
    with pytest.raises(KeyError):
        manifest.entry("unknown")
    with pytest.raises(KeyError):
        dataset.table("unknown")


def test_profile_lookup_and_invalid_profiles() -> None:
    assert get_profile("hc-lab-7file-v1") is HC_LAB_7FILE_V1
    with pytest.raises(KeyError, match="valid profiles"):
        get_profile("nope")
    tiny = replace(HC_LAB_7FILE_V1, id="tiny", patients=20, encounters=120, conditions=30)
    with pytest.raises(GenerationError, match="at least the number of patients"):
        generate(replace(tiny, encounters=10))
    with pytest.raises(GenerationError, match="conditions"):
        generate(replace(tiny, patients=2, encounters=40, conditions=500))
