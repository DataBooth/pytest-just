# Set the default shell for commands
set shell := ["bash", "-c"]

# Variables
RUST_LOG := ".ruff-warn"  # Suppress verbose logging by default
SRC_DIR := "src"          # Directory containing your Python source code (adjust as needed)

# Default recipe (lists available recipes)
default:
    @just --list

# Recipe to check code with Ruff
[no-exit-message]
check:
    @echo "Running Ruff checks..."
    RUST_LOG={{RUST_LOG}} ruff check {{SRC_DIR}}

# Recipe to fix fixable issues with Ruff
[no-exit-message]
fix:
    @echo "Fixing issues with Ruff..."
    RUST_LOG={{RUST_LOG}} ruff check --fix {{SRC_DIR}}

# Recipe to show a diff of proposed fixes (dry-run)
diff:
    @echo "Showing Ruff fixes as a diff (dry-run)..."
    RUST_LOG={{RUST_LOG}} ruff check --diff {{SRC_DIR}}

# Recipe to lint all files, including excluded ones
lint-all:
    @echo "Running Ruff on all files (ignoring excludes)..."
    RUST_LOG={{RUST_LOG}} ruff check --force-exclude {{SRC_DIR}}

# Recipe to run Ruff with a specific configuration file
config-check CONFIG_FILE="pyproject.toml":
    @echo "Running Ruff with config: {{CONFIG_FILE}}..."
    RUST_LOG={{RUST_LOG}} ruff check --config {{CONFIG_FILE}} {{SRC_DIR}}

# Recipe to format files using Ruff's formatter
format:
    @echo "Formatting code with Ruff..."
    RUST_LOG={{RUST_LOG}} ruff format {{SRC_DIR}}
