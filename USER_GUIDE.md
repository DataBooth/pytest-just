# pytest-just User Guide
`pytest-just` is a pytest plugin for testing `justfile` contracts.

It helps you catch recipe drift early:
- missing or renamed recipes
- broken dependency chains
- missing parameters
- missing variable threading
- accidental shebang usage in dry-run-safe recipes

## Quick mental model
`pytest-just` tests **justfile contracts**, not the underlying tools.

- It loads one structured snapshot via `just --dump --dump-format json`.
- It checks recipe shape/contracts (exists, deps, params, variables).
- It can use `just --show` for rendered body assertions.
- It can use `just --dry-run` for safe smoke checks.

### Minimal justfile example
```just
no_sync := "--no-sync"

lint:
    uv run ruff check .

test:
    uv run pytest -q

ci: lint test
    @echo "ci checks passed"

deploy ENV:
    @echo "deploying to {{ENV}}"

check:
    uv run ruff check . {{no_sync}}
```

### Minimal pytest example
```python
import pytest

@pytest.mark.justfile
def test_contracts(just):
    just.assert_exists("ci")
    just.assert_depends_on("ci", ["lint", "test"])
    just.assert_parameter("deploy", "ENV")
    just.assert_variable_referenced("check", "no_sync")
```

## What can be tested in isolation?
Short answer: a lot of value can be tested in isolation, but not everything.

### 1) Contract tests (primary use case) ✅
Use `pytest-just` to validate recipe structure and intent:

- recipe exists
- dependency graph is correct
- required parameters are present
- expected command text is present
- variables are threaded through recipe bodies
- shebang vs non-shebang classification

These are fast, stable checks and catch the most common automation regressions.

### 2) Dry-run command shape checks ✅
For non-shebang recipes, you can validate expected command output via dry-run:

```python
@pytest.mark.justfile
def test_test_recipe_dry_run(just):
    result = just.dry_run("test")
    assert result.returncode == 0, result.stderr
    assert "uv run pytest" in (result.stdout + result.stderr)
```

This is useful when you want to assert command composition without executing the real task.

### 3) Full runtime behaviour checks ⚠️
If you need to verify side effects or real script output (for example, files created by `ffmpeg`, Docker behaviour, or external API calls), use separate integration tests that intentionally execute recipes in a controlled environment.

`pytest-just` is designed to test contracts and orchestration, not replace end-to-end execution tests.

### Specialist recipe example (contract-only)
```python
@pytest.mark.justfile
def test_audio_intro_es_contract(just):
    just.assert_exists("audio-intro-es")
    just.assert_body_contains("audio-intro-es", "PIPER_MODEL must be set")
    just.assert_body_contains("audio-intro-es", "generate_intro_audio_piper.py")
    assert just.is_shebang("audio-intro-es")
```

The example above verifies the recipe contract clearly, without invoking the underlying audio tooling.

## 1) Install
This project uses `uv` for dependency management.

```bash
uv sync --extra dev
```

## 2) Run tests
```bash
uv run pytest -q
```

To target justfile-focused tests:
```bash
uv run pytest -m justfile -q
```

## 3) Plugin options
`pytest-just` exposes two CLI options:

- `--justfile-root`: directory containing `justfile` or `Justfile`
- `--just-bin`: executable path/name for `just` (default: `just`)

Example:
```bash
uv run pytest -q --justfile-root examples/public/actix-web --just-bin just
```

If `--justfile-root` is not provided, the plugin walks upward from the pytest root directory until it finds `justfile` or `Justfile`.

## 4) The `just` fixture
The plugin registers a **session-scoped** fixture named `just`:

```python
def test_recipe_exists(just):
    just.assert_exists("test")
```

Session scope means the JSON dump is loaded once per test run.

## 5) Accessor API
Useful accessors on `JustfileFixture`:

- `recipe_names(include_private=False)`
- `dependencies(recipe)`
- `parameters(recipe)`
- `parameter_names(recipe)`
- `is_private(recipe)`
- `is_shebang(recipe)`
- `doc(recipe)`
- `body(recipe)`
- `show(recipe)`
- `assignments()`
- `aliases()`

## 6) Assertion API
These methods are designed for concise tests:

- `assert_exists(recipe)`
- `assert_depends_on(recipe, expected, transitive=False)`
- `assert_parameter(recipe, parameter)`
- `assert_body_contains(recipe, text)`
- `assert_not_shebang(recipe)`
- `assert_variable_referenced(recipe, variable)`
- `assert_dry_run_contains(recipe, text, *args, env=None)`

## 7) Dry-run smoke checks
Use `dry_run` to verify command shape safely:

```python
def test_check_recipe_is_dry_run_safe(just):
    result = just.dry_run("check")
    assert result.returncode == 0, result.stderr
```

`dry_run` rejects shebang recipes because they can still execute interpreters even in dry-run mode.

## 8) Public examples
Sample justfiles are included under:

- `examples/public/async-compression`
- `examples/public/actix-web`
- `examples/public/martin`

These are useful for:
- regression tests
- API behaviour checks
- parser compatibility checks across real-world syntax patterns

## 9) Recommended development loop
```bash
uv sync --extra dev
uv run ruff check .
uv run ty check
uv run pytest -q
```
## 10) Property-based testing with Hypothesis
In addition to example-driven tests, `pytest-just` uses Hypothesis to generate varied inputs and verify invariants.

Current property checks cover:

- root discovery across arbitrarily nested directories
- idempotence of recipe body normalisation
- recipe signature stability when dependency/parameter order changes
- alias and assignment extraction contracts for valid dump payloads

Run only property tests:
```bash
uv run pytest -q tests/test_hypothesis_properties.py
```

Show generated-case statistics:
```bash
uv run pytest -q --hypothesis-show-statistics
```

If a property test fails, Hypothesis will shrink the failing input to a minimal reproducible example.

## 11) Troubleshooting
### `just` not found
Install `just` and/or pass `--just-bin`.

### Parse failure from `--dump`
Ensure your `just` version supports JSON dump (`>= 1.13`) and the target justfile parses cleanly.

### Recipe not found errors
Check whether the recipe is private and whether your assertion is using the expected name (not alias).
