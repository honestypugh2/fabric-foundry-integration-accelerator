"""Offline guarantees: no network, no Azure configuration.

Every test in ``tests/offline`` runs with sockets blocked and cloud-related environment
variables removed. If the offline path ever reaches for the network, these tests fail.
"""

import os
import socket
from collections.abc import Iterator

import pytest

_CLOUD_PREFIXES = ("AZURE_", "FABRIC_", "FOUNDRY_", "AZD_", "MSI_", "IDENTITY_", "ARM_")


class NetworkBlockedError(RuntimeError):
    """Raised when offline code attempts network access."""


def _blocked(*_args: object, **_kwargs: object) -> object:
    raise NetworkBlockedError("network access attempted during an offline test")


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in list(os.environ):
        if name.startswith(_CLOUD_PREFIXES):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)
    yield
