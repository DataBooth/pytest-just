# Draft: Introducing `pytest-just` — contract testing for `justfile` workflows

## Why this exists
Many teams rely on `just` for everyday workflows: test, lint, build, release, and local runbooks.

That is great for consistency, but it creates an overlooked risk: automation drift.

When a recipe name changes, a dependency chain shifts, or a parameter contract is updated, teams often find out late — in CI failures, broken local workflows, or release friction.

Traditional tests usually validate tools (`pytest`, `ruff`, application code), not orchestration contracts in the `justfile` itself.

`pytest-just` exists to test that orchestration layer directly.

## What `pytest-just` is
`pytest-just` is a pytest plugin that adds a session-scoped `just` fixture for asserting `justfile` contracts as code.

It supports checks such as:

- recipe existence
- dependency expectations
- parameter presence
- rendered body content
- alias and assignment extraction
- safe dry-run command checks

## How it works
`pytest-just` uses `just` itself as the source of truth, rather than re-implementing justfile parsing.

It relies on:

- `just --dump --dump-format json` for structured metadata
- `just --show <recipe>` for rendered command assertions
- `just --dry-run <recipe>` for safe smoke checks

This keeps tests fast, practical, and close to real behaviour.

## Example
```python
import pytest

@pytest.mark.justfile
def test_ci_contract(just):
    just.assert_exists("ci")
    just.assert_depends_on("ci", ["test"], transitive=True)
```

## What this enables in practice

- earlier feedback on automation regressions
- clearer ownership of workflow contracts
- safer refactors of team runbooks
- better confidence in multi-maintainer repositories

In plain terms: `just` keeps repeatable team tasks in one place, and `pytest-just` helps ensure those tasks keep working as your project evolves.

## Current release status
`pytest-just` is now published:

- PyPI: https://pypi.org/project/pytest-just/0.1.2/
- Source: https://github.com/DataBooth/pytest-just
- Release: https://github.com/DataBooth/pytest-just/releases/tag/v0.1.2

Current quality gates include:

- `uv` for dependency management
- `ruff` and `ty` checks
- example-driven tests
- property-based tests using Hypothesis
- GitHub Actions CI

## Experimental work in progress
There is also experimental DuckDB-based recipe corpus tooling for analysing reusable just recipes across repositories.

This is currently WIP and not yet a stable public API.

## Closing
If your team depends on `justfile` automation, treat it like production infrastructure and test it accordingly.

That is the goal of `pytest-just`: make contract testing for automation simple, fast, and maintainable.
