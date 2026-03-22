# pytest-just
A pytest plugin for testing justfiles.

## Status
Early-stage project scaffold based on `SPEC.md`.

## Goals
- Test recipe existence, dependencies, parameters, and body content.
- Validate variable threading using `just --dump --dump-format json`.
- Support safe smoke checks with `just --dry-run`.

## Tooling
- Package and commands: `uv`
- Lint/format checks: `ruff`
- Type checks: `ty`
- Logging: `loguru`

## Quick start
```bash
uv sync
uv run pytest
```
## How it works
`pytest-just` does not execute recipes directly. Instead, it asks `just` for structured metadata and rendered recipe text:

- `just --dump --dump-format json` for recipe graph, parameters, attributes, aliases, and assignments
- `just --show <recipe>` for rendered body text checks
- `just --dry-run <recipe>` for safe command smoke checks

This keeps tests fast and side-effect free while still validating justfile contracts.

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
