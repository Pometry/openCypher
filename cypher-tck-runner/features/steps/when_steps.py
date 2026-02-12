"""When step definitions for executing queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import when
from cypher_tck.graph_db import SideEffects
from raphtory import Graph
from raphtory.gql import gql
import common

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

    # Execute the query and store the result
    count_nodes_before = context.graph_db.count_nodes()
    count_relationships_before = context.graph_db.count_edges()
    try:
        table = gql(context.graph_db, query)
        context.query_result = common.ResultTable(columns=table.columns, rows=list(table))
        context.actual_error = None
    except Exception as e:
        # Store the error for validation in Then steps
        context.actual_error = e
        context.query_result = None
        
    side_effects = SideEffects( nodes_created=context.graph_db.count_nodes() - count_nodes_before, relationships_created=context.graph_db.count_edges() - count_relationships_before, )
    print(f"Side Effects: {side_effects}")
    context.side_effects = side_effects


@when("executing control query:")
def step_when_executing_control_query(context: Context) -> None:
    """Execute a control query (same as regular query execution).

    This is used in some TCK tests to distinguish between the test query
    and control queries.
    """
    step_when_executing_query(context)
