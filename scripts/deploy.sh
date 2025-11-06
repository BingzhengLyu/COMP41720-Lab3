#!/bin/bash

# Deploy application to Kubernetes
# This script deploys both services to the lab3-resilience namespace

set -e

echo "================================================"
echo "Deploying Lab 3 to Kubernetes"
echo "================================================"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Create namespace
echo ""
echo "Creating namespace..."
kubectl apply -f kubernetes/namespace.yaml

# Deploy backend service
echo ""
echo "Deploying backend-service..."
kubectl apply -f kubernetes/backend-deployment.yaml

# Deploy client service
echo ""
echo "Deploying client-service..."
kubectl apply -f kubernetes/client-deployment.yaml

# Wait for deployments to be ready
echo ""
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/backend-service -n lab3-resilience
kubectl wait --for=condition=available --timeout=120s deployment/client-service -n lab3-resilience

# Show status
echo ""
echo "================================================"
echo "Deployment Status:"
echo "================================================"
kubectl get pods -n lab3-resilience
echo ""
kubectl get services -n lab3-resilience

echo ""
echo "✓ Deployment successful!"
echo ""
echo "Access client service at: http://localhost:30080"
echo ""
echo "Test endpoints:"
echo "  Health check:     curl http://localhost:30080/health"
echo "  Call backend:     curl http://localhost:30080/api/call-backend"
echo "  Get statistics:   curl http://localhost:30080/api/stats"
echo ""
echo "Run tests:          ./scripts/run-tests.sh"

