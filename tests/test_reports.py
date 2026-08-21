from datetime import date
from decimal import Decimal

from finance_cli.models import Transaction
from finance_cli.reports import build_monthly_report


def test_build_monthly_report_calculates_totals() -> None:
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

    report = build_monthly_report(transactions)

    assert report.income == Decimal("1275.00")
    assert report.spending == Decimal("145.25")
    assert report.net_savings == Decimal("1129.75")
    assert report.savings_rate == Decimal("88.60784313725490196078431373")
    assert [(category.category, category.amount) for category in report.categories] == [
        ("Groceries", Decimal("85.25")),
        ("Transport", Decimal("60.00")),
    ]


def test_build_monthly_report_combines_same_category() -> None:
    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-40.00"),
            category="Groceries",
        ),
        Transaction(
            transaction_date=date(2026, 7, 2),
            description="Aldi",
            amount=Decimal("-30.00"),
            category="Groceries",
        ),
        Transaction(
            transaction_date=date(2026, 7, 3),
            description="Opal",
            amount=Decimal("-20.00"),
            category="Transport",
        ),
    ]

    report = build_monthly_report(transactions)

    assert report.categories[0].category == "Groceries"
    assert report.categories[0].amount == Decimal("70.00")
    assert report.categories[1].category == "Transport"


def test_build_monthly_report_has_no_rate_without_income() -> None:
    transactions = [
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        )
    ]

    report = build_monthly_report(transactions)

    assert report.income == Decimal(0)
    assert report.spending == Decimal("85.25")
    assert report.net_savings == Decimal("-85.25")
    assert report.savings_rate is None


def test_build_monthly_report_handles_no_transactions() -> None:
    report = build_monthly_report([])

    assert report.income == Decimal(0)
    assert report.spending == Decimal(0)
    assert report.net_savings == Decimal(0)
    assert report.savings_rate is None
    assert report.categories == ()
