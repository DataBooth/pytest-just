"""Build a DuckDB corpus of recipes discovered across sibling justfiles."""

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

import duckdb
import typer
from loguru import logger


@dataclass(frozen=True)
class RepoJustfile:
    """Descriptor for a repository and its canonical justfile path."""
    repo_name: str
    repo_path: Path
    justfile_path: Path


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


def _run_just(just_bin: str, repo_path: Path, justfile_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
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
        Path(__file__).resolve().parents[2],
        help="Directory containing sibling repositories.",
    ),
    exclude_repo: str = typer.Option("pytest-just", help="Repository name to exclude from ingestion."),
    local_examples_dir: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "examples" / "local",
        help="Directory where sibling justfile copies are written.",
    ),
    db_path: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "examples" / "recipes.duckdb",
        help="Output DuckDB path.",
    ),
    report_path: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "docs" / "recipe_reuse_report.md",
        help="Output markdown report path.",
    ),
    log_path: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "logs" / "recipe_db_build.log",
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
    logger.info("Starting recipe DB build at {}", generated_utc)
    logger.info("Source root: {}", source_root)

    repo_justfiles = _discover_repo_justfiles(source_root=source_root, exclude_repo=exclude_repo)
    manifest_path = _copy_local_examples(
        repo_justfiles=repo_justfiles,
        local_examples_dir=local_examples_dir,
        generated_utc=generated_utc,
    )
    logger.info("Manifest written to {}", manifest_path)

    repo_rows: list[tuple[str, str, str, bool, str]] = []
    recipe_rows: list[tuple[str, str, str, bool, bool, str, str, str, str, str, str]] = []
    failures: list[tuple[str, str]] = []

    for repo in repo_justfiles:
        dump_result = _run_just(just_bin, repo.repo_path, repo.justfile_path, "--dump", "--dump-format", "json")
        if dump_result.returncode != 0:
            error = dump_result.stderr.strip().splitlines()[-1] if dump_result.stderr.strip() else "unknown error"
            logger.warning("Skipping {} due to parse failure: {}", repo.repo_name, error)
            failures.append((repo.repo_name, error))
            repo_rows.append((repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        try:
            dump_data = json.loads(dump_result.stdout)
        except json.JSONDecodeError:
            error = "invalid JSON from just --dump"
            logger.warning("Skipping {} due to invalid JSON output", repo.repo_name)
            failures.append((repo.repo_name, error))
            repo_rows.append((repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        recipes = dump_data.get("recipes", {})
        if not isinstance(recipes, dict):
            error = "recipes is not an object"
            logger.warning("Skipping {} due to malformed recipes payload", repo.repo_name)
            failures.append((repo.repo_name, error))
            repo_rows.append((repo.repo_name, str(repo.repo_path), str(repo.justfile_path), False, error))
            continue

        repo_rows.append((repo.repo_name, str(repo.repo_path), str(repo.justfile_path), True, ""))
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

    _ensure_dir(db_path.parent)
    con = duckdb.connect(str(db_path))
    con.execute(
        """
        CREATE OR REPLACE TABLE repo_sources (
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
        CREATE OR REPLACE TABLE recipe_occurrences (
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

    if repo_rows:
        con.executemany(
            "INSERT INTO repo_sources VALUES (?, ?, ?, ?, ?)",
            repo_rows,
        )
    if recipe_rows:
        con.executemany(
            "INSERT INTO recipe_occurrences VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            recipe_rows,
        )

    con.execute(
        """
        CREATE OR REPLACE TABLE unique_recipes AS
        SELECT
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
        GROUP BY signature
        """
    )

    top_recipe_names = con.execute(
        """
        SELECT recipe_name, COUNT(DISTINCT repo_name) AS repo_count, COUNT(*) AS occurrence_count
        FROM recipe_occurrences
        GROUP BY recipe_name
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT 25
        """
    ).fetchall()

    top_signatures = con.execute(
        """
        SELECT recipe_name, repo_count, occurrence_count, signature
        FROM unique_recipes
        WHERE repo_count > 1
        ORDER BY repo_count DESC, occurrence_count DESC, recipe_name ASC
        LIMIT 25
        """
    ).fetchall()
    con.close()

    parsed_total = sum(1 for row in repo_rows if row[3])
    _write_report(
        report_path=report_path,
        db_path=db_path,
        generated_utc=generated_utc,
        repo_total=len(repo_rows),
        parsed_total=parsed_total,
        failures=failures,
        top_recipe_names=top_recipe_names,
        top_signatures=top_signatures,
    )

    logger.info("Database written to {}", db_path)
    logger.info("Report written to {}", report_path)
    logger.info("Done. repos={}, parsed={}, failures={}, recipes={}", len(repo_rows), parsed_total, len(failures), len(recipe_rows))


if __name__ == "__main__":
    app()
