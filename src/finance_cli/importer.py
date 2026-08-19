import csv
from collections.abc import Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from finance_cli.categorizer import categorize_transaction
from finance_cli.exceptions import (
    InvalidStatementError,
    InvalidTransactionError,
    StatementNotFoundError,
)
from finance_cli.models import Transaction

REQUIRED_COLUMNS = {
    "date",
    "description",
    "amount",
}


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
    *,
    auto_categorize: bool = True,
) -> list[Transaction]:
    """Import transactions from a normalized CSV statement."""

    path = Path(statement_path)

    try:
        statement_file = path.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        )
    except FileNotFoundError as error:
        raise StatementNotFoundError(f"Statement file not found: {path}") from error
    except (IsADirectoryError, PermissionError) as error:
        raise InvalidStatementError(
            f"Statement is not a readable file: {path}"
        ) from error

    with statement_file:
        reader = csv.DictReader(statement_file)

        if reader.fieldnames is None:
            raise InvalidStatementError(f"Statement is empty: {path}")

        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

        if missing_columns:
            formatted_columns = ", ".join(sorted(missing_columns))
            raise InvalidStatementError(
                f"Statement is missing required columns: " f"{formatted_columns}"
            )

        transactions: list[Transaction] = []

        for row in reader:
            try:
                transaction = parse_transaction_row(row)
            except InvalidTransactionError as error:
                raise InvalidTransactionError(
                    "Invalid transaction on CSV row " f"{reader.line_num}: {error}"
                ) from error

            if auto_categorize:
                transaction = categorize_transaction(transaction)

            transactions.append(transaction)

    return transactions
