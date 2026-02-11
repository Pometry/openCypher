"""Given step definitions for setting up graph state."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import given

if TYPE_CHECKING:
    from behave.runner import Context


@given("an empty graph")
def step_given_empty_graph(context: Context) -> None:
    """Initialize an empty graph database.

    This step ensures the graph database is cleared of all nodes and relationships.
    """
    context.graph_db.clear()


@given("any graph")
def step_given_any_graph(context: Context) -> None:
    """Use the graph in its current state.

    This step doesn't modify the graph - it can contain any data.
    """
    # No action needed - just use the current graph state
    pass


@given("having executed:")
def step_given_having_executed(context: Context) -> None:
    """Execute a setup query to prepare the graph state.

    The query is provided in the step's text block.
    Expected format:
        Given having executed:
          '''
          CREATE (...)
          '''
    """
    if not context.text:
        raise ValueError("Expected query text in 'having executed' step")

    query = context.text.strip()

    # Execute the setup query
    result = context.graph_db.execute_query(query)

    # Store the side effects from setup (in case they're needed)
    context.setup_side_effects = result.side_effects


@given('there exists a procedure {procedure_signature}')
def step_given_procedure_exists(context: Context, procedure_signature: str) -> None:
    """Register that a procedure exists for CALL testing.

    Example:
        Given there exists a procedure test.doNothing() :: ():

    This is a stub implementation. In a real implementation, you would
    register the procedure with your graph database.
    """
    # TODO: Implement procedure registration
    # For now, just store that the procedure exists
    if not hasattr(context, "procedures"):
        context.procedures = {}

    context.procedures[procedure_signature] = {
        "signature": procedure_signature,
        "data": list(context.table) if hasattr(context, "table") and context.table else [],
    }
