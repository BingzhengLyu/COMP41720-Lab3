"""
Client Service for Lab 3 - Distributed Systems
This service implements resilience patterns:
- Circuit Breaker
- Retry with Exponential Backoff and Jitter
"""

from flask import Flask, jsonify, request
import requests
import time
import random
import os
from pybreaker import CircuitBreaker, CircuitBreakerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Backend service URL
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://backend-service:5000')

# Statistics tracking
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'circuit_breaker_open_count': 0,
    'retry_attempts': 0
}


# Circuit Breaker Configuration
def circuit_breaker_listener(cb, event):
    """Listener to track circuit breaker state changes"""
    logger.info(f"Circuit Breaker Event: {event} - State: {cb.current_state}")
    if event == 'open':
        stats['circuit_breaker_open_count'] += 1


circuit_breaker = CircuitBreaker(
    fail_max=5,           # Open circuit after 5 consecutive failures
    reset_timeout=30,     # Try to close circuit after 30 seconds
    exclude=[requests.exceptions.ConnectionError],
    listeners=[circuit_breaker_listener],
    name='backend-service-breaker'
)


def add_jitter(wait_time):
    """Add jitter to prevent thundering herd problem"""
    jitter = random.uniform(0, wait_time * 0.1)  # Add up to 10% jitter
    return wait_time + jitter


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,)),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.INFO),
    reraise=True
)
def make_request_with_retry(url, timeout=5):
    """
    Make HTTP request with retry logic and exponential backoff
    - Retries up to 4 times
    - Exponential backoff: 1s, 2s, 4s, 8s (max 10s)
    - Adds jitter to prevent synchronized retries
    """
    stats['retry_attempts'] += 1
    
    # Add jitter to the wait time
    time.sleep(random.uniform(0, 0.1))  # Small initial jitter
    
    logger.info(f"Making request to {url}")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def call_backend_with_circuit_breaker(endpoint='/api/data'):
    """
    Call backend service with circuit breaker protection
    """
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        # Circuit breaker wrapped call
        @circuit_breaker
        def protected_call():
            return make_request_with_retry(url)
        
        response = protected_call()
        return response.json(), response.status_code
    
    except CircuitBreakerError:
        logger.error("Circuit breaker is OPEN - Failing fast")
        return {
            'error': 'Service Unavailable',
            'message': 'Circuit breaker is open. Backend service is currently unavailable.',
            'fallback': True
        }, 503
    
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return {
            'error': 'Timeout',
            'message': 'Backend service request timed out'
        }, 504
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        return {
            'error': 'Request Failed',
            'message': str(e)
        }, 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'client-service',
        'circuit_breaker_state': circuit_breaker.current_state
    }), 200


@app.route('/api/call-backend', methods=['GET'])
def call_backend():
    """
    Endpoint that calls the backend service with resilience patterns
    """
    stats['total_requests'] += 1
    start_time = time.time()
    
    logger.info(f"Received request #{stats['total_requests']}")
    
    # Call backend with circuit breaker and retry
    data, status_code = call_backend_with_circuit_breaker()
    
    elapsed_time = time.time() - start_time
    
    if status_code == 200:
        stats['successful_requests'] += 1
    else:
        stats['failed_requests'] += 1
    
    return jsonify({
        'client_request_id': stats['total_requests'],
        'backend_response': data,
        'elapsed_time_seconds': round(elapsed_time, 2),
        'circuit_breaker_state': circuit_breaker.current_state
    }), status_code


@app.route('/api/call-backend-without-resilience', methods=['GET'])
def call_backend_without_resilience():
    """
    Baseline endpoint - calls backend WITHOUT resilience patterns
    Used for comparison in baseline testing
    """
    stats['total_requests'] += 1
    start_time = time.time()
    
    url = f"{BACKEND_URL}/api/data"
    
    try:
        logger.info(f"Making direct request (no resilience) to {url}")
        response = requests.get(url, timeout=5)
        elapsed_time = time.time() - start_time
        
        return jsonify({
            'message': 'Request without resilience patterns',
            'backend_response': response.json(),
            'elapsed_time_seconds': round(elapsed_time, 2),
            'status_code': response.status_code
        }), response.status_code
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Direct request failed: {str(e)}")
        stats['failed_requests'] += 1
        
        return jsonify({
            'error': 'Request Failed',
            'message': str(e),
            'elapsed_time_seconds': round(elapsed_time, 2)
        }), 500


@app.route('/api/test-retry', methods=['GET'])
def test_retry():
    """
    Test endpoint for retry mechanism with transient failures
    """
    stats['total_requests'] += 1
    start_time = time.time()
    
    logger.info("Testing retry mechanism with transient failures")
    
    data, status_code = call_backend_with_circuit_breaker(endpoint='/api/transient-failure')
    
    elapsed_time = time.time() - start_time
    
    return jsonify({
        'test_type': 'retry_mechanism',
        'backend_response': data,
        'elapsed_time_seconds': round(elapsed_time, 2),
        'circuit_breaker_state': circuit_breaker.current_state
    }), status_code


@app.route('/api/circuit-breaker/reset', methods=['POST'])
def reset_circuit_breaker():
    """Manually reset the circuit breaker"""
    circuit_breaker.close()
    logger.info("Circuit breaker manually reset")
    return jsonify({
        'message': 'Circuit breaker reset',
        'state': circuit_breaker.current_state
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get service statistics"""
    return jsonify({
        'statistics': stats,
        'circuit_breaker': {
            'state': circuit_breaker.current_state,
            'fail_counter': circuit_breaker.fail_counter,
            'fail_max': circuit_breaker.fail_max,
            'reset_timeout': circuit_breaker.reset_timeout
        }
    }), 200


@app.route('/api/stress-test', methods=['POST'])
def stress_test():
    """
    Endpoint to trigger multiple requests for testing circuit breaker
    """
    num_requests = request.json.get('num_requests', 10)
    results = []
    
    logger.info(f"Starting stress test with {num_requests} requests")
    
    for i in range(num_requests):
        data, status_code = call_backend_with_circuit_breaker()
        results.append({
            'request_num': i + 1,
            'status_code': status_code,
            'circuit_breaker_state': circuit_breaker.current_state
        })
        time.sleep(0.5)  # Small delay between requests
    
    return jsonify({
        'test_type': 'stress_test',
        'total_requests': num_requests,
        'results': results,
        'final_circuit_breaker_state': circuit_breaker.current_state
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

