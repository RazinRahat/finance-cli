from pathlib import Path

from platformdirs import user_data_path

APP_NAME = "finance-cli"
DATABASE_FILENAME = "finance.db"


def default_database_path() -> Path:
    """Return the platform-appropriate finance database path."""

    return (
        user_data_path(
            APP_NAME,
            appauthor=False,
        )
        / DATABASE_FILENAME
    )
