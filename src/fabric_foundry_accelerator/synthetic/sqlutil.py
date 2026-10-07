"""Small SQL helpers for the local DuckDB engine.

Identifiers are validated against a strict pattern and quoted; literals are escaped. Only
repository-controlled names and paths reach these helpers, never free-form user SQL.
"""

import re
from pathlib import Path

_IDENTIFIER = re.compile(r"^_?[a-z][a-z0-9_]*$")


class UnsafeIdentifierError(ValueError):
    """Raised when a name is not a safe lowercase SQL identifier."""


def quote_ident(name: str) -> str:
    """Return a double-quoted identifier after validating it."""
    if not _IDENTIFIER.match(name):
        raise UnsafeIdentifierError(f"unsafe SQL identifier: {name!r}")
    return f'"{name}"'


def sql_literal(value: str | Path) -> str:
    """Return a single-quoted SQL string literal with embedded quotes escaped."""
    text = value.as_posix() if isinstance(value, Path) else value
    return "'" + text.replace("'", "''") + "'"
