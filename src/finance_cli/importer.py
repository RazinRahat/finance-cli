from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from finance_cli.models import Transaction


def parse_transaction_row(row: Mapping[str, str]) -> Transaction:
    """Convert a normalized CSV row into a Transaction."""

    transaction_date = date.fromisoformat(row["date"].strip())
    description = row["description"].strip()
    amount = Decimal(row["amount"].strip())

    return Transaction(
        transaction_date=transaction_date,
        description=description,
        amount=amount,
    )
