from pathlib import Path

from click.testing import CliRunner

from finance_cli.cli import cli


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


def test_import_statement_command_succeeds() -> None:
    runner = CliRunner()
    statement_path = Path(__file__).parent / "fixtures" / "sample_statement.csv"

    result = runner.invoke(
        cli,
        ["import-statement", str(statement_path)],
    )

    assert result.exit_code == 0
    assert "Imported 3 transactions" in result.output


def test_import_statement_command_reports_missing_file(
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    missing_statement = tmp_path / "missing.csv"

    result = runner.invoke(
        cli,
        ["import-statement", str(missing_statement)],
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

    statement_path.write_text(
        "date,description\n" "2026-07-01,Woolworths\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        cli,
        ["import-statement", str(statement_path)],
    )

    assert result.exit_code != 0
    assert "missing required columns" in result.output
    assert "amount" in result.output
    assert "Traceback" not in result.output
