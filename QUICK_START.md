# Quick Start Guide - Lab 3

This guide will help you quickly set up and run the Lab 3 resilience demonstration.

## Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Kubernetes enabled in Docker Desktop
- [ ] kubectl CLI installed
- [ ] Python 3.11+ (for local testing, optional)
- [ ] Terminal/Command Line access

## 5-Minute Setup

### Step 1: Build Docker Images (2 minutes)

```bash
cd "/Users/xwys/Autumn Semester 2/Distributed Systems/Lab 3"
./scripts/build-images.sh
```

**Expected Output:**
```
Building backend-service...
✓ backend-service image built successfully
Building client-service...
✓ client-service image built successfully
```

### Step 2: Deploy to Kubernetes (2 minutes)

```bash
./scripts/deploy.sh
```

**Expected Output:**
```
Creating namespace...
Deploying backend-service...
Deploying client-service...
Waiting for deployments to be ready...
✓ Deployment successful!
```

### Step 3: Verify Deployment (30 seconds)

```bash
# Check pods are running
kubectl get pods -n lab3-resilience

# Expected: All pods should show 1/1 READY
```

### Step 4: Test the Application (30 seconds)

```bash
# Health check
curl http://localhost:30080/health

# Make a request
curl http://localhost:30080/api/call-backend

# Get statistics
curl http://localhost:30080/api/stats
```

## Running Experiments

### Baseline Test (Without Resilience)

```bash
for i in {1..10}; do
  echo "Request $i:"
  curl -s http://localhost:30080/api/call-backend-without-resilience | jq '.status_code'
  sleep 1
done
```

### Circuit Breaker Test

```bash
# Trigger circuit breaker to open
curl -X POST http://localhost:30080/api/stress-test \
  -H "Content-Type: application/json" \
  -d '{"num_requests": 20}' | jq

# Check circuit breaker state
curl -s http://localhost:30080/health | jq '.circuit_breaker_state'
```

### Retry Test

```bash
# Test retry mechanism with transient failures
for i in {1..5}; do
  echo "Test $i:"
  curl -s http://localhost:30080/api/test-retry | jq '.elapsed_time_seconds'
  sleep 2
done
```

### Chaos Engineering Test

```bash
# Install Chaos Toolkit
pip3 install --user -r chaos-experiments/chaostoolkit-requirements.txt

# Run pod failure experiment
cd chaos-experiments
chaos run pod-failure.yaml

# Watch the system recover
kubectl get pods -n lab3-resilience -w
```

## Common Issues & Solutions

### Issue: Pods not starting

**Solution:**
```bash
# Check pod status
kubectl describe pod -n lab3-resilience <pod-name>

# Check logs
kubectl logs -n lab3-resilience <pod-name>
```

### Issue: Service not accessible

**Solution:**
```bash
# Check service endpoints
kubectl get endpoints -n lab3-resilience

# Alternative: Use port forwarding
kubectl port-forward -n lab3-resilience service/client-service 8000:8000
# Then access: http://localhost:8000
```

### Issue: Circuit breaker stuck open

**Solution:**
```bash
# Reset circuit breaker
curl -X POST http://localhost:30080/api/circuit-breaker/reset

# Or restart client pod
kubectl delete pod -n lab3-resilience -l app=client-service
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace lab3-resilience

# Or run:
kubectl delete -f kubernetes/backend-deployment.yaml
kubectl delete -f kubernetes/client-deployment.yaml
kubectl delete -f kubernetes/namespace.yaml
```

## Next Steps

1. Run the automated test suite: `./scripts/run-tests.sh`
2. Review the lab report: `LAB_REPORT.md`
3. Read detailed analysis: `docs/` directory
4. Experiment with different configurations
5. Run chaos experiments

## Key Endpoints Reference

### Client Service (http://localhost:30080)

- `GET /health` - Health check with circuit breaker state
- `GET /api/call-backend` - Call with resilience patterns
- `GET /api/call-backend-without-resilience` - Call without resilience (baseline)
- `GET /api/test-retry` - Test retry mechanism
- `GET /api/stats` - Service statistics
- `POST /api/stress-test` - Trigger circuit breaker test
- `POST /api/circuit-breaker/reset` - Reset circuit breaker

## Monitoring Commands

```bash
# Watch pods
kubectl get pods -n lab3-resilience -w

# Stream client logs
kubectl logs -n lab3-resilience -l app=client-service -f

# Stream backend logs
kubectl logs -n lab3-resilience -l app=backend-service -f

# Monitor circuit breaker state
watch -n 1 'curl -s http://localhost:30080/health | jq ".circuit_breaker_state"'
```

## Tips for Success

1. **Start with baseline** - Run without resilience first to see the problems
2. **One pattern at a time** - Test circuit breaker, then retry, then both
3. **Monitor logs** - Logs show exactly what's happening
4. **Be patient** - Wait for circuit breaker timeout (30s) to see recovery
5. **Document observations** - Take screenshots and notes for your report

## Questions?

Review the comprehensive README.md and LAB_REPORT.md for detailed information.

Good luck with your lab! 🚀

