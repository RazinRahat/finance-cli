from decimal import Decimal

import pytest

from finance_cli.formatting import (
    format_currency,
    format_percentage,
)


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


@pytest.mark.parametrize(
    ("percentage", "expected"),
    [
        (None, "N/A"),
        (Decimal(0), "0.0%"),
        (Decimal("32.84"), "32.8%"),
        (Decimal("91.66"), "91.7%"),
        (Decimal("-10.25"), "-10.2%"),
    ],
)
def test_format_percentage(
    percentage: Decimal | None,
    expected: str,
) -> None:
    assert format_percentage(percentage) == expected
