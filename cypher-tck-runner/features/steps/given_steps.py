"""Given step definitions for setting up graph state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from behave import given
from cypher_tck.graph_db import SideEffects
from raphtory import Graph
from raphtory.gql import gql
import common

if TYPE_CHECKING:
    from behave.runner import Context


@given("an empty graph")
def step_given_empty_graph(context: Context) -> None:
    """Initialize an empty graph database.

    This step ensures the graph database is cleared of all nodes and relationships.
    """
    context.graph_db = Graph()


@given("any graph")
def step_given_any_graph(context: Context) -> None:
    """Use the graph in its current state.

    This step doesn't modify the graph - it can contain any data.
    """
    # Ensure graph_db is a Raphtory Graph (should already be set by before_scenario)
    if not hasattr(context, "graph_db") or not isinstance(context.graph_db, Graph):
        context.graph_db = Graph()


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
    graph = getattr(context, "graph_db", None)
    if graph is None:
        raise ValueError("Graph database not initialized. Ensure you have an 'an empty graph' or 'any graph' step before this one.")
    
    count_nodes_before = graph.count_nodes()
    count_relationships_before = graph.count_edges()

    results = gql(graph, query)
    context.query_result = common.ResultTable(columns=results.columns, rows=list(results))
    # Store the side effects from setup (in case they're needed)
    context.setup_side_effects = SideEffects( nodes_created=graph.count_nodes() - count_nodes_before, relationships_created=graph.count_edges() - count_relationships_before, )


@given("parameters are:")
def step_given_parameters(context: Context) -> None:
    """Set query parameters for parameterized queries.

    Example:
        Given parameters are:
          | expr | ['Apa'] |
          | idx  | 0       |
    """
    if not hasattr(context, "table") or not context.table:
        raise ValueError("Expected parameter table in 'parameters are' step")

    # Parse parameters from table
    # Table format: each row has parameter name in first column, value in second column.
    # In Gherkin, the first row is treated as headers by behave, so we need to
    # include the header row as data too (TCK uses 2-column tables where every
    # row, including the first, is a key-value parameter pair).
    params = {}
    all_rows = []
    # Include header row as data (behave treats it as column names)
    if context.table.headings and len(context.table.headings) == 2:
        all_rows.append(context.table.headings)
    for row in context.table:
        all_rows.append(list(row))

    for row_values in all_rows:
        if len(row_values) != 2:
            raise ValueError(f"Expected 2 columns in parameter table, got {len(row_values)}")

        param_name = row_values[0].strip()
        param_value_str = row_values[1].strip()

        # Parse the value (similar to procedure parsing)
        if param_value_str == 'null':
            params[param_name] = None
        elif param_value_str == 'true':
            params[param_name] = True
        elif param_value_str == 'false':
            params[param_name] = False
        elif (param_value_str.startswith("'") and param_value_str.endswith("'")) or \
             (param_value_str.startswith('"') and param_value_str.endswith('"')):
            params[param_name] = param_value_str[1:-1]
        elif param_value_str.startswith('[') and param_value_str.endswith(']'):
            # Simple list parsing - for now just store as string, would need full parser for complex cases
            params[param_name] = param_value_str
        elif param_value_str.startswith('{') and param_value_str.endswith('}'):
            # Simple map parsing - for now just store as string
            params[param_name] = param_value_str
        else:
            try:
                params[param_name] = int(param_value_str)
            except ValueError:
                try:
                    params[param_name] = float(param_value_str)
                except ValueError:
                    params[param_name] = param_value_str

    context.query_parameters = params


@given('there exists a procedure {procedure_signature}')
def step_given_procedure_exists(context: Context, procedure_signature: str) -> None:
    """Register a procedure with the Rust query coordinator for CALL testing.

    Example:
        Given there exists a procedure test.doNothing() :: ():
        Given there exists a procedure test.my.proc(name :: STRING?, id :: INTEGER?) :: (city :: STRING?, country_code :: INTEGER?):
    """
    import re
    from raphtory.gql import register_procedure

    # Parse signature: name(input_params) :: (output_params)
    m = re.match(r'([\w.]+)\((.*?)\)\s*::\s*\((.*?)\)', procedure_signature, re.DOTALL)
    if not m:
        proc_name = procedure_signature.split('(')[0].strip()
        input_params = []
        output_params = []
    else:
        proc_name = m.group(1).strip()
        input_part = m.group(2).strip()
        output_part = m.group(3).strip()

        def parse_params(part):
            if not part:
                return []
            return [p.split('::')[0].strip() for p in part.split(',') if p.strip()]

        input_params = parse_params(input_part)
        output_params = parse_params(output_part)

    # Parse data table rows, converting Cypher literals to Python values
    data_rows = []
    if hasattr(context, "table") and context.table:
        headings = list(context.table.headings)
        for row in context.table:
            row_dict = {}
            for h in headings:
                raw = row[h].strip()
                if raw == 'null':
                    row_dict[h] = None
                elif raw == 'true':
                    row_dict[h] = True
                elif raw == 'false':
                    row_dict[h] = False
                elif (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
                    row_dict[h] = raw[1:-1]
                else:
                    try:
                        row_dict[h] = int(raw)
                    except ValueError:
                        try:
                            row_dict[h] = float(raw)
                        except ValueError:
                            row_dict[h] = raw
            data_rows.append(row_dict)

    # Register with the Rust coordinator
    register_procedure(context.graph_db, proc_name, input_params, output_params, data_rows)
