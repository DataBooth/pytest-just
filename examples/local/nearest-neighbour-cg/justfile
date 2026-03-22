# This is a Justfile (https://just.systems/man/en/) for managing C++ and Python projects 
# with recipes for building, cleaning, and running applications.

# Variables
app_name := "python/app/hulls.py"
image_name := "cpp-python-app"  # Name of the Docker image
dockerfile := "Dockerfile"
context := "."

# Detect compiler: prefer g++, fallback to clang++
compiler := `if command -v g++ > /dev/null 2>&1; then echo g++; elif command -v clang++ > /dev/null 2>&1; then echo clang++; else echo ""; fi`

# Set build directory variable
build_dir := "build"

# Set target executable name
target := "nearest_neighbour"

# Default recipe: lists all available recipes
default:
    @just --list


##  C++ recipes  ------------------------------------------------------


# Configure and build with CMake and Make (see CMakeLists.txt)
build:
    mkdir -p {{build_dir}}
    cd build && cmake -DPython3_EXECUTABLE="$(which python)" .. && make

# Clean build artifacts
clean:
    rm -rf {{build_dir}}


# Clean and (re)build the project
rebuild:
    just clean
    just build


# Check for C++ compiler / version
compiler:
    @if [ -z "{{compiler}}" ]; then \
        echo "No C++ compiler found (g++ or clang++ required)"; exit 1; \
    else \
        version=$({{compiler}} --version | head -n 1); \
        echo "Using compiler: {{compiler}} - version: $version"; \
    fi

# Run the target C++ application (within the build directory)
run:
   cd {{build_dir}} && ./{{target}}


# Build and run the convex hull C++ test
test-cpp-convex-hull:
    mkdir -p build
    cd build && cmake .. && make test_convex_hull
    ./build/test_convex_hull


##  Python recipes  ---------------------------------------------------

# NOTE: Use the uv package manager to install dependencies (see https://docs.astral.sh/uv/)

# Run the Streamlit app (within the Python virtual environment)
app:    
    #!/bin/bash
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Please activate the virtual environment first."
        echo "Run 'source .venv/bin/activate' to activate the virtual environment."
        echo ""
        exit 1
    fi

    if ! command -v streamlit >/dev/null 2>&1; then
        echo "Streamlit is not installed in the current environment."
        echo "Run 'uv add streamlit' after activating your virtual environment."
        exit 1
    fi

    streamlit run {{app_name}}


## ----- C++ kernel in Jupyter -------

# Open cling notebook on Binder (see https://github.com/jupyter-xeus/xeus-cling)
jupyter-cpp:
    open https://mybinder.org/v2/gh/jupyter-xeus/xeus-cling/stable?filepath=notebooks/xcpp.ipynb


# ------------- Docker Recipes --------------

# Check Docker context using your tool before building
docker-check:
    docker-context-tree --context {{context}} --dockerfile {{dockerfile}}

# Build the Docker image
docker-build:
    docker build -t {{image_name}} -f {{dockerfile}} {{context}}

# Run the Docker container (adjust ports as needed)
docker-run:
    docker run --rm -p 8501:8501 {{image_name}}

# Clean up dangling Docker images
docker-clean:
    docker image prune -f

# Push Docker image to registry (set $TAG and $REGISTRY as needed)
docker-push tag="latest" registry="":
    #!/bin/bash
    if [ -z "{{registry}}" ]; then
        echo "No registry specified. Skipping push."
        exit 1
    fi
    docker tag {{image_name}} {{registry}}/{{image_name}}:{{tag}}
    docker push {{registry}}/{{image_name}}:{{tag}}