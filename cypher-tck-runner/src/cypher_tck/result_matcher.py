"""Result matching utilities for comparing query results with expected values.

This module provides functionality to compare Cypher query results against
expected results from TCK feature files, including support for ordered and
unordered comparisons using Polars DataFrames.
"""

from __future__ import annotations

from typing import Any

import polars as pl


class ResultMatcher:
    """Matches query results against expected results."""

    @staticmethod
    def parse_table_rows(table_rows: list[list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
        """Parse table rows from Gherkin table format.

        Args:
            table_rows: List of rows from a Behave table, where first row is headers

        Returns:
            Tuple of (column_names, list of row dictionaries)
        """
        if not table_rows:
            return [], []

        headers = table_rows[0]
        rows = []

        for row in table_rows[1:]:
            row_dict = {}
            for header, value in zip(headers, row):
                row_dict[header] = ResultMatcher._parse_value(value)
            rows.append(row_dict)

        return headers, rows

    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse a string value from a Gherkin table into a Python value.

        Handles:
        - null/NULL -> None
        - true/false -> bool
        - Numbers -> int/float
        - Strings in quotes -> str
        - Lists [...]
        - Maps {...}
        - Node/relationship representations (:Label {prop: value})

        Args:
            value: String value from table cell

        Returns:
            Parsed Python value
        """
        value = value.strip()

        # Handle null
        if value.lower() == "null":
            return None

        # Handle booleans
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Handle strings (quoted)
        if (value.startswith("'") and value.endswith("'")) or (
            value.startswith('"') and value.endswith('"')
        ):
            return value[1:-1]

        # TODO: Handle more complex types:
        # - Lists: [1, 2, 3]
        # - Maps: {key: 'value'}
        # - Nodes: (:Label {prop: value})
        # - Relationships: [:TYPE {prop: value}]

        # Default: return as string
        return value

    @staticmethod
    def compare_results(
        actual_columns: list[str],
        actual_rows: list[dict[str, Any]],
        expected_columns: list[str],
        expected_rows: list[dict[str, Any]],
        ordered: bool = False,
    ) -> tuple[bool, str]:
        """Compare actual query results with expected results.

        Args:
            actual_columns: Column names from actual results
            actual_rows: Rows from actual results
            expected_columns: Expected column names
            expected_rows: Expected rows
            ordered: Whether to preserve row order in comparison

        Returns:
            Tuple of (match: bool, error_message: str)
        """
        # Check column names match
        if set(actual_columns) != set(expected_columns):
            return False, f"Column mismatch: expected {expected_columns}, got {actual_columns}"

        # Convert to Polars DataFrames for comparison
        try:
            if not actual_rows and not expected_rows:
                return True, ""

            if not actual_rows:
                return False, f"Expected {len(expected_rows)} rows, got 0"

            if not expected_rows:
                return False, f"Expected 0 rows, got {len(actual_rows)}"

            actual_df = pl.DataFrame(actual_rows)
            expected_df = pl.DataFrame(expected_rows)

            # Reorder columns to match expected order
            actual_df = actual_df.select(expected_columns)

            if not ordered:
                # For unordered comparison, sort both dataframes consistently
                # Sort by all columns to ensure deterministic comparison
                actual_df = actual_df.sort(expected_columns)
                expected_df = expected_df.sort(expected_columns)

            # Compare DataFrames
            if actual_df.equals(expected_df):
                return True, ""
            else:
                return False, (
                    f"Results don't match:\n"
                    f"Expected:\n{expected_df}\n"
                    f"Actual:\n{actual_df}"
                )

        except Exception as e:
            return False, f"Error comparing results: {e}"

    @staticmethod
    def compare_side_effects(
        actual: dict[str, int], expected: dict[str, int]
    ) -> tuple[bool, str]:
        """Compare actual side effects with expected side effects.

        Args:
            actual: Dictionary of actual side effects
            expected: Dictionary of expected side effects

        Returns:
            Tuple of (match: bool, error_message: str)
        """
        if actual == expected:
            return True, ""
        else:
            return False, f'Side effects mismatch: expected {expected}, got {actual}'

        missing = set(expected.keys()) - set(actual.keys())
        extra = set(actual.keys()) - set(expected.keys())
        different = {
            key
            for key in set(actual.keys()) & set(expected.keys())
            if actual[key] != expected[key]
        }

        errors = []
        if missing:
            errors.append(f"Missing side effects: {missing}")
        if extra:
            errors.append(f"Unexpected side effects: {extra}")
        if different:
            for key in different:
                errors.append(f"{key}: expected {expected[key]}, got {actual[key]}")

        return False, "; ".join(errors)
