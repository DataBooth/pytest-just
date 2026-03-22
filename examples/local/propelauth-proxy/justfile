default:
    @just --list

install-deps:
    npm i @propelauth/auth-proxy && npm install dotenv

proxy:
    node proxy.mjs

ps_proxy:
    ps aux | grep 'proxy.mjs'



# Docker

# Start Docker (if it is not running)
dstart:
    docker info > /dev/null 2>&1 && echo "Docker is running" || echo "Starting Docker" && open -a Docker


# Build the image from the specified Dockerfile
dbuild image_name dockerfile_path="Dockerfile":
    docker build -t {{image_name}} -f {{dockerfile_path}} .


# Get version of npm in the specific container
dnpm_version from_name="node:20-slim":
    docker run --rm {{from_name}} npm -v
