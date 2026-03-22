# Set default root directory for searches
ROOT_DIR := "."

# Set default maximum depth for searches (use -1 for unlimited depth)
MAX_DEPTH := "-1"

default:
  @just --list

# Export prod dependencies to requirements.txt from pyproject.toml
reqs:
    pdm export --o requirements.txt --without-hashes --prod

# General recipe to search for files matching a pattern
search-files pattern root_dir=ROOT_DIR depth=MAX_DEPTH:
    #!/usr/bin/env bash
    echo "Searching for files matching pattern: {{pattern}} in {{root_dir}}"
    if [ "{{depth}}" = "-1" ]; then
        find {{root_dir}} -type f -name "{{pattern}}" | grep -v "/\.git/"
    else
        find {{root_dir}} -maxdepth {{depth}} -type f -name "{{pattern}}" | grep -v "/\.git/"
    fi

# Specific recipe to search for .env files
search-env-files root_dir=ROOT_DIR depth=MAX_DEPTH: (search-files "*.env" root_dir depth)
    #!/usr/bin/env bash
    echo "Found .env files in {{root_dir}}:"
    if [ "{{depth}}" = "-1" ]; then
        find {{root_dir}} -type f -name "*.env" | grep -v "/\.git/" | xargs -I {} echo "- {}"
    else
        find {{root_dir}} -maxdepth {{depth}} -type f -name "*.env" | grep -v "/\.git/" | xargs -I {} echo "- {}"
    fi

# Recipe to list all .env files with full paths
list-dot-env root_dir=ROOT_DIR depth=MAX_DEPTH:
    #!/usr/bin/env bash
    echo "Listing all .env files in {{root_dir}}:"
    if [ "{{depth}}" = "-1" ]; then
        find {{root_dir}} -type f -name "*.env" | grep -v "/\.git/" | xargs -I {} echo "{}"
    else
        find {{root_dir}} -maxdepth {{depth}} -type f -name "*.env" | grep -v "/\.git/" | xargs -I {} echo "{}"
    fi
