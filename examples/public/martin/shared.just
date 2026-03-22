# Shared recipes imported by examples/public/martin/justfile

hello:
    @echo "hello from shared.just"

lint:
    cargo clippy --workspace --all-targets
