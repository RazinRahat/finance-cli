import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from finance_cli.categorizer import DEFAULT_CATEGORY_RULES
from finance_cli.exceptions import InvalidRulesError

CategoryRules = dict[str, tuple[str, ...]]


def load_category_rules(
    rules_path: str | Path,
) -> CategoryRules:
    """Load and validate category rules from JSON."""

    path = Path(rules_path)

    try:
        with path.open(
            mode="r",
            encoding="utf-8",
        ) as rules_file:
            raw_rules: Any = json.load(rules_file)
    except FileNotFoundError as error:
        raise InvalidRulesError(f"Rules file not found: {path}") from error
    except PermissionError as error:
        raise InvalidRulesError(f"Rules file is not readable: {path}") from error
    except json.JSONDecodeError as error:
        raise InvalidRulesError(
            f"Rules file contains invalid JSON: "
            f"{path}. Line {error.lineno}, "
            f"column {error.colno}."
        ) from error

    return _validate_rules(raw_rules)


def _validate_rules(
    raw_rules: Any,
) -> CategoryRules:
    """Validate decoded JSON category rules."""

    if not isinstance(raw_rules, dict):
        raise InvalidRulesError("Category rules must be a JSON object.")

    validated: CategoryRules = {}

    for category, keywords in raw_rules.items():
        if not isinstance(category, str):
            raise InvalidRulesError("Every category name must be a string.")

        cleaned_category = category.strip()

        if not cleaned_category:
            raise InvalidRulesError("Category names cannot be empty.")

        if not isinstance(keywords, list):
            raise InvalidRulesError(
                f"Keywords for {cleaned_category!r} " "must be a JSON array."
            )

        cleaned_keywords: list[str] = []

        for keyword in keywords:
            if not isinstance(keyword, str):
                raise InvalidRulesError(
                    f"Every keyword for " f"{cleaned_category!r} " "must be a string."
                )

            cleaned_keyword = keyword.strip()

            if not cleaned_keyword:
                raise InvalidRulesError(
                    f"Keywords for " f"{cleaned_category!r} " "cannot be empty."
                )

            cleaned_keywords.append(cleaned_keyword)

        if not cleaned_keywords:
            raise InvalidRulesError(
                f"Category {cleaned_category!r} " "must contain at least one keyword."
            )

        validated[cleaned_category] = tuple(cleaned_keywords)

    return validated


def merge_category_rules(
    custom_rules: Mapping[str, Sequence[str]],
    default_rules: Mapping[
        str,
        Sequence[str],
    ] = DEFAULT_CATEGORY_RULES,
) -> CategoryRules:
    """Merge rules with custom categories taking priority."""

    merged: CategoryRules = {
        category: tuple(keywords) for category, keywords in custom_rules.items()
    }

    for category, keywords in default_rules.items():
        if category in merged:
            existing = merged[category]

            merged[category] = (
                *existing,
                *(keyword for keyword in keywords if keyword not in existing),
            )
        else:
            merged[category] = tuple(keywords)

    return merged
