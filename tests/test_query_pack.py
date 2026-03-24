"""Unit tests for toolkit named query pack helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_just.toolkit.query_pack import list_named_queries, run_named_query


def test_list_named_queries_exposes_expected_queries() -> None:
    """Ensure named query registry includes core analytics queries."""
    names = list_named_queries()
    assert "top_recipe_names" in names
    assert "parse_failures" in names
    assert "dependency_hotspots" in names


def test_run_named_query_rejects_unknown_query_name(tmp_path: Path) -> None:
    """Ensure unknown query names fail with a clear error."""
    db_path = tmp_path / "empty.duckdb"
    with pytest.raises(ValueError, match="Unknown query"):
        run_named_query(db_path=db_path, query_name="not_a_real_query")


def test_run_named_query_rejects_non_positive_limit(tmp_path: Path) -> None:
    """Ensure invalid non-positive limits are rejected before query execution."""
    db_path = tmp_path / "empty.duckdb"
    with pytest.raises(ValueError, match="limit must be >= 1"):
        run_named_query(db_path=db_path, query_name="top_recipe_names", limit=0)

