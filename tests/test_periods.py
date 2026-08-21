from datetime import date

import pytest

from finance_cli.periods import (
    InvalidMonthError,
    month_date_range,
)


@pytest.mark.parametrize(
    ("month_value", "expected_start", "expected_end"),
    [
        (
            "2026-01",
            date(2026, 1, 1),
            date(2026, 2, 1),
        ),
        (
            "2026-07",
            date(2026, 7, 1),
            date(2026, 8, 1),
        ),
        (
            "2026-12",
            date(2026, 12, 1),
            date(2027, 1, 1),
        ),
    ],
)
def test_month_date_range(
    month_value: str,
    expected_start: date,
    expected_end: date,
) -> None:
    start_date, end_date = month_date_range(month_value)

    assert start_date == expected_start
    assert end_date == expected_end


@pytest.mark.parametrize(
    "month_value",
    [
        "",
        "2026",
        "2026-7",
        "07-2026",
        "2026/07",
        "2026-00",
        "2026-13",
        "July",
    ],
)
def test_month_date_range_rejects_invalid_values(
    month_value: str,
) -> None:
    with pytest.raises(
        InvalidMonthError,
        match="Expected YYYY-MM",
    ):
        month_date_range(month_value)
