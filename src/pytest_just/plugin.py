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

def _create_just_fixture(rootpath: Path, justfile_root: str | None, just_bin: str) -> JustfileFixture:
    if justfile_root:
        root = Path(justfile_root).resolve()
    else:
        root = _discover_justfile_root(rootpath.resolve())
    return JustfileFixture(root=root, just_bin=just_bin)


@pytest.fixture(scope="session")
def just(pytestconfig: pytest.Config) -> JustfileFixture:
    return _create_just_fixture(
        rootpath=Path(str(pytestconfig.rootpath)),
        justfile_root=pytestconfig.getoption("justfile_root"),
        just_bin=str(pytestconfig.getoption("just_bin")),
    )
