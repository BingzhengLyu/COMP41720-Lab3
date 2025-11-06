"""
Backend Service for Lab 3 - Distributed Systems
This service simulates a backend that occasionally fails or responds slowly
to test resilience patterns.
"""

from flask import Flask, jsonify, request
import random
import time
import os

app = Flask(__name__)

# Configuration for simulating failures
FAILURE_RATE = float(os.environ.get('FAILURE_RATE', '0.3'))  # 30% chance of failure
SLOW_RESPONSE_RATE = float(os.environ.get('SLOW_RESPONSE_RATE', '0.2'))  # 20% chance of slow response
SLOW_RESPONSE_DELAY = int(os.environ.get('SLOW_RESPONSE_DELAY', '5'))  # 5 seconds delay

request_count = 0


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'backend-service'
    }), 200


@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Main endpoint that simulates various failure scenarios:
    - Random failures (HTTP 500)
    - Slow responses
    - Successful responses
    """
    global request_count
    request_count += 1
    
    # Simulate slow response
    if random.random() < SLOW_RESPONSE_RATE:
        app.logger.warning(f"Request #{request_count}: Simulating slow response ({SLOW_RESPONSE_DELAY}s delay)")
        time.sleep(SLOW_RESPONSE_DELAY)
    
    # Simulate failure
    if random.random() < FAILURE_RATE:
        app.logger.error(f"Request #{request_count}: Simulating failure")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Simulated failure for testing resilience'
        }), 500
    
    # Successful response
    app.logger.info(f"Request #{request_count}: Successful response")
    return jsonify({
        'status': 'success',
        'data': {
            'message': 'Hello from Backend Service',
            'request_id': request_count,
            'timestamp': time.time()
        }
    }), 200


@app.route('/api/transient-failure', methods=['GET'])
def transient_failure():
    """
    Endpoint that simulates transient failures (HTTP 429 - Too Many Requests)
    Used for testing retry mechanisms
    """
    global request_count
    request_count += 1
    
    # 60% chance of transient failure
    if random.random() < 0.6:
        app.logger.warning(f"Request #{request_count}: Transient failure (429)")
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Please retry after some time'
        }), 429
    
    return jsonify({
        'status': 'success',
        'data': {
            'message': 'Transient failure resolved',
            'request_id': request_count
        }
    }), 200


@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Simple metrics endpoint"""
    return jsonify({
        'total_requests': request_count,
        'failure_rate': FAILURE_RATE,
        'slow_response_rate': SLOW_RESPONSE_RATE
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

