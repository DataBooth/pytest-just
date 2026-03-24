"""Lint engine for justfile corpus analysis tables."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import duckdb


_RECIPE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


@dataclass(frozen=True)
class LintFinding:
    """Represents a single lint diagnostic."""

    run_id: str
    rule_id: str
    severity: str
    repo_name: str
    recipe_name: str
    message: str
    fixable: bool


def list_rules() -> list[str]:
    """List all lint rule IDs in stable order."""
    return [
        "missing_public_doc",
        "recipe_name_style",
    ]


def _resolve_run_id(con: duckdb.DuckDBPyConnection, run_id: str | None) -> str:
    """Resolve a requested run ID, defaulting to the most recent ingested run."""
    if run_id:
        return run_id
    row = con.execute(
        """
        SELECT run_id
        FROM ingest_runs
        ORDER BY generated_utc DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        raise ValueError("No ingest runs found. Run `build` first.")
    return str(row[0])


def _missing_public_doc_findings(con: duckdb.DuckDBPyConnection, run_id: str) -> list[LintFinding]:
    """Detect public recipes that are missing documentation."""
    rows = con.execute(
        """
        SELECT repo_name, recipe_name
        FROM recipe_occurrences
        WHERE run_id = ?
          AND is_private = FALSE
          AND TRIM(COALESCE(doc, '')) = ''
        ORDER BY repo_name ASC, recipe_name ASC
        """,
        [run_id],
    ).fetchall()
    return [
        LintFinding(
            run_id=run_id,
            rule_id="missing_public_doc",
            severity="warning",
            repo_name=str(repo_name),
            recipe_name=str(recipe_name),
            message="Public recipe is missing a doc string.",
            fixable=False,
        )
        for repo_name, recipe_name in rows
    ]


def _recipe_name_style_findings(con: duckdb.DuckDBPyConnection, run_id: str) -> list[LintFinding]:
    """Detect recipe names that do not match the configured style."""
    rows = con.execute(
        """
        SELECT DISTINCT repo_name, recipe_name
        FROM recipe_occurrences
        WHERE run_id = ?
        ORDER BY repo_name ASC, recipe_name ASC
        """,
        [run_id],
    ).fetchall()

    findings: list[LintFinding] = []
    for repo_name_raw, recipe_name_raw in rows:
        recipe_name = str(recipe_name_raw)
        if _RECIPE_NAME_PATTERN.match(recipe_name):
            continue
        findings.append(
            LintFinding(
                run_id=run_id,
                rule_id="recipe_name_style",
                severity="warning",
                repo_name=str(repo_name_raw),
                recipe_name=recipe_name,
                message="Recipe name should match ^[a-z][a-z0-9_-]*$.",
                fixable=False,
            )
        )
    return findings


def run_lint(db_path: Path, run_id: str | None = None) -> tuple[str, list[LintFinding]]:
    """Run all lint rules for a run and persist diagnostics."""
    con = duckdb.connect(str(db_path))
    try:
        resolved_run_id = _resolve_run_id(con, run_id)
        findings = []
        findings.extend(_missing_public_doc_findings(con, resolved_run_id))
        findings.extend(_recipe_name_style_findings(con, resolved_run_id))

        con.execute("DELETE FROM lint_findings WHERE run_id = ?", [resolved_run_id])
        if findings:
            con.executemany(
                """
                INSERT INTO lint_findings (
                    run_id,
                    rule_id,
                    severity,
                    repo_name,
                    recipe_name,
                    message,
                    fixable
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        finding.run_id,
                        finding.rule_id,
                        finding.severity,
                        finding.repo_name,
                        finding.recipe_name,
                        finding.message,
                        finding.fixable,
                    )
                    for finding in findings
                ],
            )
    finally:
        con.close()
    return resolved_run_id, findings

