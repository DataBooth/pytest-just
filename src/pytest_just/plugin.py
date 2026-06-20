"""Pytest plugin registration and fixture wiring for pytest-just."""

from __future__ import annotations

from pathlib import Path

import pytest

from .fixture import JustfileFixture


def _discover_justfile_root(start: Path, stop_at: Path | None = None) -> Path:
    """Find the nearest ancestor directory containing a justfile.

    Parameters
    ----------
    start
        Directory to start searching from.
    stop_at
        Optional upper boundary (inclusive) to stop walking at.
    """
    stop_resolved = stop_at.resolve() if stop_at is not None else None
    for candidate in (start, *start.parents):
        if (candidate / "justfile").exists() or (candidate / "Justfile").exists():
            return candidate
        if stop_resolved is not None and candidate.resolve() == stop_resolved:
            break
    raise FileNotFoundError(
        f"No justfile or Justfile found from {start} upwards"
        + (f" (stopped at {stop_at})" if stop_at is not None else "")
        + ". "
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


def _create_just_fixture(
    rootpath: Path,
    justfile_root: str | None,
    just_bin: str,
    discovery_stop_at: Path | None = None,
) -> JustfileFixture:
    """Create a configured session fixture from parsed pytest options."""
    if justfile_root:
        root = Path(justfile_root).resolve()
    else:
        root = _discover_justfile_root(rootpath.resolve(), stop_at=discovery_stop_at)
    return JustfileFixture(root=root, just_bin=just_bin)


@pytest.fixture(scope="session")
def just(pytestconfig: pytest.Config) -> JustfileFixture:
    """Provide a session-scoped ``JustfileFixture`` instance."""
    return _create_just_fixture(
        rootpath=Path(str(pytestconfig.rootpath)),
        justfile_root=pytestconfig.getoption("justfile_root"),
        just_bin=str(pytestconfig.getoption("just_bin")),
    )
