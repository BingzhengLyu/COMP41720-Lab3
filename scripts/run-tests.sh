#!/bin/bash

# Run tests to demonstrate resilience patterns
# This script executes various test scenarios

set -e

BASE_URL="http://localhost:30080"

echo "================================================"
echo "Lab 3 - Resilience Patterns Testing"
echo "================================================"

# Check if services are accessible
echo ""
echo "1. Checking service health..."
if curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "✓ Client service is accessible"
    curl -s "$BASE_URL/health" | jq
else
    echo "✗ Client service is not accessible at $BASE_URL"
    echo "Make sure the services are deployed: ./scripts/deploy.sh"
    exit 1
fi

# Baseline test - without resilience
echo ""
echo "================================================"
echo "2. Baseline Test (WITHOUT Resilience Patterns)"
echo "================================================"
echo "Making 10 requests without resilience patterns..."
for i in {1..10}; do
    echo "Request $i:"
    response=$(curl -s "$BASE_URL/api/call-backend-without-resilience")
    status=$(echo "$response" | jq -r '.status_code // .error')
    echo "  Status: $status"
    sleep 1
done

# Test with resilience patterns
echo ""
echo "================================================"
echo "3. Test WITH Resilience Patterns"
echo "================================================"
echo "Making 10 requests with Circuit Breaker and Retry..."
for i in {1..10}; do
    echo "Request $i:"
    response=$(curl -s "$BASE_URL/api/call-backend")
    cb_state=$(echo "$response" | jq -r '.circuit_breaker_state')
    status=$(echo "$response" | jq -r '.backend_response.status // .backend_response.error')
    echo "  Circuit Breaker State: $cb_state"
    echo "  Backend Status: $status"
    sleep 1
done

# Trigger circuit breaker
echo ""
echo "================================================"
echo "4. Circuit Breaker Stress Test"
echo "================================================"
echo "Triggering circuit breaker with 20 requests..."
curl -s -X POST "$BASE_URL/api/stress-test" \
    -H "Content-Type: application/json" \
    -d '{"num_requests": 20}' | jq '.results[-5:] | .[]'

sleep 5

# Check circuit breaker state
echo ""
echo "Circuit Breaker State after stress test:"
curl -s "$BASE_URL/health" | jq '.circuit_breaker_state'

# Test fast-fail behavior
echo ""
echo "Testing fast-fail behavior (circuit breaker should be open):"
for i in {1..5}; do
    echo "Request $i:"
    start_time=$(date +%s%N)
    response=$(curl -s "$BASE_URL/api/call-backend")
    end_time=$(date +%s%N)
    elapsed=$((($end_time - $start_time) / 1000000))
    
    status=$(echo "$response" | jq -r '.backend_response.error // "success"')
    cb_state=$(echo "$response" | jq -r '.circuit_breaker_state')
    echo "  Status: $status, Circuit Breaker: $cb_state, Time: ${elapsed}ms"
    sleep 2
done

# Test retry mechanism
echo ""
echo "================================================"
echo "5. Retry Mechanism Test (Transient Failures)"
echo "================================================"
echo "Testing retry with exponential backoff..."
for i in {1..5}; do
    echo "Attempt $i:"
    response=$(curl -s "$BASE_URL/api/test-retry")
    status=$(echo "$response" | jq -r '.backend_response.status // .backend_response.error')
    elapsed=$(echo "$response" | jq -r '.elapsed_time_seconds')
    echo "  Status: $status, Elapsed Time: ${elapsed}s"
    sleep 2
done

# Get final statistics
echo ""
echo "================================================"
echo "6. Final Statistics"
echo "================================================"
curl -s "$BASE_URL/api/stats" | jq

echo ""
echo "================================================"
echo "Testing Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Reset circuit breaker: curl -X POST $BASE_URL/api/circuit-breaker/reset"
echo "  2. Run chaos experiments: cd chaos-experiments && chaos run pod-failure.yaml"
echo "  3. Monitor logs: kubectl logs -n lab3-resilience -l app=client-service -f"

