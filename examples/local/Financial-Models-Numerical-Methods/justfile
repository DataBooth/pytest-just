MARIMO_DIR := "marimo-experience"

# List all available recipes (default)
default:
    @just --list

# Add all packages from list_of_packages.txt using uv add
add-packages:
    uv add -r list_of_packages.txt && uv add marimo

# Typical Marimo recipes

# Edit Marimo app 
mo-edit app_py:
    marimo edit "{{app_py}}"

# Start Marimo app (replace app.py with your entrypoint if needed)
mo-serve:
    marimo run app.py

# Convert a Jupyter notebook to a Marimo notebook (quotes to handle spaces)
convert-ipynb-to-marimo notebook:
    marimo convert "{{notebook}}.ipynb" -o "{{MARIMO_DIR}}/{{notebook}}.py"

# Convert all notebooks in the current directory to Marimo notebooks
convert-all-ipynb-to-marimo:
    for nb in *.ipynb; do marimo convert "$$nb" "$${nb%.ipynb}.marimo"; done


convert-mo-to-md notebook:
    marimo export md "{{notebook}}.py" > "{{notebook}}.md"


# Run Marimo in production mode
mo-prod:
    marimo run --prod app.py

# Development tasks (customize as needed)
dev:
    echo "Starting development environment..."

test:
    echo "Running tests..."

lint:
    echo "Linting code..."

format:
    echo "Formatting code..."


## Tutorials

mo-tutorial:
    marimo tutorial markdown-format
