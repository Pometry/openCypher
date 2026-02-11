.PHONY: help install test lint format type-check check run clean setup-features

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies using uv
	uv sync
	uv sync --group dev

test:  ## Run unit tests with pytest
	uv run pytest tests/ -v

run:  ## Run all feature tests with behave
	uv run behave

run-example:  ## Run example feature only
	uv run behave features/example.feature

run-verbose:  ## Run feature tests with verbose output
	uv run behave -v

run-tag:  ## Run feature tests with specific tag (usage: make run-tag TAG=@match)
	uv run behave --tags=$(TAG)

lint:  ## Lint code with ruff
	uv run ruff check .

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without making changes
	uv run ruff format --check .

type-check:  ## Run type checking with mypy
	uv run mypy src/

check: lint format-check type-check  ## Run all code quality checks

fix:  ## Auto-fix linting issues
	uv run ruff check --fix .

setup-features:  ## Copy feature files from openCypher TCK (usage: make setup-features TCK=../tck/features)
	python setup_features.py $(TCK)

clean:  ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
