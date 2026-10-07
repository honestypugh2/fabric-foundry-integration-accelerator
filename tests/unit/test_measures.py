from datetime import date
from decimal import Decimal

import pytest

from fabric_foundry_accelerator.synthetic.measures import normalize_value


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), (True, 1), (7, 7), (Decimal("1.2345678"), 1.234568), (0.5, 0.5)],
)
def test_normalize_value(value: object, expected: object) -> None:
    assert normalize_value(value) == expected


def test_normalize_value_rejects_unsupported_types() -> None:
    with pytest.raises(TypeError, match="date"):
        normalize_value(date(2025, 1, 1))
