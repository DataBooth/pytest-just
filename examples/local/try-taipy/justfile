
# Default: list all available recipes
default:
    @just --list

# Run a Taipy app by name (e.g., just run app/main.py)
app app_path:
    taipy run {{app_path}}

# Stop all running Taipy processes (uses pkill, works on macOS/Linux)
stop-taipy:
    pkill -f 'python.*taipy'

# Check for any running Taipy processes
ps-taipy:
    pgrep -af 'python.*taipy' || echo "No Taipy processes running."

