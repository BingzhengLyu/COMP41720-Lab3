# Lab 3: Designing for Resilience and Observability
## COMP41720 Distributed Systems

This lab demonstrates resilience patterns in distributed systems, including Circuit Breaker, Retry with Exponential Backoff, and Chaos Engineering experiments.

## Project Structure

```
Lab 3/
├── backend-service/          # Backend service that simulates failures
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── client-service/           # Client service with resilience patterns
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── kubernetes/               # Kubernetes manifests
│   ├── namespace.yaml
│   ├── backend-deployment.yaml
│   └── client-deployment.yaml
├── chaos-experiments/        # Chaos Toolkit experiments
│   ├── network-partition.yaml
│   ├── pod-failure.yaml
│   └── chaostoolkit-requirements.txt
├── scripts/                  # Helper scripts
│   ├── build-images.sh
│   ├── deploy.sh
│   └── run-tests.sh
└── docs/                     # Documentation and observations
    ├── baseline-observations.md
    ├── circuit-breaker-analysis.md
    └── chaos-experiments.md
```

## Architecture Overview

The application consists of two services:

1. **Backend Service** (Port 5000)
   - Simulates realistic failure scenarios (HTTP 500 errors, timeouts, slow responses)
   - Configurable failure rates via environment variables
   - Multiple endpoints for testing different failure types

2. **Client Service** (Port 8000)
   - Implements Circuit Breaker pattern using `pybreaker`
   - Implements Retry with Exponential Backoff and Jitter using `tenacity`
   - Provides both resilient and non-resilient endpoints for comparison
   - Exposes statistics and circuit breaker state

## Prerequisites

- Docker Desktop with Kubernetes enabled, OR
- Minikube or Kind for local Kubernetes cluster
- kubectl CLI tool
- Python 3.11+ (for local development/testing)
- Chaos Toolkit (optional, for chaos experiments)

## Quick Start

### 1. Build Docker Images

```bash
cd "Lab 3"

# Build backend service
docker build -t backend-service:latest ./backend-service/

# Build client service
docker build -t client-service:latest ./client-service/
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Deploy services
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/client-deployment.yaml

# Verify deployment
kubectl get pods -n lab3-resilience
kubectl get services -n lab3-resilience
```

### 3. Access the Services

The client service is exposed via NodePort on port 30080:

```bash
# Health check
curl http://localhost:30080/health

# Call backend with resilience patterns
curl http://localhost:30080/api/call-backend

# Call backend WITHOUT resilience (baseline)
curl http://localhost:30080/api/call-backend-without-resilience

# Get statistics
curl http://localhost:30080/api/stats
```

## Testing Resilience Patterns

### Part A: Baseline Testing

Test the system without resilience patterns to observe failure behavior:

```bash
# Make requests without resilience
for i in {1..20}; do
  echo "Request $i:"
  curl -s http://localhost:30080/api/call-backend-without-resilience | jq
  sleep 1
done
```

**Expected Observations:**
- Direct exposure to backend failures
- Timeouts when backend is slow
- Errors propagate directly to client
- No automatic recovery

### Part B: Circuit Breaker Testing

Trigger the circuit breaker by causing multiple consecutive failures:

```bash
# Stress test to open circuit breaker
curl -X POST http://localhost:30080/api/stress-test \
  -H "Content-Type: application/json" \
  -d '{"num_requests": 20}'

# Check circuit breaker state
curl http://localhost:30080/health | jq '.circuit_breaker_state'

# Continue making requests
for i in {1..10}; do
  echo "Request $i with Circuit Breaker:"
  curl -s http://localhost:30080/api/call-backend | jq '.circuit_breaker_state'
  sleep 2
done
```

**Expected Observations:**
- Circuit breaker opens after 5 consecutive failures
- Fast-fail behavior (immediate 503 responses)
- Half-open state after 30 seconds
- Circuit closes when backend recovers

### Part C: Retry Mechanism Testing

Test retry with exponential backoff using transient failures:

```bash
# Test retry mechanism
for i in {1..10}; do
  echo "Testing retry mechanism - attempt $i:"
  curl -s http://localhost:30080/api/test-retry | jq
  sleep 3
done
```

**Expected Observations:**
- Automatic retries on transient failures (429 errors)
- Exponential backoff with jitter
- Successful requests after retries
- Reduced thundering herd problem

## Chaos Engineering Experiments

### Setup Chaos Toolkit

```bash
# Install Chaos Toolkit
pip install -r chaos-experiments/chaostoolkit-requirements.txt

# Verify installation
chaos --version
```

### Experiment 1: Pod Failure

Terminate backend pods and observe system behavior:

```bash
cd chaos-experiments

# Run experiment
chaos run pod-failure.yaml

# Monitor during experiment (in another terminal)
watch -n 1 'kubectl get pods -n lab3-resilience'
```

### Experiment 2: Network Partition

Simulate network partition:

```bash
cd chaos-experiments

# Run experiment
chaos run network-partition.yaml
```

### Observing Chaos Experiments

During experiments, monitor:

```bash
# Watch pods
kubectl get pods -n lab3-resilience -w

# Check client service logs
kubectl logs -n lab3-resilience -l app=client-service -f

# Check backend service logs
kubectl logs -n lab3-resilience -l app=backend-service -f

# Monitor circuit breaker state
watch -n 1 'curl -s http://localhost:30080/health | jq ".circuit_breaker_state"'
```

## Key Endpoints

### Client Service (http://localhost:30080)

- `GET /health` - Health check with circuit breaker state
- `GET /api/call-backend` - Call backend WITH resilience patterns
- `GET /api/call-backend-without-resilience` - Call backend WITHOUT resilience (baseline)
- `GET /api/test-retry` - Test retry mechanism with transient failures
- `GET /api/stats` - Get service statistics
- `POST /api/stress-test` - Trigger multiple requests to test circuit breaker
- `POST /api/circuit-breaker/reset` - Manually reset circuit breaker

### Backend Service (internal: backend-service:5000)

- `GET /health` - Health check
- `GET /api/data` - Main endpoint with random failures/delays
- `GET /api/transient-failure` - Endpoint for testing retries (429 errors)
- `GET /api/metrics` - Get backend metrics

## Configuration

### Backend Service Environment Variables

- `FAILURE_RATE` - Probability of HTTP 500 errors (default: 0.3)
- `SLOW_RESPONSE_RATE` - Probability of slow responses (default: 0.2)
- `SLOW_RESPONSE_DELAY` - Delay duration in seconds (default: 5)

### Circuit Breaker Configuration

In `client-service/app.py`:
- `fail_max`: 5 - Open circuit after 5 consecutive failures
- `reset_timeout`: 30 - Try to close after 30 seconds
- Half-open state: Allows limited requests through to test recovery

### Retry Configuration

In `client-service/app.py`:
- `stop_after_attempt`: 4 - Maximum 4 retry attempts
- `wait_exponential`: 1s, 2s, 4s, 8s with max 10s
- Jitter: Random 0-10% added to wait time

## Architectural Trade-offs

### Circuit Breaker
**Benefits:**
- Fast-fail behavior prevents cascading failures
- Protects client from waiting for timeouts
- Allows backend time to recover
- Improves overall system availability

**Trade-offs:**
- May reject requests even if backend has recovered
- False positives during transient issues
- Complexity in configuration (thresholds, timeouts)
- Data freshness concerns during open state

### Retry with Exponential Backoff
**Benefits:**
- Handles transient failures automatically
- Exponential backoff prevents overwhelming backend
- Jitter prevents thundering herd
- Improves success rate for temporary issues

**Trade-offs:**
- Increases latency for failed requests
- Can amplify load if not configured properly
- May mask underlying problems
- Resource consumption during retries

## Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod -n lab3-resilience <pod-name>

# Check logs
kubectl logs -n lab3-resilience <pod-name>
```

### Service not accessible
```bash
# Check service endpoints
kubectl get endpoints -n lab3-resilience

# Port forwarding as alternative
kubectl port-forward -n lab3-resilience service/client-service 8000:8000
```

### Circuit breaker stuck open
```bash
# Reset circuit breaker
curl -X POST http://localhost:30080/api/circuit-breaker/reset
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace lab3-resilience

# Or delete individually
kubectl delete -f kubernetes/client-deployment.yaml
kubectl delete -f kubernetes/backend-deployment.yaml
kubectl delete -f kubernetes/namespace.yaml

# Remove Docker images
docker rmi backend-service:latest client-service:latest
```

## Lab Report Sections

For the lab report, document:

1. **Setup & Configuration**
   - Architecture diagram
   - Deployment details
   - Configuration parameters

2. **Baseline Testing Observations**
   - System behavior without resilience patterns
   - Failure modes observed
   - Impact on availability

3. **Circuit Breaker Analysis**
   - Configuration and thresholds
   - State transitions observed
   - Trade-off analysis
   - Performance impact

4. **Retry Mechanism Analysis**
   - Retry behavior with transient failures
   - Exponential backoff demonstration
   - Jitter effectiveness
   - Trade-off analysis

5. **Chaos Engineering Results**
   - Experiment configurations
   - System behavior during failures
   - Recovery process
   - Resilience pattern effectiveness

6. **Architectural Justification**
   - Why these patterns for these failure types
   - Link to CAP theorem and distributed systems principles
   - Trade-offs for different scenarios

## References

- Circuit Breaker: https://github.com/danielfm/pybreaker
- Retry Library: https://github.com/jd/tenacity
- Chaos Toolkit: https://chaostoolkit.org/
- Kubernetes: https://kubernetes.io/docs/

## Author

Student Name: [Your Name]
Student ID: [Your ID]
Course: COMP41720 Distributed Systems
Lab: 3 - Designing for Resilience and Observability

