from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation

from finance_cli.exceptions import InvalidTransactionError
from finance_cli.models import Transaction


def parse_transaction_row(row: Mapping[str, str]) -> Transaction:
    """Convert a normalized CSV row into a Transaction."""

    transaction_date = date.fromisoformat(row["date"].strip())
    description = row["description"].strip()
    raw_amount = row["amount"].strip()

    try:
        amount = Decimal(raw_amount)
    except InvalidOperation as error:
        raise InvalidTransactionError(
            f"Invalid transaction amount: {raw_amount!r}"
        ) from error

    if not amount.is_finite():
        raise InvalidTransactionError(f"Invalid transaction amount: {raw_amount!r}")

    return Transaction(
        transaction_date=transaction_date,
        description=description,
        amount=amount,
    )
