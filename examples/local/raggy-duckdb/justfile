# Default list recipe
default:
    @just --list


# Run the pipeline with default config.toml
run question="What is RAG?":
	@echo "Running RAG pipeline with default config"
	uv run src/raggy_duckdb/cli.py run_pipeline --question={{question}}

# Run the pipeline with a specific config file
run-config config_path question:
	@echo "Running RAG pipeline with config: {{config_path}}"
	uv run src/raggy_duckdb/cli.py run_pipeline --config_path={{config_path}} --question={{question}}

# Ollama CLI management recipes

# Check if "ollama" command exists; if not, print error and exit.
ollama-exists:
    @command -v ollama > /dev/null || { \
        echo "⚠️ Ollama CLI not found. Please install it first with: just ollama-install"; \
        exit 1; \
    }

# Ollama serve with check if already running on port 11434
ollama-serve: ollama-exists
	@if lsof -i :11434 > /dev/null 2>&1; then \
		echo "⚠️ Ollama server is already running on port 11434. Skipping 'ollama serve'."; \
	else \
		echo "Serving Ollama..."; \
		ollama serve || { echo "Failed to serve Ollama. Please check your setup."; exit 1; }; \
	fi


# Install Ollama CLI via Homebrew
ollama-install:
    @echo "Installing Ollama CLI via Homebrew..."
    brew install ollama || { \
        echo "Failed to install Ollama via Homebrew. Please check your setup."; exit 1; }

# Update Ollama CLI to latest via Homebrew
ollama-update: ollama-exists
    @echo "Updating Ollama CLI via Homebrew..."
    brew upgrade ollama || { \
        echo "Failed to update Ollama. You may already be up to date."; }

# Pull an Ollama model (default: llama2)
ollama-pull model="llama2": ollama-exists
    @echo "Pulling Ollama model '{{model}}'..."
    ollama pull {{model}}

# Run Ollama generate with a prompt (default prompt)
ollama-run model="llama2" prompt="Hello Ollama!": ollama-exists
    @echo "Running Ollama generate on model '{{model}}' with prompt: {{prompt}}"
    echo "{{prompt}}" | ollama generate --model {{model}}

# Run Ollama chat interactively for simple testing
ollama-chat model="llama2": ollama-exists
    @echo "Starting Ollama chat with model '{{model}}'..."
    ollama chat --model {{model}}

# List all installed Ollama models
ollama-list-models: ollama-exists
    @echo "Listing installed Ollama models..."
    ollama list

# Test Ollama server is running and responding on port 11434
ollama-health-check:
	@echo "Checking Ollama server health on port 11434..."
	@if command -v curl > /dev/null 2>&1; then \
		if command -v jq > /dev/null 2>&1; then \
			curl --fail --silent --show-error --max-time 5 http://localhost:11434/v1/models | jq . || { \
				echo "\nFailed to parse JSON response from Ollama server."; exit 1; \
			}; \
		else \
			echo "Warning: jq is not installed, raw JSON output follows:"; \
			curl --fail --silent --show-error --max-time 5 http://localhost:11434/v1/models || { \
				echo "\nFailed to connect to Ollama server on port 11434. Is the server running?"; exit 1; \
			}; \
		fi; \
		echo "\nOllama server responded successfully."; \
	else \
		echo "curl not installed; unable to perform health check."; \
		exit 1; \
	fi


