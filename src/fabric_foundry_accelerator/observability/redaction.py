"""Redaction of sensitive values before anything is logged or audited.

Never log tokens, secrets, credentials, PHI or customer identifiers. Synthetic IDs (``SYN-…``)
and correlation IDs (32 hex characters, no dashes) are safe and are not redacted.
"""

import re
from collections.abc import Mapping

from fabric_foundry_accelerator.privacy.leak_scan import EMAIL_RE, GUID_RE, SECRET_PATTERNS

_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_SENSITIVE_KEYS = re.compile(
    r"(?i)(token|secret|password|passwd|api[_-]?key|authorization|credential)"
)
REDACTED = "[REDACTED]"


def redact_text(text: str) -> str:
    """Return ``text`` with secrets, bearer tokens, GUIDs and e-mail addresses masked."""
    result = _BEARER.sub("Bearer [REDACTED-TOKEN]", text)
    for _, pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED-SECRET]", result)
    result = GUID_RE.sub("[REDACTED-ID]", result)
    return EMAIL_RE.sub("[REDACTED-EMAIL]", result)


def redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    """Redact a flat mapping: sensitive keys are fully masked, strings are scrubbed."""
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if _SENSITIVE_KEYS.search(key):
            redacted[key] = REDACTED
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        else:
            redacted[key] = value
    return redacted
