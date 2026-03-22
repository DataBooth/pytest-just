# Release Notes

## Unreleased
### Highlights
- Bootstrapped `pytest-just` package structure.
- Added pytest plugin entry point and session-scoped `just` fixture.
- Implemented initial `JustfileFixture` accessor and assertion API.
- Added public-source-inspired example justfiles under `examples/public/`.
- Added example-driven tests validating core fixture behaviour.
- Added `USER_GUIDE.md` and draft project blog post.

### Tooling and quality gates
- `uv` for project/dependency management
- `ruff` for linting
- `ty` for type checking
- `pytest` for tests
- `loguru` for logging

### Repository milestones
- `448315e` — initial repository bootstrap
- `256383a` — public justfile examples
- `6752538` — example-driven tests and usage docs

### Known limitations
- The specification still contains a few reconstructed/truncated sections from screenshot source material.
- API contract semantics are still being tightened for exact dependency matching and explicit error taxonomy.
- CI/release automation is in progress.
