from pathlib import Path

import click

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
def import_statement_command(
    statement_path: Path,
) -> None:
    """Import and validate transactions from a CSV statement."""

    try:
        transactions = import_statement(statement_path)
    except FinanceCLIError as error:
        raise click.ClickException(str(error)) from error

    count = len(transactions)
    noun = "transaction" if count == 1 else "transactions"

    click.echo(f"Imported {count} {noun}.")


if __name__ == "__main__":
    cli()
