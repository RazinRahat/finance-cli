import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from finance_cli.database import (
    cents_to_decimal,
    decimal_to_cents,
    initialize_database,
)
from finance_cli.exceptions import InvalidTransactionError


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


@pytest.mark.parametrize(
    ("amount", "expected_cents"),
    [
        (Decimal("0.00"), 0),
        (Decimal("0.01"), 1),
        (Decimal("-0.01"), -1),
        (Decimal("84.25"), 8425),
        (Decimal("-84.25"), -8425),
        (Decimal("1250.00"), 125000),
        (Decimal(10), 1000),
        (Decimal("10.5"), 1050),
    ],
)
def test_decimal_to_cents(
    amount: Decimal,
    expected_cents: int,
) -> None:
    assert decimal_to_cents(amount) == expected_cents


@pytest.mark.parametrize(
    ("cents", "expected_amount"),
    [
        (0, Decimal(0)),
        (1, Decimal("0.01")),
        (-1, Decimal("-0.01")),
        (8425, Decimal("84.25")),
        (-8425, Decimal("-84.25")),
        (125000, Decimal(1250)),
    ],
)
def test_cents_to_decimal(
    cents: int,
    expected_amount: Decimal,
) -> None:
    assert cents_to_decimal(cents) == expected_amount


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0.001"),
        Decimal("10.999"),
        Decimal("-84.251"),
    ],
)
def test_decimal_to_cents_rejects_fractional_cents(
    amount: Decimal,
) -> None:
    with pytest.raises(
        InvalidTransactionError,
        match="fractions of a cent",
    ):
        decimal_to_cents(amount)


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_decimal_to_cents_rejects_non_finite_amounts(
    amount: Decimal,
) -> None:
    with pytest.raises(
        InvalidTransactionError,
        match="must be finite",
    ):
        decimal_to_cents(amount)


@pytest.mark.parametrize(
    "original_amount",
    [
        Decimal("0.00"),
        Decimal("0.01"),
        Decimal("-0.01"),
        Decimal("84.25"),
        Decimal("-84.25"),
        Decimal("1250.00"),
    ],
)
def test_money_conversion_round_trip(
    original_amount: Decimal,
) -> None:
    cents = decimal_to_cents(original_amount)
    restored_amount = cents_to_decimal(cents)

    assert restored_amount == original_amount
