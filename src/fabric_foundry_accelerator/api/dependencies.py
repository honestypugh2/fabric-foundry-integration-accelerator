"""Shared HTTP dependencies; no feature-router imports."""

from typing import Annotated

from fastapi import Depends, Request

from fabric_foundry_accelerator.models.execution import new_correlation_id
from fabric_foundry_accelerator.services.container import Container


def get_container(request: Request) -> Container:
    """Return the process container."""
    container: Container = request.app.state.container
    return container


def get_correlation_id(request: Request) -> str:
    """Return the request correlation ID set by middleware."""
    value: str = getattr(request.state, "correlation_id", new_correlation_id())
    return value


ContainerDep = Annotated[Container, Depends(get_container)]
CorrelationDep = Annotated[str, Depends(get_correlation_id)]
