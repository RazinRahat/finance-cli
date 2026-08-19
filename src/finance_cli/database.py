import sqlite3
from decimal import Decimal
from pathlib import Path

from finance_cli.exceptions import InvalidTransactionError

CENTS_PER_UNIT = Decimal(100)

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def initialize_database(
    database_path: str | Path,
) -> None:
    """Create the finance database and its required tables."""

    path = Path(database_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(path) as connection:
        connection.execute(CREATE_TRANSACTIONS_TABLE)


def decimal_to_cents(amount: Decimal) -> int:
    """Convert a finite monetary amount into integer cents."""

    if not amount.is_finite():
        raise InvalidTransactionError(f"Transaction amount must be finite: {amount!r}")

    cents = amount * CENTS_PER_UNIT

    if cents != cents.to_integral_value():
        raise InvalidTransactionError(
            "Transaction amount cannot contain " f"fractions of a cent: {amount!r}"
        )

    return int(cents)


def cents_to_decimal(cents: int) -> Decimal:
    """Convert integer cents into an exact decimal amount."""

    return Decimal(cents) / CENTS_PER_UNIT
