# justfile

default:
  @just --list

build:
  @echo "Building project..."
  mojo build src/main.mojo

test:
  @echo "Running tests..."
  mojo run -I src tests/test_utils.mojo
  mojo run -I src tests/test_config.mojo

clean:
  @echo "Cleaning build artifacts..."
  rm -rf build/

fmt:
  @echo "Formatting code with ruff (for Python parts)..."
  ruff format .

run:
  @echo "Running main Mojo program..."
  mojo run -I src src/main.mojo
