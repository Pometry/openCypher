# Implementation Guide

This guide explains how to implement your own Cypher query executor to work with this TCK runner.

## Architecture Overview

The TCK runner is organized into several components:

```
┌─────────────────────────────────────────────────────────┐
│                   Behave Test Runner                    │
│                  (features/steps/*.py)                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Graph Database Interface               │
│                (src/cypher_tck/graph_db.py)             │
│                                                          │
│  • GraphDatabase (abstract base class)                  │
│  • QueryResult (result container)                       │
│  • SideEffects (side effects tracking)                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Your Implementation (TODO)                 │
│                                                          │
│  • Parse Cypher queries                                 │
│  • Execute against your graph representation            │
│  • Track side effects                                   │
│  • Return QueryResult with proper format                │
└─────────────────────────────────────────────────────────┘
```

## Step 1: Implement GraphDatabase Interface

Create your own subclass of `GraphDatabase` in `src/cypher_tck/graph_db.py`:

```python
from cypher_tck.graph_db import GraphDatabase, QueryResult, SideEffects

class MyGraphDatabase(GraphDatabase):
    def __init__(self):
        # Initialize your graph storage
        self.nodes = {}  # or use NetworkX, etc.
        self.relationships = {}

    def clear(self) -> None:
        """Clear all data from the graph."""
        self.nodes.clear()
        self.relationships.clear()

    def execute_query(self, query: str, parameters: dict | None = None) -> QueryResult:
        """Execute a Cypher query."""
        # 1. Parse the query (use a Cypher parser library)
        # 2. Execute it against your graph
        # 3. Track side effects
        # 4. Return results in QueryResult format

        side_effects = SideEffects()

        # Example for CREATE ():
        if "CREATE ()" in query:
            node_id = self._create_node()
            side_effects.nodes_created = 1
            return QueryResult(columns=[], rows=[], side_effects=side_effects)

        # Add more query handling...

    def is_empty(self) -> bool:
        """Check if graph has no nodes or relationships."""
        return len(self.nodes) == 0 and len(self.relationships) == 0
```

## Step 2: Update environment.py

Modify `features/environment.py` to use your implementation:

```python
from cypher_tck.graph_db import MyGraphDatabase  # Your implementation

def before_all(context):
    # Use your implementation instead of StubGraphDatabase
    context.graph_db = MyGraphDatabase()
```

## Step 3: Query Parsing Options

You have several options for parsing Cypher queries:

### Option A: Use an Existing Cypher Parser

```python
# Example using a hypothetical Cypher parser library
from cypher_parser import parse_cypher

def execute_query(self, query: str, parameters: dict | None = None) -> QueryResult:
    ast = parse_cypher(query)
    return self._execute_ast(ast)
```

### Option B: Pattern Matching for Common Patterns

```python
import re

def execute_query(self, query: str, parameters: dict | None = None) -> QueryResult:
    query = query.strip()

    # Handle CREATE
    if match := re.match(r'CREATE\s+\((.*?)\)', query):
        return self._handle_create(match)

    # Handle MATCH
    if match := re.match(r'MATCH\s+(.*?)\s+RETURN', query):
        return self._handle_match_return(match)

    # Add more patterns...
```

### Option C: Build a Simple Recursive Descent Parser

For educational purposes, you could implement your own parser.

## Step 4: Result Formatting

Results must be returned in the correct format:

```python
# For RETURN queries:
result = QueryResult(
    columns=["name", "age"],
    rows=[
        {"name": "Alice", "age": 30},
        {"name": "Bob", "age": 25}
    ],
    side_effects=SideEffects()
)

# For mutations (CREATE, DELETE, etc.):
result = QueryResult(
    columns=[],
    rows=[],
    side_effects=SideEffects(
        nodes_created=2,
        labels_added=1
    )
)
```

## Step 5: Side Effects Tracking

Track these side effects during query execution:

- `nodes_created`: Number of nodes created
- `nodes_deleted`: Number of nodes deleted
- `relationships_created`: Number of relationships created
- `relationships_deleted`: Number of relationships deleted
- `properties_set`: Number of properties set (including updates)
- `labels_added`: Number of labels added (count unique labels only once)
- `labels_removed`: Number of labels removed

Example:

```python
def _handle_create(self, pattern):
    side_effects = SideEffects()

    # Parse pattern like (:Label {prop: 'value'})
    node = self._create_node_from_pattern(pattern)
    side_effects.nodes_created = 1

    if node.labels:
        side_effects.labels_added = len(node.labels)

    if node.properties:
        side_effects.properties_set = len(node.properties)

    return QueryResult(columns=[], rows=[], side_effects=side_effects)
```

## Step 6: Value Parsing

The `ResultMatcher` handles parsing values from feature files. You need to ensure your query results return values in compatible Python types:

- Cypher `null` → Python `None`
- Cypher `true/false` → Python `bool`
- Cypher numbers → Python `int`/`float`
- Cypher strings → Python `str`
- Cypher lists → Python `list`
- Cypher maps → Python `dict`

## Step 7: Node and Relationship Representation

For RETURN queries that return nodes/relationships, format them as:

```python
# Nodes
{
    "_id": 123,
    "_labels": ["Person", "Employee"],
    "name": "Alice",
    "age": 30
}

# Relationships
{
    "_id": 456,
    "_type": "KNOWS",
    "_start": 123,
    "_end": 789,
    "since": 2020
}
```

Or use a simpler string representation:

```python
"(:Person {name: 'Alice'})"
"[:KNOWS {since: 2020}]"
```

## Testing Your Implementation

1. Start with simple queries:
   ```bash
   uv run behave features/example.feature
   ```

2. Test specific scenarios:
   ```bash
   uv run behave features/example.feature:7  # Line number of scenario
   ```

3. Run unit tests:
   ```bash
   uv run pytest tests/ -v
   ```

4. Once basics work, copy real TCK features:
   ```bash
   python setup_features.py ../tck/features
   uv run behave features/clauses/match/Match1.feature
   ```

## Debugging Tips

1. **Print query and results in steps:**
   ```python
   # In then_steps.py
   print(f"Query: {context.last_query}")
   print(f"Result: {context.query_result}")
   ```

2. **Use behave's verbose mode:**
   ```bash
   uv run behave -v --no-capture
   ```

3. **Run single scenarios:**
   ```bash
   uv run behave features/match.feature --name="Match non-existent"
   ```

4. **Use Python debugger:**
   ```python
   # In your implementation
   import pdb; pdb.set_trace()
   ```

## Common Patterns to Implement

Here's a suggested order for implementing Cypher features:

1. **Basic RETURN**: `RETURN 1`, `RETURN 'hello'`
2. **CREATE nodes**: `CREATE ()`, `CREATE (:Label)`
3. **CREATE with properties**: `CREATE ({name: 'Alice'})`
4. **MATCH simple**: `MATCH (n) RETURN n`
5. **MATCH with labels**: `MATCH (n:Person) RETURN n`
6. **MATCH with WHERE**: `MATCH (n) WHERE n.age > 18 RETURN n`
7. **CREATE relationships**: `CREATE (a)-[:KNOWS]->(b)`
8. **MATCH relationships**: `MATCH (a)-[r]->(b) RETURN a, r, b`
9. **DELETE**: `MATCH (n) DELETE n`
10. **SET**: `MATCH (n) SET n.prop = 'value'`
11. **MERGE**: `MERGE (n:Person {name: 'Alice'})`

## Resources

- [openCypher Specification](https://opencypher.org/)
- [Cypher Query Language Reference](https://neo4j.com/docs/cypher-manual/current/)
- [TCK Feature Files](../tck/features/) (original openCypher TCK)
- [Behave Documentation](https://behave.readthedocs.io/)
- [Polars Documentation](https://pola-rs.github.io/polars/) (for result comparison)

## Example Full Implementation Skeleton

See `examples/` directory (TODO) for a complete minimal implementation using:
- Regular expressions for simple query parsing
- Python dictionaries for graph storage
- Basic support for CREATE, MATCH, and RETURN
