import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_cli.database import (
    calculate_statement_hash,
    cents_to_decimal,
    decimal_to_cents,
    get_transactions,
    initialize_database,
    save_statement_import,
    save_transaction,
    save_transactions,
)
from finance_cli.exceptions import DuplicateStatementError, InvalidTransactionError
from finance_cli.models import Transaction


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
        "import_id",
        "source_row",
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


def test_save_and_retrieve_transaction(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"
    original = Transaction(
        transaction_date=date(2026, 7, 1),
        description="Woolworths",
        amount=Decimal("-84.25"),
        category="Groceries",
    )

    transaction_id = save_transaction(
        database_path,
        original,
    )
    transactions = get_transactions(database_path)

    assert transaction_id == 1
    assert len(transactions) == 1

    restored = transactions[0]

    assert restored.id == transaction_id
    assert restored.transaction_date == original.transaction_date
    assert restored.description == original.description
    assert restored.amount == original.amount
    assert restored.category == original.category


def test_get_transactions_returns_chronological_order(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    later_transaction = Transaction(
        transaction_date=date(2026, 7, 3),
        description="Opal Travel",
        amount=Decimal("-60.00"),
        category="Transport",
    )
    earlier_transaction = Transaction(
        transaction_date=date(2026, 7, 1),
        description="Woolworths",
        amount=Decimal("-85.25"),
        category="Groceries",
    )

    save_transaction(database_path, later_transaction)
    save_transaction(database_path, earlier_transaction)

    transactions = get_transactions(database_path)

    assert [transaction.transaction_date for transaction in transactions] == [
        date(2026, 7, 1),
        date(2026, 7, 3),
    ]


def test_get_transactions_returns_empty_list_for_empty_database(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    transactions = get_transactions(database_path)

    assert transactions == []


def test_save_transactions_stores_entire_batch(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        ),
        Transaction(
            transaction_date=date(2026, 7, 2),
            description="Servo Salary",
            amount=Decimal("1275.00"),
            category="Income",
        ),
        Transaction(
            transaction_date=date(2026, 7, 3),
            description="Opal Travel",
            amount=Decimal("-60.00"),
            category="Transport",
        ),
    ]

    transaction_ids = save_transactions(
        database_path,
        transactions,
    )
    restored = get_transactions(database_path)

    assert transaction_ids == [1, 2, 3]
    assert len(restored) == 3

    assert [transaction.description for transaction in restored] == [
        "Woolworths",
        "Servo Salary",
        "Opal Travel",
    ]


def test_save_transactions_rolls_back_entire_batch_on_error(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        ),
        Transaction(
            transaction_date=date(2026, 7, 2),
            description="Invalid Precision",
            amount=Decimal("-10.001"),
            category="Uncategorized",
        ),
        Transaction(
            transaction_date=date(2026, 7, 3),
            description="Opal Travel",
            amount=Decimal("-60.00"),
            category="Transport",
        ),
    ]

    with pytest.raises(
        InvalidTransactionError,
        match="fractions of a cent",
    ):
        save_transactions(database_path, transactions)

    restored = get_transactions(database_path)

    assert restored == []


def test_save_transactions_accepts_empty_batch(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    transaction_ids = save_transactions(
        database_path,
        [],
    )

    assert transaction_ids == []
    assert get_transactions(database_path) == []


def test_initialize_database_creates_statement_imports_table(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        table = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'statement_imports'
            """).fetchone()

    assert table is not None
    assert table[0] == "statement_imports"


def test_statement_hash_depends_on_file_contents(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.csv"
    renamed_path = tmp_path / "renamed.csv"
    different_path = tmp_path / "different.csv"

    shared_content = "date,description,amount\n" "2026-07-01,Woolworths,-85.25\n"

    first_path.write_text(
        shared_content,
        encoding="utf-8",
    )
    renamed_path.write_text(
        shared_content,
        encoding="utf-8",
    )
    different_path.write_text(
        shared_content.replace("-85.25", "-84.25"),
        encoding="utf-8",
    )

    first_hash = calculate_statement_hash(first_path)
    renamed_hash = calculate_statement_hash(renamed_path)
    different_hash = calculate_statement_hash(different_path)

    assert first_hash == renamed_hash
    assert first_hash != different_hash


def test_save_statement_import_stores_transactions(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        ),
        Transaction(
            transaction_date=date(2026, 7, 2),
            description="Servo Salary",
            amount=Decimal("1270.00"),
            category="Income",
        ),
        Transaction(
            transaction_date=date(2026, 7, 3),
            description="Opal Travel",
            amount=Decimal("-60.00"),
            category="Transport",
        ),
    ]

    import_id = save_statement_import(
        database_path,
        statement_path,
        transactions,
    )

    restored = get_transactions(database_path)

    assert import_id == 1
    assert len(restored) == 3


def test_save_statement_import_rejects_same_content_under_new_name(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"
    original_path = tmp_path / "july.csv"
    renamed_path = tmp_path / "july-copy.csv"

    content = "date,description,amount\n" "2026-07-01,Woolworths,-85.25\n"

    original_path.write_text(content, encoding="utf-8")
    renamed_path.write_text(content, encoding="utf-8")

    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        )
    ]

    save_statement_import(
        database_path,
        original_path,
        transactions,
    )

    with pytest.raises(
        DuplicateStatementError,
        match="already been imported",
    ):
        save_statement_import(
            database_path,
            renamed_path,
            transactions,
        )

    assert len(get_transactions(database_path)) == 1


def test_failed_statement_import_can_be_retried(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"
    statement_path = tmp_path / "statement.csv"

    statement_path.write_text(
        "date,description,amount\n" "2026-07-01,Woolworths,-85.25\n",
        encoding="utf-8",
    )

    invalid_transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Invalid Precision",
            amount=Decimal("-85.251"),
        )
    ]

    with pytest.raises(
        InvalidTransactionError,
        match="fractions of a cent",
    ):
        save_statement_import(
            database_path,
            statement_path,
            invalid_transactions,
        )

    valid_transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        )
    ]

    import_id = save_statement_import(
        database_path,
        statement_path,
        valid_transactions,
    )

    assert import_id == 1
    assert len(get_transactions(database_path)) == 1


def test_get_transactions_filters_by_date_range(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "finance.db"

    transactions = [
        Transaction(
            transaction_date=date(2026, 6, 30),
            description="June Transaction",
            amount=Decimal("-10.00"),
        ),
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="July Start",
            amount=Decimal("-20.00"),
        ),
        Transaction(
            transaction_date=date(2026, 7, 31),
            description="July End",
            amount=Decimal("-30.00"),
        ),
        Transaction(
            transaction_date=date(2026, 8, 1),
            description="August Transaction",
            amount=Decimal("-40.00"),
        ),
    ]

    save_transactions(database_path, transactions)

    results = get_transactions(
        database_path,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 8, 1),
    )

    assert [transaction.description for transaction in results] == [
        "July Start",
        "July End",
    ]
