"""Tests for the graph database stub."""

from __future__ import annotations

from cypher_tck.graph_db import SideEffects, StubGraphDatabase


def test_side_effects_to_dict() -> None:
    """Test SideEffects.to_dict() conversion."""
    effects = SideEffects(
        nodes_created=2, nodes_deleted=1, labels_added=3, properties_set=5
    )

    result = effects.to_dict()

    assert result == {
        "+nodes": 2,
        "-nodes": 1,
        "+labels": 3,
        "properties set": 5,
    }


def test_side_effects_has_no_effects() -> None:
    """Test SideEffects.has_no_effects()."""
    empty_effects = SideEffects()
    assert empty_effects.has_no_effects() is True

    non_empty_effects = SideEffects(nodes_created=1)
    assert non_empty_effects.has_no_effects() is False


def test_stub_graph_database_clear() -> None:
    """Test StubGraphDatabase.clear()."""
    db = StubGraphDatabase()

    assert db.is_empty() is True

    db.clear()

    assert db.is_empty() is True


def test_stub_graph_database_execute_query() -> None:
    """Test StubGraphDatabase.execute_query()."""
    db = StubGraphDatabase()

    result = db.execute_query("RETURN 1")

    assert result.columns == []
    assert result.rows == []
    assert result.is_empty() is True
