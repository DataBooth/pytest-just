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
