from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import click

from finance_cli.categorizer import DEFAULT_CATEGORY_RULES
from finance_cli.config import default_database_path
from finance_cli.database import (
    get_stored_categories,
    get_transactions,
    save_statement_import,
)
from finance_cli.exceptions import FinanceCLIError
from finance_cli.formatting import (
    format_currency,
    format_percentage,
)
from finance_cli.importer import import_statement
from finance_cli.periods import month_date_range
from finance_cli.reports import build_monthly_report

CommandFunction = TypeVar(
    "CommandFunction",
    bound=Callable[..., Any],
)

DATABASE_OPTION_HELP = (
    "SQLite database path. Defaults to the " "platform-specific user data directory."
)


def database_option(
    function: CommandFunction,
) -> CommandFunction:
    """Add the shared database option to a Click command."""

    decorated = click.option(
        "--database",
        "database_path",
        type=click.Path(
            path_type=Path,
            dir_okay=False,
        ),
        envvar="FINANCE_CLI_DATABASE",
        help=DATABASE_OPTION_HELP,
    )(function)

    return cast(CommandFunction, decorated)


def _resolve_database_path(
    database_path: Path | None,
) -> Path:
    """Return an explicit or default database path."""

    if database_path is not None:
        return database_path

    return default_database_path()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Import, categorize, and analyze personal financial transactions."""


@cli.command()
def hello() -> None:
    """Confirm that the application is working."""
    click.echo("Personal Finance CLI is working!")


@cli.command("import-statement")
@click.argument(
    "statement_path",
    type=click.Path(path_type=Path),
)
@click.option(
    "--categorize/--no-categorize",
    default=True,
    help="Automatically categorize imported transactions.",
)
@database_option
def import_statement_command(
    statement_path: Path,
    categorize: bool,
    database_path: Path | None,
) -> None:
    """Import and validate transactions from a CSV statement."""

    selected_database = _resolve_database_path(database_path)

    try:
        transactions = import_statement(
            statement_path,
            auto_categorize=categorize,
        )
        save_statement_import(
            selected_database,
            statement_path,
            transactions,
        )
    except FinanceCLIError as error:
        raise click.ClickException(str(error)) from error

    transaction_count = len(transactions)
    categorized_count = sum(
        transaction.category != "Uncategorized" for transaction in transactions
    )
    uncategorized_count = transaction_count - categorized_count

    noun = "transaction" if transaction_count == 1 else "transactions"

    click.echo(
        f"Imported {transaction_count} {noun}. "
        f"Categorized: {categorized_count}. "
        f"Uncategorized: {uncategorized_count}."
    )


@cli.command("transactions")
@click.option(
    "--month",
    "month_value",
    required=True,
    help="Month to display in YYYY-MM format.",
)
@database_option
@click.option(
    "--category",
    help="Only display transactions in this category.",
)
def transactions_command(
    month_value: str,
    database_path: Path | None,
    category: str | None,
) -> None:
    """Display transactions for a month."""

    selected_database = _resolve_database_path(database_path)

    try:
        start_date, end_date = month_date_range(month_value)
        transactions = get_transactions(
            selected_database,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
    except FinanceCLIError as error:
        raise click.ClickException(str(error)) from error

    if not transactions:
        message = f"No transactions found for {month_value}"

        if category is not None:
            message += f" in category {category!r}"

        click.echo(f"{message}.")
        return

    heading = f"Transactions for {month_value}"

    if category is not None:
        heading += f" — {category}"

    click.echo(f"{heading}\n")
    click.echo(
        f"{'Date':<12}" f"{'Description':<32}" f"{'Category':<18}" f"{'Amount':>14}"
    )
    click.echo("-" * 76)

    for transaction in transactions:
        description = transaction.description[:30]
        category = transaction.category[:16]
        amount = format_currency(transaction.amount)

        click.echo(
            f"{transaction.transaction_date.isoformat():<12}"
            f"{description:<32}"
            f"{category:<18}"
            f"{amount:>14}"
        )


@cli.command("report")
@click.option(
    "--month",
    "month_value",
    required=True,
    help="Month to report in YYYY-MM format.",
)
@database_option
def report_command(
    month_value: str,
    database_path: Path | None,
) -> None:
    """Generate a financial report for one month."""

    selected_database = _resolve_database_path(database_path)

    try:
        start_date, end_date = month_date_range(month_value)
        transactions = get_transactions(
            selected_database,
            start_date=start_date,
            end_date=end_date,
        )
    except FinanceCLIError as error:
        raise click.ClickException(str(error)) from error

    report = build_monthly_report(transactions)
    month_label = start_date.strftime("%B %Y")

    click.echo(f"Monthly Report — {month_label}\n")
    click.echo(f"{'Income:':<20}" f"{format_currency(report.income):>14}")
    click.echo(f"{'Spending:':<20}" f"{format_currency(report.spending):>14}")
    click.echo(f"{'Net savings:':<20}" f"{format_currency(report.net_savings):>14}")
    click.echo(f"{'Savings rate:':<20}" f"{format_percentage(report.savings_rate):>14}")

    if not report.categories:
        click.echo("\nNo spending recorded.")
        return

    click.echo("\nSpending by category")
    click.echo("-" * 36)

    for category in report.categories:
        click.echo(
            f"{category.category[:20]:<22}" f"{format_currency(category.amount):>14}"
        )


@cli.command("categories")
@click.option(
    "--stored",
    is_flag=True,
    help="Show categories present in the database.",
)
@database_option
def categories_command(
    stored: bool,
    database_path: Path | None,
) -> None:
    """Display categorization rules and stored categories."""

    click.echo("Default categorization rules\n")

    for category, keywords in DEFAULT_CATEGORY_RULES.items():
        formatted_keywords = ", ".join(keywords)
        click.echo(f"{category:<16}{formatted_keywords}")

    if not stored:
        return

    selected_database = _resolve_database_path(database_path)

    try:
        stored_categories = get_stored_categories(selected_database)
    except FinanceCLIError as error:
        raise click.ClickException(str(error)) from error

    click.echo("\nStored categories\n")

    if not stored_categories:
        click.echo("No categories stored.")
        return

    for category in stored_categories:
        click.echo(f"- {category}")


if __name__ == "__main__":
    cli()
