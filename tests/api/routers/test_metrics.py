from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_observability():
    """Mock observability components to prevent actual telemetry connections."""
    with (
        patch("oms_sensemaking.core.observability.initialize_observability") as mock_init,
        patch("oms_sensemaking.core.observability.instrument_fastapi") as mock_instrument,
        patch("oms_sensemaking.core.observability.record_queue_processing_time") as mock_queue_time,
        patch("oms_sensemaking.core.observability.record_event_processed") as mock_event_processed,
        patch("oms_sensemaking.core.observability.record_event_failed") as mock_event_failed,
        patch("oms_sensemaking.core.observability.REQUESTS_PROCESSING_TIME") as mock_requests_time,
        patch("oms_sensemaking.core.observability.REQUESTS_TOTAL") as mock_requests_total,
    ):
        mock_init.return_value = None
        mock_instrument.return_value = None
        mock_queue_time.return_value = None
        mock_event_processed.return_value = None
        mock_event_failed.return_value = None

        mock_requests_time.labels.return_value.observe = MagicMock()
        mock_requests_total.labels.return_value.inc = MagicMock()

        yield {
            "init": mock_init,
            "instrument": mock_instrument,
            "queue_time": mock_queue_time,
            "event_processed": mock_event_processed,
            "event_failed": mock_event_failed,
        }


class TestMetricsEndpoints:
    """Test class for metrics generation endpoints."""

    def test_connectivity(self, client: TestClient) -> None:
        """Test basic connectivity to the service."""
        # Test basic service endpoint
        response = client.get("/version.json")
        assert response.status_code == 200, "Service should be accessible"

    def test_hello_world_endpoint(self, client: TestClient) -> None:
        """Test the hello-world metrics endpoint."""
        response = client.post("/test/hello-world")

        # Check if test endpoints are enabled
        if response.status_code == 404:
            pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "message" in data
        assert "events_processed" in data
        assert "events_failed" in data
        assert "total_time" in data

        assert data["events_processed"] == 3
        assert data["events_failed"] == 2
        assert "Hello world events generated!" in data["message"]

    def test_metrics_test_endpoint(self, client: TestClient) -> None:
        """Test the metrics-test endpoint."""
        response = client.post("/test/metrics-test")

        if response.status_code == 404:
            pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "message" in data
        assert "queues_processed" in data
        assert "total_events" in data
        assert "total_time" in data

        assert data["queues_processed"] == 3
        assert data["total_events"] == 9  # 3 queues * 3 events each
        assert "Test metrics generated!" in data["message"]

    def test_custom_event_endpoint(self, client: TestClient) -> None:
        """Test the custom-event endpoint with different queue names."""
        queue_names = ["test_queue_1", "test_queue_2", "production_queue"]

        for queue_name in queue_names:
            response = client.post(f"/test/custom-event?queue_name={queue_name}")

            if response.status_code == 404:
                pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

            assert (
                response.status_code == 200
            ), f"Expected 200 for queue {queue_name}, got {response.status_code}: {response.text}"

            data = response.json()
            assert "message" in data
            assert "queue_name" in data
            assert "events_processed" in data
            assert "events_failed" in data
            assert "total_time" in data

            assert data["queue_name"] == queue_name
            assert data["events_processed"] == 2
            assert data["events_failed"] == 1
            assert "Custom event metrics generated!" in data["message"]

    def test_custom_event_json_endpoint(self, client: TestClient) -> None:
        """Test the custom-event-json endpoint with different payloads."""
        test_payloads = [
            {"queue_name": "json_queue_1", "events_processed": 3, "events_failed": 1},
            {"queue_name": "json_queue_2", "events_processed": 5, "events_failed": 2},
            {"queue_name": "high_volume_queue", "events_processed": 10, "events_failed": 0},
        ]

        for i, payload in enumerate(test_payloads):
            response = client.post("/test/custom-event-json", json=payload)

            if response.status_code == 404:
                pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

            assert (
                response.status_code == 200
            ), f"Expected 200 for payload {i+1}, got {response.status_code}: {response.text}"

            data = response.json()
            assert "message" in data
            assert "queue_name" in data
            assert "events_processed" in data
            assert "events_failed" in data
            assert "total_time" in data
            assert "request_data" in data

            assert data["queue_name"] == payload["queue_name"]
            assert data["events_processed"] == payload["events_processed"]
            assert data["events_failed"] == payload["events_failed"]
            assert data["request_data"] == payload
            assert "Custom event metrics generated from JSON!" in data["message"]

    def test_metrics_generation_sequence(self, client: TestClient) -> None:
        """Test a sequence of metrics generation calls to simulate real usage."""
        # Test if endpoints are available first
        response = client.post("/test/hello-world")
        if response.status_code == 404:
            pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

        # Generate hello world metrics
        response = client.post("/test/hello-world")
        assert response.status_code == 200
        hello_data = response.json()
        assert hello_data["events_processed"] == 3
        assert hello_data["events_failed"] == 2

        # Generate basic metrics
        response = client.post("/test/metrics-test")
        assert response.status_code == 200
        metrics_data = response.json()
        assert metrics_data["queues_processed"] == 3

        # Generate custom event metrics
        response = client.post("/test/custom-event?queue_name=sequence_test")
        assert response.status_code == 200
        custom_data = response.json()
        assert custom_data["queue_name"] == "sequence_test"

        # Generate JSON custom metrics
        json_payload = {"queue_name": "sequence_json", "events_processed": 4, "events_failed": 1}
        response = client.post("/test/custom-event-json", json=json_payload)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["queue_name"] == "sequence_json"
        assert json_data["events_processed"] == 4
        assert json_data["events_failed"] == 1

    def test_error_handling(self, client: TestClient) -> None:
        """Test error handling for invalid requests."""
        # Test with invalid JSON payload
        response = client.post("/test/custom-event-json", json={"invalid": "data"})

        if response.status_code == 404:
            pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

        # Should still work with default values
        assert response.status_code == 200
        data = response.json()
        assert data["queue_name"] == "default_queue"  # Default value
        assert data["events_processed"] == 2  # Default value
        assert data["events_failed"] == 1  # Default value

    def test_endpoint_performance(self, client: TestClient) -> None:
        """Test that endpoints respond within reasonable time limits."""
        response = client.post("/test/hello-world")

        if response.status_code == 404:
            pytest.skip("Test endpoints are disabled. Set TOGGLE_TEST_ENDPOINTS=true to enable them.")

        assert response.status_code == 200

        # Check that the total_time in response is reasonable (should be less than 2 seconds)
        data = response.json()
        total_time_str = data["total_time"]
        total_time_seconds = float(total_time_str.replace("s", ""))
        assert total_time_seconds < 2.0, f"Endpoint took too long: {total_time_seconds}s"
