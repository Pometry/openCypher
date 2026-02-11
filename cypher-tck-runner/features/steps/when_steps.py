"""When step definitions for executing queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import when

if TYPE_CHECKING:
    from behave.runner import Context


@when("executing query:")
def step_when_executing_query(context: Context) -> None:
    """Execute a Cypher query.

    The query is provided in the step's text block.
    Expected format:
        When executing query:
          '''
          MATCH (n) RETURN n
          '''
    """
    if not context.text:
        raise ValueError("Expected query text in 'executing query' step")

    query = context.text.strip()
    context.last_query = query

    try:
        # Execute the query and store the result
        context.query_result = context.graph_db.execute_query(query)
        context.actual_error = None
    except Exception as e:
        # Store the error for validation in Then steps
        context.actual_error = e
        context.query_result = None


@when("executing control query:")
def step_when_executing_control_query(context: Context) -> None:
    """Execute a control query (same as regular query execution).

    This is used in some TCK tests to distinguish between the test query
    and control queries.
    """
    step_when_executing_query(context)
