from datetime import date
from decimal import Decimal

from finance_cli.importer import parse_transaction_row


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
