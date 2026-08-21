from decimal import Decimal


def format_currency(amount: Decimal) -> str:
    """Format a decimal amount as dollar currency."""

    sign = "-" if amount < 0 else ""
    absolute_amount = abs(amount)

    return f"{sign}${absolute_amount:,.2f}"
