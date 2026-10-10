"""``ffia foundry readiness``: read-only checks that a Foundry project is ready for the agent demos.

Every check is a GET against Azure Resource Manager or the Foundry project endpoint, for the
resource named in the git-ignored bindings file. Nothing is created or changed. Each failing check
carries a remediation. Identifiers are never printed.
"""

import asyncio
from typing import Any, Literal, cast

import httpx
from pydantic import BaseModel, ConfigDict

from fabric_foundry_accelerator.config.bindings import FoundryBinding
from fabric_foundry_accelerator.providers.fabric.auth import TokenProvider

ARM = "https://management.azure.com"
ARM_SCOPE = "https://management.azure.com/.default"
FOUNDRY_SCOPE = "https://ai.azure.com/.default"
ARM_API_VERSION = "2025-06-01"
PROJECT_API_VERSION = "v1"

Status = Literal["PASS", "WARN", "FAIL", "SKIPPED"]


class FoundryCheck(BaseModel):
    """One readiness check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    status: Status
    detail: str
    remediation: str = ""


class FoundryReport(BaseModel):
    """All checks and an overall verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ready: bool
    checks: tuple[FoundryCheck, ...]


def project_endpoint(binding: FoundryBinding) -> str:
    """The Foundry project endpoint (no secrets; derived from resource and project names)."""
    return binding.endpoint


class FoundryReadiness:
    """Runs the read-only checks with an injected HTTP client and token provider."""

    def __init__(self, tokens: TokenProvider, http: httpx.AsyncClient | None = None) -> None:
        """Create the checker; tests inject a mock transport."""
        self._tokens = tokens
        self._http = http or httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()

    async def _get(
        self, url: str, scope: str, params: dict[str, str]
    ) -> tuple[int, dict[str, Any]]:
        token = await self._tokens.token(scope)
        try:
            response = await self._http.get(
                url, params=params, headers={"Authorization": f"Bearer {token}"}
            )
        except httpx.HTTPError as error:
            return 0, {"error": {"code": type(error).__name__}}
        try:
            body = cast("dict[str, Any]", response.json()) if response.content else {}
        except ValueError:
            body = {}
        return response.status_code, body

    def _account_url(self, b: FoundryBinding) -> str:
        return (
            f"{ARM}/subscriptions/{b.subscription_id}/resourceGroups/{b.resource_group}"
            f"/providers/Microsoft.CognitiveServices/accounts/{b.account}"
        )

    async def _account(self, b: FoundryBinding) -> FoundryCheck:
        status, body = await self._get(
            self._account_url(b), ARM_SCOPE, {"api-version": ARM_API_VERSION}
        )
        if status != 200:
            return FoundryCheck(
                name="Foundry resource",
                status="FAIL",
                detail=f"not readable (HTTP {status})",
                remediation=(
                    "Check the subscription, resource group and name in the bindings file, "
                    "and `az login --tenant`."
                ),
            )
        props = cast("dict[str, Any]", body.get("properties", {}))
        ok = body.get("kind") == "AIServices" and props.get("provisioningState") == "Succeeded"
        projects = bool(props.get("allowProjectManagement"))
        return FoundryCheck(
            name="Foundry resource",
            status="PASS" if ok and projects else "FAIL",
            detail=f"kind {body.get('kind')}, {props.get('provisioningState')}, projects enabled: {projects}",
            remediation=""
            if ok and projects
            else "Create an AIServices resource with --allow-project-management.",
        )

    async def _project(self, b: FoundryBinding) -> FoundryCheck:
        url = f"{self._account_url(b)}/projects/{b.project}"
        status, body = await self._get(url, ARM_SCOPE, {"api-version": ARM_API_VERSION})
        state = cast("dict[str, Any]", body.get("properties", {})).get("provisioningState")
        ok = status == 200 and state == "Succeeded"
        return FoundryCheck(
            name="Foundry project",
            status="PASS" if ok else "FAIL",
            detail=f"{state}" if status == 200 else f"not readable (HTTP {status})",
            remediation=""
            if ok
            else "Create the project: az cognitiveservices account project create.",
        )

    async def _deployments(self, b: FoundryBinding) -> FoundryCheck:
        status, body = await self._get(
            f"{self._account_url(b)}/deployments", ARM_SCOPE, {"api-version": ARM_API_VERSION}
        )
        if status != 200:
            return FoundryCheck(
                name="Model deployments", status="FAIL", detail=f"not readable (HTTP {status})"
            )
        rows = cast("list[dict[str, Any]]", body.get("value", []))
        ready = {
            str(r.get("name")): f"{cast('dict[str, Any]', r.get('sku', {})).get('name')}"
            for r in rows
            if cast("dict[str, Any]", r.get("properties", {})).get("provisioningState")
            == "Succeeded"
        }
        missing = [d for d in b.model_deployments if d not in ready]
        ok = not missing if b.model_deployments else bool(ready)
        detail = ", ".join(f"{name} ({sku})" for name, sku in sorted(ready.items())) or "none"
        return FoundryCheck(
            name="Model deployments",
            status="PASS" if ok else "FAIL",
            detail=detail + (f"; missing: {', '.join(missing)}" if missing else ""),
            remediation=""
            if ok
            else "Deploy a GA model: az cognitiveservices account deployment create.",
        )

    async def _data_plane(self, b: FoundryBinding) -> list[FoundryCheck]:
        base = project_endpoint(b)
        params = {"api-version": PROJECT_API_VERSION}
        status, agents_body = await self._get(f"{base}/agents", FOUNDRY_SCOPE, params)
        if status in (401, 403):
            return [
                FoundryCheck(
                    name="Project data-plane access",
                    status="FAIL",
                    detail=f"HTTP {status}",
                    remediation=(
                        "Assign the Foundry User role on the Foundry resource or project "
                        "to the signed-in user."
                    ),
                )
            ]
        if status != 200:
            return [
                FoundryCheck(
                    name="Project data-plane access", status="FAIL", detail=f"HTTP {status}"
                )
            ]
        checks = [
            FoundryCheck(
                name="Project data-plane access",
                status="PASS",
                detail="agents and connections readable",
            )
        ]
        names = {
            str(a.get("name")) for a in cast("list[dict[str, Any]]", agents_body.get("data", []))
        }
        for agent in b.agents:
            found = agent in names
            checks.append(
                FoundryCheck(
                    name=f"Agent {agent}",
                    status="PASS" if found else "WARN",
                    detail="exists" if found else "not found",
                    remediation=""
                    if found
                    else "Create it with the code-first sample (approval required).",
                )
            )
        if b.fabric_connection:
            _, conn_body = await self._get(f"{base}/connections", FOUNDRY_SCOPE, params)
            conns = {
                str(c.get("name")) for c in cast("list[dict[str, Any]]", conn_body.get("value", []))
            }
            found = b.fabric_connection in conns
            checks.append(
                FoundryCheck(
                    name="Fabric data agent connection",
                    status="PASS" if found else "FAIL",
                    detail="exists" if found else "not found",
                    remediation=""
                    if found
                    else (
                        "Foundry portal → Connected resources → New connection → Microsoft Fabric "
                        "(workspace and artifact IDs)."
                    ),
                )
            )
        return checks

    async def run(self, binding: FoundryBinding) -> FoundryReport:
        """Run every check."""
        checks = [await self._account(binding)]
        if checks[0].status == "PASS":
            checks += [await self._project(binding), await self._deployments(binding)]
            checks += await self._data_plane(binding)
        return FoundryReport(ready=all(c.status != "FAIL" for c in checks), checks=tuple(checks))


def run_sync(checker: FoundryReadiness, binding: FoundryBinding) -> FoundryReport:
    """Synchronous wrapper for the CLI."""

    async def _run() -> FoundryReport:
        try:
            return await checker.run(binding)
        finally:
            await checker.aclose()

    return asyncio.run(_run())
