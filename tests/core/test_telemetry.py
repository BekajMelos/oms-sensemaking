from unittest.mock import MagicMock, patch

from oms_sensemaking.core.telemetry import (
    TelemetryManager,
    get_telemetry_manager,
    initialize_telemetry,
    record_processing_completion,
    record_processing_failure,
    record_processing_success,
)


class TestTelemetryManager:
    """Test the TelemetryManager class"""

    def test_telemetry_manager_initialization_success(self):
        """Test successful initialization of TelemetryManager"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            # Mock the OpenTelemetry setup
            with (
                patch("oms_sensemaking.core.telemetry.InMemoryMetricReader") as mock_reader,
                patch("oms_sensemaking.core.telemetry.MeterProvider") as mock_provider,
                patch("oms_sensemaking.core.telemetry.metrics.set_meter_provider") as mock_set_provider,
                patch("oms_sensemaking.core.telemetry.metrics.get_meter") as mock_get_meter,
            ):
                mock_meter = MagicMock()
                mock_get_meter.return_value = mock_meter

                manager = TelemetryManager()

                # Verify OpenTelemetry was set up
                mock_reader.assert_called_once()
                mock_provider.assert_called_once()
                mock_set_provider.assert_called_once()
                mock_get_meter.assert_called_once()

                # Verify metrics were created
                assert manager.meter is not None
                assert manager.queue_processing_time is not None
                assert manager.events_processed is not None
                assert manager.events_failed is not None

    def test_telemetry_manager_initialization_disabled(self):
        """Test TelemetryManager initialization when telemetry is disabled"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = False

            manager = TelemetryManager()

            # Verify telemetry is disabled
            assert manager.meter is None
            assert manager.queue_processing_time is None
            assert manager.events_processed is None
            assert manager.events_failed is None

    def test_telemetry_manager_initialization_failure(self):
        """Test TelemetryManager initialization when OpenTelemetry setup fails"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            # Mock OpenTelemetry setup to fail
            with patch("oms_sensemaking.core.telemetry.InMemoryMetricReader") as mock_reader:
                # Make the setup fail
                mock_reader.side_effect = Exception("OpenTelemetry setup failed")

                manager = TelemetryManager()

                # This test verifies that the manager handles the failure gracefully
                assert manager is not None

    def test_record_queue_processing_time_success(self):
        """Test successful recording of queue processing time"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            manager = TelemetryManager()
            manager.queue_processing_time = MagicMock()

            # Test recording processing time
            manager.record_queue_processing_time("test-queue", 0.123)

            # Verify the metric was recorded
            manager.queue_processing_time.record.assert_called_once_with(0.123, attributes={"queue_name": "test-queue"})

    def test_record_queue_processing_time_disabled(self):
        """Test queue processing time recording when telemetry is disabled"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = False

            manager = TelemetryManager()
            manager.queue_processing_time = MagicMock()

            # Test recording processing time (should do nothing)
            manager.record_queue_processing_time("test-queue", 0.123)

            # Verify the metric was not recorded
            manager.queue_processing_time.record.assert_not_called()

    def test_record_event_processed_success(self):
        """Test successful recording of event processed"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            manager = TelemetryManager()
            manager.events_processed = MagicMock()

            # Test recording event processed
            manager.record_event_processed("test-queue")

            # Verify the metric was incremented
            manager.events_processed.add.assert_called_once_with(1, attributes={"queue_name": "test-queue"})

    def test_record_event_failed_success(self):
        """Test successful recording of event failed"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            manager = TelemetryManager()
            manager.events_failed = MagicMock()

            # Test recording event failed
            manager.record_event_failed("test-queue")

            # Verify the metric was incremented
            manager.events_failed.add.assert_called_once_with(1, attributes={"queue_name": "test-queue"})

    def test_record_queue_processing_time_exception_handling(self):
        """Test exception handling in queue processing time recording"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            manager = TelemetryManager()
            manager.queue_processing_time = MagicMock()
            manager.queue_processing_time.record.side_effect = Exception("Metric recording failed")

            # Test recording should not raise exception
            manager.record_queue_processing_time("test-queue", 0.123)

            # Verify the metric was attempted to be recorded
            manager.queue_processing_time.record.assert_called_once()


class TestTelemetryFunctions:
    """Test the telemetry utility functions"""

    def test_get_telemetry_manager_singleton(self):
        """Test that get_telemetry_manager returns the same instance"""
        # Reset the global variable
        import oms_sensemaking.core.telemetry as telemetry_module

        telemetry_module.telemetry_manager = None

        manager1 = get_telemetry_manager()
        manager2 = get_telemetry_manager()

        assert manager1 is manager2

    def test_initialize_telemetry(self):
        """Test telemetry initialization"""
        # Reset the global variable
        import oms_sensemaking.core.telemetry as telemetry_module

        telemetry_module.telemetry_manager = None

        with patch("oms_sensemaking.core.telemetry.get_telemetry_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            initialize_telemetry()

            mock_get_manager.assert_called_once()

    def test_record_processing_completion_success(self):
        """Test successful processing completion recording"""
        with (
            patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings,
            patch("oms_sensemaking.core.telemetry.get_telemetry_manager") as mock_get_manager,
            patch("time.time") as mock_time,
        ):
            mock_settings.enable_telemetry = True
            mock_time.return_value = 100.5

            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            start_time = 100.0
            record_processing_completion("test-queue", start_time, success=True)

            # Verify processing time was recorded
            mock_manager.record_queue_processing_time.assert_called_once_with("test-queue", 0.5)
            # Verify event processed was recorded
            mock_manager.record_event_processed.assert_called_once_with("test-queue")
            # Verify event failed was not recorded
            mock_manager.record_event_failed.assert_not_called()

    def test_record_processing_completion_failure(self):
        """Test failed processing completion recording"""
        with (
            patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings,
            patch("oms_sensemaking.core.telemetry.get_telemetry_manager") as mock_get_manager,
            patch("time.time") as mock_time,
        ):
            mock_settings.enable_telemetry = True
            mock_time.return_value = 100.5

            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager

            start_time = 100.0
            record_processing_completion("test-queue", start_time, success=False)

            # Verify processing time was recorded
            mock_manager.record_queue_processing_time.assert_called_once_with("test-queue", 0.5)
            # Verify event failed was recorded
            mock_manager.record_event_failed.assert_called_once_with("test-queue")
            # Verify event processed was not recorded
            mock_manager.record_event_processed.assert_not_called()

    def test_record_processing_completion_disabled(self):
        """Test processing completion recording when telemetry is disabled"""
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = False

            # Should not raise any exceptions or call any telemetry methods
            record_processing_completion("test-queue", 100.0, success=True)

    def test_record_processing_success(self):
        """Test record_processing_success helper function"""
        with patch("oms_sensemaking.core.telemetry.record_processing_completion") as mock_record:
            record_processing_success("test-queue", 100.0)

            mock_record.assert_called_once_with("test-queue", 100.0, success=True)

    def test_record_processing_failure(self):
        """Test record_processing_failure helper function"""
        with patch("oms_sensemaking.core.telemetry.record_processing_completion") as mock_record:
            record_processing_failure("test-queue", 100.0)

            mock_record.assert_called_once_with("test-queue", 100.0, success=False)

    def test_record_processing_completion_exception_handling(self):
        """Test exception handling in processing completion recording"""
        with (
            patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings,
            patch("oms_sensemaking.core.telemetry.get_telemetry_manager") as mock_get_manager,
            patch("time.time") as mock_time,
        ):
            mock_settings.enable_telemetry = True
            mock_time.return_value = 100.5

            mock_manager = MagicMock()
            mock_manager.record_queue_processing_time.side_effect = Exception("Telemetry failed")
            mock_get_manager.return_value = mock_manager

            start_time = 100.0

            # Should not raise exception
            record_processing_completion("test-queue", start_time, success=True)


class TestTelemetryIntegration:
    """Test telemetry integration with real OpenTelemetry components"""

    def test_real_opentelemetry_metrics_creation(self):
        """Test that real OpenTelemetry metrics can be created"""
        # This test verifies the actual OpenTelemetry integration works
        with patch("oms_sensemaking.core.telemetry.SETTINGS") as mock_settings:
            mock_settings.enable_telemetry = True

            # Create a real TelemetryManager instance
            manager = TelemetryManager()

            # Verify metrics were created with correct names and descriptions
            if manager.queue_processing_time:
                assert manager.queue_processing_time.name == "queue_processing_time_seconds"
                expected_desc = "Time from reading object from queue to being processed"
                assert expected_desc in manager.queue_processing_time.description
                assert manager.queue_processing_time.unit == "s"

            if manager.events_processed:
                assert manager.events_processed.name == "events_processed_total"
                assert "Total number of events processed by queue" in manager.events_processed.description
                assert manager.events_processed.unit == "1"

            if manager.events_failed:
                assert manager.events_failed.name == "events_failed_total"
                assert "Total number of events that failed processing" in manager.events_failed.description
                assert manager.events_failed.unit == "1"

    def test_telemetry_manager_thread_safety(self):
        """Test that telemetry manager can be accessed from multiple threads"""
        import queue
        import threading

        results = queue.Queue()

        def worker():
            try:
                manager = get_telemetry_manager()
                results.put(("success", manager is not None))
            except Exception as e:
                results.put(("error", str(e)))

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        while not results.empty():
            status, result = results.get()
            assert status == "success"
            assert result is True
