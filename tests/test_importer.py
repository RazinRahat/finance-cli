from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_cli.exceptions import (
    InvalidStatementError,
    InvalidTransactionError,
    StatementNotFoundError,
)
from finance_cli.importer import (
    import_statement,
    parse_transaction_row,
)


def test_parse_valid_transaction_row() -> None:
    row = {
        "date": "2026-07-01",
        "description": "Woolworths Eastwood",
        "amount": "-84.25",
    }

    transaction = parse_transaction_row(row)

    assert transaction.transaction_date == date(2026, 7, 1)
    assert transaction.description == "Woolworths Eastwood"
    assert transaction.amount == Decimal("-84.25")
    assert transaction.category == "Uncategorized"


def test_parse_transaction_row_removes_surrounding_whitespace() -> None:
    row = {
        "date": " 2026-07-01 ",
        "description": "  Woolworths Eastwood  ",
        "amount": " -84.25 ",
    }

    transaction = parse_transaction_row(row)

    assert transaction.transaction_date == date(2026, 7, 1)
    assert transaction.description == "Woolworths Eastwood"
    assert transaction.amount == Decimal("-84.25")


@pytest.mark.parametrize(
    "invalid_amount",
    [
        "eighty dollars",
        "",
        "NaN",
        "Infinity",
        "-Infinity",
    ],
)
def test_parse_transaction_row_rejects_invalid_amount(
    invalid_amount: str,
) -> None:
    row = {
        "date": "2026-07-01",
        "description": "Woolworths Eastwood",
        "amount": invalid_amount,
    }

    with pytest.raises(
        InvalidTransactionError,
        match="Invalid transaction amount",
    ):
        parse_transaction_row(row)


@pytest.mark.parametrize(
    "invalid_date",
    [
        "",
        "31/07/2026",
        "2026/07/31",
        "31-07-2026",
        "2026-02-30",
        "not-a-date",
    ],
)
def test_parse_transaction_row_rejects_invalid_date(
    invalid_date: str,
) -> None:
    row = {
        "date": invalid_date,
        "description": "Woolworths Eastwood",
        "amount": "-84.25",
    }

    with pytest.raises(
        InvalidTransactionError,
        match="Invalid transaction date",
    ):
        parse_transaction_row(row)


def test_parse_transaction_row_rejects_empty_description() -> None:
    row = {
        "date": "2026-07-01",
        "description": "   ",
        "amount": "-84.25",
    }

    with pytest.raises(
        InvalidTransactionError,
        match="Transaction description cannot be empty",
    ):
        parse_transaction_row(row)


def test_import_statement_returns_transactions() -> None:
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    transactions = import_statement(statement_path)

    assert len(transactions) == 3

    assert transactions[0].transaction_date == date(2026, 7, 1)
    assert transactions[0].description == "Woolworths"
    assert transactions[0].amount == Decimal("-85.25")

    assert transactions[1].description == "Servo Salary"
    assert transactions[1].amount == Decimal("1275.00")

    assert transactions[2].description == "Opal Travel"
    assert transactions[2].amount == Decimal("-60.00")


def test_import_statement_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing_statement = tmp_path / "missing.csv"

    with pytest.raises(
        StatementNotFoundError,
        match="Statement file not found",
    ):
        import_statement(missing_statement)


def test_import_statement_rejects_empty_file(
    tmp_path: Path,
) -> None:
    statement_path = tmp_path / "empty.csv"
    statement_path.write_text("", encoding="utf-8")

    with pytest.raises(
        InvalidStatementError,
        match="Statement is empty",
    ):
        import_statement(statement_path)


@pytest.mark.parametrize(
    ("csv_content", "missing_column"),
    [
        (
            "description,amount\nWoolworths,-84.25\n",
            "date",
        ),
        (
            "date,amount\n2026-07-01,-84.25\n",
            "description",
        ),
        (
            "date,description\n2026-07-01,Woolworths\n",
            "amount",
        ),
    ],
)
def test_import_statement_rejects_missing_columns(
    tmp_path: Path,
    csv_content: str,
    missing_column: str,
) -> None:
    statement_path = tmp_path / "invalid.csv"
    statement_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(
        InvalidStatementError,
        match=missing_column,
    ):
        import_statement(statement_path)


def test_import_statement_reports_invalid_row_number(
    tmp_path: Path,
) -> None:
    statement_path = tmp_path / "invalid-row.csv"
    statement_path.write_text(
        "date,description,amount\n"
        "2026-07-01,Woolworths,-84.25\n"
        "2026-07-02,Opal,not-an-amount\n",
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidTransactionError,
        match="CSV row 3",
    ):
        import_statement(statement_path)


def test_import_statement_rejects_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        InvalidStatementError,
        match="not a readable file",
    ):
        import_statement(tmp_path)
