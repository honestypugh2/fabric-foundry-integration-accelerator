"""The offline demo is a release gate: it must pass with the network blocked and no Azure configuration."""

from collections.abc import Callable
from pathlib import Path

import pytest

from fabric_foundry_accelerator.services.container import Container
from fabric_foundry_accelerator.services.demo import demo_check, run_offline_demo

pytestmark = pytest.mark.offline


async def test_offline_demo_release_gate(
    make_container: Callable[..., Container], tmp_path: Path
) -> None:
    container = make_container()
    check = await demo_check(container, azure_probe=False)
    assert check.recommended_mode.value == "OFFLINE"
    report = await run_offline_demo(container, work_dir=tmp_path)
    assert report.passed, [s for s in report.steps if s.required and not s.passed]
    assert report.live_operations == 0
    assert report.cloud_operations == 0
