# https://just.systems/

# Default output directory for PDF/HTML documents created from markdown
default_output_dir := "docs/output"

# Set the shell to bash
set shell := ["bash", "-uc"]

# Define the public repo URL
PUBLIC_REPO := "https://github.com/DataBooth/horselogic-nb-publish.git"


# List all just recipes
default:
  @just --list


# Export requirements.txt from pyproject.toml using PDM
reqs:
    pdm export --o requirements.txt --without-hashes --prod

qproject project_name="notebooks":
    quarto create-project {{project_name}} --type website && cd {{project_name}}

qrender project_name="notebooks":
    quarto render {{project_name}}

qpreview project_name="notebooks":
    quarto preview {{project_name}}

qpublish location="gh-pages" project_name="notebooks":
    quarto publish --no-prompt {{location}} {{project_name}}


# Define the main publishing recipe (I think quarto publish is effectively this recipe - although not to public_repo)
publish:
    #!/usr/bin/env bash
    set -euo pipefail

    # Store the original directory
    ORIGINAL_DIR=$(pwd)

    # Render the Quarto project
    cd notebooks
    quarto render
    cd "$ORIGINAL_DIR"

    # Check if public_repo directory exists
    if [ -d "public_repo" ]; then
        echo "public_repo directory exists. Updating..."
        cd public_repo
        git fetch origin
        git checkout gh-pages
        git pull origin gh-pages
    else
        echo "Cloning public repo..."
        git clone {{PUBLIC_REPO}} public_repo
        cd public_repo
        # Create and switch to gh-pages branch (or switch if it already exists)
        git checkout gh-pages 2>/dev/null || git checkout -b gh-pages
        # If the branch was newly created, you might want to set its upstream
        git push --set-upstream origin gh-pages
    fi

    # Remove existing files (except .git)
    find . -mindepth 1 -maxdepth 1 -not -name '.git' -exec rm -rf {} +

    # Copy rendered files from notebooks/_site to public repo
    cp -R "$ORIGINAL_DIR/notebooks/_site/"* .

    # Add, commit, and push changes
    git add .
    git commit -m "Update published notebooks" || echo "No changes to commit"
    git push origin gh-pages

    # Clean up
    cd "$ORIGINAL_DIR"
    rm -rf public_repo

reset_ghpages:
    #!/usr/bin/env bash
    set -euo pipefail

    # Store the original directory
    ORIGINAL_DIR=$(pwd)

    # Render the Quarto project
    cd notebooks
    quarto render
    cd "$ORIGINAL_DIR"

    # Remove existing public_repo directory if it exists
    rm -rf public_repo

    # Clone the public repo
    git clone {{PUBLIC_REPO}} public_repo
    cd public_repo

    # Delete the gh-pages branch locally and remotely
    git push origin --delete gh-pages || true
    git branch -D gh-pages || true

    # Create a new gh-pages branch
    git checkout --orphan gh-pages

    # Remove all files from the working directory
    git rm -rf .

    # Copy rendered files from notebooks/_site to public repo
    cp -R "$ORIGINAL_DIR/notebooks/_site/"* .

    # Add, commit, and push changes
    git add .
    git commit -m "Reset gh-pages branch"
    git push origin gh-pages --force

    # Clean up
    cd "$ORIGINAL_DIR"
    rm -rf public_repo

    echo "gh-pages branch has been reset and updated with new content."


render:
    cd notebooks && quarto render

list-notebooks:
    @echo "Available notebooks:"
    @ls -1 notebooks/*.ipynb 2>/dev/null || echo "No notebooks found"


# Copy local DuckDB database to MotherDuck
cp2md local_db remote_db:
    #!/usr/bin/env sh
    echo "Copying database to MotherDuck: {{local_db}} -> {{remote_db}}..."
    duckdb << EOF
    ATTACH 'md:';
    CREATE OR REPLACE DATABASE {{remote_db}} FROM '{{local_db}}';    
    EOF
    echo "Database copied to MotherDuck successfully."


# Execute and render a Quarto notebook (to .html)
quarto notebook="notebooks/logfile-reconciliation-RPE.ipynb" quarto_render_dir="quarto_output":
    #!/usr/bin/env bash
    set -euo pipefail

    notebook_abs_path=$(realpath "{{notebook}}")
    notebook_dir=$(dirname "$notebook_abs_path")
    output_dir=$(realpath "${notebook_dir}/{{quarto_render_dir}}")
    notebook_name=$(basename "{{notebook}}")

    # Ensure the output directory exists
    mkdir -p "$output_dir"

    # Change to the notebook directory before rendering
    cd "$notebook_dir"

    # Render the notebook
    quarto render "$notebook_name" --execute --output-dir "$output_dir"

    echo "Rendered $notebook_name to $output_dir"

# Package up the .html version of the notebook and supporting files
zip-quarto notebook="notebooks/logfile-reconciliation-RPE.ipynb" output_zip="analysis.zip":
    #!/usr/bin/env bash
    set -euo pipefail

    # Extract the base name without extension
    base_name=$(basename "{{notebook}}" .ipynb)
    dir_name=$(dirname "{{notebook}}")

    # Check if the HTML file exists
    if [ ! -f "${dir_name}/${base_name}.html" ]; then
        echo "Error: ${dir_name}/${base_name}.html not found. Make sure the notebook has been rendered to HTML."
        exit 1
    fi

    # Check if the supporting files directory exists
    if [ ! -d "${dir_name}/${base_name}_files" ]; then
        echo "Error: ${dir_name}/${base_name}_files directory not found. Supporting files are required."
        exit 1
    fi

    # Create the ZIP file
    zip -r "{{output_zip}}" "${dir_name}/${base_name}.html" "${dir_name}/${base_name}_files"

    echo "Created {{output_zip}} with ${base_name}.html and supporting files."

# Compress the report .html
zip-report report_html:
    #!/usr/bin/env bash
    zip -er report.zip {{report_html}}

# Create/update the project directory tree structure in markdown
dir-md outfile="docs/complete_directory_structure.md":
    echo '```' > {{outfile}}
    tree --noreport --gitignore -I '__pycache__|*.csv|*.log' >> {{outfile}}
    echo '```' >> {{outfile}}

# Export Jupyter notebook to Python and run it, optionally capturing output
run-notebook notebook keep_py="false" capture_output="false":
    #!/usr/bin/env bash
    set -euo pipefail

    notebook_abs_path=$(realpath "{{notebook}}")
    notebook_dir=$(dirname "$notebook_abs_path")
    notebook_name=$(basename "$notebook_abs_path")
    base_name=$(basename "$notebook_abs_path" .ipynb)

    echo "Converting {{notebook}} to Python script..."
    jupyter nbconvert --to python "$notebook_abs_path" --TemplateExporter.exclude_raw=True --no-prompt

    echo "Running ${notebook_dir}/${base_name}.py..."
    if [ "{{capture_output}}" = "true" ]; then
        output_file="${notebook_dir}/${base_name}_output.txt"
        (cd "$notebook_dir" && python "${base_name}.py") 2>&1 | tee "$output_file"
        echo "Output captured in $output_file"
    else
        (cd "$notebook_dir" && python "${base_name}.py")
    fi

    if [ "{{keep_py}}" != "true" ]; then
        echo "Removing ${notebook_dir}/${base_name}.py"
        rm "${notebook_dir}/${base_name}.py"
    else
        echo "Keeping ${notebook_dir}/${base_name}.py"
    fi

# Run two notebooks in sequence with options to keep .py files and capture output
run-notebooks notebook1="notebooks/logfile-reconciliation-RPE.ipynb" notebook2="notebooks/logfile-reconciliation-CB.ipynb" keep_py="false" capture_output="false":
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Running first notebook: {{notebook1}}"
    just run-notebook {{notebook1}} {{keep_py}} {{capture_output}}

    echo "Running second notebook: {{notebook2}}"
    just run-notebook {{notebook2}} {{keep_py}} {{capture_output}}

    echo "Notebook execution complete."
    if [ "{{keep_py}}" = "true" ]; then
        echo ".py files have been retained."
    else
        echo ".py files have been removed."
    fi
    if [ "{{capture_output}}" = "true" ]; then
        echo "Output has been captured for each notebook."
    fi


# Check if pandoc is installed
check-pandoc:
    #!/usr/bin/env bash
    if ! command -v pandoc &> /dev/null; then
        echo "Error: Pandoc is not installed. Please install pandoc to proceed."
        exit 1
    fi

# Match files and display them
match-files md_pattern:
    #!/usr/bin/env bash
    set -euo pipefail
    shopt -s nullglob
    matched_files=({{md_pattern}})
    shopt -u nullglob
    if [ ${#matched_files[@]} -eq 0 ]; then
        echo "No files matched the pattern: {{md_pattern}}"
        exit 0
    fi
    echo "Files to be converted:"
    for file in "${matched_files[@]}"; do
        echo "  $(pwd)/$file"
    done

# Ask for user confirmation
confirm-action:
    #!/usr/bin/env bash
    read -p "Proceed with conversion? [Y/n] " -n 1 -r user_input
    echo
    if [[ ! $user_input =~ ^[Yy]?$ ]]; then
        echo "Conversion cancelled by user."
        exit 0
    fi

# Convert markdown to PDF
convert-to-pdf file output_file:
    pandoc "{{file}}" -o "{{output_file}}" \
        --pdf-engine=xelatex \
        -V mainfont="DejaVu Sans" \
        -V monofont="DejaVu Sans Mono" \
        --highlight-style=tango

# Convert markdown to HTML
convert-to-html file output_file:
    pandoc "{{file}}" -o "{{output_file}}" \
        -s --toc --toc-depth=2 \
        --highlight-style=tango \
        -c https://cdn.jsdelivr.net/npm/water.css@2/out/water.css

convert-md md_pattern="docs/*.md" output_dir="docs/output" format="pdf":
    #!/usr/bin/env bash
    set -euo pipefail

    # Validate format
    if [[ "{{format}}" != "pdf" && "{{format}}" != "html" ]]; then
        echo "Error: Invalid format. Use 'pdf' or 'html'."
        exit 1
    fi

    just match-files "{{md_pattern}}"

    full_output_dir="$(pwd)/{{output_dir}}"
    echo "Output directory: $full_output_dir"
    echo "Output format: {{format}}"

    just confirm-action

    # Ensure the output directory exists
    mkdir -p "$full_output_dir"

    for file in {{md_pattern}}; do
        if [ -f "$file" ]; then
            output_file="$full_output_dir/$(basename "${file%.md}.{{format}}")"
            echo "Converting $file to $output_file"

            if [ "{{format}}" = "pdf" ]; then
                just convert-to-pdf "$file" "$output_file" || echo "Warning: Failed to convert $file to PDF. Skipping."
            else
                just convert-to-html "$file" "$output_file" || echo "Warning: Failed to convert $file to HTML. Skipping."
            fi
        else
            echo "Warning: $file not found or not a regular file. Skipping."
        fi
    done

    echo "Conversion complete. Output files are in $full_output_dir"


# Show the values of the arguments
show_args md_pattern="docs/*.md" output_dir="docs/output" format="pdf":
    #!/usr/bin/env bash
    echo "Argument values:"
    echo "  md_pattern: {{md_pattern}}"
    echo "  output_dir: {{output_dir}}"
    echo "  format: {{format}}"


# Extract SQL statements from a Jupyter notebook
extract-sql notebook output="":
    #!/usr/bin/env python3
    import json
    import re
    from pathlib import Path

    def extract_sql(notebook_path, output_path=None):
        notebook_path = Path(notebook_path)
        
        if output_path is None or output_path == "":
            output_path = notebook_path.with_stem(notebook_path.stem).with_suffix(".sql")
        else:
            output_path = Path(output_path)
        
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
        
        sql_statements = []
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                source = ''.join(cell['source'])
                matches = re.findall(r'sql\s*=\s*"""(.*?)"""', source, re.DOTALL)
                sql_statements.extend(matches)
        
        with open(output_path, 'w') as f:
            for stmt in sql_statements:
                f.write(stmt.strip() + '\n\n')
        
        if sql_statements:
            print(f"SQL statements extracted from '{notebook_path}' and saved to '{output_path}'")
        else:
            print("Warning: No SQL statements found or extracted.")
    
    extract_sql('{{notebook}}', '{{output}}')