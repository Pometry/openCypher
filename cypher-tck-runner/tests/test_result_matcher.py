"""Tests for the ResultMatcher class."""

from __future__ import annotations

import pytest

from cypher_tck.result_matcher import ResultMatcher


def test_parse_value_null() -> None:
    """Test parsing null values."""
    assert ResultMatcher._parse_value("null") is None
    assert ResultMatcher._parse_value("NULL") is None


def test_parse_value_boolean() -> None:
    """Test parsing boolean values."""
    assert ResultMatcher._parse_value("true") is True
    assert ResultMatcher._parse_value("false") is False
    assert ResultMatcher._parse_value("True") is True
    assert ResultMatcher._parse_value("False") is False


def test_parse_value_numbers() -> None:
    """Test parsing numeric values."""
    assert ResultMatcher._parse_value("42") == 42
    assert ResultMatcher._parse_value("-17") == -17
    assert ResultMatcher._parse_value("3.14") == 3.14
    assert ResultMatcher._parse_value("-2.5") == -2.5


def test_parse_value_strings() -> None:
    """Test parsing string values."""
    assert ResultMatcher._parse_value("'hello'") == "hello"
    assert ResultMatcher._parse_value('"world"') == "world"
    assert ResultMatcher._parse_value("'with spaces'") == "with spaces"


def test_parse_table_rows_empty() -> None:
    """Test parsing empty table."""
    columns, rows = ResultMatcher.parse_table_rows([])
    assert columns == []
    assert rows == []


def test_parse_table_rows_with_data() -> None:
    """Test parsing table with data."""
    table_rows = [
        ["name", "age", "active"],
        ["Alice", "30", "true"],
        ["Bob", "25", "false"],
    ]

    columns, rows = ResultMatcher.parse_table_rows(table_rows)

    assert columns == ["name", "age", "active"]
    assert rows == [
        {"name": "Alice", "age": 30, "active": True},
        {"name": "Bob", "age": 25, "active": False},
    ]


def test_compare_results_exact_match() -> None:
    """Test comparing results that match exactly."""
    actual_columns = ["name", "value"]
    actual_rows = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]

    expected_columns = ["name", "value"]
    expected_rows = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]

    match, error = ResultMatcher.compare_results(
        actual_columns, actual_rows, expected_columns, expected_rows, ordered=True
    )

    assert match is True
    assert error == ""


def test_compare_results_unordered_match() -> None:
    """Test comparing results with different order (unordered comparison)."""
    actual_columns = ["name", "value"]
    actual_rows = [{"name": "b", "value": 2}, {"name": "a", "value": 1}]

    expected_columns = ["name", "value"]
    expected_rows = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]

    match, error = ResultMatcher.compare_results(
        actual_columns, actual_rows, expected_columns, expected_rows, ordered=False
    )

    assert match is True
    assert error == ""


def test_compare_results_column_mismatch() -> None:
    """Test comparing results with different columns."""
    actual_columns = ["name", "value"]
    actual_rows = [{"name": "a", "value": 1}]

    expected_columns = ["name", "age"]
    expected_rows = [{"name": "a", "age": 1}]

    match, error = ResultMatcher.compare_results(
        actual_columns, actual_rows, expected_columns, expected_rows
    )

    assert match is False
    assert "Column mismatch" in error


def test_compare_side_effects_match() -> None:
    """Test comparing matching side effects."""
    actual = {"+nodes": 2, "+labels": 1}
    expected = {"+nodes": 2, "+labels": 1}

    match, error = ResultMatcher.compare_side_effects(actual, expected)

    assert match is True
    assert error == ""


def test_compare_side_effects_missing() -> None:
    """Test comparing side effects with missing effects."""
    actual = {"+nodes": 2}
    expected = {"+nodes": 2, "+labels": 1}

    match, error = ResultMatcher.compare_side_effects(actual, expected)

    assert match is False
    assert "Missing side effects" in error


def test_compare_side_effects_extra() -> None:
    """Test comparing side effects with extra effects."""
    actual = {"+nodes": 2, "+labels": 1, "properties set": 3}
    expected = {"+nodes": 2, "+labels": 1}

    match, error = ResultMatcher.compare_side_effects(actual, expected)

    assert match is False
    assert "Unexpected side effects" in error
