"""Behave environment configuration and hooks.

This module sets up the test environment for each scenario, including
initializing the graph database and storing scenario context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cypher_tck.graph_db import StubGraphDatabase

if TYPE_CHECKING:
    from behave.model import Scenario
    from behave.runner import Context


def before_all(context: Context) -> None:
    """Initialize the test environment before any scenarios run."""
    # Initialize the graph database (replace with your implementation)
    context.graph_db = StubGraphDatabase()


def before_scenario(context: Context, scenario: Scenario) -> None:
    """Set up state before each scenario.

    Args:
        context: Behave context object
        scenario: The scenario about to be executed
    """
    # Clear the graph database before each scenario
    context.graph_db.clear()

    # Initialize scenario-specific state
    context.query_result = None
    context.last_query = None
    context.expected_error = None
    context.actual_error = None


def after_scenario(context: Context, scenario: Scenario) -> None:
    """Clean up after each scenario.

    Args:
        context: Behave context object
        scenario: The scenario that was just executed
    """
    # Clean up any resources if needed
    pass


def before_step(context: Context, step: Any) -> None:
    """Hook called before each step.

    Args:
        context: Behave context object
        step: The step about to be executed
    """
    pass


def after_step(context: Context, step: Any) -> None:
    """Hook called after each step.

    Args:
        context: Behave context object
        step: The step that was just executed
    """
    pass
