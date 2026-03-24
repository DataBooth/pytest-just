"""Golden and behavioural tests for the recipe DB build script."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import duckdb
from pytest_just.toolkit import recipe_db as builder
from pytest_just.toolkit.query_pack import run_named_query


def test_discover_repo_justfiles_respects_exclusion_and_case(tmp_path: Path) -> None:
    """Ensure repo discovery honours exclusions and case-insensitive justfile matching."""
    source_root = tmp_path / "source"
    source_root.mkdir()

    repo_a = source_root / "repo-a"
    repo_b = source_root / "repo-b"
    repo_excluded = source_root / "pytest-just"
    repo_none = source_root / "repo-none"
    for repo in (repo_a, repo_b, repo_excluded, repo_none):
        repo.mkdir()

    (repo_a / "justfile").write_text("test:\n    @echo a\n", encoding="utf-8")
    (repo_b / "Justfile").write_text("test:\n    @echo b\n", encoding="utf-8")
    (repo_excluded / "justfile").write_text("test:\n    @echo excluded\n", encoding="utf-8")

    discovered = builder._discover_repo_justfiles(source_root=source_root, exclude_repo="pytest-just")
    names = [item.repo_name for item in discovered]

    assert names == ["repo-a", "repo-b"]
    assert discovered[0].justfile_path.name == "justfile"
    assert discovered[1].justfile_path.name == "Justfile"


def test_build_pipeline_writes_expected_tables_with_mocked_just(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Ensure the build pipeline writes expected DB, manifest, report, and log outputs."""
    source_root = tmp_path / "source"
    source_root.mkdir()

    repo_ok = source_root / "repo-ok"
    repo_fail = source_root / "repo-fail"
    repo_excluded = source_root / "pytest-just"
    for repo in (repo_ok, repo_fail, repo_excluded):
        repo.mkdir()

    (repo_ok / "justfile").write_text("# placeholder\n", encoding="utf-8")
    (repo_fail / "justfile").write_text("# placeholder\n", encoding="utf-8")
    (repo_excluded / "justfile").write_text("# placeholder\n", encoding="utf-8")

    local_examples_dir = tmp_path / "examples-local"
    local_examples_dir.mkdir()
    (local_examples_dir / "README.md").write_text("# keep me\n", encoding="utf-8")

    db_path = tmp_path / "recipes.duckdb"
    report_path = tmp_path / "recipe_reuse_report.md"
    log_path = tmp_path / "recipe_db_build.log"

    dump_payload = {
        "aliases": {"t": {"target": "test"}},
        "assignments": {"PY": {"value": "python", "export": False}},
        "recipes": {
            "test": {
                "body": [["uv run pytest -q"]],
                "dependencies": [],
                "doc": "Run tests",
                "name": "test",
                "parameters": [],
                "private": False,
                "quiet": False,
                "shebang": False,
                "attributes": [],
            },
            "deploy": {
                "body": [["#!/usr/bin/env bash"], ["echo deploy {{ENV}}"]],
                "dependencies": [{"arguments": [], "recipe": "test"}],
                "doc": None,
                "name": "deploy",
                "parameters": [
                    {"default": None, "export": False, "kind": "singular", "name": "ENV"},
                ],
                "private": False,
                "quiet": False,
                "shebang": True,
                "attributes": [],
            },
        },
        "settings": {},
        "warnings": [],
    }

    def fake_run_just(
        just_bin: str,
        repo_path: Path,
        justfile_path: Path,
        *args: str,
    ) -> subprocess.CompletedProcess[str]:
        """Simulate `just` invocations for successful and failing repositories."""
        assert just_bin == "just"
        assert justfile_path.exists()

        if repo_path.name == "repo-fail" and args == ("--dump", "--dump-format", "json"):
            return subprocess.CompletedProcess(
                args=["just", *args],
                returncode=1,
                stdout="",
                stderr="syntax error near recipe",
            )

        if args == ("--dump", "--dump-format", "json"):
            return subprocess.CompletedProcess(
                args=["just", *args],
                returncode=0,
                stdout=json.dumps(dump_payload),
                stderr="",
            )

        if args == ("--show", "test"):
            return subprocess.CompletedProcess(
                args=["just", *args],
                returncode=0,
                stdout="uv run pytest -q\n",
                stderr="",
            )

        if args == ("--show", "deploy"):
            # Exercise fallback body extraction path.
            return subprocess.CompletedProcess(
                args=["just", *args],
                returncode=1,
                stdout="",
                stderr="show failed",
            )

        raise AssertionError(f"Unexpected invocation: {repo_path} {args}")

    monkeypatch.setattr(builder, "_run_just", fake_run_just)

    builder.build(
        source_root=source_root,
        exclude_repo="pytest-just",
        local_examples_dir=local_examples_dir,
        db_path=db_path,
        report_path=report_path,
        log_path=log_path,
        just_bin="just",
    )

    manifest = local_examples_dir / "MANIFEST.tsv"
    assert manifest.exists()
    manifest_text = manifest.read_text(encoding="utf-8")
    assert "repo-ok" in manifest_text
    assert "repo-fail" in manifest_text
    assert "pytest-just" not in manifest_text

    con = duckdb.connect(str(db_path))
    repo_counts_row = con.execute(
        """
        SELECT
            COUNT(*) AS repo_total,
            SUM(CASE WHEN parsed_success THEN 1 ELSE 0 END) AS parsed_total,
            SUM(CASE WHEN NOT parsed_success THEN 1 ELSE 0 END) AS failed_total
        FROM repo_sources
        """,
    ).fetchone()
    assert repo_counts_row is not None
    repo_total, parsed_total, failed_total = repo_counts_row
    assert (repo_total, parsed_total, failed_total) == (2, 1, 1)

    recipe_count_row = con.execute("SELECT COUNT(*) FROM recipe_occurrences").fetchone()
    assert recipe_count_row is not None
    recipe_count = recipe_count_row[0]
    run_row = con.execute("SELECT run_id, schema_version FROM ingest_runs").fetchone()
    assert run_row is not None
    run_id, schema_version = run_row
    assert isinstance(run_id, str) and run_id
    assert schema_version == 2

    dependency_count_row = con.execute("SELECT COUNT(*) FROM recipe_dependencies").fetchone()
    assert dependency_count_row is not None
    dependency_count = dependency_count_row[0]

    parameter_count_row = con.execute("SELECT COUNT(*) FROM recipe_parameters").fetchone()
    assert parameter_count_row is not None
    parameter_count = parameter_count_row[0]

    alias_count_row = con.execute("SELECT COUNT(*) FROM recipe_aliases").fetchone()
    assert alias_count_row is not None
    alias_count = alias_count_row[0]

    unique_count_row = con.execute("SELECT COUNT(*) FROM unique_recipes").fetchone()
    assert unique_count_row is not None
    unique_count = unique_count_row[0]
    assert recipe_count == 2
    assert dependency_count == 1
    assert parameter_count == 1
    assert alias_count == 1
    assert unique_count == 2

    deploy_body_row = con.execute(
        "SELECT sample_body_text FROM unique_recipes WHERE recipe_name = 'deploy'",
    ).fetchone()
    assert deploy_body_row is not None
    deploy_body = deploy_body_row[0]
    con.close()
    assert "#!/usr/bin/env bash" in deploy_body
    query_columns, query_rows = run_named_query(
        db_path=db_path,
        query_name="top_recipe_names",
        limit=10,
        run_id=run_id,
    )
    assert query_columns == ["recipe_name", "repo_count", "occurrence_count"]
    assert [row[0] for row in query_rows] == ["deploy", "test"]

    parse_columns, parse_rows = run_named_query(
        db_path=db_path,
        query_name="parse_failures",
        limit=10,
        run_id=run_id,
    )
    assert parse_columns == ["repo_name", "parse_error"]
    assert parse_rows == [("repo-fail", "syntax error near recipe")]

    report_text = report_path.read_text(encoding="utf-8")
    assert "Schema version: `2`" in report_text
    assert "Run ID:" in report_text
    assert "Repositories parsed: `1`" in report_text
    assert "repo-fail" in report_text

    log_text = log_path.read_text(encoding="utf-8")
    assert "Skipping repo-fail due to parse failure" in log_text
