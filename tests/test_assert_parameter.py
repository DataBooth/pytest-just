"""Tests for ``JustfileFixture.assert_parameter`` parameter attribute assertions."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pytest_just import JustfileFixture


pytestmark = pytest.mark.skipif(shutil.which("just") is None, reason="just binary is required")


@pytest.fixture
def jf(tmp_path: Path) -> JustfileFixture:
    """Fixture with flag-annotated parameters."""
    (tmp_path / "justfile").write_text(
        "[arg('interactive', short = 'i', long, value = 'true')]\n"
        "[arg('profile', short = 'p', long)]\n"
        "deploy interactive='' profile='' name='':\n"
        "    @echo {{ interactive }} {{ profile }} {{ name }}\n",
        encoding="utf-8",
    )
    return JustfileFixture(root=tmp_path)


def test_assert_parameter_short(jf: JustfileFixture) -> None:
    """Short flag assertion passes when correct."""
    jf.assert_parameter("deploy", "interactive", short="i")


def test_assert_parameter_long(jf: JustfileFixture) -> None:
    """Long flag assertion passes when correct."""
    jf.assert_parameter("deploy", "profile", long="profile")


def test_assert_parameter_value(jf: JustfileFixture) -> None:
    """Value flag assertion passes when correct."""
    jf.assert_parameter("deploy", "interactive", value="true")


def test_assert_parameter_combined(jf: JustfileFixture) -> None:
    """Multiple flag assertions in one call."""
    jf.assert_parameter("deploy", "interactive", short="i", long="interactive", value="true")


def test_assert_parameter_missing_param(jf: JustfileFixture) -> None:
    """Raises AssertionError for nonexistent parameter."""
    with pytest.raises(AssertionError, match="missing parameter"):
        jf.assert_parameter("deploy", "nonexistent", short="x")


def test_assert_parameter_wrong_short(jf: JustfileFixture) -> None:
    """Raises AssertionError when short flag doesn't match."""
    with pytest.raises(AssertionError, match="expected short"):
        jf.assert_parameter("deploy", "interactive", short="x")


def test_assert_parameter_unexpected_attr(jf: JustfileFixture) -> None:
    """Raises AssertionError for an attribute not in the dump schema."""
    with pytest.raises(AssertionError, match="unexpected attribute"):
        jf.assert_parameter("deploy", "interactive", bogus="x")
