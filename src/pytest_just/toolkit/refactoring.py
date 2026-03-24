"""Suggestion-first refactor planner for justfile corpus data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import duckdb

from pytest_just.toolkit.linting import _resolve_run_id, run_lint


@dataclass(frozen=True)
class RefactorSuggestion:
    """Represents a non-applied refactor suggestion and preview."""

    run_id: str
    suggestion_id: str
    rule_id: str
    repo_name: str
    recipe_name: str
    proposed_action: str
    patch_preview: str


def _preview_for_missing_public_doc(recipe_name: str) -> tuple[str, str]:
    """Build action + preview for missing recipe documentation."""
    proposed_action = f"Add recipe documentation comment for `{recipe_name}`"
    patch_preview = (
        "--- justfile\n"
        "+++ justfile\n"
        "@@\n"
        f"+# {recipe_name}: add documentation describing purpose and side effects\n"
        f" {recipe_name}:"
    )
    return proposed_action, patch_preview


def _preview_for_recipe_name_style(recipe_name: str) -> tuple[str, str]:
    """Build action + preview for non-conforming recipe names."""
    suggested = recipe_name.lower().replace(" ", "-")
    proposed_action = f"Rename recipe `{recipe_name}` to style-compliant `{suggested}`"
    patch_preview = (
        "--- justfile\n"
        "+++ justfile\n"
        "@@\n"
        f"-{recipe_name}:\n"
        f"+{suggested}:"
    )
    return proposed_action, patch_preview


def generate_refactor_plan(db_path: Path, run_id: str | None = None) -> tuple[str, list[RefactorSuggestion]]:
    """Generate and persist suggestion-only refactor plans for a run."""
    lint_run_id, _ = run_lint(db_path=db_path, run_id=run_id)
    con = duckdb.connect(str(db_path))
    try:
        resolved_run_id = _resolve_run_id(con, lint_run_id)
        lint_rows = con.execute(
            """
            SELECT rule_id, repo_name, recipe_name
            FROM lint_findings
            WHERE run_id = ?
            ORDER BY repo_name ASC, recipe_name ASC, rule_id ASC
            """,
            [resolved_run_id],
        ).fetchall()

        suggestions: list[RefactorSuggestion] = []
        for rule_id_raw, repo_name_raw, recipe_name_raw in lint_rows:
            rule_id = str(rule_id_raw)
            repo_name = str(repo_name_raw)
            recipe_name = str(recipe_name_raw)

            if rule_id == "missing_public_doc":
                proposed_action, patch_preview = _preview_for_missing_public_doc(recipe_name)
            elif rule_id == "recipe_name_style":
                proposed_action, patch_preview = _preview_for_recipe_name_style(recipe_name)
            else:
                continue

            suggestions.append(
                RefactorSuggestion(
                    run_id=resolved_run_id,
                    suggestion_id=uuid4().hex,
                    rule_id=rule_id,
                    repo_name=repo_name,
                    recipe_name=recipe_name,
                    proposed_action=proposed_action,
                    patch_preview=patch_preview,
                )
            )

        con.execute("DELETE FROM refactor_plans WHERE run_id = ?", [resolved_run_id])
        if suggestions:
            created_utc = datetime.now(timezone.utc).isoformat()
            con.executemany(
                """
                INSERT INTO refactor_plans (
                    run_id,
                    suggestion_id,
                    rule_id,
                    repo_name,
                    recipe_name,
                    proposed_action,
                    patch_preview,
                    created_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        suggestion.run_id,
                        suggestion.suggestion_id,
                        suggestion.rule_id,
                        suggestion.repo_name,
                        suggestion.recipe_name,
                        suggestion.proposed_action,
                        suggestion.patch_preview,
                        created_utc,
                    )
                    for suggestion in suggestions
                ],
            )
    finally:
        con.close()
    return resolved_run_id, suggestions

