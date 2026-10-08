"""OpenTelemetry tracing with an opt-in Azure Monitor (Application Insights) exporter.

Spans carry the correlation ID, provider, execution label, fallback flag and tool names, so a
trace in Application Insights lines up with the audit record and the API response. Question and
answer text are never recorded (only their lengths): prompts can contain business data.

Without a connection string, the OpenTelemetry API is a no-op and nothing leaves the process.
"""

from collections.abc import Sequence

from opentelemetry import trace
from opentelemetry.trace import Span, Tracer
from pydantic import SecretStr

TRACER_NAME = "fabric_foundry_accelerator"


def get_tracer() -> Tracer:
    """Return the package tracer (no-op until a provider is configured)."""
    return trace.get_tracer(TRACER_NAME)


def configure_tracing(connection_string: SecretStr | None) -> str:
    """Enable Azure Monitor export when a connection string is set; return a status line."""
    if connection_string is None or not connection_string.get_secret_value():
        return "Tracing: OpenTelemetry API only (no exporter configured)"
    from azure.monitor.opentelemetry import (  # noqa: PLC0415 - opt-in only
        configure_azure_monitor,  # pyright: ignore[reportUnknownVariableType]
    )

    configure_azure_monitor(
        connection_string=connection_string.get_secret_value(), enable_live_metrics=False
    )
    return "Tracing: exporting to Application Insights (Azure Monitor OpenTelemetry)"


def record_envelope(
    span: Span,
    *,
    correlation_id: str,
    provider: str,
    label: str,
    fallback_used: bool,
    tools: Sequence[str] = (),
    grounded: bool | None = None,
) -> None:
    """Attach the evidence fields of a result envelope to a span."""
    span.set_attribute("ffia.correlation_id", correlation_id)
    span.set_attribute("ffia.provider", provider)
    span.set_attribute("ffia.execution_label", label)
    span.set_attribute("ffia.fallback_used", fallback_used)
    if tools:
        span.set_attribute("ffia.tools", list(tools))
    if grounded is not None:
        span.set_attribute("ffia.grounded", grounded)
