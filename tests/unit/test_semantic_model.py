from pathlib import Path

import pytest
from pydantic import ValidationError

from fabric_foundry_accelerator.models.semantic import (
    SemanticMeasure,
    SemanticModel,
    is_identifier,
    load_semantic_model,
)
from fabric_foundry_accelerator.synthetic.paths import semantic_model_path
from fabric_foundry_accelerator.synthetic.profiles import PROFILES

GUIDE_MEASURES = {
    "total_encounters",
    "ed_visit_count",
    "average_length_of_stay",
    "readmission_rate_30_day",
    "total_paid_amount",
    "total_denied_claim_amount",
    "denial_rate",
    "average_charges_per_encounter",
    "patient_count",
    "high_risk_patient_count",
    "high_risk_patient_pct",
}


@pytest.mark.parametrize("profile_id", sorted(PROFILES))
def test_semantic_models_load_and_exclude_bed_occupancy(data_root: Path, profile_id: str) -> None:
    model = load_semantic_model(semantic_model_path(data_root, profile_id))
    assert model.profile == profile_id
    assert {m.name for m in model.measures} >= GUIDE_MEASURES
    assert "bed_occupancy_rate" in {m.name for m in model.excluded_measures}
    assert all(
        r.cardinality == "one_to_many" and r.cross_filter == "single" for r in model.relationships
    )


def test_hc_model_matches_guide_contract(data_root: Path) -> None:
    model = load_semantic_model(semantic_model_path(data_root, "hc-lab-7file-v1"))
    assert {t.name for t in model.tables} == {
        "gold_encounter_summary",
        "gold_financial",
        "gold_readmissions",
        "dim_date",
        "dim_patient",
        "dim_facility",
        "dim_payer",
    }
    date_roles = {
        r.to_table: r.to_column for r in model.relationships if r.from_table == "dim_date"
    }
    assert date_roles == {
        "gold_encounter_summary": "encounter_date",
        "gold_financial": "claim_date",
        "gold_readmissions": "index_discharge_date",
    }
    payer = [r for r in model.relationships if r.from_table == "dim_payer"]
    assert [r.to_table for r in payer] == ["gold_financial"]
    assert model.storage_mode == "DirectLake"


def test_core_model_uses_physical_role_playing_dates(data_root: Path) -> None:
    model = load_semantic_model(semantic_model_path(data_root, "core-healthcare-v1"))
    roles = {r.from_table for r in model.relationships if r.role}
    assert roles == {"dim_date_admission", "dim_date_discharge", "dim_date_claim"}
    assert all(r.active for r in model.relationships)


def test_measure_lookup_and_unknown_measure(data_root: Path) -> None:
    model = load_semantic_model(semantic_model_path(data_root, "hc-lab-7file-v1"))
    assert model.measure("denial_rate").format == "percent"
    with pytest.raises(KeyError):
        model.measure("missing")


def _measure(**overrides: object) -> SemanticMeasure:
    fields: dict[str, object] = {
        "name": "m",
        "display_name": "M",
        "home_table": "f",
        "description": "d",
        "definition": "d",
        "format": "integer",
        "sql": "SELECT 1",
        "dax": "1",
    }
    fields.update(overrides)
    return SemanticMeasure.model_validate(fields)


@pytest.mark.parametrize("sql", ["DROP TABLE x", "SELECT 1; DROP TABLE x"])
def test_measure_sql_must_be_a_single_select(sql: str) -> None:
    with pytest.raises(ValidationError, match="single SELECT"):
        _measure(sql=sql)


def _model(**overrides: object) -> SemanticModel:
    fields: dict[str, object] = {
        "id": "m",
        "profile": "p",
        "name": "n",
        "description": "d",
        "synthetic_notice": "s",
        "storage_mode": "DirectLake",
        "tables": [
            {"name": "f", "role": "fact", "grain": "g", "description": "d"},
            {"name": "d", "role": "dimension", "grain": "g", "description": "d"},
        ],
        "relationships": [
            {
                "from_table": "d",
                "from_column": "k",
                "to_table": "f",
                "to_column": "k",
                "description": "r",
            }
        ],
        "measures": [_measure().model_dump()],
    }
    fields.update(overrides)
    return SemanticModel.model_validate(fields)


def test_model_reference_validation() -> None:
    assert _model().measure("m").name == "m"
    with pytest.raises(ValidationError, match="unknown table"):
        _model(
            relationships=[
                {
                    "from_table": "x",
                    "from_column": "k",
                    "to_table": "f",
                    "to_column": "k",
                    "description": "r",
                }
            ]
        )
    with pytest.raises(ValidationError, match="dimension to a fact"):
        _model(
            relationships=[
                {
                    "from_table": "f",
                    "from_column": "k",
                    "to_table": "d",
                    "to_column": "k",
                    "description": "r",
                }
            ]
        )
    with pytest.raises(ValidationError, match="duplicate measure"):
        _model(measures=[_measure().model_dump(), _measure().model_dump()])
    with pytest.raises(ValidationError, match="unknown home table"):
        _model(measures=[_measure(home_table="zz").model_dump()])
    with pytest.raises(ValidationError, match="duplicate table"):
        _model(
            tables=[{"name": "f", "role": "fact", "grain": "g", "description": "d"}] * 2,
            relationships=[],
        )


def test_is_identifier() -> None:
    assert is_identifier("gold_financial")
    assert not is_identifier("x; drop")
