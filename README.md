# pytest-just
A pytest plugin for testing justfiles.
[![CI](https://github.com/DataBooth/pytest-just/actions/workflows/ci.yml/badge.svg)](https://github.com/DataBooth/pytest-just/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/pytest-just.svg)](https://pypi.org/project/pytest-just/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytest-just.svg)](https://pypi.org/project/pytest-just/)
[![License: MIT](https://img.shields.io/pypi/l/pytest-just.svg)](https://github.com/DataBooth/pytest-just/blob/main/LICENSE)

## Package status
`pytest-just` is published on PyPI.

- PyPI: https://pypi.org/project/pytest-just/
- Source: https://github.com/DataBooth/pytest-just
- Latest release notes: `RELEASE_NOTES.md`
## What is pytest-just?
`pytest-just` is a plugin that adds a session-scoped `just` fixture to pytest so you can test `justfile` contracts directly in your test suite.

It is designed for assertions about recipe structure and intent, including:

- recipe existence
- dependency relationships
- parameter contracts
- rendered body content
- alias and assignment mapping

## Why use pytest-just?
As projects grow, `justfile` automation often becomes critical but under-tested. Small recipe changes can quietly break CI, local developer workflows, or release steps.

`pytest-just` helps by making contract checks:

- fast
- repeatable
- easy to run in CI
- explicit in code review

This catches automation drift early without requiring full end-to-end execution of every command.

## Tooling
- Package and commands: `uv`
- Lint/format checks: `ruff`
- Type checks: `ty`
- Logging: `loguru`
## Install from PyPI
Add `pytest-just` to your test dependencies:

```bash
uv add --dev pytest-just
```

You also need the `just` binary available in your environment:

```bash
just --version
```

## Quick start (package usage)
Create tests that use the plugin fixture:

```python
import pytest

@pytest.mark.justfile
def test_ci_depends_on_test(just):
    just.assert_exists("ci")
    just.assert_depends_on("ci", ["test"], transitive=True)
```

Run:
```bash
uv run pytest -q
```
## How does pytest-just work?
`pytest-just` primarily validates recipe contracts instead of running full recipe side effects. It asks `just` for structured metadata and rendered recipe text:

- `just --dump --dump-format json` for recipe graph, parameters, attributes, aliases, and assignments
- `just --show <recipe>` for rendered body text checks
- `just --dry-run <recipe>` for safe command smoke checks
This keeps tests fast and mostly side-effect free while still validating real justfile behaviour.

## Plugin behaviour
The plugin registers:
- a session-scoped `just` fixture (`JustfileFixture`)
- a `justfile` marker

CLI options:
- `--justfile-root`: directory containing `justfile`/`Justfile` (auto-discovered by default)
- `--just-bin`: path or name of the `just` binary (default: `just`)

Auto-discovery walks upwards from `pytest` root until it finds `justfile` or `Justfile`.

## API summary (`JustfileFixture`)
Primary accessors:
- `recipe_names(include_private=False)`
- `dependencies(recipe)`
- `parameters(recipe)` / `parameter_names(recipe)`
- `is_shebang(recipe)` / `is_private(recipe)`
- `doc(recipe)` / `body(recipe)` / `show(recipe)`
- `assignments()` / `aliases()`

Assertions:
- `assert_exists(recipe)`
- `assert_depends_on(recipe, expected, transitive=False)`
- `assert_parameter(recipe, parameter)`
- `assert_body_contains(recipe, text)`
- `assert_not_shebang(recipe)`
- `assert_variable_referenced(recipe, variable)`

Execution support:
- `dry_run(recipe, *args, env=None)` returns `subprocess.CompletedProcess[str]`

## Example usage
```python
import pytest

@pytest.mark.justfile
def test_ci_depends_on_test(just):
    just.assert_exists("ci")
    just.assert_depends_on("ci", ["test"], transitive=True)
```

## Example justfiles for development
Sample real-world-inspired justfiles live under `examples/public/` and include:
- dependency chains
- private recipes
- parameterised recipes
- shebang recipes
- imported justfiles

Use them to exercise fixture behaviour while developing the plugin.

## Development workflow
If you are contributing to this repository:
```bash
uv sync --extra dev
uv run ruff check .
uv run ty check
uv run pytest -q
```

## Property-based testing (Hypothesis)
The test suite includes property-based tests using `hypothesis` to stress stable invariants such as:

- justfile root discovery across varying directory depth
- body normalisation idempotence
- recipe signature order invariance
- alias and assignment mapping round-trip behaviour

Run only property tests:
```bash
uv run pytest -q tests/test_hypothesis_properties.py
```

Show Hypothesis run statistics:
```bash
uv run pytest -q --hypothesis-show-statistics
```

## CI
GitHub Actions runs on pull requests and pushes to `main`, executing:

- `uv run ruff check .`
- `uv run ty check`
- `uv run pytest -q --hypothesis-show-statistics`
