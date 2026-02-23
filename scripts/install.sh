#!/usr/bin/env bash
set -e

REPO_URL="git@github.com:scottfrasso/geo-storm.git"
REPO_DIR="geo-storm"
HEALTH_URL="http://localhost:8080/health"
TIMEOUT=30
INTERVAL=2

echo "GeoStorm Installer"
echo "==================="
echo ""

# Check for required tools
for cmd in git docker; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: $cmd is not installed. Please install it and try again."
        exit 1
    fi
done

# Check that Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Clone the repository
if [ -d "$REPO_DIR" ]; then
    echo "Directory '$REPO_DIR' already exists. Pulling latest changes..."
    cd "$REPO_DIR"
    git pull
else
    echo "Cloning GeoStorm..."
    git clone "$REPO_URL"
    cd "$REPO_DIR"
fi

# Build and start the container
echo ""
echo "Starting GeoStorm..."
docker compose up -d --build

# Wait for health check
echo ""
echo "Waiting for GeoStorm to be ready..."
elapsed=0
while [ $elapsed -lt $TIMEOUT ]; do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo ""
        echo "==================="
        echo "GeoStorm is running!"
        echo ""
        echo "  Open http://localhost:8080"
        echo ""
        echo "A demo project with 90 days of sample data is ready to explore."
        echo "==================="
        exit 0
    fi
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    printf "."
done

echo ""
echo "Warning: GeoStorm did not respond within ${TIMEOUT}s."
echo "The container may still be starting. Check status with:"
echo ""
echo "  docker compose logs -f"
echo ""
exit 1
