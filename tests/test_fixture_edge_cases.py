from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from pytest_just.errors import JustCommandError, JustJsonFormatError, UnknownRecipeError
from pytest_just.fixture import JustfileFixture


pytestmark = pytest.mark.skipif(shutil.which("just") is None, reason="just binary is required")


def test_assert_depends_on_transitive_and_exact_semantics(tmp_path: Path) -> None:
    justfile = tmp_path / "justfile"
    justfile.write_text(
        "a: b c\n"
        "    @echo a\n"
        "b: d\n"
        "    @echo b\n"
        "c:\n"
        "    @echo c\n"
        "d:\n"
        "    @echo d\n",
        encoding="utf-8",
    )
    just = JustfileFixture(root=tmp_path)

    just.assert_depends_on("a", ["b", "c"], exact=True)
    just.assert_depends_on("a", ["d"], transitive=True)

    with pytest.raises(AssertionError):
        just.assert_depends_on("a", ["b"], exact=True)

    with pytest.raises(AssertionError):
        just.assert_depends_on("a", ["a"], transitive=True)


def test_aliases_are_exposed_from_dump(tmp_path: Path) -> None:
    justfile = tmp_path / "justfile"
    justfile.write_text(
        "alias t := test\n"
        "test:\n"
        "    @echo test\n",
        encoding="utf-8",
    )
    just = JustfileFixture(root=tmp_path)

    assert just.aliases()["t"] == "test"
    just.assert_exists("test")


def test_import_collision_surfaces_as_command_error(tmp_path: Path) -> None:
    (tmp_path / "a.just").write_text("dup:\n    @echo a\n", encoding="utf-8")
    (tmp_path / "b.just").write_text("dup:\n    @echo b\n", encoding="utf-8")
    (tmp_path / "justfile").write_text('import "a.just"\nimport "b.just"\n', encoding="utf-8")

    just = JustfileFixture(root=tmp_path)
    with pytest.raises(JustCommandError):
        just.recipe_names()


def test_invalid_json_payload_raises_json_format_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "justfile").write_text("test:\n    @echo ok\n", encoding="utf-8")
    just = JustfileFixture(root=tmp_path)

    def fake_run(*_args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["just", "--dump", "--dump-format", "json"],
            returncode=0,
            stdout='{"recipes": []}',
            stderr="",
        )

    monkeypatch.setattr(just, "_run", fake_run)
    with pytest.raises(JustJsonFormatError):
        just.recipe_names()


def test_unknown_recipe_uses_specific_error_type(tmp_path: Path) -> None:
    (tmp_path / "justfile").write_text("test:\n    @echo ok\n", encoding="utf-8")
    just = JustfileFixture(root=tmp_path)

    with pytest.raises(UnknownRecipeError):
        just.dependencies("missing")


def test_unknown_recipe_error_message_contains_context(tmp_path: Path) -> None:
    (tmp_path / "justfile").write_text("test:\n    @echo ok\n", encoding="utf-8")
    just = JustfileFixture(root=tmp_path)

    with pytest.raises(UnknownRecipeError) as exc_info:
        just.show("missing")

    message = str(exc_info.value)
    assert "missing" in message
    assert "Available recipes:" in message
    assert "test" in message


def test_imported_recipe_is_visible(tmp_path: Path) -> None:
    (tmp_path / "shared.just").write_text("hello:\n    @echo hi\n", encoding="utf-8")
    (tmp_path / "justfile").write_text('import "shared.just"\n', encoding="utf-8")
    just = JustfileFixture(root=tmp_path)

    just.assert_exists("hello")
    just.assert_body_contains("hello", "@echo hi")


def test_dry_run_rejects_shebang_recipe(tmp_path: Path) -> None:
    (tmp_path / "justfile").write_text(
        "deploy:\n"
        "    #!/usr/bin/env bash\n"
        "    echo deploy\n",
        encoding="utf-8",
    )
    just = JustfileFixture(root=tmp_path)

    with pytest.raises(AssertionError) as exc_info:
        just.dry_run("deploy")

    assert "not dry-run safe" in str(exc_info.value)


def test_assert_dry_run_contains_failure_includes_output(tmp_path: Path) -> None:
    (tmp_path / "justfile").write_text("test:\n    echo hello-world\n", encoding="utf-8")
    just = JustfileFixture(root=tmp_path)

    with pytest.raises(AssertionError) as exc_info:
        just.assert_dry_run_contains("test", "goodbye-world")

    message = str(exc_info.value)
    assert "dry-run output" in message
    assert "hello-world" in message
