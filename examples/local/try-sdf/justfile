# Tasks

# List the available tasks
default:
    @just --list

# Update/export reqs to requirements.txt
reqs:
    pdm export --o requirements.txt --without-hashes --prod

# Get the sdf version number
sdf-version:
    sdf --version

# fluff dotsql:
#     sqlfluff fix --dialect ansi {{dotsql}}

sdf-run:
    sdf run --show all

sdf-compile:
    sdf compile --show all

