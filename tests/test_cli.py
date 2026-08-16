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
