# Release Notes

## Unreleased
### Planned
- Add packaging/publish automation and release checklist guidance.
- Expand property-based coverage for additional contract edges.

## 0.1.0 — 2026-03-22
### Highlights
- Bootstrapped `pytest-just` package structure.
- Added pytest plugin entry point and session-scoped `just` fixture.
- Implemented initial `JustfileFixture` accessor and assertion API.
- Added public-source-inspired example justfiles under `examples/public/`.
- Added example-driven tests validating core fixture behaviour.
- Added `USER_GUIDE.md` and draft project blog post.
- Added property-based tests with `hypothesis` for key invariants.
- Added CI workflow for pull requests and `main` branch pushes.

### Tooling and quality gates
- `uv` for project/dependency management
- `ruff` for linting
- `ty` for type checking
- `pytest` for tests
- `hypothesis` for property-based testing
- `loguru` for logging

### Repository milestones
- `448315e` — initial repository bootstrap
- `256383a` — public justfile examples
- `6752538` — example-driven tests and usage docs
