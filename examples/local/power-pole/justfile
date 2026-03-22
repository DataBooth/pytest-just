# List all available recipes
default:
    @just --list

healthcheck:
    @echo "Checking API health..."
    @python api/healthcheck.py

train:
    @echo "Training the model..."
    @python api/train.py

predict steps:
    @if [ -z "{{steps}}" ]; then \
        echo "Error: steps argument is required"; \
        exit 1; \
    fi
    @echo "Making predictions for {{steps}} steps..."
    @python api/predict.py "{{steps}}"

model_history:
    @echo "Fetching model history..."
    @python api/model_history.py
