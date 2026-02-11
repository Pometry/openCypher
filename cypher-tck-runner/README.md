# openCypher TCK Runner

A modern Python test runner for openCypher Technology Compatibility Kit (TCK) using Behave.

## Features

- Modern Python 3.12+ project structure
- Behave (Gherkin) test runner for openCypher TCK features
- Polars-based result comparison framework
- Side effects tracking and validation
- Extensible graph database stub for custom implementations

## Setup

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install development dependencies
uv sync --group dev
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all features
uv run behave

# Run specific feature
uv run behave features/clauses/match/Match1.feature

# Run with tags
uv run behave --tags=@match

# Run with verbose output
uv run behave -v
```

## Project Structure

```
cypher-tck-runner/
├── features/              # Gherkin feature files
│   ├── steps/            # Step definitions
│   │   ├── given_steps.py
│   │   ├── when_steps.py
│   │   └── then_steps.py
│   └── environment.py    # Behave hooks and configuration
├── src/
│   └── cypher_tck/       # Core implementation
│       ├── graph_db.py   # Graph database stub
│       ├── result_matcher.py  # Result comparison with Polars
│       ├── side_effects.py    # Side effects tracking
│       └── query_executor.py  # Query execution stub
└── pyproject.toml
```

## Development

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/

# Run all checks
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
```

## Implementation Guide

The project provides a skeleton with TODO stubs. To implement your own Cypher execution:

1. **Graph Database**: Implement the `GraphDatabase` interface in `src/cypher_tck/graph_db.py`
2. **Query Executor**: Implement the `QueryExecutor` interface in `src/cypher_tck/query_executor.py`
3. **Result Handling**: The `ResultMatcher` in `src/cypher_tck/result_matcher.py` handles comparisons

See the docstrings in each module for implementation details.

## License

Apache License 2.0 (matching the openCypher TCK)
