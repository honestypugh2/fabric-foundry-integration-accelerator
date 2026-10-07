"""The offline data path end to end: generate-check -> build -> validate -> provider -> recovery.

This is the Phase 2 slice of the offline demo release gate.
"""

import os
import socket
from pathlib import Path

import pytest

from fabric_foundry_accelerator.models.execution import ExecutionLabel
from fabric_foundry_accelerator.providers.fabric import LocalFabricProvider
from fabric_foundry_accelerator.providers.fabric.local import WORKSPACE_ID
from fabric_foundry_accelerator.recovery.scenario import load_scenario, run_recovery_drill
from fabric_foundry_accelerator.synthetic.pipeline import build_and_validate, check_profile
from fabric_foundry_accelerator.synthetic.profiles import PROFILES
from tests.offline.conftest import NetworkBlockedError

pytestmark = pytest.mark.offline


def test_network_is_really_blocked() -> None:
    with pytest.raises(NetworkBlockedError):
        socket.create_connection(("example.com", 443))
    assert not [n for n in os.environ if n.startswith("AZURE_")]


async def test_offline_data_path_end_to_end(tmp_path: Path, data_root: Path) -> None:
    for profile in PROFILES.values():
        assert check_profile(profile, data_root) == []
        report = build_and_validate(profile, data_root=data_root, output_root=tmp_path)
        assert report.passed, report.baseline_differences

    provider = LocalFabricProvider(data_root, output_root=tmp_path)
    items = await provider.list_items(WORKSPACE_ID)
    lakehouses = [i.id for i in items.data if i.type == "Lakehouse"]
    assert len(lakehouses) == len(PROFILES)
    measures = await provider.evaluate_measures(
        "local-sm-hc-lab-7file-v1", ["readmission_rate_30_day"]
    )
    assert measures.execution_label is ExecutionLabel.LOCAL
    assert measures.cloud_operation_performed is False

    drill = run_recovery_drill(
        load_scenario(data_root / "recovery" / "scenario.yaml"),
        data_root=data_root,
        work_dir=tmp_path / "recovery",
    )
    assert drill.execution_label is ExecutionLabel.SIMULATED
    assert drill.data.recovered
