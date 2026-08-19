import csv
from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from finance_cli.exceptions import InvalidTransactionError
from finance_cli.models import Transaction


def _parse_date(raw_date: str) -> date:
    """Convert an ISO date string into a date object."""

    cleaned_date = raw_date.strip()

    try:
        return date.fromisoformat(cleaned_date)
    except ValueError as error:
        raise InvalidTransactionError(
            f"Invalid transaction date: {cleaned_date!r}. " "Expected YYYY-MM-DD"
        ) from error


def _parse_amount(raw_amount: str) -> Decimal:
    """Convert a monetary string into a finite Decimal."""

    cleaned_amount = raw_amount.strip()

    try:
        amount = Decimal(cleaned_amount)
    except InvalidOperation as error:
        raise InvalidTransactionError(
            f"Invalid transaction amount: {cleaned_amount!r}"
        ) from error

    if not amount.is_finite():
        raise InvalidTransactionError(f"Invalid transaction amount: {cleaned_amount!r}")

    return amount


def _parse_description(raw_description: str) -> str:
    """Clean and validate a transaction description."""

    description = raw_description.strip()

    if not description:
        raise InvalidTransactionError("Transaction description cannot be empty")

    return description


def _require_value(
    row: Mapping[str, str | None],
    field: str,
) -> str:
    """Return a CSV field value or raise a transaction error."""

    value = row.get(field)

    if value is None:
        raise InvalidTransactionError(f"Missing transaction field: {field!r}")

    return value


def parse_transaction_row(
    row: Mapping[str, str | None],
) -> Transaction:
    """Convert a normalized CSV row into a Transaction."""

    transaction_date = _parse_date(_require_value(row, "date"))
    description = _parse_description(_require_value(row, "description"))
    amount = _parse_amount(_require_value(row, "amount"))

    return Transaction(
        transaction_date=transaction_date,
        description=description,
        amount=amount,
    )


def import_statement(
    statement_path: str | Path,
) -> list[Transaction]:
    """Import transactions from a normalized CSV statement."""

    path = Path(statement_path)

    with path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as statement_file:
        reader = csv.DictReader(statement_file)

        transactions = [parse_transaction_row(row) for row in reader]

    return transactions
