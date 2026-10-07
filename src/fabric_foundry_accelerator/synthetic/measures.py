"""Local evaluation of semantic-model measures with DuckDB.

Only measures declared in the repository's semantic model are executed (an allow-list);
callers can never submit free-form SQL.
"""

from collections.abc import Sequence
from decimal import Decimal

import duckdb

from fabric_foundry_accelerator.models.semantic import SemanticModel

MeasureScalar = int | float | None


def normalize_value(value: object) -> MeasureScalar:
    """Convert a DuckDB scalar into a JSON-friendly int, float or None."""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal | float):
        return round(float(value), 6)
    raise TypeError(f"unsupported measure value type: {type(value).__name__}")


def evaluate_measures(
    con: duckdb.DuckDBPyConnection, model: SemanticModel, names: Sequence[str] | None = None
) -> dict[str, MeasureScalar]:
    """Evaluate named measures (default: all) against the Gold tables visible to ``con``.

    Raises:
        KeyError: when a requested measure is not declared in the semantic model.
    """
    selected = [model.measure(n) for n in names] if names is not None else list(model.measures)
    results: dict[str, MeasureScalar] = {}
    for measure in selected:
        row = con.execute(measure.sql).fetchone()
        results[measure.name] = normalize_value(row[0] if row else None)
    return results
