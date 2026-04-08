"""Tests for ``JustfileFixture`` module-aware recipe resolution."""

from __future__ import annotations

import shutil
from textwrap import dedent
from pathlib import Path

import pytest

from pytest_just import JustfileFixture
from pytest_just.errors import UnknownRecipeError


pytestmark = pytest.mark.skipif(shutil.which("just") is None, reason="just binary is required")


@pytest.fixture
def module_tree(tmp_path: Path) -> JustfileFixture:
    """Justfile with a module and submodule."""
    (tmp_path / "justfile").write_text(dedent("""
        mod infra
        
        root:
            @echo root
    """), encoding="utf-8")
    mod = tmp_path / "infra"
    mod.mkdir()
    (mod / "mod.just").write_text(dedent("""
        mod deploy
        
        _require-infra:
            @true
        
        status: _require-infra
            @echo ok
    """), encoding="utf-8")
    sub = mod / "deploy"
    sub.mkdir()
    (sub / "mod.just").write_text(dedent("""
        [private]
        up profile='default': _require-deploy
            @echo up {{ profile }}
        
        _require-deploy:
            @true
    """), encoding="utf-8")
    return JustfileFixture(root=tmp_path)


def test_recipes_flattened_by_namepath(module_tree: JustfileFixture) -> None:
    """Recipes from modules appear keyed by full namepath."""
    names = module_tree.recipe_names(include_private=True)
    assert "root" in names
    assert "infra::status" in names
    assert "infra::_require-infra" in names
    assert "infra::deploy::up" in names
    assert "infra::deploy::_require-deploy" in names


def test_is_private_with_namepath(module_tree: JustfileFixture) -> None:
    """Privacy checks work with full module paths."""
    assert not module_tree.is_private("root")
    assert not module_tree.is_private("infra::status")
    assert module_tree.is_private("infra::_require-infra")
    assert module_tree.is_private("infra::deploy::up")


def test_dependencies_with_namepath(module_tree: JustfileFixture) -> None:
    """Dependency inspection works with full module paths.

    Note: just stores dependency names as module-local names (not namepaths),
    so dependencies() returns local names like ``_require-infra``.
    """
    assert "_require-infra" in module_tree.dependencies("infra::status")
    assert "_require-deploy" in module_tree.dependencies("infra::deploy::up")


def test_parameters_with_namepath(module_tree: JustfileFixture) -> None:
    """Parameter inspection works with full module paths."""
    assert "profile" in module_tree.parameter_names("infra::deploy::up")


def test_unknown_namepath_raises(module_tree: JustfileFixture) -> None:
    """Unknown namepath raises UnknownRecipeError."""
    with pytest.raises(UnknownRecipeError):
        module_tree.dependencies("infra::nonexistent")


def test_module_namepaths(module_tree: JustfileFixture) -> None:
    """module_namepaths discovers module paths from the dump."""
    assert "infra" in module_tree.module_namepaths
    assert "infra::deploy" in module_tree.module_namepaths


def test_recipe_names_excludes_private_by_default(module_tree: JustfileFixture) -> None:
    """Public recipe listing excludes private recipes across modules."""
    public = module_tree.recipe_names()
    assert "infra::status" in public
    assert "infra::_require-infra" not in public
    assert "infra::deploy::up" not in public  # marked [private]


def test_flatten_static_method() -> None:
    """_flatten works as a standalone static method."""
    dump = {
        "recipes": {
            "root": {"namepath": "root", "private": False},
        },
        "modules": {
            "foo": {
                "recipes": {
                    "bar": {"namepath": "foo::bar", "private": False},
                },
                "modules": {
                    "baz": {
                        "recipes": {
                            "qux": {"namepath": "foo::baz::qux", "private": True},
                        },
                        "modules": {},
                    }
                },
            }
        },
    }

    result = JustfileFixture._flatten(dump)
    recipes = result["recipes"]
    assert set(recipes.keys()) == {"root", "foo::bar", "foo::baz::qux"}
    assert recipes["root"]["private"] is False
    assert recipes["foo::bar"]["private"] is False
    assert recipes["foo::baz::qux"]["private"] is True
    assert result["modules"] == ["foo", "foo::baz"]
