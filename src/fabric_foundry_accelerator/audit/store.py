"""Append-only audit records keyed by correlation ID.

Every important operation leaves structured evidence: who asked, which provider was requested
and selected, how the result was labeled, whether a cloud operation was performed, whether a
fallback happened and why, and which change/approval it relates to. Details are redacted.
"""

import json
import threading
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Protocol

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from fabric_foundry_accelerator.models.execution import (
    ExecutionEnvelope,
    ExecutionLabel,
    OperatingMode,
    new_correlation_id,
    utc_now,
)
from fabric_foundry_accelerator.observability.redaction import redact_mapping


class AuditRecord(BaseModel):
    """One audit entry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit_id: str = Field(default_factory=new_correlation_id)
    correlation_id: str
    timestamp: AwareDatetime = Field(default_factory=utc_now)
    actor: str
    action: str
    capability: str
    requested_provider: str
    selected_provider: str
    operating_mode: OperatingMode
    execution_label: ExecutionLabel
    cloud_operation_performed: bool
    success: bool
    duration_ms: float | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    change_id: str | None = None
    approval_id: str | None = None
    tool: str | None = None
    details: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict[str, str | int | float | bool | None]
    )


class AuditStore(Protocol):
    """Persistence port for audit records."""

    def record(self, record: AuditRecord) -> AuditRecord:
        """Store a record and return it."""
        ...

    def for_correlation(self, correlation_id: str) -> list[AuditRecord]:
        """Return records for a correlation ID, oldest first."""
        ...

    def recent(self, limit: int = 50) -> list[AuditRecord]:
        """Return the most recent records, newest last."""
        ...


def safe_details(details: Mapping[str, object]) -> dict[str, str | int | float | bool | None]:
    """Redact details and coerce values to JSON scalars."""
    redacted = redact_mapping(details)
    return {
        k: v if isinstance(v, str | int | float | bool) or v is None else str(v)
        for k, v in redacted.items()
    }


def audit_from_envelope[T](
    envelope: ExecutionEnvelope[T],
    *,
    actor: str,
    action: str,
    capability: str,
    success: bool = True,
    duration_ms: float | None = None,
    details: Mapping[str, object] | None = None,
    tool: str | None = None,
) -> AuditRecord:
    """Build an audit record from an envelope (the envelope carries the execution facts)."""
    return AuditRecord(
        correlation_id=envelope.correlation_id,
        actor=actor,
        action=action,
        capability=capability,
        requested_provider=envelope.requested_provider,
        selected_provider=envelope.selected_provider,
        operating_mode=envelope.operating_mode,
        execution_label=envelope.execution_label,
        cloud_operation_performed=envelope.cloud_operation_performed,
        success=success,
        duration_ms=duration_ms,
        fallback_used=envelope.fallback_used,
        fallback_reason=envelope.fallback_reason,
        tool=tool,
        details=safe_details(details or {}),
    )


class InMemoryAuditStore:
    """Thread-safe in-memory audit store (tests, ephemeral demos)."""

    def __init__(self) -> None:
        """Create an empty store."""
        self._records: list[AuditRecord] = []
        self._lock = threading.Lock()

    def record(self, record: AuditRecord) -> AuditRecord:
        """Store a record."""
        with self._lock:
            self._records.append(record)
        return record

    def for_correlation(self, correlation_id: str) -> list[AuditRecord]:
        """Return records for a correlation ID."""
        with self._lock:
            return [r for r in self._records if r.correlation_id == correlation_id]

    def recent(self, limit: int = 50) -> list[AuditRecord]:
        """Return recent records."""
        with self._lock:
            return list(self._records[-limit:])


class JsonlAuditStore:
    """Append-only JSON Lines audit store on local disk."""

    def __init__(self, path: Path) -> None:
        """Create a store writing to ``path`` (parent folders are created)."""
        self._path = path
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, record: AuditRecord) -> AuditRecord:
        """Append a record."""
        line = record.model_dump_json()
        with self._lock, self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return record

    def _all(self) -> list[AuditRecord]:
        if not self._path.is_file():
            return []
        with self._lock:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        return [AuditRecord.model_validate(json.loads(line)) for line in lines if line.strip()]

    def for_correlation(self, correlation_id: str) -> list[AuditRecord]:
        """Return records for a correlation ID."""
        return [r for r in self._all() if r.correlation_id == correlation_id]

    def recent(self, limit: int = 50) -> list[AuditRecord]:
        """Return recent records."""
        return self._all()[-limit:]


def elapsed_ms(started: datetime) -> float:
    """Return milliseconds since ``started`` (UTC-aware)."""
    return round((utc_now() - started).total_seconds() * 1000, 3)
