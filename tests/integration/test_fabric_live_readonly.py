"""Opt-in, read-only smoke test against the presenter's demo tenant.

Runs only with explicit ``FFIA_FABRIC_LIVE=1`` and private .env or YAML bindings, and selected with
``pytest -m live``. It performs GET requests (and token acquisition) only; it never writes.
"""

import os

import pytest
from tests.conftest import CONFIG_ROOT, DATA_ROOT

from fabric_foundry_accelerator.config.bindings import load_bindings
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.providers.fabric.auth import AzureCliTokenProvider
from fabric_foundry_accelerator.providers.fabric.live import LiveFabricProvider
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient
from fabric_foundry_accelerator.services.fabric_readiness import run_readiness

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("FFIA_FABRIC_LIVE") != "1",
        reason="live read-only tests need explicit FFIA_FABRIC_LIVE=1 and private cloud bindings",
    ),
]


async def test_tenant_is_ready_and_bound_workspaces_are_visible() -> None:
    settings = Settings(config_root=CONFIG_ROOT)
    bindings = load_bindings(settings.config_root, settings.overlay, settings=settings)
    if bindings is None:
        pytest.skip("Configure private cloud bindings in .env or the legacy local YAML")
    client = FabricRestClient(AzureCliTokenProvider(bindings.tenant_id))
    try:
        report = await run_readiness(client, bindings, bindings.tenant_id)
        failed = [f"{c.name}: {c.detail}" for c in report.checks if c.status == "FAIL"]
        assert report.ready, failed
        provider = LiveFabricProvider(
            client, bindings, data_root=DATA_ROOT, mode=OperatingMode.HYBRID
        )
        workspaces = await provider.list_workspaces()
        assert workspaces.execution_label is ExecutionLabel.LIVE
        visible = {w.id.lower() for w in workspaces.data}
        assert all(b.workspace_id.lower() in visible for b in bindings.workspaces.values())
    finally:
        await client.aclose()
