# LinkedIn announcement (draft)
I’ve released **pytest-just v0.1.2**.

Why this matters:

`just` is one of the cleanest ways to organise repeatable development and delivery tasks (test, lint, build, release) behind simple, memorable commands.  
Instead of scattered scripts and tribal knowledge, teams get one visible task interface that is easier to onboard to, review, and maintain.

The challenge is that automation itself can drift quietly as projects change.

`pytest-just` is a pytest plugin that helps teams test `justfile` contracts early and reliably, without over-relying on full command execution.  
In plain terms: it helps ensure your team’s shared task commands keep working as the project evolves.

What it supports:
- recipe existence/dependency/parameter assertions
- rendered command checks with `just --show`
- safe smoke checks with `just --dry-run`
- property-based verification for core invariants using Hypothesis

Built with:
- `uv` for dependency management
- `ruff` + `ty` for quality gates
- GitHub Actions CI on PRs and `main`

If you use `just` in your workflow, I’d value feedback on what would make this most useful for your team.

Repo: https://github.com/DataBooth/pytest-just
PyPI: https://pypi.org/project/pytest-just/0.1.2/
