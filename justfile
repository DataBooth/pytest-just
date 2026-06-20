default:
    @just --list

# Development workflows
setup:
    uv sync --all-extras

lint:
    uv run ruff check .

typecheck:
    uv run ty check

test:
    uv run pytest -q

check: lint typecheck test

# Documentation workflows (Great Docs)
docs-init:
    uv run great-docs init

docs-build:
    uv run great-docs build

docs-preview:
    uv run great-docs preview

docs-scan:
    uv run great-docs scan --verbose

docs-setup-pages:
    uv run great-docs setup-github-pages --main-branch main --python-version 3.12 --package-manager uv

# Prepublish profile: temporarily ignore the future live docs URL and current generated source-link mismatch URLs.
docs-check-links:
    uv run great-docs check-links --docs-only -i "https://databooth.github.io/pytest-just/.*" -i "https://github.com/DataBooth/pytest-just/blob/main/pytest_just/.*"

# Strict profile: no temporary ignores.
docs-check-links-strict:
    uv run great-docs check-links --docs-only

docs-workflow:
    just docs-build
    just docs-check-links

docs-workflow-strict:
    just docs-build
    just docs-check-links-strict

# Toolkit corpus workflows
corpus-build:
    uv run python scripts/build_recipe_db.py build

corpus-list-queries:
    uv run python scripts/build_recipe_db.py list-queries

corpus-query query_name="top_recipe_names" limit="25":
    uv run python scripts/build_recipe_db.py query {{query_name}} --limit {{limit}} --format markdown

corpus-lint:
    uv run python scripts/build_recipe_db.py lint --format markdown

corpus-refactor-plan:
    uv run python scripts/build_recipe_db.py refactor --format markdown

corpus-refactor-apply:
    uv run python scripts/build_recipe_db.py refactor --apply --format markdown

corpus-refactor-apply-no-validate:
    uv run python scripts/build_recipe_db.py refactor --apply --no-validate --format markdown

demo-workflow:
    just corpus-build
    just corpus-query
    just corpus-lint
    just corpus-refactor-plan
