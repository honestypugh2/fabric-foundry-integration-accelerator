import io
import json
import sys
from pathlib import Path

import pytest
import structlog

from fabric_foundry_accelerator.audit.store import (
    AuditRecord,
    InMemoryAuditStore,
    JsonlAuditStore,
    safe_details,
)
from fabric_foundry_accelerator.models.execution import ExecutionLabel, OperatingMode
from fabric_foundry_accelerator.observability.logging import (
    bind_correlation_id,
    clear_context,
    configure_logging,
    get_logger,
)
from fabric_foundry_accelerator.observability.redaction import redact_mapping, redact_text

GUID = "-".join(["1b4e28ba", "2fa1", "11d2", "883f", "0016d3cca427"])
EMAIL = "person@" + "corp.test"
TOKEN = "Bearer " + "abc" * 10


def test_redact_text_masks_tokens_ids_emails_and_secrets() -> None:
    secret = "gh" + "p_" + "a" * 36
    text = redact_text(f"{TOKEN} {GUID} {EMAIL} {secret} SYN-P-00001 {'a' * 32}")
    assert "abcabc" not in text and GUID not in text and EMAIL not in text and secret not in text
    assert "SYN-P-00001" in text and "a" * 32 in text  # synthetic IDs and correlation IDs are safe


def test_redact_mapping_masks_sensitive_keys() -> None:
    redacted = redact_mapping(
        {"access_token": "x", "Authorization": "y", "note": EMAIL, "count": 3}
    )
    assert redacted == {
        "access_token": "[REDACTED]",
        "Authorization": "[REDACTED]",
        "note": "[REDACTED-EMAIL]",
        "count": 3,
    }


def test_safe_details_coerces_values() -> None:
    assert safe_details({"a": [1], "b": None, "password": "x"}) == {
        "a": "[1]",
        "b": None,
        "password": "[REDACTED]",
    }


def _record(correlation_id: str) -> AuditRecord:
    return AuditRecord(
        correlation_id=correlation_id,
        actor="t",
        action="read:x",
        capability="fabric_data",
        requested_provider="p",
        selected_provider="p",
        operating_mode=OperatingMode.OFFLINE,
        execution_label=ExecutionLabel.LOCAL,
        cloud_operation_performed=False,
        success=True,
    )


@pytest.mark.parametrize("kind", ["memory", "jsonl"])
def test_audit_stores(kind: str, tmp_path: Path) -> None:
    store = (
        InMemoryAuditStore()
        if kind == "memory"
        else JsonlAuditStore(tmp_path / "nested" / "audit.jsonl")
    )
    assert store.recent() == [] and store.for_correlation("a" * 32) == []
    for cid in ("a" * 32, "b" * 32, "a" * 32):
        store.record(_record(cid))
    assert len(store.for_correlation("a" * 32)) == 2
    assert len(store.recent(2)) == 2
    if kind == "jsonl":
        lines = (tmp_path / "nested" / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 3 and json.loads(lines[0])["correlation_id"] == "a" * 32


def test_logging_redacts_and_binds_correlation(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stderr", buffer)
    configure_logging(level="INFO", json=True)
    bind_correlation_id("c" * 32)
    get_logger("t").info("event", note=f"{TOKEN} {EMAIL}", api_key="value")
    clear_context()
    line = json.loads(buffer.getvalue().strip().splitlines()[-1])
    assert line["correlation_id"] == "c" * 32
    assert (
        line["api_key"] == "[REDACTED]"
        and EMAIL not in line["note"]
        and "abcabc" not in line["note"]
    )
    configure_logging()
    structlog.reset_defaults()


def test_logging_follows_replaced_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    first = io.StringIO()
    monkeypatch.setattr(sys, "stderr", first)
    configure_logging()
    first.close()
    second = io.StringIO()
    monkeypatch.setattr(sys, "stderr", second)
    get_logger("t").warning("after swap")
    assert "after swap" in second.getvalue()
    structlog.reset_defaults()
