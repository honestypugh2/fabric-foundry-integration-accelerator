"""Token acquisition for live Fabric and Power BI calls. Tokens are never logged or returned."""

import asyncio
from typing import Protocol

FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
POWER_BI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"


class TokenProvider(Protocol):
    """Returns a bearer token for a scope."""

    async def token(self, scope: str) -> str:
        """Return an access token for ``scope``."""
        ...


class AzureCliTokenProvider:
    """Uses the developer's ``az login`` session for one pinned tenant (delegated user identity)."""

    def __init__(self, tenant_id: str, *, process_timeout: int = 30) -> None:
        """Bind to a tenant so calls never drift to another signed-in tenant.

        Args:
            tenant_id: Tenant to pin.
            process_timeout: Seconds before giving up on ``az``. An expired session makes ``az``
                fall back to interactive browser sign-in, which would otherwise hang the command.
        """
        self._tenant_id = tenant_id
        self._process_timeout = process_timeout

    async def token(self, scope: str) -> str:
        """Return an access token for ``scope`` in the pinned tenant."""
        from azure.identity import AzureCliCredential  # noqa: PLC0415 - live path only

        credential = AzureCliCredential(
            tenant_id=self._tenant_id, process_timeout=self._process_timeout
        )
        access = await asyncio.to_thread(credential.get_token, scope)
        return access.token
