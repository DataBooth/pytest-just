from __future__ import annotations

from pathlib import Path

import pytest

from .fixture import JustfileFixture


def _discover_justfile_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "justfile").exists() or (candidate / "Justfile").exists():
            return candidate
    raise FileNotFoundError(
        f"No justfile or Justfile found from {start} upwards. "
        "Pass --justfile-root to specify the directory explicitly."
    )


def pytest_addoption(parser: pytest.Parser) -> None:
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
    config.addinivalue_line("markers", "justfile: marks tests as justfile recipe tests")


@pytest.fixture(scope="session")
def just(pytestconfig: pytest.Config) -> JustfileFixture:
    root_option = pytestconfig.getoption("justfile_root")
    if root_option:
        root = Path(root_option).resolve()
    else:
        root = _discover_justfile_root(Path(str(pytestconfig.rootpath)).resolve())

    just_bin = str(pytestconfig.getoption("just_bin"))
    return JustfileFixture(root=root, just_bin=just_bin)
