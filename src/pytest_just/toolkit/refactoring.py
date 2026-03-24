"""Suggestion-first refactor planner and safe apply support for corpus data."""

from __future__ import annotations

import difflib
import hashlib
import subprocess
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


@dataclass(frozen=True)
class RefactorEdit:
    """Represents a materialised refactor edit that has been applied."""

    run_id: str
    edit_id: str
    suggestion_id: str
    justfile_path: str
    before_hash: str
    after_hash: str
    patch_text: str


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


def _hash_text(text: str) -> str:
    """Return a stable hash for text blobs."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _style_compliant_recipe_name(recipe_name: str) -> str:
    """Generate a style-compliant recipe name candidate."""
    return recipe_name.lower().replace(" ", "-")


def _build_patch(before: str, after: str, path: Path) -> str:
    """Build a unified diff patch from before/after file content."""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
            lineterm="",
        )
    )


def _apply_missing_public_doc(recipe_name: str, content: str) -> str:
    """Insert a simple doc comment above a recipe declaration when missing."""
    lines = content.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(f"{recipe_name}:"):
            if index > 0 and lines[index - 1].lstrip().startswith("#"):
                return content
            comment = f"# {recipe_name}: document purpose and side effects\n"
            lines.insert(index, comment)
            return "".join(lines)
    return content


def _apply_recipe_name_style(recipe_name: str, content: str) -> str:
    """Rename a top-level recipe declaration to a style-compliant name."""
    suggested = _style_compliant_recipe_name(recipe_name)
    if suggested == recipe_name:
        return content
    lines = content.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(f"{recipe_name}:"):
            lines[index] = line.replace(f"{recipe_name}:", f"{suggested}:", 1)
            return "".join(lines)
    return content


def _apply_suggestion_to_content(suggestion: RefactorSuggestion, content: str) -> str:
    """Apply an individual suggestion to file content."""
    if suggestion.rule_id == "missing_public_doc":
        return _apply_missing_public_doc(suggestion.recipe_name, content)
    if suggestion.rule_id == "recipe_name_style":
        return _apply_recipe_name_style(suggestion.recipe_name, content)
    return content


def _validate_justfile(just_bin: str, justfile_path: Path) -> None:
    """Validate justfile syntax using `just --dump`."""
    result = subprocess.run(
        [just_bin, "--justfile", str(justfile_path), "--dump", "--dump-format", "json"],
        cwd=justfile_path.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "just validation failed"
        raise RuntimeError(f"just validation failed for {justfile_path}: {error}")


def _run_validation_command(command: str, cwd: Path) -> None:
    """Run an optional repository validation command."""
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=True,
        check=False,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "validation command failed"
        raise RuntimeError(f"validation command failed in {cwd}: {error}")


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


def apply_refactor_plan(
    db_path: Path,
    *,
    run_id: str | None = None,
    just_bin: str = "just",
    validation_command: str | None = None,
    backup_suffix: str = ".bak",
    validate: bool = True,
) -> tuple[str, list[RefactorEdit]]:
    """Apply planned refactors with backup, validation, and rollback support."""
    resolved_run_id, _ = generate_refactor_plan(db_path=db_path, run_id=run_id)
    con = duckdb.connect(str(db_path))

    backups: dict[Path, str] = {}
    pending_content: dict[Path, str] = {}
    pending_edits: list[RefactorEdit] = []
    created_utc = datetime.now(timezone.utc).isoformat()
    try:
        repo_rows = con.execute(
            """
            SELECT repo_name, justfile_path
            FROM repo_sources
            WHERE run_id = ? AND parsed_success = TRUE
            """,
            [resolved_run_id],
        ).fetchall()
        repo_to_justfile = {str(repo_name): Path(str(justfile_path)) for repo_name, justfile_path in repo_rows}

        suggestion_rows = con.execute(
            """
            SELECT suggestion_id, rule_id, repo_name, recipe_name, proposed_action, patch_preview
            FROM refactor_plans
            WHERE run_id = ?
            ORDER BY repo_name ASC, recipe_name ASC, suggestion_id ASC
            """,
            [resolved_run_id],
        ).fetchall()
        suggestions = [
            RefactorSuggestion(
                run_id=resolved_run_id,
                suggestion_id=str(suggestion_id),
                rule_id=str(rule_id),
                repo_name=str(repo_name),
                recipe_name=str(recipe_name),
                proposed_action=str(proposed_action),
                patch_preview=str(patch_preview),
            )
            for suggestion_id, rule_id, repo_name, recipe_name, proposed_action, patch_preview in suggestion_rows
        ]

        for suggestion in suggestions:
            justfile_path = repo_to_justfile.get(suggestion.repo_name)
            if justfile_path is None or not justfile_path.exists():
                continue
            if justfile_path not in backups:
                original = justfile_path.read_text(encoding="utf-8")
                backups[justfile_path] = original
                pending_content[justfile_path] = original

            before_text = pending_content[justfile_path]
            after_text = _apply_suggestion_to_content(suggestion, before_text)
            if after_text == before_text:
                continue

            pending_content[justfile_path] = after_text
            patch_text = _build_patch(before_text, after_text, justfile_path)
            pending_edits.append(
                RefactorEdit(
                    run_id=resolved_run_id,
                    edit_id=uuid4().hex,
                    suggestion_id=suggestion.suggestion_id,
                    justfile_path=str(justfile_path),
                    before_hash=_hash_text(before_text),
                    after_hash=_hash_text(after_text),
                    patch_text=patch_text,
                )
            )

        if not pending_edits:
            return resolved_run_id, []

        for path, original_text in backups.items():
            backup_path = path.with_name(path.name + backup_suffix)
            backup_path.write_text(original_text, encoding="utf-8")

        for path, new_text in pending_content.items():
            if backups[path] != new_text:
                path.write_text(new_text, encoding="utf-8")

        if validate:
            for path in pending_content:
                if backups[path] != pending_content[path]:
                    _validate_justfile(just_bin=just_bin, justfile_path=path)
            if validation_command:
                for repo_dir in sorted({str(path.parent) for path in pending_content}):
                    _run_validation_command(validation_command, cwd=Path(repo_dir))

        con.executemany(
            """
            INSERT INTO refactor_edits (
                run_id,
                edit_id,
                suggestion_id,
                justfile_path,
                before_hash,
                after_hash,
                patch_text,
                applied_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    edit.run_id,
                    edit.edit_id,
                    edit.suggestion_id,
                    edit.justfile_path,
                    edit.before_hash,
                    edit.after_hash,
                    edit.patch_text,
                    created_utc,
                )
                for edit in pending_edits
            ],
        )
    except Exception:
        for path, original_text in backups.items():
            path.write_text(original_text, encoding="utf-8")
        raise
    finally:
        con.close()
    return resolved_run_id, pending_edits

