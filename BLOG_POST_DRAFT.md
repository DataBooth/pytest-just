# Draft: Introducing `pytest-just` — Contract Testing for justfiles

## What
`pytest-just` is a pytest plugin that lets teams test their `justfile` as first-class infrastructure.

Most projects rely on `just` recipes for development, CI, release, and local automation. But recipe behaviour often lives in an untested gap between docs and scripts. `pytest-just` closes that gap by turning recipe expectations into executable tests.

## Why
`justfile` regressions are common and subtle:

- a recipe is renamed or removed
- dependencies drift (`dev` no longer calls `lint`)
- parameters silently change
- variable threading breaks between recipes
- command bodies change in ways that invalidate team conventions

Traditional unit/integration tests do not catch these issues because they test tools (`pytest`, `ruff`, `cargo`, etc.), not orchestration contracts in the justfile itself.

`pytest-just` focuses directly on those contracts.

## How
The core design principle is simple: use `just` itself as the source of truth.

`pytest-just` reads:
- `just --dump --dump-format json` for structured recipe metadata
- `just --show <recipe>` for rendered command text checks
- `just --dry-run <recipe>` for safe smoke validation

This avoids reimplementing the justfile grammar and keeps tests side-effect light.

### Example
```python
import pytest

@pytest.mark.justfile
def test_ci_contract(just):
    just.assert_exists("ci")
    just.assert_depends_on("ci", ["test"], transitive=True)
```

### What this enables
- fast feedback for recipe drift
- readable, intention-focused tests
- safer refactoring of automation workflows
- confidence for multi-maintainer repos where justfiles are shared infrastructure

## Current status
The project currently includes:
- package scaffold and plugin wiring
- initial fixture API
- sample real-world justfiles for compatibility testing
- example-driven test suite
- `uv` + `ruff` + `ty` development workflow

## Next
Near-term roadmap:
1. tighten API contracts and error taxonomy
2. deepen edge-case coverage (schema drift, aliases, import collisions)
3. finalise CI and publish pipeline
4. cut the first tagged release

## Closing
If your team treats `justfile` as critical build and delivery infrastructure, it deserves tests. `pytest-just` is designed to make that practical, fast, and maintainable.
