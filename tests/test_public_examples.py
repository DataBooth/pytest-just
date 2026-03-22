"""Contract tests against curated public justfile examples."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_just.errors import UnknownRecipeError

from pytest_just.fixture import JustfileFixture
from pytest_just.plugin import _discover_justfile_root


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EXAMPLES = REPO_ROOT / "examples" / "public"


def _fixture(example_name: str) -> JustfileFixture:
    """Construct a fixture for a named public example directory."""
    return JustfileFixture(root=PUBLIC_EXAMPLES / example_name, just_bin="just")


def test_async_compression_example_contracts() -> None:
    """Validate core contract expectations for async-compression recipes."""
    just = _fixture("async-compression")

    just.assert_exists("check")
    just.assert_depends_on("check", ["clippy"])
    just.assert_parameter("check-features", "async_runtime")
    just.assert_body_contains("check", "cargo +nightly fmt -- --check")
    just.assert_variable_referenced("check-features", "async_runtime")

    assert "_list" not in just.recipe_names()
    assert "_list" in just.recipe_names(include_private=True)


def test_actix_web_example_contracts() -> None:
    """Validate core contract expectations for actix-web recipes."""
    just = _fixture("actix-web")

    just.assert_exists("test-all")
    just.assert_depends_on("test-all", ["test"])
    just.assert_body_contains("check", "cargo {{ toolchain }} check")
    just.assert_variable_referenced("check", "toolchain")

    assert just.is_private("check-min")
    assert "check-min" not in just.recipe_names()
    assert "check-min" in just.recipe_names(include_private=True)
    assert "toolchain" in just.assignments()


def test_martin_example_contracts_and_imports() -> None:
    """Validate imports, parameters, and shebang behaviour in martin recipes."""
    just = _fixture("martin")

    just.assert_exists("hello")
    just.assert_body_contains("hello", "hello from shared.just")
    just.assert_parameter("build-release", "target")
    just.assert_variable_referenced("bless", "ci_mode")

    assert just.is_shebang("build-release")
    assert just.is_shebang("bless")
    just.assert_not_shebang("test")

    with pytest.raises(AssertionError):
        just.assert_not_shebang("build-release")


def test_dry_run_returns_completed_process_for_non_shebang_recipe() -> None:
    """Ensure dry-run executes successfully for non-shebang recipes."""
    just = _fixture("actix-web")
    result = just.dry_run("test")

    assert result.returncode == 0, result.stderr
    assert "cargo" in (result.stdout + result.stderr)


def test_assert_dry_run_contains_helper() -> None:
    """Ensure dry-run assertion helper passes when output contains expected text."""
    just = _fixture("actix-web")
    just.assert_dry_run_contains("test", "cargo")


def test_unknown_recipe_error_lists_available_recipes() -> None:
    """Ensure unknown recipe errors include available recipe context."""
    just = _fixture("async-compression")

    with pytest.raises(UnknownRecipeError) as exc_info:
        just.recipe_names()
        just.dependencies("does-not-exist")

    assert "Available recipes:" in str(exc_info.value)


def test_discover_justfile_root_walks_upwards(tmp_path: Path) -> None:
    """Ensure root discovery walks ancestors to find a justfile."""
    root = tmp_path / "project"
    nested = root / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (root / "justfile").write_text("default:\n    @echo hi\n", encoding="utf-8")

    assert _discover_justfile_root(nested) == root


def test_discover_justfile_root_raises_when_missing(tmp_path: Path) -> None:
    """Ensure root discovery fails clearly when no justfile exists."""
    start = tmp_path / "no-justfile" / "deep"
    start.mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        _discover_justfile_root(start)
