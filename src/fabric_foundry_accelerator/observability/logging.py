"""Structured, redacted logging with a correlation ID bound per request or operation."""

import logging
import sys
from collections.abc import MutableMapping

import structlog
from structlog.typing import EventDict, WrappedLogger

from fabric_foundry_accelerator.observability.redaction import redact_mapping


def _redact_processor(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    redacted: MutableMapping[str, object] = redact_mapping(dict(event_dict))
    return dict(redacted)


class _StderrLogger:
    """Write each line to the *current* ``sys.stderr``.

    Resolving the stream per call keeps logging working when stderr is swapped (test capture,
    MCP stdio hosts); stdout is never used so stdio MCP traffic stays clean.
    """

    def msg(self, message: str) -> None:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()

    log = debug = info = warn = warning = error = critical = exception = fatal = failure = err = msg


def _stderr_logger_factory(*_: object) -> _StderrLogger:
    return _StderrLogger()


def configure_logging(*, level: str = "INFO", json: bool = False) -> None:
    """Configure structlog. Safe to call more than once."""
    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer(colors=False)
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_processor,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=_stderr_logger_factory,
        cache_logger_on_first_use=False,
    )


def bind_correlation_id(correlation_id: str) -> None:
    """Bind a correlation ID to every log line emitted in the current context."""
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_context() -> None:
    """Clear bound context variables."""
    structlog.contextvars.clear_contextvars()


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    """Return a structured logger."""
    logger: structlog.typing.FilteringBoundLogger = structlog.get_logger(name)
    return logger
