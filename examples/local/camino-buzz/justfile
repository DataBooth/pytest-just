# List available commands
default:
    @just --list

# Run the application in development mode
[no-cd]
dev:
    briefcase dev

# Build the application
[no-cd]
build:
    briefcase build

# Run the built application
[no-cd]
run:
    briefcase run

# Package the application for distribution
[no-cd]
package:
    briefcase package

# Clean up build artifacts
[no-cd]
clean:
    briefcase clean

# Run tests
test:
    python -m pytest tests/

# Create a new release
release VERSION:
    git tag -a v{{VERSION}} -m "Release {{VERSION}}"
    git push origin v{{VERSION}}