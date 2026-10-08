"""Opt-in, read-only smoke test against the presenter's demo tenant.

Runs only with ``FFIA_FABRIC_LIVE=1`` and the git-ignored bindings file, and only when selected with
``pytest -m live``. It performs GET requests (and token acquisition) only; it never writes.
"""

import os
from pathlib import Path

import pytest
from tests.conftest import CONFIG_ROOT, DATA_ROOT

from fabric_foundry_accelerator.config.bindings import load_bindings
from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.providers.fabric.auth import AzureCliTokenProvider
from fabric_foundry_accelerator.providers.fabric.live import LiveFabricProvider
from fabric_foundry_accelerator.providers.fabric.rest import FabricRestClient
from fabric_foundry_accelerator.services.fabric_readiness import run_readiness

OVERLAY = os.environ.get("FFIA_OVERLAY", "example-healthcare")
BINDINGS = load_bindings(Path(CONFIG_ROOT), OVERLAY)

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("FFIA_FABRIC_LIVE") != "1" or BINDINGS is None,
        reason="live read-only tests need FFIA_FABRIC_LIVE=1 and the local bindings file",
    ),
]


async def test_tenant_is_ready_and_bound_workspaces_are_visible() -> None:
    assert BINDINGS is not None
    client = FabricRestClient(AzureCliTokenProvider(BINDINGS.tenant_id))
    try:
        report = await run_readiness(client, BINDINGS, BINDINGS.tenant_id)
        failed = [f"{c.name}: {c.detail}" for c in report.checks if c.status == "FAIL"]
        assert report.ready, failed
        provider = LiveFabricProvider(
            client, BINDINGS, data_root=DATA_ROOT, mode=OperatingMode.HYBRID
        )
        workspaces = await provider.list_workspaces()
        assert workspaces.execution_label is ExecutionLabel.LIVE
        visible = {w.id.lower() for w in workspaces.data}
        assert all(b.workspace_id.lower() in visible for b in BINDINGS.workspaces.values())
    finally:
        await client.aclose()
