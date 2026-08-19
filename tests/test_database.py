import sqlite3
from pathlib import Path

from finance_cli.database import initialize_database


def test_initialize_database_creates_transactions_table(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        table = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'transactions'
            """).fetchone()

    assert table is not None
    assert table[0] == "transactions"


def test_transactions_table_has_expected_columns(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(transactions)").fetchall()

    column_names = {column[1] for column in columns}

    assert column_names == {
        "id",
        "transaction_date",
        "description",
        "amount_cents",
        "category",
        "created_at",
    }


def test_initialize_database_can_run_multiple_times(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    initialize_database(database_path)
    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        table_count = connection.execute("""
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'transactions'
            """).fetchone()

    assert table_count is not None
    assert table_count[0] == 1


def test_initialize_database_creates_parent_directories(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "nested" / "data" / "finance.db"

    initialize_database(database_path)

    assert database_path.exists()
    assert database_path.is_file()
