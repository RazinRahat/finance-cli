from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from click.testing import CliRunner

from finance_cli.cli import cli
from finance_cli.database import (
    get_transactions,
    save_transaction,
    save_transactions,
)
from finance_cli.models import Transaction


def test_cli_shows_help() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "Import, categorize, and analyze" in result.output


def test_hello_command() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["hello"])

    assert result.exit_code == 0
    assert "Personal Finance CLI is working!" in result.output


def test_import_statement_command_succeeds(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        ["import-statement", str(statement_path), "--database", str(database_path)],
    )

    assert result.exit_code == 0
    assert "Imported 3 transactions" in result.output
    assert database_path.exists()


def test_import_statement_command_reports_missing_file(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    missing_statement = tmp_path / "missing.csv"

    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        ["import-statement", str(missing_statement), "--database", str(database_path)],
    )

    assert result.exit_code != 0
    assert "Error:" in result.output
    assert "Statement file not found" in result.output
    assert "Traceback" not in result.output


def test_import_statement_command_reports_invalid_columns(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = tmp_path / "invalid.csv"

    database_path = tmp_path / "finance.db"

    statement_path.write_text(
        "date,description\n" "2026-07-01,Woolworths\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["import-statement", str(statement_path), "--database", str(database_path)],
    )

    assert result.exit_code != 0
    assert "missing required columns" in result.output
    assert "amount" in result.output
    assert "Traceback" not in result.output


def test_import_statement_command_reports_category_counts(tmp_path: Path) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        ["import-statement", str(statement_path), "--database", str(database_path)],
    )

    assert result.exit_code == 0
    assert "Categorized: 3" in result.output
    assert "Uncategorized: 0" in result.output


def test_import_statement_command_can_disable_categorization(tmp_path: Path) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        [
            "import-statement",
            str(statement_path),
            "--no-categorize",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "Categorized: 0" in result.output
    assert "Uncategorized: 3" in result.output


def test_import_statement_command_rejects_duplicate_import(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"
    database_path = tmp_path / "finance.db"

    arguments = [
        "import-statement",
        str(statement_path),
        "--database",
        str(database_path),
    ]

    first_result = runner.invoke(cli, arguments)
    second_result = runner.invoke(cli, arguments)

    assert first_result.exit_code == 0
    assert second_result.exit_code != 0
    assert "already been imported" in second_result.output
    assert "Traceback" not in second_result.output

    stored_transactions = get_transactions(database_path)

    assert len(stored_transactions) == 3


def test_import_statement_uses_database_environment_variable(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"
    database_path = tmp_path / "environment.db"

    result = runner.invoke(
        cli,
        [
            "import-statement",
            str(statement_path),
        ],
        env={
            "FINANCE_CLI_DATABASE": str(database_path),
        },
    )

    assert result.exit_code == 0
    assert database_path.exists()
    assert len(get_transactions(database_path)) == 3


def test_transactions_command_displays_selected_month(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    save_transactions(
        database_path,
        [
            Transaction(
                transaction_date=date(2026, 7, 1),
                description="Woolworths",
                amount=Decimal("-85.25"),
                category="Groceries",
            ),
            Transaction(
                transaction_date=date(2026, 8, 1),
                description="August Merchant",
                amount=Decimal("-20.00"),
                category="Other",
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "transactions",
            "--month",
            "2026-07",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "Transactions for 2026-07" in result.output
    assert "Woolworths" in result.output
    assert "-$85.25" in result.output
    assert "August Merchant" not in result.output


def test_transactions_command_rejects_invalid_month(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        [
            "transactions",
            "--month",
            "July",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code != 0
    assert "Expected YYYY-MM" in result.output
    assert "Traceback" not in result.output


def test_transactions_command_reports_empty_month(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    result = runner.invoke(
        cli,
        [
            "transactions",
            "--month",
            "2026-07",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "No transactions found for 2026-07" in result.output


def test_report_command_displays_monthly_totals(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    save_transactions(
        database_path,
        [
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
                description="Opal",
                amount=Decimal("-60.00"),
                category="Transport",
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "report",
            "--month",
            "2026-07",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "Monthly Report" in result.output
    assert "July 2026" in result.output
    assert "$1,275.00" in result.output
    assert "$145.25" in result.output
    assert "$1,129.75" in result.output
    assert "88.6%" in result.output
    assert "Groceries" in result.output
    assert "$85.25" in result.output
    assert "Transport" in result.output
    assert "$60.00" in result.output


def test_report_command_rejects_invalid_month(
    tmp_path: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "report",
            "--month",
            "2026-13",
            "--database",
            str(tmp_path / "finance.db"),
        ],
    )

    assert result.exit_code != 0
    assert "Expected YYYY-MM" in result.output
    assert "Traceback" not in result.output


def test_transactions_command_filters_by_category(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    save_transactions(
        database_path,
        [
            Transaction(
                transaction_date=date(2026, 7, 1),
                description="Woolworths TownHall",
                amount=Decimal("-85.25"),
                category="Groceries",
            ),
            Transaction(
                transaction_date=date(2026, 7, 2),
                description="Opal Travel",
                amount=Decimal("-20.00"),
                category="Transport",
            ),
            Transaction(
                transaction_date=date(2026, 7, 3),
                description="Aldi North Ryde",
                amount=Decimal("-30.00"),
                category="Groceries",
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "transactions",
            "--month",
            "2026-07",
            "--category",
            "groceries",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "Woolworths TownHall" in result.output
    assert "Aldi North Ryde" in result.output
    assert "Opal Travel" not in result.output


def test_transactions_command_reports_empty_category(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    save_transaction(
        database_path,
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Woolworths",
            amount=Decimal("-85.25"),
            category="Groceries",
        ),
    )

    result = runner.invoke(
        cli,
        [
            "transactions",
            "--month",
            "2026-07",
            "--category",
            "Dining",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "No transactions found" in result.output
    assert "Dining" in result.output


@pytest.mark.parametrize(
    "command_name",
    [
        "import-statement",
        "transactions",
        "report",
    ],
)
def test_database_commands_expose_database_option(
    command_name: str,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [command_name, "--help"],
    )

    assert result.exit_code == 0
    assert "--database" in result.output
    assert result.output.count("--database") == 1


def test_categories_command_displays_default_rules() -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["categories"],
    )

    assert result.exit_code == 0
    assert "Default categorization rules" in result.output
    assert "Groceries" in result.output
    assert "woolworths" in result.output
    assert "Transport" in result.output
    assert "opal" in result.output
    assert "Subscriptions" in result.output
    assert "netflix" in result.output


def test_categories_command_displays_stored_categories(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    save_transactions(
        database_path,
        [
            Transaction(
                transaction_date=date(2026, 7, 1),
                description="Woolworths",
                amount=Decimal("-84.25"),
                category="Groceries",
            ),
            Transaction(
                transaction_date=date(2026, 7, 2),
                description="Unknown Merchant",
                amount=Decimal("-10.00"),
                category="Uncategorized",
            ),
        ],
    )

    result = runner.invoke(
        cli,
        [
            "categories",
            "--stored",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "Stored categories" in result.output
    assert "- Groceries" in result.output
    assert "- Uncategorized" in result.output


def test_categories_command_handles_empty_database(
    tmp_path: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "categories",
            "--stored",
            "--database",
            str(tmp_path / "finance.db"),
        ],
    )

    assert result.exit_code == 0
    assert "No categories stored" in result.output


def test_import_statement_uses_custom_rules(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"
    rules_path = tmp_path / "rules.json"
    database_path = tmp_path / "finance.db"

    rules_path.write_text(
        """
        {
          "Household": [
            "woolworths"
          ]
        }
        """,
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "import-statement",
            str(statement_path),
            "--rules",
            str(rules_path),
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0

    transactions = get_transactions(database_path)

    assert transactions[0].category == "Household"
    assert transactions[1].category == "Income"
    assert transactions[2].category == "Transport"


def test_import_rejects_rules_when_categorization_disabled(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"
    rules_path = tmp_path / "rules.json"

    rules_path.write_text(
        '{"Groceries": ["woolworths"]}',
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        [
            "import-statement",
            str(statement_path),
            "--rules",
            str(rules_path),
            "--no-categorize",
            "--database",
            str(tmp_path / "finance.db"),
        ],
    )

    assert result.exit_code != 0
    assert "--rules cannot be combined" in result.output


def test_categorize_command_updates_transaction(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    database_path = tmp_path / "finance.db"

    transaction_id = save_transaction(
        database_path,
        Transaction(
            transaction_date=date(2026, 7, 1),
            description="Unknown Cafe",
            amount=Decimal("-12.50"),
        ),
    )

    result = runner.invoke(
        cli,
        [
            "categorize",
            str(transaction_id),
            "Dining",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0
    assert "categorized as Dining" in result.output

    transaction = get_transactions(database_path)[0]

    assert transaction.category == "Dining"
    assert transaction.category_source == "manual"


def test_categorize_command_reports_unknown_transaction(
    tmp_path: Path,
) -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "categorize",
            "999",
            "Dining",
            "--database",
            str(tmp_path / "finance.db"),
        ],
    )

    assert result.exit_code != 0
    assert "Transaction not found" in result.output
    assert "Traceback" not in result.output
