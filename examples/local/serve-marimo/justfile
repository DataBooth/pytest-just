# Default recipe: list all available commands
default:
    just --list

# Build the Docker image for the Marimo/Streamlit app
docker-build:
    docker build -t marimo-app .

# Run the Docker container, mapping port 8000 (Marimo server)
docker-run:
    docker run --rm -it -p 8000:8000 marimo-app

# Rebuild and run Docker (for convenience)
docker-rebuild-run:
    just docker-build
    just docker-run

# Remove the Docker image
docker-clean:
    docker rmi marimo-app || true

# Run Marimo in edit mode (editable notebooks, all in directory)
marimo-edit:
    marimo edit notebooks

# Run Marimo in run mode (single notebook, read-only)
marimo-run FILE="notebooks/simple_demo.py":
    marimo run {{FILE}}

# Run Marimo ASGI server (serving all notebooks in read-only mode)
marimo-asgi:
    uvicorn marimo_server:app --host 0.0.0.0 --port 8000

# Run Streamlit app (if you have one)
app:
    streamlit run app/main.py

# List all notebooks in the notebooks directory
list-notebooks:
    ls -lh notebooks/*.py

# Run the FastAPI app that serves Marimo notebooks
fastapi:
    uvicorn marimo_server:app --host 0.0.0.0 --port 8000
