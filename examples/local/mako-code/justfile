# Justfile (uses uv and Python 3.12)

# Set virtual environment path name
venv-path := ".venv"

# Default task
default:
    @just --list

# Setup both frontend and backend
setup: setup-frontend setup-backend

# Setup frontend dependencies
[no-cd]
setup-frontend:
    echo "Setting up frontend dependencies..."
    cd frontend && npm install

# Setup backend dependencies using uv and requirements.txt
setup-backend:
    echo "Setting up backend using uv and requirements.txt..."
    cd backend && uv venv --python=python3.12
    cd backend && if [ ! -f pyproject.toml ]; then uv init --bare; fi
    echo "Installing Python requirements using uv add..."
    cd backend && uv add -r requirements.txt


# Run both frontend and backend
run:
    echo "Starting frontend and backend development servers..."
    just backend &
    just frontend

# Run frontend server
frontend:
    echo "Starting frontend server..."    cd frontend && npm run dev

# Run backend server
backend:
    echo "Starting backend server..."
    echo "API docs available at http://localhost:8001/api/docs"
    cd backend && . {{venv-path}}/bin/activate \
        && ENVIRONMENT=development uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Build frontend for production
build:
    echo "Building frontend for production..."
    cd frontend && npm run build

# Clean environment
clean:
    echo "Cleaning up build artifacts and environments..."
    rm -rf frontend/node_modules
    rm -rf frontend/build
    rm -rf backend/{{venv-path}}
    rm -rf backend/__pycache__
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +

