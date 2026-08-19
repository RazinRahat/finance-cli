import sqlite3
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_cli.exceptions import (
    DatabaseError,
    InvalidTransactionError,
)
from finance_cli.models import Transaction

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


def save_transaction(
    database_path: str | Path,
    transaction: Transaction,
) -> int:
    """Store one transaction and return its database ID."""

    path = Path(database_path)
    initialize_database(path)

    values = (
        transaction.transaction_date.isoformat(),
        transaction.description,
        decimal_to_cents(transaction.amount),
        transaction.category,
    )

    try:
        with closing(sqlite3.connect(path)) as connection, connection:
            cursor = connection.execute(
                """
                    INSERT INTO transactions (
                        transaction_date,
                        description,
                        amount_cents,
                        category
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                values,
            )

            transaction_id = cursor.lastrowid
    except sqlite3.Error as error:
        raise DatabaseError("Could not save transaction to the database.") from error

    if transaction_id is None:
        raise DatabaseError("The database did not return a transaction ID.")

    return transaction_id


def get_transactions(
    database_path: str | Path,
) -> list[Transaction]:
    """Return every stored transaction in chronological order."""

    path = Path(database_path)
    initialize_database(path)

    try:
        with closing(sqlite3.connect(path)) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute("""
                SELECT
                    id,
                    transaction_date,
                    description,
                    amount_cents,
                    category
                FROM transactions
                ORDER BY transaction_date, id
                """).fetchall()
    except sqlite3.Error as error:
        raise DatabaseError("Could not read transactions from the database.") from error

    return [
        Transaction(
            id=row["id"],
            transaction_date=date.fromisoformat(row["transaction_date"]),
            description=row["description"],
            amount=cents_to_decimal(row["amount_cents"]),
            category=row["category"],
        )
        for row in rows
    ]
