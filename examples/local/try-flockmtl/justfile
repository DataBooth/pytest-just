# Justfile for FlockMTL/Ollama Project

# Default: List all available recipes
default:
    @just --list

# Run the Python manager script
run:
    python scripts/flockmtl_manager.py

# Pull a specific Ollama model (usage: just ollama-pull llama2)
ollama-pull MODEL:
    ollama pull {{MODEL}}

# List all available Ollama models
ollama-list:
    ollama list

# Show the status of all running Ollama models
ollama-ps:
    ollama ps

# Run Ollama server (foreground)
ollama-serve:
    ollama serve

# Run an Ollama prompt interactively with a specified model
# Usage: just ollama-chat llama2 "Why is the sky blue?"
ollama-chat MODEL PROMPT:
    ollama run {{MODEL}} --prompt "{{PROMPT}}"