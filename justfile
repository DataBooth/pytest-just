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

