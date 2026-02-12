"""Then step definitions for asserting results and side effects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import then

from cypher_tck.result_matcher import ResultMatcher

if TYPE_CHECKING:
    from behave.runner import Context


@then("the result should be, in any order:")
def step_then_result_unordered(context: Context) -> None:
    """Assert that query results match expected results (order doesn't matter).

    Expected format:
        Then the result should be, in any order:
          | column1 | column2 |
          | value1  | value2  |
    """
    if context.actual_error:
        raise AssertionError(
            f"Query failed with error: {context.actual_error}\n"
            f"Query was: {context.last_query}"
        )

    if not context.query_result:
        raise AssertionError("No query result available")

    # Parse expected results from the table
    table_rows = [[cell for cell in row] for row in context.table]
    expected_columns, expected_rows = ResultMatcher.parse_table_rows(table_rows)

    # Compare results (unordered)
    match, error = ResultMatcher.compare_results(
        actual_columns=context.query_result.columns,
        actual_rows=context.query_result.rows,
        expected_columns=expected_columns,
        expected_rows=expected_rows,
        ordered=False,
    )

    if not match:
        raise AssertionError(
            f"Result mismatch:\n{error}\n" f"Query was: {context.last_query}"
        )


@then("the result should be, in order:")
def step_then_result_ordered(context: Context) -> None:
    """Assert that query results match expected results (order matters).

    Expected format:
        Then the result should be, in order:
          | column1 | column2 |
          | value1  | value2  |
    """
    if context.actual_error:
        raise AssertionError(
            f"Query failed with error: {context.actual_error}\n"
            f"Query was: {context.last_query}"
        )

    if not context.query_result:
        raise AssertionError("No query result available")

    # Parse expected results from the table
    table_rows = [[cell for cell in row] for row in context.table]
    expected_columns, expected_rows = ResultMatcher.parse_table_rows(table_rows)

    # Compare results (ordered)
    match, error = ResultMatcher.compare_results(
        actual_columns=context.query_result.columns,
        actual_rows=context.query_result.rows,
        expected_columns=expected_columns,
        expected_rows=expected_rows,
        ordered=True,
    )

    if not match:
        raise AssertionError(
            f"Result mismatch:\n{error}\n" f"Query was: {context.last_query}"
        )


@then("the result should be empty")
def step_then_result_empty(context: Context) -> None:
    """Assert that the query returned no rows.

    Expected format:
        Then the result should be empty
    """
    if context.actual_error:
        raise AssertionError(
            f"Query failed with error: {context.actual_error}\n"
            f"Query was: {context.last_query}"
        )

    if not context.query_result:
        raise AssertionError("No query result available")

    if not context.query_result.is_empty():
        raise AssertionError(
            f"Expected empty result, but got {len(context.query_result.rows)} rows:\n"
            f"{context.query_result.rows}\n"
            f"Query was: {context.last_query}"
        )


@then("no side effects")
def step_then_no_side_effects(context: Context) -> None:
    """Assert that the query produced no side effects.

    Expected format:
        And no side effects
    """
    if not context.query_result:
        raise AssertionError("No query result available")

    side_effects = context.side_effects

    if not side_effects.has_no_effects():
        raise AssertionError(
            f"Expected no side effects, but got: {side_effects.to_dict()}\n"
            f"Query was: {context.last_query}"
        )


@then("the side effects should be:")
def step_then_side_effects(context: Context) -> None:
    """Assert that the query produced specific side effects.

    Expected format:
        And the side effects should be:
          | +nodes | 1 |
          | +labels | 2 |
    """
    if not context.query_result:
        raise AssertionError("No query result available")

    # Parse expected side effects from the table
    expected_effects = {}
    
    # If table has no rows, it means the single row was treated as headers
    # In that case, use headings as key-value pairs
    if len(context.table.rows) == 0 and len(context.table.headings) >= 2:
        # Parse as key-value pairs from headings (e.g., | +nodes | 1 |)
        # Iterate in pairs: effect_name, effect_value
        for i in range(0, len(context.table.headings), 2):
            effect_name = context.table.headings[i]
            effect_value = int(context.table.headings[i + 1])
            expected_effects[effect_name] = effect_value
    else:
        # Parse as normal rows
        for row in context.table:
            effect_name = row[0]
            effect_value = int(row[1])
            expected_effects[effect_name] = effect_value

    # Get actual side effects
    actual_effects = context.side_effects.to_dict()

    # Compare side effects
    match, error = ResultMatcher.compare_side_effects(actual_effects, expected_effects)

    if not match:
        raise AssertionError(
            f"Side effects mismatch: {error}\n" f"Query was: {context.last_query}"
        )


@then("a {error_type} should be raised at compile time: {error_detail}")
def step_then_compile_error(context: Context, error_type: str, error_detail: str) -> None:
    """Assert that the query raised a specific compile-time error.

    Expected format:
        Then a SyntaxError should be raised at compile time: InvalidParameterUse

    Args:
        error_type: Type of error (e.g., 'SyntaxError', 'TypeError')
        error_detail: Specific error detail (e.g., 'InvalidParameterUse')
    """
    if not context.actual_error:
        raise AssertionError(
            f"Expected {error_type} ({error_detail}), but query succeeded\n"
            f"Query was: {context.last_query}"
        )

    # TODO: Implement more sophisticated error matching
    # For now, just check that an error was raised
    # In a real implementation, you would check:
    # 1. The error type matches
    # 2. The error detail/code matches
    # 3. It was raised at compile time (not runtime)

    error_message = str(context.actual_error)

    # Basic check: error occurred
    # You may want to add more specific checks based on your implementation
    if context.query_result is not None:
        raise AssertionError(
            f"Expected {error_type} ({error_detail}), "
            f"but query executed successfully\n"
            f"Query was: {context.last_query}"
        )


@then("a {error_type} should be raised at runtime: {error_detail}")
def step_then_runtime_error(context: Context, error_type: str, error_detail: str) -> None:
    """Assert that the query raised a specific runtime error.

    Expected format:
        Then a TypeError should be raised at runtime: PropertyAccessOnNonMap

    Args:
        error_type: Type of error (e.g., 'TypeError', 'ArithmeticError')
        error_detail: Specific error detail
    """
    if not context.actual_error:
        raise AssertionError(
            f"Expected {error_type} ({error_detail}), but query succeeded\n"
            f"Query was: {context.last_query}"
        )

    # TODO: Implement more sophisticated error matching
    # Similar to compile-time errors, but check that it was a runtime error
