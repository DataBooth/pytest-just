app_name := "app/main.py"

# Default recipe: list all available recipes
default:
    @just --list


# Run the Streamlit app locally (requires activated venv = .venv)
app:
    #!/bin/bash
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Please activate the virtual environment first."
        echo "Run 'source .venv/bin/activate' to activate the virtual environment."
        exit 1
    fi
    python {{app_name}}


# Run the Streamlit app locally (requires activated venv = .venv)
app-ui:
    #!/bin/bash
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Please activate the virtual environment first."
        echo "Run 'source .venv/bin/activate' to activate the virtual environment."
        exit 1
    fi
    if ! command -v streamlit >/dev/null 2>&1; then
        echo "Streamlit is not installed in the current environment."
        echo "Run 'uv add streamlit' after activating your virtual environment."
        exit 1
    fi
    streamlit run {{app_name}}

## --------- Docker recipes ---------

# Build the Docker image (Dockerfile) for Linux just/bootstrap testing
docker-build:
    docker build -t linux-just-bootstrap-test .

# Run the Docker container interactively and remove on exit
docker-run:
   docker run -it --rm linux-just-bootstrap-test
