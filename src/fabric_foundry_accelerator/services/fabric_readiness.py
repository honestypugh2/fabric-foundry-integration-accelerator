"""``ffia fabric readiness``: read-only checks that a demo tenant is ready for the live labs.

Every check is a GET (or token acquisition) against the tenant pinned in the local bindings file
(or ``--tenant``). Nothing is created or changed. Each failing check carries the remediation step.
"""

import asyncio
import re
from typing import Literal

from azure.core.exceptions import ClientAuthenticationError
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.config.bindings import TenantBindings
from fabric_foundry_accelerator.providers.errors import ProviderError
from fabric_foundry_accelerator.providers.fabric.auth import FABRIC_SCOPE
from fabric_foundry_accelerator.providers.fabric.rest import (
    FabricApiError,
    FabricRestClient,
    JsonObject,
)

ReadinessStatus = Literal["PASS", "WARN", "FAIL", "SKIPPED"]


class SettingRequirement(BaseModel):
    """A tenant setting the labs rely on.

    Matched by ``settingName`` first, then by a portal-title pattern, because Microsoft documents
    the response shape but not a stable catalog of setting names.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    purpose: str
    names: tuple[str, ...]
    title_pattern: str
    required: bool = True

    def find(self, settings: list[JsonObject]) -> JsonObject | None:
        """Return the matching setting, if the tenant reported one."""
        wanted = {n.casefold() for n in self.names}
        for setting in settings:
            if str(setting.get("settingName", "")).casefold() in wanted:
                return setting
        pattern = re.compile(self.title_pattern, re.IGNORECASE)
        return next((s for s in settings if pattern.search(str(s.get("title", "")))), None)


SETTING_REQUIREMENTS: tuple[SettingRequirement, ...] = (
    SettingRequirement(
        purpose="Users can create Fabric items",
        names=("FabricGAWorkloads",),
        title_pattern=r"users can create fabric items",
    ),
    SettingRequirement(
        purpose="XMLA endpoints (Power BI Modeling MCP and DAX tools)",
        names=("AllowXMLAEndpoints", "XmlaEndpoints"),
        title_pattern=r"xmla endpoint",
    ),
    SettingRequirement(
        purpose="Semantic model Execute Queries REST API (DAX reconciliation)",
        names=("ExecuteQueriesRestApi", "DatasetExecuteQueries"),
        title_pattern=r"execute queries rest api",
    ),
    SettingRequirement(
        purpose="Git integration for workspaces",
        names=("EnableGitIntegration", "GitIntegrationTenantSwitch"),
        title_pattern=r"synchronize workspace items with their git|git integration",
    ),
    SettingRequirement(
        purpose="Fabric data agent items (preview features)",
        names=("AISkillArtifactTenantSwitch",),
        title_pattern=r"data agent",
        required=False,
    ),
    SettingRequirement(
        purpose="Copilot and Azure OpenAI features",
        names=("CopilotTenantSwitch",),
        title_pattern=r"copilot and other features powered by azure openai",
        required=False,
    ),
)


class ReadinessCheck(BaseModel):
    """One readiness check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    status: ReadinessStatus
    detail: str
    remediation: str = ""


class ReadinessReport(BaseModel):
    """All checks and an overall verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ready: bool
    checks: tuple[ReadinessCheck, ...]


def _first_line(error: BaseException) -> str:
    # Error text from azure-identity is already token-sanitized; keep it short and single-line.
    return (str(error).strip().splitlines() or [""])[0][:160]


def _mask(value: str) -> str:
    return f"{value[:4]}…{value[-4:]}" if len(value) > 12 else value


async def _api_access(client: FabricRestClient) -> tuple[ReadinessCheck, list[JsonObject]]:
    try:
        workspaces = await client.get_all("/workspaces")
    except FabricApiError as error:
        remediation = (
            "Sign in once at https://app.fabric.microsoft.com with this account so the Fabric service "
            "activates it, and make sure it has a Fabric (Free) or Power BI Pro/PPU license."
            if error.code == "UserNotLicensed"
            else "Check the account, tenant and network, then retry."
        )
        return ReadinessCheck(
            name="Fabric API access", status="FAIL", detail=str(error), remediation=remediation
        ), []
    return ReadinessCheck(
        name="Fabric API access", status="PASS", detail=f"{len(workspaces)} workspaces visible"
    ), workspaces


async def _capacity(client: FabricRestClient) -> ReadinessCheck:
    capacities = await client.get_all("/capacities")
    active = [c for c in capacities if str(c.get("state", "")).lower() == "active"]
    if active:
        skus = sorted({str(c.get("sku", "?")) for c in active})
        return ReadinessCheck(
            name="Fabric capacity",
            status="PASS",
            detail=f"{len(active)} active ({', '.join(skus)})",
        )
    return ReadinessCheck(
        name="Fabric capacity",
        status="FAIL",
        detail=f"{len(capacities)} capacities visible, none active",
        remediation=(
            "Start a Fabric trial (Fabric portal → account manager → Start trial) or create an F2+ capacity "
            "in an Azure subscription of this tenant (register Microsoft.Fabric, then create it in the "
            "Azure portal), and make the account a capacity administrator or contributor."
        ),
    )


def _workspaces(rows: list[JsonObject], bindings: TenantBindings | None) -> list[ReadinessCheck]:
    if bindings is None or not bindings.workspaces:
        return [
            ReadinessCheck(
                name="Bound dev workspace",
                status="WARN",
                detail="No workspace aliases are bound",
                remediation="Create a dedicated dev workspace on the capacity and add it to the local bindings file.",
            )
        ]
    checks: list[ReadinessCheck] = []
    for alias, binding in bindings.workspaces.items():
        match = next(
            (r for r in rows if str(r.get("id", "")).lower() == binding.workspace_id.lower()), None
        )
        if match is None:
            checks.append(
                ReadinessCheck(
                    name=f"Workspace {alias}",
                    status="FAIL",
                    detail=f"workspace {_mask(binding.workspace_id)} is not visible to this account",
                    remediation="Check the workspace ID in the bindings file and the account's workspace role.",
                )
            )
            continue
        on_capacity = bool(match.get("capacityId"))
        checks.append(
            ReadinessCheck(
                name=f"Workspace {alias}",
                status="PASS" if on_capacity else "FAIL",
                detail="visible and assigned to a capacity"
                if on_capacity
                else "visible but not on a capacity",
                remediation=""
                if on_capacity
                else "Assign the workspace to the trial or F capacity (workspace settings → License info).",
            )
        )
    return checks


async def _tenant_settings(client: FabricRestClient) -> list[ReadinessCheck]:
    try:
        settings = await client.get_all("/admin/tenantsettings")
    except ProviderError as error:
        return [
            ReadinessCheck(
                name="Tenant settings",
                status="SKIPPED",
                detail=(
                    f"cannot read tenant settings ({type(error).__name__}); "
                    "a Fabric administrator role is required"
                ),
                remediation=(
                    "Ask a Fabric administrator to confirm the settings listed in "
                    "docs/operations/fabric-tenant-readiness.md."
                ),
            )
        ]
    checks: list[ReadinessCheck] = []
    for requirement in SETTING_REQUIREMENTS:
        setting = requirement.find(settings)
        name = f"Tenant setting: {requirement.purpose}"
        if setting is None:
            checks.append(
                ReadinessCheck(
                    name=name,
                    status="WARN" if requirement.required else "SKIPPED",
                    detail="not identified in the tenant settings response",
                    remediation="Confirm it manually in the Fabric admin portal → Tenant settings.",
                )
            )
            continue
        enabled = bool(setting.get("enabled"))
        checks.append(
            ReadinessCheck(
                name=name,
                status="PASS" if enabled else ("FAIL" if requirement.required else "WARN"),
                detail=f"{setting.get('settingName', '?')}: {'enabled' if enabled else 'disabled'}",
                remediation=""
                if enabled
                else "Enable it in the Fabric admin portal → Tenant settings (or for the lab group).",
            )
        )
    return checks


async def run_readiness(
    client: FabricRestClient, bindings: TenantBindings | None, tenant_id: str
) -> ReadinessReport:
    """Run every read-only check against one pinned tenant."""
    checks = [
        ReadinessCheck(
            name="Pinned tenant",
            status="PASS" if bindings else "WARN",
            detail=f"tenant {_mask(tenant_id)}"
            + ("" if bindings else " (from --tenant; no bindings file)"),
            remediation=""
            if bindings
            else "Create the git-ignored bindings file to pin the tenant and dev workspace.",
        )
    ]
    try:
        await client.token_for(FABRIC_SCOPE)
    except (ClientAuthenticationError, ProviderError, OSError) as error:
        checks.append(
            ReadinessCheck(
                name="Azure CLI sign-in",
                status="FAIL",
                detail=f"no token for the pinned tenant ({type(error).__name__}: {_first_line(error)})",
                remediation=(
                    "Run `az login --tenant <TENANT_ID>` with the demo tenant admin account. "
                    "If `az` opens a browser or reports AADSTS90072, the cached session belongs to "
                    "a different tenant or has expired."
                ),
            )
        )
        return ReadinessReport(ready=False, checks=tuple(checks))
    checks.append(
        ReadinessCheck(
            name="Azure CLI sign-in", status="PASS", detail="token acquired for the pinned tenant"
        )
    )
    access, workspaces = await _api_access(client)
    checks.append(access)
    if access.status == "PASS":
        checks.append(await _capacity(client))
        checks += _workspaces(workspaces, bindings)
        checks += await _tenant_settings(client)
    ready = all(c.status != "FAIL" for c in checks)
    return ReadinessReport(ready=ready, checks=tuple(checks))


def run_readiness_sync(
    client: FabricRestClient, bindings: TenantBindings | None, tenant_id: str
) -> ReadinessReport:
    """Synchronous wrapper for the CLI."""

    async def _run() -> ReadinessReport:
        try:
            return await run_readiness(client, bindings, tenant_id)
        finally:
            await client.aclose()

    return asyncio.run(_run())
