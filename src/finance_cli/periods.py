import re
from datetime import date

from finance_cli.exceptions import FinanceCLIError

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class InvalidMonthError(FinanceCLIError):
    """Raised when a month does not use YYYY-MM format."""


def month_date_range(
    month_value: str,
) -> tuple[date, date]:
    """Return the inclusive start and exclusive end of a month."""

    if not MONTH_PATTERN.fullmatch(month_value):
        raise InvalidMonthError(f"Invalid month: {month_value!r}. " "Expected YYYY-MM.")

    year_text, month_text = month_value.split("-")
    year = int(year_text)
    month = int(month_text)

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date
