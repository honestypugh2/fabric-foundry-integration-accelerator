from pathlib import Path

import pytest

from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.providers.errors import InvalidRequestError, UnknownResourceError
from fabric_foundry_accelerator.providers.fabric import FabricProvider, LocalFabricProvider
from fabric_foundry_accelerator.providers.fabric.local import WORKSPACE_ID
from fabric_foundry_accelerator.synthetic.baseline import load_baseline
from fabric_foundry_accelerator.synthetic.paths import expected_baseline_path
from fabric_foundry_accelerator.synthetic.pipeline import ValidationReport

HC_LAKEHOUSE = "local-lh-hc-lab-7file-v1"
HC_MODEL = "local-sm-hc-lab-7file-v1"


@pytest.fixture
def provider(built: tuple[Path, dict[str, ValidationReport]], data_root: Path) -> FabricProvider:
    return LocalFabricProvider(data_root, output_root=built[0])


async def test_every_result_is_labeled_local_with_no_cloud_operation(
    provider: FabricProvider,
) -> None:
    workspaces = await provider.list_workspaces(correlation_id="a" * 32)
    assert workspaces.correlation_id == "a" * 32
    for envelope in (
        workspaces,
        await provider.list_items(WORKSPACE_ID),
        await provider.list_tables(HC_LAKEHOUSE),
        await provider.read_table(HC_LAKEHOUSE, "gold_financial", limit=1),
        await provider.get_semantic_model(HC_MODEL),
        await provider.evaluate_measures(HC_MODEL, ["claim_count"]),
    ):
        assert envelope.execution_label is ExecutionLabel.LOCAL
        assert envelope.operating_mode is OperatingMode.OFFLINE
        assert envelope.cloud_operation_performed is False
        assert envelope.simulation_notice and "No Microsoft Fabric" in envelope.simulation_notice
        assert envelope.equivalent_fabric_service
        assert envelope.evidence[0].category.value == "SIMULATED LOCALLY"


async def test_catalog_lists_items_and_24_hc_tables(provider: FabricProvider) -> None:
    items = (await provider.list_items(WORKSPACE_ID)).data
    assert {i.type for i in items} == {"Lakehouse", "SemanticModel"}
    assert HC_LAKEHOUSE in {i.id for i in items}
    tables = (await provider.list_tables(HC_LAKEHOUSE)).data
    assert len(tables) == 24
    assert {t.layer for t in tables} == {"bronze", "silver", "gold"}
    assert next(t for t in tables if t.name == "bronze_vitals").row_count == 4299


async def test_read_table_is_bounded_and_json_safe(provider: FabricProvider) -> None:
    preview = (await provider.read_table(HC_LAKEHOUSE, "gold_financial", limit=3)).data
    assert len(preview.rows) == 3
    assert preview.truncated and preview.total_rows == 1025
    row = preview.rows[0]
    assert isinstance(row["claim_amount"], str)
    assert isinstance(row["claim_date"], str)
    assert {c.name for c in preview.columns} >= {"claim_id", "payer_key"}


@pytest.mark.parametrize("limit", [0, 101])
async def test_read_table_rejects_out_of_contract_limits(
    provider: FabricProvider, limit: int
) -> None:
    with pytest.raises(InvalidRequestError):
        await provider.read_table(HC_LAKEHOUSE, "gold_financial", limit=limit)


@pytest.mark.parametrize("table", ["missing", "gold_financial; DROP TABLE x", "../raw/patients"])
async def test_read_table_only_accepts_catalogued_tables(
    provider: FabricProvider, table: str
) -> None:
    with pytest.raises(UnknownResourceError):
        await provider.read_table(HC_LAKEHOUSE, table)


async def test_unknown_workspace_item_and_measure_are_rejected(provider: FabricProvider) -> None:
    with pytest.raises(UnknownResourceError):
        await provider.list_items("other")
    with pytest.raises(UnknownResourceError):
        await provider.list_tables("local-lh-unknown")
    with pytest.raises(UnknownResourceError):
        await provider.list_tables(HC_MODEL)
    with pytest.raises(UnknownResourceError, match="unknown measure"):
        await provider.evaluate_measures(HC_MODEL, ["bed_occupancy_rate"])


async def test_measures_match_committed_baseline(provider: FabricProvider, data_root: Path) -> None:
    baseline = load_baseline(expected_baseline_path(data_root, "hc-lab-7file-v1"))
    values = (await provider.evaluate_measures(HC_MODEL)).data
    assert {v.name: v.value for v in values} == baseline.measures
    rate = next(v for v in values if v.name == "readmission_rate_30_day")
    assert rate.synthetic_demonstration and rate.format == "percent"


async def test_semantic_model_is_returned(provider: FabricProvider) -> None:
    model = (await provider.get_semantic_model(HC_MODEL)).data
    assert model.profile == "hc-lab-7file-v1"
    assert provider.name == "Local Fabric Educational Provider"


def test_local_provider_refuses_live_mode(data_root: Path) -> None:
    with pytest.raises(ValueError, match="LIVE"):
        LocalFabricProvider(data_root, mode=OperatingMode.LIVE)


async def test_hybrid_mode_is_recorded(
    built: tuple[Path, dict[str, ValidationReport]], data_root: Path
) -> None:
    provider = LocalFabricProvider(data_root, output_root=built[0], mode=OperatingMode.HYBRID)
    envelope = await provider.list_workspaces()
    assert envelope.operating_mode is OperatingMode.HYBRID
    assert envelope.execution_label is ExecutionLabel.LOCAL
