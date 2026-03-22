# List available commands
default:
    @just --list

# Show available pixi tasks (use 'pixi run <task>' to run them)
pixi-tasks:
    @echo "Available pixi tasks (run with 'pixi run <task>'):"
    @echo ""
    @pixi task list

# Diff a puzzle against its original template
# Usage: just pdiff p04  OR  just pdiff p04_layout_tensor
pdiff target:
    #!/usr/bin/env bash
    set -euo pipefail
    pnum=$(echo "{{target}}" | sed 's/_.*$//')
    file="{{target}}"
    diff -U1 "problems-original/$pnum/$file.mojo" "problems/$pnum/$file.mojo" || true

# List all available puzzles
puzzles:
    @echo "Available puzzles:"
    @find problems-original -maxdepth 2 -name '*.mojo' -type f | \
     sed 's|problems-original/||' | \
     sed 's|/\(.*\)\.mojo|/\1|' | \
     sort

# Run a specific puzzle (e.g., just run p04)
run puzzle:
    pixi run {{puzzle}}

# Test a specific puzzle solution (e.g., just test p04)
test puzzle:
    pixi run tests {{puzzle}}

# Test all puzzle solutions
test-all:
    pixi run tests

# Format code in problems/ and solutions/
format:
    pixi run format

# Check if code is formatted correctly (CI check)
format-check:
    pixi run format-check

# Show GPU specifications
gpu-specs:
    pixi run gpu-specs

# Build and serve the puzzle book locally
book:
    pixi run book

# Clean profiling artifacts
clean-profiles:
    pixi run clean-profiles

# Clean all generated files (animations + profiles)
clean-all:
    pixi run clean-all
