# Marimo multi-target build/publish

# List all available recipes (default)
default:
    just --list

# Build site for all enabled targets
build:
    uv run build.py

# Build site for testing target only
build-testing template="databooth.html.j2":
    uv run build.py --target testing --template {{template}}

# Serve the testing site locally (using Python's http.server)
serve-testing:
    uv run python -m http.server -d _site/testing

# Serve the main site locally (default _site)
serve:
    uv run python -m http.server -d _site

# Clean all generated site directories
clean:
    rm -rf _site

## Marimo-specific commands

# Add a new Marimo app
mo-app notebook:
    uv run marimo run {{notebook}}

# Open Marimo notebook in editable mode
mo-edit notebook:
    uv run marimo edit {{notebook}}

# Create and open a new Marimo notebook
mo-new:
    uv run marimo new

# Install Python dependencies (pip or uv)
install:
    uv sync

# Run tests
test:
    pytest

# Show environment variables loaded from .env
env:
    cat .env