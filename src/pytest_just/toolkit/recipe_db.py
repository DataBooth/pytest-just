"""Build and query a DuckDB corpus of recipes discovered across sibling justfiles."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import duckdb
import typer
from loguru import logger
from pytest_just import __version__
from pytest_just.toolkit.linting import list_rules, run_lint
from pytest_just.toolkit.query_pack import list_named_queries, run_named_query
from pytest_just.toolkit.refactoring import apply_refactor_plan, generate_refactor_plan


@dataclass(frozen=True)
class RepoJustfile:
    """Descriptor for a repository and its canonical justfile path."""

    repo_name: str
    repo_path: Path
    justfile_path: Path


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SOURCE_ROOT = _PROJECT_ROOT.parent
_DEFAULT_LOCAL_EXAMPLES_DIR = _PROJECT_ROOT / "examples" / "local"
_DEFAULT_DB_PATH = _PROJECT_ROOT / "examples" / "recipes.duckdb"
_DEFAULT_REPORT_PATH = _PROJECT_ROOT / "docs" / "recipe_reuse_report.md"
_DEFAULT_LOG_PATH = _PROJECT_ROOT / "logs" / "recipe_db_build.log"
_LATEST_SCHEMA_VERSION = 4

app = typer.Typer(help="Build a DuckDB recipe corpus from sibling justfiles.")


def _discover_repo_justfiles(source_root: Path, exclude_repo: str) -> list[RepoJustfile]:
    """Discover sibling repositories that contain a justfile."""
    repos: list[RepoJustfile] = []
    for entry in sorted(source_root.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir() or entry.name == exclude_repo:
            continue
        candidates = [
            p
            for p in sorted(entry.iterdir(), key=lambda p: p.name.lower())
            if p.is_file() and p.name.lower() == "justfile"
        ]
        if not candidates:
            continue
        repos.append(
            RepoJustfile(
                repo_name=entry.name,
                repo_path=entry,
                justfile_path=candidates[0],
            )
        )
    return repos


def _run_just(
    just_bin: str,
    repo_path: Path,
    justfile_path: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    """Execute ``just`` against an explicit justfile path."""
    command = [just_bin, "--justfile", str(justfile_path), *args]
    return subprocess.run(
        command,
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )


def _extract_dependencies(recipe_payload: dict[str, Any]) -> list[str]:
    """Extract dependency names from a recipe payload."""
    deps: list[str] = []
    for dep in recipe_payload.get("dependencies", []):
        if isinstance(dep, dict):
            dep_name = dep.get("recipe")
            if isinstance(dep_name, str):
                deps.append(dep_name)
    return deps


def _extract_parameters(recipe_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract normalised parameter dictionaries from a recipe payload."""
    params = recipe_payload.get("parameters", [])
    if not isinstance(params, list):
        return []
    out: list[dict[str, Any]] = []
    for item in params:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": item.get("name"),
                "kind": item.get("kind"),
                "default": item.get("default"),
                "export": item.get("export"),
            }
        )
    return out


def _fallback_body_text(recipe_payload: dict[str, Any]) -> str:
    """Render textual body content from structured fragments."""
    lines = recipe_payload.get("body", [])
    if not isinstance(lines, list):
        return ""
    rendered_lines: list[str] = []
    for line in lines:
        if not isinstance(line, list):
            continue
        fragments: list[str] = []
        for fragment in line:
            if isinstance(fragment, str):
                fragments.append(fragment)
            elif isinstance(fragment, list):
                fragments.append(json.dumps(fragment, ensure_ascii=False))
            else:
                fragments.append(str(fragment))
        rendered_lines.append("".join(fragments))
    return "\n".join(rendered_lines).strip()


def _normalise_body(text: str) -> str:
    """Trim and whitespace-normalise command text line by line."""
    stripped_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    filtered = [line for line in stripped_lines if line]
    return "\n".join(filtered)


def _recipe_signature(
    recipe_name: str,
    dependencies: list[str],
    parameters: list[dict[str, Any]],
    body_normalised: str,
    is_shebang: bool,
) -> str:
    """Compute a stable signature hash for recipe shape and content."""
    payload = {
        "recipe_name": recipe_name,
        "dependencies": sorted(set(dependencies)),
        "parameters": sorted(parameters, key=lambda p: (str(p.get("name")), str(p.get("kind")))),
        "body_normalised": body_normalised,
        "is_shebang": is_shebang,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _ensure_dir(path: Path) -> None:
    """Create a directory tree if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)


def _stringify_scalar(value: Any) -> str:
    """Serialise scalar values into stable textual form."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _record_schema_migration(
    con: duckdb.DuckDBPyConnection,
    version: int,
    applied_utc: str,
) -> None:
    """Persist an applied schema migration version."""
    con.execute(
        "INSERT INTO schema_migrations (version, applied_utc) VALUES (?, ?)",
        [version, applied_utc],
    )


def _has_migration(con: duckdb.DuckDBPyConnection, version: int) -> bool:
    """Return whether a schema migration version has already been applied."""
    row = con.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE version = ?",
        [version],
    ).fetchone()
    assert row is not None
    return bool(row[0])


def _ensure_column(
    con: duckdb.DuckDBPyConnection,
    *,
    table_name: str,
    column_name: str,
    column_type: str,
) -> None:
    """Add a column if it does not exist on a table."""
    columns = {str(row[1]) for row in con.execute(f"PRAGMA table_info('{table_name}')").fetchall()}
    if column_name not in columns:
        con.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _apply_schema_migrations(con: duckdb.DuckDBPyConnection, applied_utc: str) -> int:
    """Apply in-place schema migrations and return latest schema version."""
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_utc VARCHAR
        )
        """
    )

    if not _has_migration(con, 1):
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS repo_sources (
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
            CREATE TABLE IF NOT EXISTS recipe_occurrences (
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
        _record_schema_migration(con, 1, applied_utc)

    if not _has_migration(con, 2):
        _ensure_column(
            con,
            table_name="repo_sources",
            column_name="run_id",
            column_type="VARCHAR",
        )
        _ensure_column(
            con,
            table_name="recipe_occurrences",
            column_name="run_id",
            column_type="VARCHAR",
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS ingest_runs (
                run_id VARCHAR PRIMARY KEY,
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
            CREATE TABLE IF NOT EXISTS recipe_dependencies (
                run_id VARCHAR,
                repo_name VARCHAR,
                recipe_name VARCHAR,
                dependency_name VARCHAR,
                dependency_index INTEGER
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_parameters (
                run_id VARCHAR,
                repo_name VARCHAR,
                recipe_name VARCHAR,
                parameter_name VARCHAR,
                parameter_kind VARCHAR,
                parameter_default VARCHAR,
                parameter_export BOOLEAN,
                parameter_index INTEGER
            )
            """
        )
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_aliases (
                run_id VARCHAR,
                repo_name VARCHAR,
                alias_name VARCHAR,
                target_recipe VARCHAR
            )
            """
        )
        _record_schema_migration(con, 2, applied_utc)

    if not _has_migration(con, 3):
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS lint_findings (
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
        _record_schema_migration(con, 3, applied_utc)
    if not _has_migration(con, 4):
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS refactor_plans (
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
            CREATE TABLE IF NOT EXISTS refactor_edits (
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
        _record_schema_migration(con, 4, applied_utc)
    return _LATEST_SCHEMA_VERSION


def _copy_local_examples(
    repo_justfiles: list[RepoJustfile],
    local_examples_dir: Path,
    generated_utc: str,
) -> Path:
    """Copy discovered justfiles into local examples and emit a manifest file."""
    _ensure_dir(local_examples_dir)
    manifest_path = local_examples_dir / "MANIFEST.tsv"

    for child in local_examples_dir.iterdir():
        if child.name in {"README.md", "MANIFEST.tsv"}:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    rows: list[tuple[str, str, str, str]] = []
    for repo in repo_justfiles:
        target_dir = local_examples_dir / repo.repo_name
        _ensure_dir(target_dir)
        target_path = target_dir / "justfile"
        shutil.copy2(repo.justfile_path, target_path)
        rows.append((repo.repo_name, repo.justfile_path.name, str(repo.justfile_path), str(target_path)))

    with manifest_path.open("w", encoding="utf-8") as f:
        f.write(f"generated_utc\t{generated_utc}\n")
        f.write("repo\tsource_name\tsource_path\tdestination_path\n")
        for repo_name, source_name, src, dst in rows:
            f.write(f"{repo_name}\t{source_name}\t{src}\t{dst}\n")

    logger.info("Copied {} local justfiles into {}", len(rows), local_examples_dir)
    return manifest_path


def _write_report(
    report_path: Path,
    db_path: Path,
    run_id: str,
    schema_version: int,
    generated_utc: str,
    repo_total: int,
    parsed_total: int,
    failures: list[tuple[str, str]],
    top_recipe_names: list[tuple[str, int, int]],
    top_signatures: list[tuple[str, int, int, str]],
) -> None:
    """Write a markdown summary of discovered recipe reuse."""
    _ensure_dir(report_path.parent)
    lines: list[str] = []
    lines.append("# Recipe reuse report")
    lines.append(f"Generated: {generated_utc}")
    lines.append(f"Run ID: `{run_id}`")
    lines.append(f"Schema version: `{schema_version}`")
    lines.append(f"Database: `{db_path}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Repositories discovered: `{repo_total}`")
    lines.append(f"- Repositories parsed: `{parsed_total}`")
    lines.append(f"- Repositories skipped (parse failed): `{len(failures)}`")
    lines.append("")
    if failures:
        lines.append("## Skipped repositories")
        for repo_name, error in failures:
            lines.append(f"- `{repo_name}`: {error}")
        lines.append("")
    lines.append("## Most common recipe names")
    lines.append("| recipe_name | repo_count | occurrence_count |")
    lines.append("|---|---:|---:|")
    for recipe_name, repo_count, occurrence_count in top_recipe_names:
        lines.append(f"| `{recipe_name}` | {repo_count} | {occurrence_count} |")
    lines.append("")
    lines.append("## Most reused unique signatures (name + shape)")
    lines.append("| recipe_name | repo_count | occurrence_count | signature_prefix |")
    lines.append("|---|---:|---:|---|")
    for recipe_name, repo_count, occurrence_count, signature in top_signatures:
        lines.append(f"| `{recipe_name}` | {repo_count} | {occurrence_count} | `{signature[:12]}` |")
    lines.append("")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@app.command()
def build(
    source_root: Path = typer.Option(
        _DEFAULT_SOURCE_ROOT,
        help="Directory containing sibling repositories.",
    ),
    exclude_repo: str = typer.Option("pytest-just", help="Repository name to exclude from ingestion."),
    local_examples_dir: Path = typer.Option(
        _DEFAULT_LOCAL_EXAMPLES_DIR,
        help="Directory where sibling justfile copies are written.",
    ),
    db_path: Path = typer.Option(
        _DEFAULT_DB_PATH,
        help="Output DuckDB path.",
    ),
    report_path: Path = typer.Option(
        _DEFAULT_REPORT_PATH,
        help="Output markdown report path.",
    ),
    log_path: Path = typer.Option(
        _DEFAULT_LOG_PATH,
        help="Path to log file.",
    ),
    just_bin: str = typer.Option("just", help="just executable path/name."),
) -> None:
    """Build the recipe database and companion markdown report."""
    _ensure_dir(log_path.parent)
    logger.remove()
    logger.add(log_path, level="INFO")
    logger.add(lambda msg: print(msg, end=""), level="INFO")

    generated_utc = datetime.now(timezone.utc).isoformat()
    run_id = uuid4().hex
    logger.info("Starting recipe DB build at {}", generated_utc)
    logger.info("Run ID: {}", run_id)
    logger.info("Source root: {}", source_root)

    repo_justfiles = _discover_repo_justfiles(source_root=source_root, exclude_repo=exclude_repo)
    manifest_path = _copy_local_examples(
        repo_justfiles=repo_justfiles,
        local_examples_dir=local_examples_dir,
        generated_utc=generated_utc,
    )
    logger.info("Manifest written to {}", manifest_path)

    repo_rows: list[tuple[str, str, str, str, bool, str]] = []
    recipe_rows: list[tuple[str, str, str, str, bool, bool, str, str, str, str, str, str]] = []
    dependency_rows: list[tuple[str, str, str, str, int]] = []
    parameter_rows: list[tuple[str, str, str, str, str, str, bool, int]] = []
    alias_rows: list[tuple[str, str, str, str]] = []
    failures: list[tuple[str, str]] = []

    for repo in repo_justfiles:
        dump_result = _run_just(just_bin, repo.repo_path, repo.justfile_path, "--dump", "--dump-format", "json")
        if dump_result.returncode != 0:
            error = dump_result.stderr.strip().splitlines()[-1] if dump_result.stderr.strip() else "unknown error"
            logger.warning("Skipping {} due to parse failure: {}", repo.repo_name, error)
            failures.append((repo.repo_name, error))
            repo_rows.append((run_id, repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        try:
            dump_data = json.loads(dump_result.stdout)
        except json.JSONDecodeError:
            error = "invalid JSON from just --dump"
            logger.warning("Skipping {} due to invalid JSON output", repo.repo_name)
            failures.append((repo.repo_name, error))
            repo_rows.append((run_id, repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        recipes = dump_data.get("recipes", {})
        if not isinstance(recipes, dict):
            error = "recipes is not an object"
            logger.warning("Skipping {} due to malformed recipes payload", repo.repo_name)
            failures.append((repo.repo_name, error))
            repo_rows.append((run_id, repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        repo_rows.append((run_id, repo.repo_name, str(repo.repo_path), str(repo.justfile_path), True, ""))
        aliases = dump_data.get("aliases", {})
        if isinstance(aliases, dict):
            for alias_name, alias_payload in aliases.items():
                if not isinstance(alias_name, str) or not isinstance(alias_payload, dict):
                    continue
                target_recipe = alias_payload.get("target")
                if isinstance(target_recipe, str):
                    alias_rows.append((run_id, repo.repo_name, alias_name, target_recipe))

        for recipe_name, payload in recipes.items():
            if not isinstance(recipe_name, str) or not isinstance(payload, dict):
                continue

            dependencies = _extract_dependencies(payload)
            parameters = _extract_parameters(payload)
            is_private = bool(payload.get("private", False))
            is_shebang = bool(payload.get("shebang", False))
            doc = str(payload.get("doc") or "")

            show_result = _run_just(just_bin, repo.repo_path, repo.justfile_path, "--show", recipe_name)
            if show_result.returncode == 0:
                body_text = show_result.stdout.strip()
            else:
                logger.warning(
                    "Failed to render `just --show {}` in {}. Falling back to body fragments.",
                    recipe_name,
                    repo.repo_name,
                )
                body_text = _fallback_body_text(payload)

            body_normalised = _normalise_body(body_text)
            signature = _recipe_signature(
                recipe_name=recipe_name,
                dependencies=dependencies,
                parameters=parameters,
                body_normalised=body_normalised,
                is_shebang=is_shebang,
            )

            recipe_rows.append(
                (
                    run_id,
                    repo.repo_name,
                    recipe_name,
                    signature,
                    is_private,
                    is_shebang,
                    doc,
                    json.dumps(dependencies, ensure_ascii=False),
                    json.dumps(parameters, ensure_ascii=False),
                    body_text,
                    body_normalised,
                    str(repo.justfile_path),
                )
            )

            for dependency_index, dependency_name in enumerate(dependencies):
                dependency_rows.append(
                    (run_id, repo.repo_name, recipe_name, dependency_name, dependency_index)
                )
            for parameter_index, parameter in enumerate(parameters):
                parameter_rows.append(
                    (
                        run_id,
                        repo.repo_name,
                        recipe_name,
                        str(parameter.get("name") or ""),
                        str(parameter.get("kind") or ""),
                        _stringify_scalar(parameter.get("default")),
                        bool(parameter.get("export", False)),
                        parameter_index,
                    )
                )

    _ensure_dir(db_path.parent)
    con = duckdb.connect(str(db_path))
    schema_version = _apply_schema_migrations(con, generated_utc)
    con.execute(
        """
        INSERT INTO ingest_runs (
            run_id,
            generated_utc,
            tool_version,
            source_root,
            exclude_repo,
            schema_version
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [run_id, generated_utc, __version__, str(source_root), exclude_repo, schema_version],
    )

    if repo_rows:
        con.executemany(
            """
            INSERT INTO repo_sources (
                run_id,
                repo_name,
                repo_path,
                justfile_path,
                parsed_success,
                parse_error
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            repo_rows,
        )
    if recipe_rows:
        con.executemany(
            """
            INSERT INTO recipe_occurrences (
                run_id,
                repo_name,
                recipe_name,
                signature,
                is_private,
                is_shebang,
                doc,
                dependencies_json,
                parameters_json,
                body_text,
                body_normalised,
                justfile_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            recipe_rows,
        )
    if dependency_rows:
        con.executemany(
            """
            INSERT INTO recipe_dependencies (
                run_id,
                repo_name,
                recipe_name,
                dependency_name,
                dependency_index
            ) VALUES (?, ?, ?, ?, ?)
            """,
            dependency_rows,
        )
    if parameter_rows:
        con.executemany(
            """
            INSERT INTO recipe_parameters (
                run_id,
                repo_name,
                recipe_name,
                parameter_name,
                parameter_kind,
                parameter_default,
                parameter_export,
                parameter_index
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            parameter_rows,
        )
    if alias_rows:
        con.executemany(
            """
            INSERT INTO recipe_aliases (
                run_id,
                repo_name,
                alias_name,
                target_recipe
            ) VALUES (?, ?, ?, ?)
            """,
            alias_rows,
        )

    con.execute(
        """
        CREATE OR REPLACE TABLE unique_recipes AS
        SELECT
            run_id,
            signature,
            any_value(recipe_name) AS recipe_name,
            any_value(is_private) AS is_private,
            any_value(is_shebang) AS is_shebang,
            any_value(doc) AS sample_doc,
            any_value(dependencies_json) AS sample_dependencies_json,
            any_value(parameters_json) AS sample_parameters_json,
            any_value(body_text) AS sample_body_text,
            any_value(body_normalised) AS body_normalised,
            COUNT(*) AS occurrence_count,
            COUNT(DISTINCT repo_name) AS repo_count
        FROM recipe_occurrences
        GROUP BY run_id, signature
        """
    )

    top_recipe_names = con.execute(
        """
        SELECT recipe_name, COUNT(DISTINCT repo_name) AS repo_count, COUNT(*) AS occurrence_count
        FROM recipe_occurrences
        WHERE run_id = ?
        GROUP BY recipe_name
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT 25
        """,
        [run_id],
    ).fetchall()

    top_signatures = con.execute(
        """
        SELECT recipe_name, repo_count, occurrence_count, signature
        FROM unique_recipes
        WHERE run_id = ? AND repo_count > 1
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT 25
        """,
        [run_id],
    ).fetchall()
    con.close()

    parsed_total = sum(1 for row in repo_rows if row[4])
    _write_report(
        report_path=report_path,
        db_path=db_path,
        run_id=run_id,
        schema_version=schema_version,
        generated_utc=generated_utc,
        repo_total=len(repo_rows),
        parsed_total=parsed_total,
        failures=failures,
        top_recipe_names=top_recipe_names,
        top_signatures=top_signatures,
    )

    logger.info("Database written to {}", db_path)
    logger.info("Report written to {}", report_path)
    logger.info(
        "Done. run_id={}, repos={}, parsed={}, failures={}, recipes={}",
        run_id,
        len(repo_rows),
        parsed_total,
        len(failures),
        len(recipe_rows),
    )


@app.command("query")
def query_corpus(
    query_name: str = typer.Argument(
        ...,
        help="Named query identifier. Use `list-queries` to view available queries.",
    ),
    db_path: Path = typer.Option(
        _DEFAULT_DB_PATH,
        help="Path to corpus DuckDB file.",
    ),
    limit: int = typer.Option(
        25,
        min=1,
        help="Maximum row count.",
    ),
    run_id: str | None = typer.Option(
        None,
        help="Optional run ID filter.",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format: markdown, json, or tsv.",
    ),
) -> None:
    """Run a named analytics query against the corpus database."""
    format_lower = output_format.lower()
    if format_lower not in {"markdown", "json", "tsv"}:
        raise typer.BadParameter("format must be one of: markdown, json, tsv")

    columns, rows = run_named_query(
        db_path=db_path,
        query_name=query_name,
        limit=limit,
        run_id=run_id,
    )
    if format_lower == "json":
        payload = [dict(zip(columns, row)) for row in rows]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if format_lower == "tsv":
        print("\t".join(columns))
        for row in rows:
            print("\t".join(_stringify_scalar(value).replace("\t", " ") for value in row))
        return

    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join(["---"] * len(columns)) + "|")
    for row in rows:
        rendered = [_stringify_scalar(value).replace("\n", " ") for value in row]
        print("| " + " | ".join(rendered) + " |")

@app.command("lint")
def lint_corpus(
    db_path: Path = typer.Option(
        _DEFAULT_DB_PATH,
        help="Path to corpus DuckDB file.",
    ),
    run_id: str | None = typer.Option(
        None,
        help="Optional run ID filter.",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format: markdown, json, or tsv.",
    ),
    fail_on: str = typer.Option(
        "none",
        help="Exit policy: none, warning, or error.",
    ),
) -> None:
    """Run lint rules against corpus data and emit diagnostics."""
    format_lower = output_format.lower()
    if format_lower not in {"markdown", "json", "tsv"}:
        raise typer.BadParameter("format must be one of: markdown, json, tsv")

    fail_on_lower = fail_on.lower()
    if fail_on_lower not in {"none", "warning", "error"}:
        raise typer.BadParameter("fail-on must be one of: none, warning, error")

    resolved_run_id, findings = run_lint(db_path=db_path, run_id=run_id)
    if format_lower == "json":
        payload = [
            {
                "run_id": finding.run_id,
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "repo_name": finding.repo_name,
                "recipe_name": finding.recipe_name,
                "message": finding.message,
                "fixable": finding.fixable,
            }
            for finding in findings
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif format_lower == "tsv":
        print("run_id\trule_id\tseverity\trepo_name\trecipe_name\tfixable\tmessage")
        for finding in findings:
            message = finding.message.replace("\t", " ").replace("\n", " ")
            print(
                "\t".join(
                    [
                        finding.run_id,
                        finding.rule_id,
                        finding.severity,
                        finding.repo_name,
                        finding.recipe_name,
                        str(finding.fixable).lower(),
                        message,
                    ]
                )
            )
    else:
        print(
            "| run_id | rule_id | severity | repo_name | recipe_name | fixable | message |"
        )
        print("|---|---|---|---|---|---|---|")
        for finding in findings:
            message = finding.message.replace("\n", " ")
            print(
                "| {} | {} | {} | {} | {} | {} | {} |".format(
                    finding.run_id,
                    finding.rule_id,
                    finding.severity,
                    finding.repo_name,
                    finding.recipe_name,
                    str(finding.fixable).lower(),
                    message,
                )
            )

    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    error_count = sum(1 for finding in findings if finding.severity == "error")
    logger.info(
        "Lint complete for run_id={} rules={} findings={} warnings={} errors={}",
        resolved_run_id,
        len(list_rules()),
        len(findings),
        warning_count,
        error_count,
    )
    if fail_on_lower == "warning" and (warning_count + error_count) > 0:
        raise typer.Exit(code=1)
    if fail_on_lower == "error" and error_count > 0:
        raise typer.Exit(code=1)

@app.command("refactor")
def refactor_corpus(
    db_path: Path = typer.Option(
        _DEFAULT_DB_PATH,
        help="Path to corpus DuckDB file.",
    ),
    run_id: str | None = typer.Option(
        None,
        help="Optional run ID filter.",
    ),
    output_format: str = typer.Option(
        "markdown",
        "--format",
        help="Output format: markdown, json, or tsv.",
    ),
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply planned refactors to justfiles using backup/rollback safeguards.",
    ),
    validate: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Run validation hooks after apply (default: enabled).",
    ),
    just_bin: str = typer.Option(
        "just",
        help="just executable path/name used for syntax validation.",
    ),
    validation_command: str | None = typer.Option(
        None,
        help="Optional repository command run after just syntax checks.",
    ),
    backup_suffix: str = typer.Option(
        ".bak",
        help="Backup suffix used when apply mode is enabled.",
    ),
) -> None:
    """Generate refactor suggestions, optionally apply them safely, and print results."""
    format_lower = output_format.lower()
    if format_lower not in {"markdown", "json", "tsv"}:
        raise typer.BadParameter("format must be one of: markdown, json, tsv")

    if apply:
        resolved_run_id, edits = apply_refactor_plan(
            db_path=db_path,
            run_id=run_id,
            just_bin=just_bin,
            validation_command=validation_command,
            backup_suffix=backup_suffix,
            validate=validate,
        )
        if format_lower == "json":
            payload = [
                {
                    "run_id": edit.run_id,
                    "edit_id": edit.edit_id,
                    "suggestion_id": edit.suggestion_id,
                    "justfile_path": edit.justfile_path,
                    "before_hash": edit.before_hash,
                    "after_hash": edit.after_hash,
                    "patch_text": edit.patch_text,
                }
                for edit in edits
            ]
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif format_lower == "tsv":
            print("run_id\tedit_id\tsuggestion_id\tjustfile_path\tbefore_hash\tafter_hash")
            for edit in edits:
                print(
                    "\t".join(
                        [
                            edit.run_id,
                            edit.edit_id,
                            edit.suggestion_id,
                            edit.justfile_path,
                            edit.before_hash,
                            edit.after_hash,
                        ]
                    )
                )
        else:
            print("| run_id | edit_id | suggestion_id | justfile_path |")
            print("|---|---|---|---|")
            for edit in edits:
                print(
                    "| {} | {} | {} | {} |".format(
                        edit.run_id,
                        edit.edit_id,
                        edit.suggestion_id,
                        edit.justfile_path,
                    )
                )
                print("```diff")
                print(edit.patch_text)
                print("```")

        logger.info(
            "Refactor apply complete for run_id={} edits={} validate={} validation_command={}",
            resolved_run_id,
            len(edits),
            validate,
            validation_command or "",
        )
        return

    resolved_run_id, suggestions = generate_refactor_plan(db_path=db_path, run_id=run_id)
    if format_lower == "json":
        payload = [
            {
                "run_id": suggestion.run_id,
                "suggestion_id": suggestion.suggestion_id,
                "rule_id": suggestion.rule_id,
                "repo_name": suggestion.repo_name,
                "recipe_name": suggestion.recipe_name,
                "proposed_action": suggestion.proposed_action,
                "patch_preview": suggestion.patch_preview,
            }
            for suggestion in suggestions
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif format_lower == "tsv":
        print("run_id\tsuggestion_id\trule_id\trepo_name\trecipe_name\tproposed_action")
        for suggestion in suggestions:
            action = suggestion.proposed_action.replace("\t", " ").replace("\n", " ")
            print(
                "\t".join(
                    [
                        suggestion.run_id,
                        suggestion.suggestion_id,
                        suggestion.rule_id,
                        suggestion.repo_name,
                        suggestion.recipe_name,
                        action,
                    ]
                )
            )
    else:
        print("| run_id | suggestion_id | rule_id | repo_name | recipe_name | proposed_action |")
        print("|---|---|---|---|---|---|")
        for suggestion in suggestions:
            action = suggestion.proposed_action.replace("\n", " ")
            print(
                "| {} | {} | {} | {} | {} | {} |".format(
                    suggestion.run_id,
                    suggestion.suggestion_id,
                    suggestion.rule_id,
                    suggestion.repo_name,
                    suggestion.recipe_name,
                    action,
                )
            )
            print("```diff")
            print(suggestion.patch_preview)
            print("```")

    logger.info(
        "Refactor planning complete for run_id={} suggestions={}",
        resolved_run_id,
        len(suggestions),
    )



@app.command("list-queries")
def list_queries() -> None:
    """List named query identifiers available to the query command."""
    for query_name in list_named_queries():
        print(query_name)


if __name__ == "__main__":
    app()
