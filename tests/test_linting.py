"""Unit tests for toolkit linting helpers."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from pytest_just.toolkit.linting import list_rules, run_lint


def test_list_rules_exposes_expected_rule_ids() -> None:
    """Ensure rule registry publishes stable rule IDs."""
    assert list_rules() == ["missing_public_doc", "recipe_name_style"]


def test_run_lint_requires_existing_ingest_run(tmp_path: Path) -> None:
    """Ensure lint execution fails clearly when no corpus run has been ingested."""
    db_path = tmp_path / "empty.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        CREATE TABLE ingest_runs (
            run_id VARCHAR,
            generated_utc VARCHAR
        )
        """
    )
    con.execute(
        """
        CREATE TABLE lint_findings (
            run_id VARCHAR,
            rule_id VARCHAR,
            severity VARCHAR,
            repo_name VARCHAR,
            recipe_name VARCHAR,
            message VARCHAR,
            fixable BOOLEAN
        )
        """
    )
    con.close()

    with pytest.raises(ValueError, match="No ingest runs found"):
        run_lint(db_path=db_path)

