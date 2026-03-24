"""Tests for safe refactor apply mode with backup and rollback behaviour."""

from __future__ import annotations

import subprocess
from pathlib import Path

import duckdb
import pytest

from pytest_just.toolkit.refactoring import apply_refactor_plan


def _initialise_refactor_test_db(db_path: Path, justfile_path: Path, run_id: str = "run-1") -> None:
    """Create a minimal schema and seed data for refactor apply tests."""
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        CREATE TABLE ingest_runs (
            run_id VARCHAR,
            generated_utc VARCHAR,
            tool_version VARCHAR,
            source_root VARCHAR,
            exclude_repo VARCHAR,
            schema_version INTEGER
        )
        """
    )
    con.execute(
        """
        CREATE TABLE repo_sources (
            run_id VARCHAR,
            repo_name VARCHAR,
            repo_path VARCHAR,
            justfile_path VARCHAR,
            parsed_success BOOLEAN,
            parse_error VARCHAR
        )
        """
    )
    con.execute(
        """
        CREATE TABLE recipe_occurrences (
            run_id VARCHAR,
            repo_name VARCHAR,
            recipe_name VARCHAR,
            signature VARCHAR,
            is_private BOOLEAN,
            is_shebang BOOLEAN,
            doc VARCHAR,
            dependencies_json VARCHAR,
            parameters_json VARCHAR,
            body_text VARCHAR,
            body_normalised VARCHAR,
            justfile_path VARCHAR
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
    con.execute(
        """
        CREATE TABLE refactor_plans (
            run_id VARCHAR,
            suggestion_id VARCHAR,
            rule_id VARCHAR,
            repo_name VARCHAR,
            recipe_name VARCHAR,
            proposed_action VARCHAR,
            patch_preview VARCHAR,
            created_utc VARCHAR
        )
        """
    )
    con.execute(
        """
        CREATE TABLE refactor_edits (
            run_id VARCHAR,
            edit_id VARCHAR,
            suggestion_id VARCHAR,
            justfile_path VARCHAR,
            before_hash VARCHAR,
            after_hash VARCHAR,
            patch_text VARCHAR,
            applied_utc VARCHAR
        )
        """
    )

    con.execute(
        """
        INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?)
        """,
        [run_id, "2026-01-01T00:00:00+00:00", "0.1.2", "/tmp", "pytest-just", 4],
    )
    con.execute(
        """
        INSERT INTO repo_sources VALUES (?, ?, ?, ?, ?, ?)
        """,
        [run_id, "repo-a", str(justfile_path.parent), str(justfile_path), True, ""],
    )
    con.execute(
        """
        INSERT INTO recipe_occurrences VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            "repo-a",
            "deploy",
            "signature-1",
            False,
            False,
            "",
            "[]",
            "[]",
            "echo deploy",
            "echo deploy",
            str(justfile_path),
        ],
    )
    con.close()


def test_apply_refactor_plan_success_creates_backup_and_audit_rows(tmp_path: Path) -> None:
    """Ensure apply mode updates justfile content, creates backup, and persists edits."""
    justfile_path = tmp_path / "justfile"
    original = "deploy:\n    @echo deploy\n"
    justfile_path.write_text(original, encoding="utf-8")
    db_path = tmp_path / "recipes.duckdb"
    _initialise_refactor_test_db(db_path=db_path, justfile_path=justfile_path)

    run_id, edits = apply_refactor_plan(
        db_path=db_path,
        run_id="run-1",
        validate=False,
    )

    assert run_id == "run-1"
    assert len(edits) == 1
    updated = justfile_path.read_text(encoding="utf-8")
    assert updated.startswith("# deploy: document purpose and side effects\n")
    backup_path = justfile_path.with_name("justfile.bak")
    assert backup_path.exists()
    assert backup_path.read_text(encoding="utf-8") == original

    con = duckdb.connect(str(db_path))
    count_row = con.execute("SELECT COUNT(*) FROM refactor_edits WHERE run_id = ?", [run_id]).fetchone()
    assert count_row is not None
    assert count_row[0] == 1
    con.close()


def test_apply_refactor_plan_rolls_back_when_just_validation_fails(tmp_path: Path) -> None:
    """Ensure failed syntax validation restores original justfile content."""
    justfile_path = tmp_path / "justfile"
    original = "deploy:\n    @echo deploy\n"
    justfile_path.write_text(original, encoding="utf-8")
    db_path = tmp_path / "recipes.duckdb"
    _initialise_refactor_test_db(db_path=db_path, justfile_path=justfile_path)

    with pytest.raises(RuntimeError, match="just validation failed"):
        apply_refactor_plan(
            db_path=db_path,
            run_id="run-1",
            validate=True,
            just_bin="python",
        )

    assert justfile_path.read_text(encoding="utf-8") == original
    con = duckdb.connect(str(db_path))
    count_row = con.execute("SELECT COUNT(*) FROM refactor_edits WHERE run_id = ?", ["run-1"]).fetchone()
    assert count_row is not None
    assert count_row[0] == 0
    con.close()


def test_apply_refactor_plan_rolls_back_when_validation_command_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Ensure failed post-apply command validation restores original justfile content."""
    justfile_path = tmp_path / "justfile"
    original = "deploy:\n    @echo deploy\n"
    justfile_path.write_text(original, encoding="utf-8")
    db_path = tmp_path / "recipes.duckdb"
    _initialise_refactor_test_db(db_path=db_path, justfile_path=justfile_path)

    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        command = args[0]
        if isinstance(command, list):
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="{}", stderr="")
        return subprocess.CompletedProcess(args=command, returncode=1, stdout="", stderr="hook failed")

    monkeypatch.setattr("pytest_just.toolkit.refactoring.subprocess.run", fake_run)

    with pytest.raises(RuntimeError, match="validation command failed"):
        apply_refactor_plan(
            db_path=db_path,
            run_id="run-1",
            validate=True,
            validation_command="false",
        )

    assert justfile_path.read_text(encoding="utf-8") == original
    con = duckdb.connect(str(db_path))
    count_row = con.execute("SELECT COUNT(*) FROM refactor_edits WHERE run_id = ?", ["run-1"]).fetchone()
    assert count_row is not None
    assert count_row[0] == 0
    con.close()

