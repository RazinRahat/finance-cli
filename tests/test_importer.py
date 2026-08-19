from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from finance_cli.exceptions import InvalidTransactionError
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
    assert transactions[0].description == "Woolworths Eastwood"
    assert transactions[0].amount == Decimal("-84.25")

    assert transactions[1].description == "BP Salary"
    assert transactions[1].amount == Decimal("1250.00")

    assert transactions[2].description == "Opal Travel"
    assert transactions[2].amount == Decimal("-20.00")
