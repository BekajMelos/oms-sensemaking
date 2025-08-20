"""Tests for the test router endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from httpx import Response


def test_hello_world_endpoint(client: TestClient):
    """Test the hello-world endpoint generates events correctly."""

    response: Response = client.post("/test/hello-world")

    # Check response status and structure
    assert response.status_code == 200

    response_data: dict = response.json()
    assert response_data["message"] == "Hello world events generated!"
    assert response_data["events_processed"] == 3
    assert response_data["events_failed"] == 2
    assert "total_time" in response_data

    # Verify total_time format and reasonable duration
    total_time_str = response_data["total_time"]
    assert total_time_str.endswith("s")
    total_time = float(total_time_str[:-1])  # Remove 's' and convert to float
    assert total_time > 0.1  # Should take at least 0.1s due to sleep calls
    assert total_time < 2.0  # Should complete within reasonable time


def test_metrics_test_endpoint(client: TestClient):
    """Test the metrics-test endpoint generates variety of metrics."""
    response: Response = client.post("/test/metrics-test")

    # Check response status and structure
    assert response.status_code == 200

    response_data: dict = response.json()
    assert response_data["message"] == "Test metrics generated!"
    assert response_data["queues_processed"] == 3
    assert response_data["total_events"] == 9  # 3 queues * (2 success + 1 failure)
    assert "total_time" in response_data

    # Verify total_time format and reasonable duration
    total_time_str = response_data["total_time"]
    assert total_time_str.endswith("s")
    total_time = float(total_time_str[:-1])
    assert total_time > 0.1  # Should take at least 0.1s due to sleep calls
    assert total_time < 1.0  # Should complete within reasonable time


def test_custom_event_endpoint(client: TestClient):
    """Test the custom-event endpoint generates custom metrics."""
    response: Response = client.post("/test/custom-event")

    # Check response status and structure
    assert response.status_code == 200

    response_data: dict = response.json()
    assert response_data["message"] == "Custom event metrics generated!"
    assert response_data["queue_name"] == "custom_test_queue"
    assert response_data["events_processed"] == 2
    assert response_data["events_failed"] == 1
    assert "total_time" in response_data

    # Verify total_time format and reasonable duration
    total_time_str = response_data["total_time"]
    assert total_time_str.endswith("s")
    total_time = float(total_time_str[:-1])
    assert total_time > 0.05  # Should take at least 0.05s due to sleep calls
    assert total_time < 0.5  # Should complete within reasonable time


def test_hello_world_endpoint_with_mocked_time(client: TestClient):
    """Test hello-world endpoint with mocked time to avoid actual delays."""
    with patch("time.sleep") as mock_sleep:
        response: Response = client.post("/test/hello-world")

        assert response.status_code == 200
        response_data: dict = response.json()

        # Verify sleep was called the expected number of times
        # 3 successful events + 2 failed events = 5 sleep calls
        assert mock_sleep.call_count == 5

        # Verify the response structure
        assert response_data["events_processed"] == 3
        assert response_data["events_failed"] == 2


def test_custom_event_endpoint_with_mocked_time(client: TestClient):
    """Test custom-event endpoint with mocked time to avoid actual delays."""
    with patch("time.sleep") as mock_sleep:
        response: Response = client.post("/test/custom-event")

        assert response.status_code == 200
        response_data: dict = response.json()

        # Verify sleep was called the expected number of times
        # 2 successful events + 1 failed event = 3 sleep calls
        assert mock_sleep.call_count == 3

        # Verify the response structure
        assert response_data["queue_name"] == "custom_test_queue"
        assert response_data["events_processed"] == 2
        assert response_data["events_failed"] == 1
