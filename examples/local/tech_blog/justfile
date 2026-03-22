# justfile example recipes

# Set default shell
set shell := ["bash", "-cu"]

# Default recipe: lists all available recipes
default:
    @just --list

# Example DuckDB recipes

query-duckdb db="my_database.duckdb" table="my_table":
    # Executes a SQL query on a DuckDB database
    duckdb {{db}} -c "SELECT * FROM {{table}} LIMIT 10;"

load-csv-to-duckdb db="my_database.duckdb" csv="data.csv" table="my_table":
    # Loads a CSV file into a DuckDB table
    duckdb {{db}} -c "CREATE TABLE IF NOT EXISTS {{table}} AS SELECT * FROM read_csv('{{csv}}');"


# Git commands
git-status:
    # Shows the current git status
    git status

git-pull:
    # Pulls the latest changes from the remote repository
    git pull origin main

git-push message="Update":
    # Commits and pushes changes to the remote repository
    git add .
    git commit -m "{{message}}"
    git push origin main

git-checkout branch="main":
    # Checks out a specific branch
    git checkout {{branch}}
