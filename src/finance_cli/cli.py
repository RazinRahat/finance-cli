from pathlib import Path

import click

from finance_cli.config import default_database_path
from finance_cli.database import save_statement_import
from finance_cli.exceptions import FinanceCLIError
from finance_cli.importer import import_statement


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
@click.option(
    "--database",
    "database_path",
    type=click.Path(
        path_type=Path,
        dir_okay=False,
    ),
    envvar="FINANCE_CLI_DATABASE",
    help=(
        "SQLite database path. Defaults to the "
        "platform-specific user data directory."
    ),
)
def import_statement_command(
    statement_path: Path,
    categorize: bool,
    database_path: Path | None,
) -> None:
    """Import and validate transactions from a CSV statement."""

    selected_database = (
        database_path if database_path is not None else default_database_path()
    )

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


if __name__ == "__main__":
    cli()
