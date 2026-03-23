# LinkedIn announcement (draft)
I’ve just released **pytest-just v0.1.2**.

`pytest-just` is a pytest plugin that helps teams test `justfile` contracts early and reliably, without over-relying on full command execution.

What it supports:
- recipe existence/dependency/parameter assertions
- rendered command checks with `just --show`
- safe smoke checks with `just --dry-run`
- property-based verification for core invariants using Hypothesis

Built with:
- `uv` for dependency management
- `ruff` + `ty` for quality gates
- GitHub Actions CI on PRs and `main`

If you use `just` in your workflow, I’d value your feedback on what should come next.

Repo: https://github.com/DataBooth/pytest-just
PyPI: https://pypi.org/project/pytest-just/0.1.2/
