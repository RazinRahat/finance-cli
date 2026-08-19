from collections.abc import Mapping, Sequence
from dataclasses import replace

from finance_cli.models import Transaction

DEFAULT_CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "Income": (
        "salary",
        "payroll",
        "wages",
    ),
    "Groceries": (
        "woolworths",
        "coles",
        "aldi",
        "iga",
    ),
    "Dining": (
        "uber eats",
        "restaurant",
        "cafe",
        "mcdonald",
    ),
    "Transport": (
        "opal",
        "uber trip",
        "transport",
    ),
    "Subscriptions": (
        "netflix",
        "spotify",
        "amazon prime",
    ),
}


def _normalize_text(text: str) -> str:
    """Normalize text for case-insensitive matching."""

    return " ".join(text.casefold().split())


def categorize_description(
    description: str,
    rules: Mapping[str, Sequence[str]] = DEFAULT_CATEGORY_RULES,
) -> str:
    """Return the first category whose keyword matches a description."""

    normalized_description = _normalize_text(description)

    for category, keywords in rules.items():
        for keyword in keywords:
            normalized_keyword = _normalize_text(keyword)

            if normalized_keyword in normalized_description:
                return category

    return "Uncategorized"


def categorize_transaction(
    transaction: Transaction,
    rules: Mapping[str, Sequence[str]] = DEFAULT_CATEGORY_RULES,
) -> Transaction:
    """Return a copy of a transaction with an assigned category."""

    category = categorize_description(
        transaction.description,
        rules=rules,
    )

    return replace(
        transaction,
        category=category,
    )
