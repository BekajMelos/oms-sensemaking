#!/usr/bin/env python3
"""
Test Metrics Generator Script

This script calls the test endpoints to generate real metrics
that can be observed in Prometheus and Grafana.
"""

import time
from typing import Any, Dict

import requests

# Configuration
BASE_URL = "https://localhost:5001"
TEST_ENDPOINTS = {
    "hello_world": "/test/hello-world",
    "metrics_test": "/test/metrics-test",
    "custom_event": "/test/custom-event",
    "custom_event_json": "/test/custom-event-json",
}

VERIFY_SSL = False


def make_request(endpoint: str, method: str = "GET", data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Make an HTTP request to the specified endpoint."""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == "GET":
            response = requests.get(url, verify=VERIFY_SSL, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, verify=VERIFY_SSL, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.SSLError as e:
        print(f"SSL Error for {url}: {e}")
        return {"error": "SSL Error", "details": str(e)}
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error for {url}: {e}")
        return {"error": "Connection Error", "details": str(e)}
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error for {url}: {e}")
        return {"error": "Timeout Error", "details": str(e)}
    except requests.exceptions.RequestException as e:
        print(f"Request Error for {url}: {e}")
        return {"error": "Request Error", "details": str(e)}


def test_connectivity() -> bool:
    """Test basic connectivity to the service."""
    print("Testing connectivity...")

    try:
        response = requests.post(f"{BASE_URL}/test/hello-world", verify=VERIFY_SSL, timeout=5)
        if response.status_code == 200:
            print("Service is accessible!")
            return True
        else:
            print(f"Service responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Cannot connect to service: {e}")
        return False


def generate_hello_world_metrics() -> None:
    """Generate metrics by calling the hello-world endpoint."""
    print("\nGenerating Hello World metrics...")

    for i in range(3):
        result = make_request(TEST_ENDPOINTS["hello_world"], method="POST")
        if "error" not in result:
            print(f"  Request {i+1}: {result.get('message', 'Success')}")
        else:
            print(f"  Request {i+1}: {result['error']}")
        time.sleep(0.5)


def generate_basic_metrics() -> None:
    """Generate metrics by calling the metrics-test endpoint."""
    print("\nGenerating basic metrics...")

    for i in range(2):
        result = make_request(TEST_ENDPOINTS["metrics_test"], method="POST")
        if "error" not in result:
            print(f"  Request {i+1}: {result.get('message', 'Success')}")
        else:
            print(f"  Request {i+1}: {result['error']}")
        time.sleep(0.5)


def generate_custom_event_metrics() -> None:
    """Generate custom event metrics with different queue names."""
    print("\nGenerating custom event metrics...")

    # Test with different queue names
    queue_names = ["test_queue_1", "test_queue_2", "production_queue"]

    for queue_name in queue_names:
        print(f"  Testing queue: {queue_name}")
        result = make_request(TEST_ENDPOINTS["custom_event"], method="POST", data={"queue_name": queue_name})

        if "error" not in result:
            print(f"    Success: {result.get('message', 'Success')}")
            print(f"    Events processed: {result.get('events_processed', 'N/A')}")
            print(f"    Events failed: {result.get('events_failed', 'N/A')}")
        else:
            print(f"    Error: {result['error']}")

        time.sleep(0.5)


def generate_json_custom_metrics() -> None:
    """Generate custom metrics using the JSON endpoint."""
    print("\nGenerating JSON custom metrics...")

    # Test different JSON payloads
    test_payloads = [
        {"queue_name": "json_queue_1", "events_processed": 3, "events_failed": 1},
        {"queue_name": "json_queue_2", "events_processed": 5, "events_failed": 2},
        {"queue_name": "high_volume_queue", "events_processed": 10, "events_failed": 0},
    ]

    for i, payload in enumerate(test_payloads):
        print(f"  Test payload {i+1}: {payload}")
        result = make_request(TEST_ENDPOINTS["custom_event_json"], method="POST", data=payload)

        if "error" not in result:
            print(f"    Success: {result.get('message', 'Success')}")
            print(f"    Queue: {result.get('queue_name', 'N/A')}")
            print(f"    Processed: {result.get('events_processed', 'N/A')}")
            print(f"    Failed: {result.get('events_failed', 'N/A')}")
        else:
            print(f"    Error: {result['error']}")

        time.sleep(0.5)


def main():
    """Main function to run all metric generation tests."""

    if not test_connectivity():
        return

    # Generate different types of metrics
    generate_hello_world_metrics()
    generate_basic_metrics()
    generate_custom_event_metrics()
    generate_json_custom_metrics()


if __name__ == "__main__":
    main()
