# Default: List all available recipes
default:
    @just --list


# Run dagster job
dagrun:
    dagster dev -f taxi_pipeline_native.py

# Start Dagster webserver (Dagit UI)
dagit:
    dagster webserver

# Run all Dagster jobs/assets (materialize everything)
materialise:
    python -c "from my_project import defs; from dagster import materialize; materialize(defs.assets)"

# Run pytest-based tests
test:
    pytest tests/

# Lint Python code with ruff
lint:
    ruff .

# Remove generated data and artifacts
clean:
    rm -rf data/nyc_taxi.duckdb data/nyc_taxi_export.parquet .pytest_cache

# Show Dagster asset graph (if using Dagster CLI)
asset-graph:
    dagster asset graph

# Show Dagster version
dag-version:
    dagster --version



# dagster project from-example --name my-tmp-dagster-project --example assets_pandas_pyspark