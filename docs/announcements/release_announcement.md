# pytest-just v0.1.0 release announcement (draft)
Today I am releasing `pytest-just` v0.1.0: a pytest plugin for testing `justfile` contracts with fast, side-effect-aware checks.

`pytest-just` focuses on verifying recipe intent and structure:

- recipe existence, dependencies, parameters, aliases, and assignments
- rendered body checks via `just --show`
- safe smoke checks via `just --dry-run` for non-shebang recipes
- clear, explicit error taxonomy for common failure modes

Highlights in this release:

- session-scoped `just` fixture and pytest marker integration
- real-world example corpus under `examples/public/` and `examples/local/`
- documentation in `README.md` and `USER_GUIDE.md`
- property-based tests with Hypothesis for core invariants
- CI checks on pull requests and `main` branch pushes

Repository: https://github.com/DataBooth/pytest-just

Feedback, issues, and contributions are very welcome.
