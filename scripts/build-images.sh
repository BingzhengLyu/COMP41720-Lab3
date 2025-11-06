#!/bin/bash

# Build Docker images for Lab 3
# This script builds both backend and client service images

set -e

echo "================================================"
echo "Building Docker Images for Lab 3"
echo "================================================"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Build backend service
echo ""
echo "Building backend-service..."
docker build -t backend-service:latest ./backend-service/
echo "✓ backend-service image built successfully"

# Build client service
echo ""
echo "Building client-service..."
docker build -t client-service:latest ./client-service/
echo "✓ client-service image built successfully"

# List images
echo ""
echo "================================================"
echo "Docker Images:"
echo "================================================"
docker images | grep -E "REPOSITORY|backend-service|client-service"

echo ""
echo "✓ All images built successfully!"
echo ""
echo "Next steps:"
echo "  1. Deploy to Kubernetes: ./scripts/deploy.sh"
echo "  2. Run tests: ./scripts/run-tests.sh"

