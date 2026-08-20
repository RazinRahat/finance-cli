from pathlib import Path

from finance_cli.config import default_database_path


def test_default_database_path_is_a_database_file() -> None:
    database_path = default_database_path()

    assert isinstance(database_path, Path)
    assert database_path.name == "finance.db"
    assert database_path.parent.name == "finance-cli"
