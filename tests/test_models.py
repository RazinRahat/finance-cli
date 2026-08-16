from datetime import date
from decimal import Decimal

from finance_cli.models import Transaction


def test_transaction_uses_uncategorized_by_default() -> None:
    transaction = Transaction(
        transaction_date=date(2026, 7, 1),
        description="Woolworths Eastwood",
        amount=Decimal("-84.25"),
    )

    assert transaction.transaction_date == date(2026, 7, 1)
    assert transaction.description == "Woolworths Eastwood"
    assert transaction.amount == Decimal("-84.25")
    assert transaction.category == "Uncategorized"
