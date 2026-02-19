"""Graph database stub interface for TCK testing.

This module provides a minimal interface for managing graph state during TCK tests.
Implementers should subclass GraphDatabase and provide concrete implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SideEffects:
    """Track side effects from graph operations."""

    nodes_created: int = 0
    nodes_deleted: int = 0
    relationships_created: int = 0
    relationships_deleted: int = 0
    properties_set: int = 0
    labels_added: int = 0
    labels_removed: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary format matching TCK expectations."""
        result = {}
        if self.nodes_created > 0:
            result["+nodes"] = self.nodes_created
        if self.nodes_deleted > 0:
            result["-nodes"] = self.nodes_deleted
        if self.relationships_created > 0:
            result["+relationships"] = self.relationships_created
        if self.relationships_deleted > 0:
            result["-relationships"] = self.relationships_deleted
        if self.properties_set > 0:
            result["+properties"] = self.properties_set
        if self.labels_added > 0:
            result["+labels"] = self.labels_added
        if self.labels_removed > 0:
            result["-labels"] = self.labels_removed
        return result

    def has_no_effects(self) -> bool:
        """Check if there are no side effects."""
        return all(
            value == 0
            for value in [
                self.nodes_created,
                self.nodes_deleted,
                self.relationships_created,
                self.relationships_deleted,
                self.properties_set,
                self.labels_added,
                self.labels_removed,
            ]
        )


@dataclass
class Node:
    """Represents a graph node."""

    id: int
    labels: set[str] = field(default_factory=set)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Represents a graph relationship."""

    id: int
    start_node_id: int
    end_node_id: int
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


class GraphDatabase(ABC):
    """Abstract base class for graph database implementations.

    Implementers should subclass this and provide concrete implementations
    for their specific graph database backend.
    """

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the graph database."""
        pass

    @abstractmethod
    def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> QueryResult:
        """Execute a Cypher query and return results.

        Args:
            query: The Cypher query string
            parameters: Optional query parameters

        Returns:
            QueryResult containing the result data and side effects
        """
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Check if the graph database is empty (no nodes or relationships)."""
        pass


@dataclass
class QueryResult:
    """Result of a Cypher query execution."""

    columns: list[str]
    rows: list[dict[str, Any]]
    side_effects: SideEffects = field(default_factory=SideEffects)

    def is_empty(self) -> bool:
        """Check if the result set is empty."""
        return len(self.rows) == 0


class StubGraphDatabase(GraphDatabase):
    """Stub implementation for testing the runner itself.

    This is a minimal implementation that does nothing. You should replace
    this with your actual graph database implementation.
    """

    def __init__(self) -> None:
        self._is_empty = True
        self._last_side_effects = SideEffects()

    def clear(self) -> None:
        """Clear the graph database."""
        self._is_empty = True
        self._last_side_effects = SideEffects()

    def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> QueryResult:
        """Execute a query (stub implementation).

        TODO: Implement actual Cypher query execution.
        """
        # TODO: Parse and execute the query
        # For now, return empty results
        return QueryResult(columns=[], rows=[], side_effects=SideEffects())

    def is_empty(self) -> bool:
        """Check if the graph is empty."""
        # TODO: Implement actual check
        return self._is_empty
