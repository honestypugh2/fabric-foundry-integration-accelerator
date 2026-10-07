from datetime import date
from pathlib import Path

import duckdb
import pytest

from fabric_foundry_accelerator.models.checks import failed
from fabric_foundry_accelerator.synthetic.medallion import (
    DataNotBuiltError,
    DataValidationError,
    TableSpec,
    build_profile,
    foreign_key_check,
    key_check,
    lakehouse_tables,
    open_lakehouse,
    read_sql,
    silver_diagnostics,
)
from fabric_foundry_accelerator.synthetic.paths import raw_dir
from fabric_foundry_accelerator.synthetic.pipeline import ValidationReport
from fabric_foundry_accelerator.synthetic.profiles import HC_LAB_7FILE_V1
from fabric_foundry_accelerator.synthetic.sqlutil import (
    UnsafeIdentifierError,
    quote_ident,
    sql_literal,
)

# (encounter_id, patient, type, admit, discharge). Cutoff = latest encounter_date = 2025-03-31.
READMISSION_CASES = [
    ("E01", "P1", "Inpatient", date(2025, 1, 1), date(2025, 1, 5)),
    ("E02", "P1", "Inpatient", date(2025, 1, 6), date(2025, 1, 8)),  # 1 day after E01 -> readmit
    ("E03", "P1", "Inpatient", date(2025, 2, 7), date(2025, 2, 9)),  # 30 days after E02 -> readmit
    ("E04", "P2", "Inpatient", date(2025, 1, 1), date(2025, 1, 10)),
    ("E05", "P2", "Inpatient", date(2025, 2, 10), date(2025, 2, 11)),  # 31 days -> not
    ("E06", "P3", "Inpatient", date(2025, 1, 1), date(2025, 1, 10)),
    (
        "E07",
        "P3",
        "Inpatient",
        date(2025, 1, 10),
        date(2025, 1, 12),
    ),  # same day -> not strictly after
    ("E08", "P3", "ED", date(2025, 1, 20), date(2025, 1, 20)),  # ED never qualifies
    ("E09", "P4", "Inpatient", date(2025, 3, 10), date(2025, 3, 12)),  # < 30 days before cutoff
    ("E10", "P4", "Outpatient", date(2025, 3, 31), date(2025, 3, 31)),  # defines the cutoff
]


@pytest.fixture
def readmissions() -> dict[str, tuple[object, ...]]:
    with duckdb.connect() as con:
        con.execute(
            "CREATE TABLE silver_encounters (encounter_id VARCHAR, patient_id VARCHAR, "
            "facility_id VARCHAR, encounter_date DATE, discharge_date DATE, "
            "is_inpatient BOOLEAN, is_chronology_valid BOOLEAN)"
        )
        con.executemany(
            "INSERT INTO silver_encounters VALUES (?, ?, 'FAC-01', ?, ?, ?, true)",
            [[e, p, a, d, t == "Inpatient"] for e, p, t, a, d in READMISSION_CASES],
        )
        gold_sql = read_sql("gold_shared/readmissions.sql")
        columns = (
            "index_encounter_id, days_to_next_admission, is_readmitted_30d, is_followup_eligible"
        )
        query = f"SELECT {columns} FROM ({gold_sql})"  # noqa: S608 - packaged SQL file
        rows = con.execute(query).fetchall()
    return {str(r[0]): tuple(r[1:]) for r in rows}


def test_one_row_per_index_inpatient_encounter(readmissions: dict[str, tuple[object, ...]]) -> None:
    assert sorted(readmissions) == ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E09"]


@pytest.mark.parametrize(
    ("index", "days", "readmitted"),
    [
        ("E01", 1, True),
        ("E02", 30, True),
        ("E04", 31, False),
        ("E06", None, False),
        ("E03", None, False),
    ],
)
def test_readmission_interval_is_1_to_30_days_strictly_after_discharge(
    readmissions: dict[str, tuple[object, ...]], index: str, days: int | None, readmitted: bool
) -> None:
    assert readmissions[index][:2] == (days, readmitted)


def test_followup_eligibility_requires_30_days_before_cutoff(
    readmissions: dict[str, tuple[object, ...]],
) -> None:
    assert readmissions["E01"][2] is True
    assert readmissions["E09"][2] is False


def test_hc_build_produces_guide_tables(built: tuple[Path, dict[str, ValidationReport]]) -> None:
    _, reports = built
    counts = reports["hc-lab-7file-v1"].build.row_counts
    assert len(counts["bronze"]) == 7 and len(counts["silver"]) == 7
    gold = counts["gold"]
    assert sum(1 for t in gold if t.startswith("gold_")) == 6
    assert sum(1 for t in gold if t.startswith("dim_")) == 4
    assert counts["bronze"]["bronze_vitals"] == 4299
    assert counts["silver"]["silver_conditions"] == 428


@pytest.mark.parametrize("profile_id", ["hc-lab-7file-v1", "core-healthcare-v1"])
def test_builds_pass_all_checks_and_match_committed_baselines(
    built: tuple[Path, dict[str, ValidationReport]], profile_id: str
) -> None:
    report = built[1][profile_id]
    assert failed(list(report.checks)) == []
    assert report.baseline_differences == ()
    assert report.passed


def test_core_build_has_physical_role_playing_dates(
    built: tuple[Path, dict[str, ValidationReport]],
) -> None:
    gold = built[1]["core-healthcare-v1"].build.row_counts["gold"]
    assert {"dim_date_admission", "dim_date_discharge", "dim_date_claim"} <= set(gold)
    assert "_date_spine" not in gold


def test_silver_preserves_literal_text_and_blank_encounter_ids(
    built: tuple[Path, dict[str, ValidationReport]],
) -> None:
    output_root, _ = built
    with open_lakehouse(output_root, "hc-lab-7file-v1") as con:
        diagnostics = silver_diagnostics(con)
        literal = con.execute(
            "SELECT count(*) FROM silver_clinical_notes WHERE contains(note_text, chr(92) || 'n')"
        ).fetchone()
    assert diagnostics["notes_with_literal_newline"] == 56
    assert literal == (56,)
    assert diagnostics["conditions_with_blank_encounter_id"] == 428
    assert diagnostics["notes_with_embedded_newline"] == 0


def test_dim_patient_excludes_direct_identifiers(
    built: tuple[Path, dict[str, ValidationReport]],
) -> None:
    output_root, _ = built
    with open_lakehouse(output_root, "hc-lab-7file-v1") as con:
        columns = {str(r[0]) for r in con.execute("DESCRIBE dim_patient").fetchall()}
    assert not {"first_name", "last_name", "date_of_birth"} & columns


def test_bronze_count_mismatch_blocks_the_build(tmp_path: Path, data_root: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    for source in raw_dir(data_root, HC_LAB_7FILE_V1.id).iterdir():
        (raw / source.name).write_bytes(source.read_bytes())
    lines = (raw / "patients.csv").read_text(encoding="utf-8").splitlines()
    (raw / "patients.csv").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(DataValidationError, match="Bronze validation failed") as error:
        build_profile(HC_LAB_7FILE_V1, raw_dir=raw, output_root=tmp_path / "out")
    assert error.value.checks
    assert not (tmp_path / "out" / "gold").exists()


def test_key_and_foreign_key_checks_detect_problems() -> None:
    with duckdb.connect() as con:
        con.execute("CREATE TABLE dim (k VARCHAR)")
        con.execute("INSERT INTO dim VALUES ('a'), ('a'), (NULL)")
        con.execute("CREATE TABLE fact (k VARCHAR)")
        con.execute("INSERT INTO fact VALUES ('a'), ('b'), (NULL)")
        assert not key_check(con, "dim", ["k"]).passed
        result = foreign_key_check(con, "fact", "k", "dim", "k")
    assert not result.passed
    assert result.detail.startswith("1 fact rows")


def test_open_lakehouse_requires_a_build(tmp_path: Path) -> None:
    assert lakehouse_tables(tmp_path, "hc-lab-7file-v1") == []
    with pytest.raises(DataNotBuiltError, match="ffia data build"):
        open_lakehouse(tmp_path, "hc-lab-7file-v1")


def test_sql_helpers_reject_unsafe_identifiers_and_escape_literals() -> None:
    assert quote_ident("gold_financial") == '"gold_financial"'
    assert quote_ident("_date_spine") == '"_date_spine"'
    for bad in ("x; DROP TABLE y", "Upper", 'a"b', ""):
        with pytest.raises(UnsafeIdentifierError):
            quote_ident(bad)
    assert sql_literal("it's") == "'it''s'"
    assert sql_literal(Path("a/b.parquet")) == "'a/b.parquet'"


def test_table_spec_staging_flag() -> None:
    assert TableSpec("_x", "f.sql").staging
    assert not TableSpec("x", "f.sql").staging
