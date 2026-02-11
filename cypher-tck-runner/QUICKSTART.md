# Quick Start Guide

Get up and running with the openCypher TCK runner in 5 minutes.

## Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

## Installation

### 1. Install uv (if you haven't already)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Set up the project

```bash
cd cypher-tck-runner

# Install dependencies
uv sync
uv sync --group dev
```

## Running Tests

### Test the example feature

```bash
# Run the example feature (will fail since stub implementation does nothing)
uv run behave features/example.feature
```

You should see output showing the scenarios running (they'll fail because the stub implementation doesn't execute queries yet).

### Run with verbose output

```bash
uv run behave features/example.feature -v
```

## Copying Real TCK Features

To test against the actual openCypher TCK features:

```bash
# From the cypher-tck-runner directory
python setup_features.py ../tck/features

# Now run the real features
uv run behave features/clauses/match/Match1.feature
```

## Project Structure

```
cypher-tck-runner/
├── features/                      # Gherkin feature files
│   ├── steps/                     # Step definitions (the glue code)
│   │   ├── given_steps.py        # "Given" steps for setup
│   │   ├── when_steps.py         # "When" steps for actions
│   │   └── then_steps.py         # "Then" steps for assertions
│   ├── environment.py            # Behave hooks and context setup
│   ├── behave.ini                # Behave configuration
│   └── example.feature           # Example feature for testing
│
├── src/cypher_tck/               # Core implementation
│   ├── graph_db.py               # Graph database interface (TODO: implement)
│   └── result_matcher.py         # Result comparison with Polars
│
├── tests/                         # Unit tests
│   ├── test_graph_db.py
│   └── test_result_matcher.py
│
├── pyproject.toml                # Project configuration
├── Makefile                      # Common commands
├── README.md                     # Project overview
├── IMPLEMENTATION.md             # Detailed implementation guide
└── setup_features.py             # Script to copy TCK features
```

## Development Workflow

### 1. Implement Your Graph Database

Edit `src/cypher_tck/graph_db.py` and implement the `GraphDatabase` interface:

```python
class MyGraphDatabase(GraphDatabase):
    def clear(self):
        # Clear your graph

    def execute_query(self, query, parameters=None):
        # Parse and execute Cypher query
        # Return QueryResult with columns, rows, and side_effects

    def is_empty(self):
        # Check if graph is empty
```

### 2. Update environment.py

Change `features/environment.py` to use your implementation:

```python
from cypher_tck.graph_db import MyGraphDatabase

def before_all(context):
    context.graph_db = MyGraphDatabase()  # Use your implementation
```

### 3. Run Tests

```bash
# Run behave tests
make run

# Run unit tests
make test

# Run all quality checks
make check
```

### 4. Iterate

Start with simple queries and gradually add more features:

1. `RETURN 1` (literals)
2. `CREATE ()` (node creation)
3. `MATCH (n) RETURN n` (basic matching)
4. And so on...

## Available Make Commands

```bash
make help            # Show all available commands
make install         # Install dependencies
make run             # Run all feature tests
make run-example     # Run only example.feature
make test            # Run unit tests
make lint            # Check code style
make format          # Format code
make type-check      # Run type checking
make check           # Run all checks
make clean           # Remove generated files
```

## Next Steps

1. Read [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed implementation guide
2. Look at the step definitions in `features/steps/` to understand how tests work
3. Explore `src/cypher_tck/result_matcher.py` to see how results are compared
4. Check out the [Behave documentation](https://behave.readthedocs.io/)
5. Review the [openCypher specification](https://opencypher.org/)

## Common Issues

### Tests are skipped

If you see "No steps defined", make sure:
- You're in the `cypher-tck-runner` directory
- The `features/steps/` directory exists with step definitions

### Import errors

Make sure dependencies are installed:
```bash
uv sync
uv sync --group dev
```

### Type checking fails

Run with less strict checking:
```bash
uv run mypy src/ --strict=false
```

## Example: Running Your First Query

Here's a minimal example to get started:

```python
# In src/cypher_tck/graph_db.py

class SimpleGraphDatabase(GraphDatabase):
    def __init__(self):
        self.nodes = []

    def clear(self):
        self.nodes.clear()

    def execute_query(self, query, parameters=None):
        # Handle RETURN 1
        if "RETURN 1" in query:
            return QueryResult(
                columns=["1"],
                rows=[{"1": 1}],
                side_effects=SideEffects()
            )

        # Handle CREATE ()
        if "CREATE ()" in query:
            self.nodes.append({})
            return QueryResult(
                columns=[],
                rows=[],
                side_effects=SideEffects(nodes_created=1)
            )

        return QueryResult(columns=[], rows=[], side_effects=SideEffects())

    def is_empty(self):
        return len(self.nodes) == 0
```

Update `features/environment.py`:

```python
from cypher_tck.graph_db import SimpleGraphDatabase

def before_all(context):
    context.graph_db = SimpleGraphDatabase()
```

Now run:

```bash
uv run behave features/example.feature
```

You should see some tests passing!

## Getting Help

- Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for detailed guidance
- Look at existing step definitions in `features/steps/`
- Review test failures with `uv run behave -v`
- Use Python debugger: add `import pdb; pdb.set_trace()` in your code

Happy testing! 🚀
