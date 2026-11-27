"""When step definitions for executing queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from behave import when
from cypher_tck.graph_db import SideEffects
from raphtory import Graph
from raphtory.cypher import cypher
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
    """Count distinct label types in the graph.

    Multi-label nodes store labels as colon-separated strings (e.g., "Foo:Bar").
    Each individual label is counted separately.
    """
    labels = set()
    for node in graph.nodes:
        if node.node_type is not None and node.node_type != "":
            for label in node.node_type.split(":"):
                if label:
                    labels.add(label)
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
    table = None
    try:
        # Pass parameters if they were set by a "Given parameters are:" step
        params = getattr(context, 'query_parameters', None)
        table = cypher(context.graph_db, query, params=params)
        # Rows as plain dictionaries, nodes, edges and paths as Cypher text
        rows_as_dicts = []
        for row in table:
            row_dict = {col: row.text(col) for col in table.columns}
            rows_as_dicts.append(row_dict)
        context.query_result = common.ResultTable(columns=table.columns, rows=rows_as_dicts)
        context.actual_error = None
    except Exception as e:
        # Store the error for validation in Then steps
        context.actual_error = e
        context.query_result = None

    nodes_created = max(0, context.graph_db.count_nodes() - count_nodes_before)
    count_diff_properties = max(0, _count_properties(context.graph_db) - count_properties_before)

    # Deletion/mutation side effects reported by GQL engine (Raphtory is append-only for nodes).
    nodes_deleted = getattr(table, "nodes_deleted", 0)
    relationships_deleted = getattr(table, "relationships_deleted", 0)
    # properties_removed: from DELETE/REMOVE ops + overwrites from SET (old value removed)
    properties_removed = (getattr(table, "properties_removed", 0)) + \
                         (getattr(table, "properties_overwritten", 0))
    labels_removed = getattr(table, "labels_removed", 0)

    # labels_added: GQL reports labels added by MERGE/SET n:Label operations.
    # For CREATE operations, the graph-state diff is used instead.
    # Use GQL value when it's > 0 (MERGE/SET case), else graph-state diff (CREATE case).
    labels_added_gql = getattr(table, "labels_added", 0)
    labels_added_diff = max(0, _count_labels(context.graph_db) - count_labels_before)
    labels_added = labels_added_gql if labels_added_gql > 0 else labels_added_diff

    # relationships_created: take max of GQL-reported and graph-state diff.
    # GQL captures MERGE-created parallel edges invisible to graph-state diff (Raphtory deduplicates).
    # Graph-state diff captures CREATE relationships not reported in the arc (arc is last-write-wins).
    # When MERGE creates 1 + CREATE creates 1 more: GQL=1, diff=2 → max=2 (correct).
    # When MERGE creates a parallel edge (invisible to diff): GQL=1, diff=0 → max=1 (correct).
    relationships_created_gql = getattr(table, "relationships_created", 0)
    relationships_created_diff = max(0, context.graph_db.count_edges() - count_relationships_before)
    relationships_created = max(relationships_created_gql, relationships_created_diff)

    # properties_set: take max of (graph-state diff + overwrites) and GQL-reported.
    # GQL captures properties on MERGE-created parallel edges invisible to graph-state diff;
    # graph-state diff captures properties from CREATE that GQL doesn't report.
    properties_overwritten = getattr(table, "properties_overwritten", 0)
    properties_set_gql = getattr(table, "properties_set", 0)
    properties_set_diff = count_diff_properties + properties_overwritten
    properties_set = max(properties_set_diff, properties_set_gql)

    side_effects = SideEffects(
        nodes_created=nodes_created,
        nodes_deleted=nodes_deleted,
        relationships_created=relationships_created,
        relationships_deleted=relationships_deleted,
        properties_set=properties_set,
        properties_removed=properties_removed,
        labels_added=labels_added,
        labels_removed=labels_removed,
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
