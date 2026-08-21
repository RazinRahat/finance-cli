from pathlib import Path

import pytest

from finance_cli.categorizer import categorize_description
from finance_cli.exceptions import InvalidRulesError
from finance_cli.rules import (
    load_category_rules,
    merge_category_rules,
)


def test_load_category_rules_returns_validated_rules(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "categories.json"
    rules_path.write_text(
        """
        {
          "Study": [
            "officeworks",
            "macquarie university"
          ],
          "Coffee": [
            "mecca coffee"
          ]
        }
        """,
        encoding="utf-8",
    )

    rules = load_category_rules(rules_path)

    assert rules == {
        "Study": (
            "officeworks",
            "macquarie university",
        ),
        "Coffee": ("mecca coffee",),
    }


@pytest.mark.parametrize(
    ("json_content", "expected_message"),
    [
        (
            '["woolworths", "coles"]',
            "must be a JSON object",
        ),
        (
            '{"Groceries": "woolworths"}',
            "must be a JSON array",
        ),
        (
            '{"Groceries": []}',
            "at least one keyword",
        ),
        (
            '{"": ["woolworths"]}',
            "Category names cannot be empty",
        ),
        (
            '{"Groceries": [""]}',
            "cannot be empty",
        ),
        (
            '{"Groceries": [42]}',
            "must be a string",
        ),
    ],
)
def test_load_category_rules_rejects_invalid_structure(
    tmp_path: Path,
    json_content: str,
    expected_message: str,
) -> None:
    rules_path = tmp_path / "invalid.json"
    rules_path.write_text(
        json_content,
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidRulesError,
        match=expected_message,
    ):
        load_category_rules(rules_path)


def test_load_category_rules_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    rules_path = tmp_path / "invalid.json"
    rules_path.write_text(
        '{"Groceries": ["woolworths",]}',
        encoding="utf-8",
    )

    with pytest.raises(
        InvalidRulesError,
        match="invalid JSON",
    ):
        load_category_rules(rules_path)


def test_custom_rules_take_priority_over_defaults() -> None:
    custom_rules = {"Household": ("woolworths",)}

    merged = merge_category_rules(custom_rules)

    category = categorize_description(
        "WOOLWORTHS EASTWOOD",
        rules=merged,
    )

    assert category == "Household"


def test_custom_rules_extend_existing_category() -> None:
    custom_rules = {"Groceries": ("panetta mercato",)}

    merged = merge_category_rules(custom_rules)

    assert merged["Groceries"] == (
        "panetta mercato",
        "woolworths",
        "coles",
        "aldi",
        "iga",
    )
