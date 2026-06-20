"""Tests for ``JustfileFixture.dry_run`` across all recipe types."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pytest_just import JustfileFixture


pytestmark = pytest.mark.skipif(shutil.which("just") is None, reason="just binary is required")


@pytest.fixture
def linewise(tmp_path: Path) -> JustfileFixture:
    """Justfile with a linewise recipe."""
    (tmp_path / "justfile").write_text(
        "greet name='world':\n"
        "    echo hello {{ name }}\n",
        encoding="utf-8",
    )
    return JustfileFixture(root=tmp_path)


@pytest.fixture
def shebang(tmp_path: Path) -> JustfileFixture:
    """Justfile with a shebang recipe."""
    (tmp_path / "justfile").write_text(
        "deploy:\n"
        "    #!/usr/bin/env bash\n"
        "    echo deploying\n",
        encoding="utf-8",
    )
    return JustfileFixture(root=tmp_path)


@pytest.fixture
def script(tmp_path: Path) -> JustfileFixture:
    """Justfile with a [script] recipe."""
    (tmp_path / "justfile").write_text(
        "[script]\n"
        "check target='all':\n"
        "    echo checking {{ target }}\n"
        "    echo done\n",
        encoding="utf-8",
    )
    return JustfileFixture(root=tmp_path)


def test_dry_run_linewise(linewise: JustfileFixture) -> None:
    """Linewise dry-run resolves variables and prints commands."""
    result = linewise.dry_run("greet")
    assert result.returncode == 0
    assert "echo hello world" in result.stderr


def test_dry_run_shebang(shebang: JustfileFixture) -> None:
    """Shebang dry-run prints the script body without executing."""
    result = shebang.dry_run("deploy")
    assert result.returncode == 0
    assert "echo deploying" in result.stderr


def test_dry_run_script(script: JustfileFixture) -> None:
    """[script] dry-run resolves variables and prints the script body."""
    result = script.dry_run("check")
    assert result.returncode == 0
    assert "checking all" in result.stderr


def test_dry_run_with_args(linewise: JustfileFixture) -> None:
    """Arguments are interpolated into the dry-run output."""
    result = linewise.dry_run("greet", "alice")
    assert result.returncode == 0
    assert "echo hello alice" in result.stderr
