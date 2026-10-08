"""A small, read-mostly client for the Fabric REST API and Power BI ``executeQueries``.

Errors are translated into the provider error classes the router understands:

- 404 → ``UnknownResourceError``, a client error that never falls back;
- 400 and 403 → ``InvalidRequestError``, a client error;
- 401 (including ``UserNotLicensed``), 429 after bounded retries, 5xx and timeouts →
  ``ProviderUnavailableError``, which may fall back for reads.

Tokens and response bodies are never logged.
"""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast

import httpx

from fabric_foundry_accelerator.providers.errors import (
    InvalidRequestError,
    ProviderUnavailableError,
    UnknownResourceError,
)
from fabric_foundry_accelerator.providers.fabric.auth import (
    FABRIC_SCOPE,
    POWER_BI_SCOPE,
    TokenProvider,
)

FABRIC_BASE_URL = "https://api.fabric.microsoft.com/v1"
POWER_BI_BASE_URL = "https://api.powerbi.com/v1.0/myorg"
MAX_PAGES = 50
MAX_THROTTLE_RETRIES = 2
MAX_RETRY_AFTER_SECONDS = 30.0
LRO_POLL_LIMIT = 30

JsonObject = dict[str, Any]

GUIDANCE = {
    "UserNotLicensed": (
        "The signed-in account is not active in Fabric. Sign in once at https://app.fabric.microsoft.com "
        "with this account, confirm it has a Fabric (Free) or Power BI license, then retry. "
        "Run `ffia fabric readiness` for a full check."
    ),
    "InsufficientScopes": "The token lacks the required delegated scopes for this API.",
}


class FabricApiError(ProviderUnavailableError):
    """A non-client failure from the Fabric or Power BI API, with its documented error code."""

    def __init__(self, status: int, code: str, message: str, request_id: str | None) -> None:
        """Keep the documented error fields; never the token or full body."""
        hint = GUIDANCE.get(code, "")
        super().__init__(f"HTTP {status} {code}: {message}{' ' + hint if hint else ''}")
        self.status = status
        self.code = code
        self.request_id = request_id


def _error_fields(response: httpx.Response) -> tuple[str, str, str | None]:
    try:
        body = cast("Mapping[str, Any]", response.json())
    except ValueError:
        return f"HTTP{response.status_code}", response.reason_phrase, None
    error = body.get("error")
    if isinstance(error, Mapping):  # Power BI error shape
        nested = cast("Mapping[str, Any]", error)
        return str(nested.get("code", "Unknown")), str(nested.get("message", "")), None
    return (
        str(body.get("errorCode", f"HTTP{response.status_code}")),
        str(body.get("message", response.reason_phrase))[:300],
        cast("str | None", body.get("requestId")),
    )


class FabricRestClient:
    """Authenticated JSON calls with throttling, pagination and long-running operation support."""

    def __init__(
        self,
        tokens: TokenProvider,
        *,
        http: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        fabric_base_url: str = FABRIC_BASE_URL,
        power_bi_base_url: str = POWER_BI_BASE_URL,
    ) -> None:
        """Create a client. Pass ``http`` to inject a transport (tests use a mock transport)."""
        self._tokens = tokens
        self._http = http or httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        self._sleep = sleep
        self.fabric_base_url = fabric_base_url.rstrip("/")
        self.power_bi_base_url = power_bi_base_url.rstrip("/")

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    async def _send(
        self,
        method: str,
        url: str,
        *,
        scope: str,
        json: object | None = None,
        params: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        token = await self._tokens.token(scope)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        for attempt in range(MAX_THROTTLE_RETRIES + 1):
            try:
                response = await self._http.request(
                    method, url, headers=headers, json=json, params=params
                )
            except httpx.TimeoutException as error:
                raise ProviderUnavailableError(f"{method} {url} timed out") from error
            except httpx.TransportError as error:
                raise ProviderUnavailableError(
                    f"{method} {url} failed: {type(error).__name__}"
                ) from error
            if response.status_code == 429 and attempt < MAX_THROTTLE_RETRIES:
                retry_after = float(response.headers.get("Retry-After", "1") or 1)
                await self._sleep(min(max(retry_after, 0.0), MAX_RETRY_AFTER_SECONDS))
                continue
            return self._raise_for_status(response)
        raise AssertionError("unreachable")  # pragma: no cover - loop always returns or raises

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> httpx.Response:
        status = response.status_code
        if status < 400:
            return response
        code, message, request_id = _error_fields(response)
        if status == 404:
            raise UnknownResourceError(f"{code}: {message}")
        if status in (400, 403, 409):
            raise InvalidRequestError(f"HTTP {status} {code}: {message}")
        raise FabricApiError(status, code, message, request_id)

    async def token_for(self, scope: str) -> None:
        """Acquire (and discard) a token: proves the credential works for ``scope``."""
        await self._tokens.token(scope)

    async def get_json(self, url: str, *, scope: str) -> JsonObject:
        """GET an absolute URL and return its JSON object."""
        return cast("JsonObject", (await self._send("GET", url, scope=scope)).json())

    async def get_all(
        self, path: str, *, key: str = "value", params: Mapping[str, str] | None = None
    ) -> list[JsonObject]:
        """GET a Fabric list endpoint and follow ``continuationToken`` pages (bounded)."""
        items: list[JsonObject] = []
        query = dict(params or {})
        for _ in range(MAX_PAGES):
            response = await self._send(
                "GET", f"{self.fabric_base_url}{path}", scope=FABRIC_SCOPE, params=query
            )
            body = cast("JsonObject", response.json())
            items.extend(cast("list[JsonObject]", body.get(key, [])))
            token = body.get("continuationToken")
            if not token:
                return items
            query["continuationToken"] = str(token)
        raise ProviderUnavailableError(f"{path}: more than {MAX_PAGES} pages; narrow the request")

    async def post_fabric(self, path: str, body: JsonObject) -> JsonObject:
        """POST to Fabric; follow a 202 long-running operation to its result."""
        response = await self._send(
            "POST", f"{self.fabric_base_url}{path}", scope=FABRIC_SCOPE, json=body
        )
        if response.status_code != 202:
            return cast("JsonObject", response.json() if response.content else {})
        return await self._wait_for_operation(response)

    async def _wait_for_operation(self, accepted: httpx.Response) -> JsonObject:
        location = accepted.headers.get("Location")
        if not location:
            raise ProviderUnavailableError("202 Accepted without a Location header")
        delay = float(accepted.headers.get("Retry-After", "2") or 2)
        for _ in range(LRO_POLL_LIMIT):
            await self._sleep(min(delay, MAX_RETRY_AFTER_SECONDS))
            state = cast(
                "JsonObject", (await self._send("GET", location, scope=FABRIC_SCOPE)).json()
            )
            status = str(state.get("status", ""))
            if status == "Succeeded":
                result = await self._send(
                    "GET", f"{location.rstrip('/')}/result", scope=FABRIC_SCOPE
                )
                return cast("JsonObject", result.json() if result.content else {})
            if status in ("Failed", "Undefined"):
                error = cast("Mapping[str, Any]", state.get("error") or {})
                raise FabricApiError(
                    500, str(error.get("errorCode", status)), str(error.get("message", "")), None
                )
        raise ProviderUnavailableError("long-running operation did not finish in time")

    async def execute_dax(self, workspace_id: str, dataset_id: str, query: str) -> list[JsonObject]:
        """Run one DAX query (read-only) and return the rows of the first table."""
        url = f"{self.power_bi_base_url}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
        body = {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}
        response = await self._send("POST", url, scope=POWER_BI_SCOPE, json=body)
        results = cast("list[JsonObject]", response.json().get("results", []))
        tables = cast("list[JsonObject]", results[0].get("tables", [])) if results else []
        return cast("list[JsonObject]", tables[0].get("rows", [])) if tables else []
