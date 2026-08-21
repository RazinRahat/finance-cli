from dataclasses import dataclass
from decimal import Decimal

from finance_cli.models import Transaction

ZERO = Decimal(0)
ONE_HUNDRED = Decimal(100)


@dataclass(frozen=True)
class CategorySpending:
    """Total spending for one category."""

    category: str
    amount: Decimal


@dataclass(frozen=True)
class MonthlyReport:
    """Aggregated financial results for one month."""

    income: Decimal
    spending: Decimal
    net_savings: Decimal
    savings_rate: Decimal | None
    categories: tuple[CategorySpending, ...]


def build_monthly_report(
    transactions: list[Transaction],
) -> MonthlyReport:
    """Calculate financial totals from monthly transactions."""

    income = sum(
        (
            transaction.amount
            for transaction in transactions
            if transaction.amount > ZERO
        ),
        start=ZERO,
    )

    spending = sum(
        (
            -transaction.amount
            for transaction in transactions
            if transaction.amount < ZERO
        ),
        start=ZERO,
    )

    net_savings = income - spending

    savings_rate = net_savings / income * ONE_HUNDRED if income > ZERO else None

    category_totals: dict[str, Decimal] = {}

    for transaction in transactions:
        if transaction.amount >= ZERO:
            continue

        category_totals[transaction.category] = (
            category_totals.get(
                transaction.category,
                ZERO,
            )
            - transaction.amount
        )

    categories = tuple(
        CategorySpending(
            category=category,
            amount=amount,
        )
        for category, amount in sorted(
            category_totals.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )

    return MonthlyReport(
        income=income,
        spending=spending,
        net_savings=net_savings,
        savings_rate=savings_rate,
        categories=categories,
    )
