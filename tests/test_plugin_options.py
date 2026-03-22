from __future__ import annotations

from pathlib import Path

import pytest

from pytest_just.plugin import _create_just_fixture, _discover_justfile_root


def test_discover_prefers_nearest_parent_justfile(tmp_path: Path) -> None:
    top = tmp_path / "top"
    middle = top / "middle"
    leaf = middle / "leaf"
    leaf.mkdir(parents=True)
    (top / "justfile").write_text("top:\n    @echo top\n", encoding="utf-8")
    (middle / "justfile").write_text("middle:\n    @echo middle\n", encoding="utf-8")

    assert _discover_justfile_root(leaf) == middle


def test_session_fixture_uses_explicit_root_option(tmp_path: Path) -> None:
    explicit_root = tmp_path / "explicit"
    explicit_root.mkdir(parents=True)
    (explicit_root / "justfile").write_text("test:\n    @echo ok\n", encoding="utf-8")

    auto_root = tmp_path / "auto"
    nested = auto_root / "nested"
    nested.mkdir(parents=True)
    (auto_root / "justfile").write_text("other:\n    @echo auto\n", encoding="utf-8")

    just_obj = _create_just_fixture(
        rootpath=nested,
        justfile_root=str(explicit_root),
        just_bin="custom-just",
    )

    assert just_obj._root == explicit_root.resolve()
    assert just_obj._just_bin == "custom-just"


def test_session_fixture_auto_discovers_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    nested = root / "a" / "b"
    nested.mkdir(parents=True)
    (root / "justfile").write_text("test:\n    @echo ok\n", encoding="utf-8")

    just_obj = _create_just_fixture(
        rootpath=nested,
        justfile_root=None,
        just_bin="just",
    )

    assert just_obj._root == root.resolve()


def test_session_fixture_raises_when_no_justfile_found(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        _create_just_fixture(
            rootpath=nested,
            justfile_root=None,
            just_bin="just",
        )
