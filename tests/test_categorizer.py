from datetime import date
from decimal import Decimal

import pytest

from finance_cli.categorizer import (
    categorize_description,
    categorize_transaction,
)
from finance_cli.models import Transaction


@pytest.mark.parametrize(
    ("description", "expected_category"),
    [
        ("WOOLWORTHS CHATSWOOD", "Groceries"),
        ("Coles Macquarie", "Groceries"),
        ("ALDI NORTH SYDNEY", "Groceries"),
        ("OPAL TRAVEL", "Transport"),
        ("UBER TRIP SYDNEY CBD", "Transport"),
        ("NETFLIX.COM", "Subscriptions"),
        ("Spotify Premium", "Subscriptions"),
        ("SERVO SALARY", "Income"),
        ("PAYROLL DEPOSIT", "Income"),
    ],
)
def test_categorize_description_matches_known_merchants(
    description: str,
    expected_category: str,
) -> None:
    category = categorize_description(description)

    assert category == expected_category


def test_categorize_description_returns_uncategorized_for_unknown_merchant() -> None:
    category = categorize_description("Unknown Sydney Merchant")

    assert category == "Uncategorized"


@pytest.mark.parametrize(
    "description",
    [
        "WOOLWORTHS EASTWOOD",
        "woolworths eastwood",
        "Woolworths Eastwood",
        "  WOOLWORTHS EASTWOOD  ",
        "WOOLWORTHS    EASTWOOD",
    ],
)
def test_categorize_description_ignores_case_and_whitespace(
    description: str,
) -> None:
    category = categorize_description(description)

    assert category == "Groceries"


def test_categorize_description_accepts_custom_rules() -> None:
    custom_rules = {
        "Education": (
            "officeworks",
            "macquarie university",
        ),
        "Coffee": ("mecca coffee",),
    }

    category = categorize_description(
        "OFFICEWORKS NORTH RYDE",
        rules=custom_rules,
    )

    assert category == "Education"


def test_categorize_transaction_returns_categorized_copy() -> None:
    original = Transaction(
        transaction_date=date(2026, 7, 1),
        description="Woolworths Eastwood",
        amount=Decimal("-84.25"),
    )

    categorized = categorize_transaction(original)

    assert categorized.category == "Groceries"
    assert categorized.transaction_date == original.transaction_date
    assert categorized.description == original.description
    assert categorized.amount == original.amount

    assert original.category == "Uncategorized"
    assert categorized is not original
