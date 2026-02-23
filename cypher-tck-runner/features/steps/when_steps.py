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


def _count_properties(graph):
    """Count total number of property values across all nodes and edges."""
    total = 0
    for node in graph.nodes:
        total += len(node.properties.as_dict())
    for edge in graph.edges:
        total += len(edge.properties.as_dict())
    return total


def _count_labels(graph):
    """Count distinct label types in the graph."""
    labels = set()
    for node in graph.nodes:
        if node.node_type is not None and node.node_type != "":
            labels.add(node.node_type)
    return len(labels)


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
    count_properties_before = _count_properties(context.graph_db)
    count_labels_before = _count_labels(context.graph_db)
    try:
        # Pass parameters if they were set by a "Given parameters are:" step
        params = getattr(context, 'query_parameters', None)
        table = gql(context.graph_db, query, params=params)
        # Convert GqlRow objects to plain dictionaries
        rows_as_dicts = []
        for row in table:
            # GqlRow objects can be converted to dict by accessing as dictionary
            row_dict = {col: row[col] for col in table.columns}
            rows_as_dicts.append(row_dict)
        context.query_result = common.ResultTable(columns=table.columns, rows=rows_as_dicts)
        context.actual_error = None
    except Exception as e:
        # Store the error for validation in Then steps
        context.actual_error = e
        context.query_result = None

    nodes_created = context.graph_db.count_nodes() - count_nodes_before
    relationships_created = context.graph_db.count_edges() - count_relationships_before
    properties_set = _count_properties(context.graph_db) - count_properties_before
    labels_added = _count_labels(context.graph_db) - count_labels_before

    side_effects = SideEffects(
        nodes_created=nodes_created,
        relationships_created=relationships_created,
        properties_set=max(0, properties_set),
        labels_added=max(0, labels_added),
    )
    print(f"Side Effects: {side_effects}")
    context.side_effects = side_effects


@when("executing control query:")
def step_when_executing_control_query(context: Context) -> None:
    """Execute a control query (same as regular query execution).

    This is used in some TCK tests to distinguish between the test query
    and control queries.
    """
    step_when_executing_query(context)
