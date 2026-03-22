"""Pytest plugin registration and fixture wiring for pytest-just."""

from __future__ import annotations

from pathlib import Path

import pytest

from .fixture import JustfileFixture


def _discover_justfile_root(start: Path) -> Path:
    """Find the nearest ancestor directory containing a justfile."""
    for candidate in (start, *start.parents):
        if (candidate / "justfile").exists() or (candidate / "Justfile").exists():
            return candidate
    raise FileNotFoundError(
        f"No justfile or Justfile found from {start} upwards. "
        "Pass --justfile-root to specify the directory explicitly."
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register command-line options for the plugin."""
    group = parser.getgroup("pytest-just")
    group.addoption(
        "--justfile-root",
        action="store",
        default=None,
        help="Directory containing justfile/Justfile (auto-discovered by default).",
    )
    group.addoption(
        "--just-bin",
        action="store",
        default="just",
        help="Path or command name for the just binary.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register pytest markers used by this plugin."""
    config.addinivalue_line("markers", "justfile: marks tests as justfile recipe tests")


def _create_just_fixture(rootpath: Path, justfile_root: str | None, just_bin: str) -> JustfileFixture:
    """Create a configured session fixture from parsed pytest options."""
    if justfile_root:
        root = Path(justfile_root).resolve()
    else:
        root = _discover_justfile_root(rootpath.resolve())
    return JustfileFixture(root=root, just_bin=just_bin)


@pytest.fixture(scope="session")
def just(pytestconfig: pytest.Config) -> JustfileFixture:
    """Provide a session-scoped ``JustfileFixture`` instance."""
    return _create_just_fixture(
        rootpath=Path(str(pytestconfig.rootpath)),
        justfile_root=pytestconfig.getoption("justfile_root"),
        just_bin=str(pytestconfig.getoption("just_bin")),
    )
