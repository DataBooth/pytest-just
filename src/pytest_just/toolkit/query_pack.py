"""Named query packs for justfile corpus analytics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

NAMED_QUERIES: dict[str, str] = {
    "top_recipe_names": """
        SELECT
            recipe_name,
            COUNT(DISTINCT repo_name) AS repo_count,
            COUNT(*) AS occurrence_count
        FROM recipe_occurrences
        WHERE (? IS NULL OR run_id = ?)
        GROUP BY recipe_name
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT ?
    """,
    "top_reused_signatures": """
        SELECT
            recipe_name,
            repo_count,
            occurrence_count,
            signature
        FROM unique_recipes
        WHERE (? IS NULL OR run_id = ?) AND repo_count > 1
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT ?
    """,
    "parse_failures": """
        SELECT
            repo_name,
            parse_error
        FROM repo_sources
        WHERE (? IS NULL OR run_id = ?) AND parsed_success = FALSE
        ORDER BY repo_name ASC
        LIMIT ?
    """,
    "dependency_hotspots": """
        SELECT
            dependency_name,
            COUNT(*) AS dependent_recipe_count,
            COUNT(DISTINCT repo_name) AS repo_count
        FROM recipe_dependencies
        WHERE (? IS NULL OR run_id = ?)
        GROUP BY dependency_name
        ORDER BY dependent_recipe_count DESC, repo_count DESC, dependency_name ASC
        LIMIT ?
    """,
}


def list_named_queries() -> list[str]:
    """Return available named query identifiers sorted by name."""
    return sorted(NAMED_QUERIES)


def run_named_query(
    db_path: Path,
    query_name: str,
    *,
    limit: int = 25,
    run_id: str | None = None,
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Execute a named query against a corpus database."""
    if query_name not in NAMED_QUERIES:
        known = ", ".join(list_named_queries())
        raise ValueError(f"Unknown query `{query_name}`. Known queries: {known}")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    con = duckdb.connect(str(db_path))
    try:
        relation = con.execute(NAMED_QUERIES[query_name], [run_id, run_id, limit])
        rows = relation.fetchall()
        columns = [item[0] for item in (relation.description or [])]
    finally:
        con.close()
    return columns, rows

