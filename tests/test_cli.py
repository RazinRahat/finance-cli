from pathlib import Path

from click.testing import CliRunner

from finance_cli.cli import cli
from finance_cli.database import get_transactions


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
