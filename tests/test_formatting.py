from decimal import Decimal

import pytest

from finance_cli.formatting import format_currency


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal(0), "$0.00"),
        (Decimal("0.1"), "$0.10"),
        (Decimal("84.25"), "$84.25"),
        (Decimal("-84.25"), "-$84.25"),
        (Decimal(1250), "$1,250.00"),
        (Decimal("-1250.5"), "-$1,250.50"),
    ],
)
def test_format_currency(
    amount: Decimal,
    expected: str,
) -> None:
    assert format_currency(amount) == expected
