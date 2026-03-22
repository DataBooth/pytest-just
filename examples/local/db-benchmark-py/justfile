# Cross-platform task runner for db-benchmark-py
# Requires: just (cross-platform), uv (Python), R (for original functionality)

# Cross-platform settings (just uses system defaults)
# Windows: cmd.exe, Unix: sh

# Default Python command - use python3 for explicit version
python := "python3"

# Default recipe - show help
default:
    just --list

# === Modern Python Development ===

# Install development environment
setup:
    @echo "Setting up development environment..."
    uv sync --extra dev --extra reporting
    @echo "✅ Setup complete! Run 'just test-setup' to verify"

# Test the development setup
test-setup:
    @echo "Testing Python package installation..."
    uv run db-benchmark
    @echo "Testing core dependencies..."
    uv run python -c "import pandas, polars, psutil, rich, typer; print('✅ All core dependencies working')"
    @echo "✅ Development setup verified!"

# Run Python linting and type checking
lint:
    @echo "Running linting and type checks..."
    uv run ruff check .
    uv run mypy src/

# Format code
fmt:
    @echo "Formatting code..."
    uv run ruff format .

# Run Python tests
test:
    uv run pytest

# === Original Benchmark Functionality ===

# Check if R is available and working
check-r:
    @echo "Checking R installation..."
    {{python}} -c "import subprocess; subprocess.run(['R', '--version'], check=True)"
    @echo "Testing data.table availability..."
    Rscript -e "library('data.table'); cat('✅ R and data.table working\n')"

# Generate test data using original R script
generate-data-r nrows="1e6" k="1e2" na="0" sort="0":
    @echo "Generating {{nrows}} rows with original R script..."
    @mkdir -p data || echo "data directory exists"
    Rscript _data/groupby-datagen.R {{nrows}} {{k}} {{na}} {{sort}}
    @echo "Moving generated data to data/ directory..."
    @if [ "{{os()}}" = "windows" ]; then \
        powershell -c "if (Test-Path 'G1_{{nrows}}_{{k}}_{{na}}_{{sort}}.csv') { Move-Item 'G1_{{nrows}}_{{k}}_{{na}}_{{sort}}.csv' 'data/' }"; \
    else \
        [ -f "G1_{{nrows}}_{{k}}_{{na}}_{{sort}}.csv" ] && mv "G1_{{nrows}}_{{k}}_{{na}}_{{sort}}.csv" data/ || echo "File already in place"; \
    fi
    @echo "✅ Data generation complete: data/G1_{{nrows}}_{{k}}_{{na}}_{{sort}}.csv"

# List generated datasets
list-data:
    @echo "Generated datasets in data/ directory:"
    @if [ "{{os()}}" = "windows" ]; then \
        powershell -c "if (Test-Path 'data') { Get-ChildItem data/*.csv | ForEach-Object { '  ' + $_.Name } } else { 'No data directory found' }"; \
    else \
        if [ -d "data" ]; then ls -1 data/*.csv 2>/dev/null | sed 's|^|  |' || echo "  No CSV files found"; else echo "  No data directory found"; fi; \
    fi

# Run a single solution benchmark (original R launcher)
run-original-single solution="pandas" task="groupby" nrow="1e6":
    @echo "Running {{solution}} {{task}} benchmark on {{nrow}} rows..."
    ./_launcher/solution.R --solution={{solution}} --task={{task}} --nrow={{nrow}} --quiet=false

# Check original benchmark environment
check-original:
    @echo "Checking original benchmark prerequisites..."
    @echo "1. Checking R installation:"
    just check-r
    @echo "2. Checking swap status:"
    @if [ "{{os()}}" = "windows" ]; then \
        powershell -c "Get-WmiObject -Class Win32_PageFileUsage | Format-Table Name, CurrentUsage"; \
    else \
        free -h | grep -i swap || echo "free command not available"; \
    fi
    @echo "3. Checking solution directories:"
    @echo "  Available solutions:"
    @if [ "{{os()}}" = "windows" ]; then \
        powershell -c "Get-ChildItem -Directory | Where-Object { $_.Name -match '^[a-z]' } | ForEach-Object { '    ' + $_.Name }"; \
    else \
        find . -maxdepth 1 -type d -name "[a-z]*" | sort | sed 's|^\./|    |'; \
    fi
    @echo "✅ Original benchmark environment check complete"

# === Development Utilities ===

# Clean generated files and caches
clean:
    @echo "Cleaning generated files..."
    @if [ "{{os()}}" = "windows" ]; then \
        powershell -c "Remove-Item -Recurse -Force .pytest_cache, __pycache__, '*.pyc' -ErrorAction SilentlyContinue"; \
    else \
        rm -rf .pytest_cache __pycache__ **/__pycache__ **/*.pyc; \
    fi
    @echo "✅ Cleanup complete"

# Show system information
system-info:
    @echo "System Information:"
    @echo "  OS: {{os()}}"
    @echo "  Architecture: {{arch()}}"
    @echo "  Python version:"
    uv run python --version | sed 's/^/    /'
    @echo "  UV version:"
    uv --version | sed 's/^/    /'
    @echo "  Just version:"
    just --version | sed 's/^/    /'
    @if command -v R >/dev/null 2>&1; then \
        echo "  R version:"; \
        R --version | head -1 | sed 's/^/    /'; \
    else \
        echo "  R: Not installed"; \
    fi

# === Testing and Validation ===

# Full development test suite
test-all: test-setup lint test
    @echo "✅ All tests passed!"

# Quick smoke test of key functionality
smoke-test:
    @echo "Running smoke tests..."
    just test-setup
    just check-r
    just generate-data-r 1e4 1e1 0 0  # Small dataset for testing
    just list-data
    @echo "✅ Smoke test complete - basic functionality verified!"

# === Future Python Implementation (Placeholders) ===

# Generate data using Python (coming in Phase 2)
generate-data-python size="1e6":
    @echo "🚧 Python data generation not yet implemented"
    @echo "Will generate {{size}} rows using Python..."
    @echo "For now, use: just generate-data-r {{size}}"

# Run Python-only benchmarks (coming in Phase 2)
run-python solutions="pandas,polars":
    @echo "🚧 Python benchmark runner not yet implemented"
    @echo "Will run solutions: {{solutions}}"
    @echo "For now, use original: just run-original-single <solution>"