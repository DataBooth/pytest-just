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

## Plugin usage
The plugin registers:
- a session-scoped `just` fixture (`JustfileFixture`)
- a `justfile` marker

Options:
- `--justfile-root`
- `--just-bin`
