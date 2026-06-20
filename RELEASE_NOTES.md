# Release Notes

## Unreleased
### Planned
- Add packaging/publish automation and release checklist guidance.
- Expand property-based coverage for additional contract edges.
## 0.1.3 — 2026-06-20
### Highlights
- Added Great Docs configuration and contributor documentation guidance.
- Added a dedicated docs workflow for GitHub Pages builds and deployments.
- Added `just` recipes for docs build, preview, scan, and link-check workflows.
- Added a prepublish link-check profile and documented strict-profile follow-up work.
- Kept package runtime support at Python 3.10 while scoping docs tooling to Python 3.11+.
- Added an optional discovery boundary for justfile root lookup and used it in tmp-path tests to avoid false passes/failures from ancestor justfiles outside the test sandbox.

## 0.1.2 — 2026-03-22
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
