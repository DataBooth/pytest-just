# Default: Show available commands
default:
    just --list

# Kill any process holding a lock on yellow_taxi.duckdb
kill-duckdb:
    lsof -t yellow_taxi.duckdb | xargs -r kill || true

# Launch DuckDB UI after ensuring no lock
duckdb-ui database="yellow_taxi.duckdb":
    just kill-duckdb
    duckdb --ui {{database}}


# SQLMesh: Create a new plan (with auto-apply)
plan:
    sqlmesh plan --auto-apply

# SQLMesh: Run all models
run:
    sqlmesh run

# SQLMesh: Format all SQL models
format:
    sqlmesh format

# SQLMesh: Lint all SQL models
lint:
    sqlmesh lint

# SQLMesh: Clean all SQLMesh state
clean:
    sqlmesh clean

# SQLMesh: List all models
list-models:
    sqlmesh models

# SQLMesh: Preview a model (replace <model> with your model name)
preview model:
    sqlmesh preview {{model}}

# SQLMesh: Evaluate a model (replace <model> with your model name)
evaluate model:
    sqlmesh evaluate {{model}}

# SQLMesh: Run audits
audit:
    sqlmesh audit

# SQLMesh: Generate a DAG visualization
dag:
    sqlmesh dag
