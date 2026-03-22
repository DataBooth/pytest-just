# Just recipes for the mojo-data-star project
# These recipes are intended to work across macOS, Linux, and Windows.
# pixi manages the Python and Mojo environments; just delegates to pixi tasks.

default: build

alias t := test

# Build the Mojo extension module for Python interop
build:
	pixi run build

# Run Mojo TestSuite tests
test-mojo:
	pixi run test-mojo

# Run Python tests with pytest
test-py:
	pixi run test-py

# Run all tests (Mojo + Python)
test:
	pixi run test

# Start the FastAPI app for interactive exploration
serve:
	pixi run serve
