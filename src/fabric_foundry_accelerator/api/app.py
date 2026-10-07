"""FastAPI control plane.

Layers stay separate: HTTP (this package) -> services -> providers -> clients. Route handlers
contain no business logic; they validate input, call a service and return its result.
"""

import re
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from fabric_foundry_accelerator import __version__
from fabric_foundry_accelerator.api.routes import router
from fabric_foundry_accelerator.fallback.router import CapabilityUnavailableError
from fabric_foundry_accelerator.models.changes import ExecutionResult
from fabric_foundry_accelerator.models.execution import new_correlation_id
from fabric_foundry_accelerator.observability.logging import (
    bind_correlation_id,
    clear_context,
    get_logger,
)
from fabric_foundry_accelerator.observability.redaction import redact_text
from fabric_foundry_accelerator.patterns.catalog import UnknownNeedError
from fabric_foundry_accelerator.providers.errors import (
    InvalidRequestError,
    ProviderUnavailableError,
    UnknownResourceError,
)
from fabric_foundry_accelerator.providers.fabric.port import (
    ItemInfo,
    MeasureValue,
    TableInfo,
    TablePreview,
    WorkspaceInfo,
)
from fabric_foundry_accelerator.recovery.scenario import RecoveryReport
from fabric_foundry_accelerator.services.changes import ApprovalError, LiveWriteUnavailableError
from fabric_foundry_accelerator.services.container import Container, build_container
from fabric_foundry_accelerator.services.evaluation import EvaluationResult
from fabric_foundry_accelerator.synthetic.medallion import DataNotBuiltError

CORRELATION_HEADER = "X-Correlation-ID"
_CORRELATION_RE = re.compile(r"^[0-9a-f]{32}$")
_log = get_logger("ffia.api")

_ERRORS: tuple[tuple[type[Exception], int], ...] = (
    (UnknownResourceError, 404),
    (KeyError, 404),
    (InvalidRequestError, 422),
    (UnknownNeedError, 422),
    (ApprovalError, 409),
    (LiveWriteUnavailableError, 409),
    (CapabilityUnavailableError, 503),
    (ProviderUnavailableError, 503),
    (DataNotBuiltError, 503),
)


def _error_response(request: Request, error: Exception, status: int) -> JSONResponse:
    # KeyError's str() wraps the key in quotes; use the raw message instead.
    message = str(error.args[0]) if isinstance(error, KeyError) and error.args else str(error)
    body: dict[str, object] = {
        "error": type(error).__name__,
        "detail": redact_text(message),
        "correlation_id": getattr(request.state, "correlation_id", None),
    }
    if isinstance(error, CapabilityUnavailableError):
        body["route_decision"] = error.decision.model_dump(mode="json")
    if isinstance(error, LiveWriteUnavailableError):
        body["redirected_to_local"] = False
    return JSONResponse(status_code=status, content=body)


def _new_app() -> FastAPI:
    app = FastAPI(
        title="Fabric Foundry Integration Accelerator API",
        version=__version__,
        description="Control plane for the offline-first Fabric + Foundry reference implementation.",
    )
    app.include_router(router)
    return app


# Payloads carried inside ExecutionEnvelope.data. The envelope is generic over ``object`` on
# the wire, so these are published as extra components for typed clients.
ENVELOPE_PAYLOADS: tuple[type[BaseModel], ...] = (
    WorkspaceInfo,
    ItemInfo,
    TableInfo,
    TablePreview,
    MeasureValue,
    EvaluationResult,
    ExecutionResult,
    RecoveryReport,
)


def openapi_document() -> dict[str, object]:
    """Return the OpenAPI document without building a container (no data, no providers)."""
    document: dict[str, Any] = _new_app().openapi()
    _, definitions = models_json_schema(
        [(model, "serialization") for model in ENVELOPE_PAYLOADS],
        ref_template="#/components/schemas/{model}",
    )
    schemas: dict[str, Any] = document.setdefault("components", {}).setdefault("schemas", {})
    for name, schema in definitions.get("$defs", {}).items():
        schemas.setdefault(name, schema)
    return document


def create_app(container: Container | None = None) -> FastAPI:
    """Create the API application around a container (built from settings when omitted)."""
    services = container or build_container()
    app = _new_app()
    app.state.container = services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(services.settings.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", CORRELATION_HEADER],
        expose_headers=[CORRELATION_HEADER],
    )

    @app.middleware("http")
    async def correlation(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get(CORRELATION_HEADER, "")
        correlation_id = supplied if _CORRELATION_RE.match(supplied) else new_correlation_id()
        request.state.correlation_id = correlation_id
        bind_correlation_id(correlation_id)
        try:
            response = await call_next(request)
        finally:
            clear_context()
        response.headers[CORRELATION_HEADER] = correlation_id
        return response

    for error_type, status in _ERRORS:

        def handler(request: Request, error: Exception, status: int = status) -> JSONResponse:
            return _error_response(request, error, status)

        app.add_exception_handler(error_type, handler)

    _log.info("api.ready", environment=services.environment.name, mode=services.mode.value)
    return app
