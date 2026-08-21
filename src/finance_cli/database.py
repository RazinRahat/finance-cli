import hashlib
import sqlite3
from collections.abc import Iterable
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path

from finance_cli.exceptions import (
    DatabaseError,
    DuplicateStatementError,
    InvalidTransactionError,
)
from finance_cli.models import Transaction

CENTS_PER_UNIT = Decimal(100)

HASH_CHUNK_SIZE = 64 * 1024

CREATE_STATEMENT_IMPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS statement_imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_hash TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_id INTEGER,
    source_row INTEGER,
    transaction_date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    category TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_id)
        REFERENCES statement_imports(id)
        ON DELETE CASCADE,
    UNIQUE (import_id, source_row)
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
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(CREATE_STATEMENT_IMPORTS_TABLE)
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

    transaction_ids = save_transactions(
        database_path,
        [transaction],
    )

    return transaction_ids[0]


def get_transactions(
    database_path: str | Path,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[Transaction]:
    """Return every stored transaction in chronological order."""

    path = Path(database_path)
    initialize_database(path)

    conditions: list[str] = []
    parameters: list[str] = []

    if start_date is not None:
        conditions.append("transaction_date >= ?")
        parameters.append(start_date.isoformat())

    if end_date is not None:
        conditions.append("transaction_date < ?")
        parameters.append(end_date.isoformat())

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            id,
            transaction_date,
            description,
            amount_cents,
            category
        FROM transactions
        {where_clause}
        ORDER BY transaction_date, id
    """

    try:
        with closing(sqlite3.connect(path)) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                query,
                parameters,
            ).fetchall()
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


def _transaction_values(
    transaction: Transaction,
) -> tuple[str, str, int, str]:
    """Convert a Transaction into SQLite-compatible values."""

    return (
        transaction.transaction_date.isoformat(),
        transaction.description,
        decimal_to_cents(transaction.amount),
        transaction.category,
    )


def save_transactions(
    database_path: str | Path,
    transactions: Iterable[Transaction],
) -> list[int]:
    """Store transactions atomically and return their IDs."""

    path = Path(database_path)
    initialize_database(path)

    transaction_ids: list[int] = []

    try:
        with closing(sqlite3.connect(path)) as connection, connection:
            for transaction in transactions:
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
                    _transaction_values(transaction),
                )

                transaction_id = cursor.lastrowid

                if transaction_id is None:
                    raise DatabaseError(
                        "The database did not return " "a transaction ID."
                    )

                transaction_ids.append(transaction_id)
    except sqlite3.Error as error:
        raise DatabaseError("Could not save transactions to the database.") from error

    return transaction_ids


def calculate_statement_hash(
    statement_path: str | Path,
) -> str:
    """Return a SHA-256 hash of a statement's contents."""

    path = Path(statement_path)
    digest = hashlib.sha256()

    with path.open("rb") as statement_file:
        while chunk := statement_file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def save_statement_import(
    database_path: str | Path,
    statement_path: str | Path,
    transactions: Iterable[Transaction],
) -> int:
    """Atomically save one statement and its transactions."""

    database = Path(database_path)
    statement = Path(statement_path)

    initialize_database(database)

    statement_hash = calculate_statement_hash(statement)
    source_name = statement.name

    try:
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                import_cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO statement_imports (
                        file_hash,
                        source_name
                    )
                    VALUES (?, ?)
                    """,
                    (
                        statement_hash,
                        source_name,
                    ),
                )

                if import_cursor.rowcount == 0:
                    raise DuplicateStatementError(
                        "This statement has already " "been imported."
                    )

                import_id = import_cursor.lastrowid

                if import_id is None:
                    raise DatabaseError(
                        "The database did not return " "a statement import ID."
                    )

                for source_row, transaction in enumerate(
                    transactions,
                    start=2,
                ):
                    connection.execute(
                        """
                        INSERT INTO transactions (
                            import_id,
                            source_row,
                            transaction_date,
                            description,
                            amount_cents,
                            category
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            import_id,
                            source_row,
                            *_transaction_values(transaction),
                        ),
                    )
    except sqlite3.Error as error:
        raise DatabaseError("Could not save the statement import.") from error

    return import_id
