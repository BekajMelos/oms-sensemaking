"""Unit tests for service settings reload and controller restart functions."""

from threading import Thread
from unittest.mock import MagicMock, patch

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.service import (
    _controller_lock,
    _controller_threads,
    reload_settings_and_restart_controllers,
    reload_settings_from_db,
    restart_controllers,
)


class TestReloadSettingsFromDb:
    """Test class for reload_settings_from_db function."""

    @patch("oms_sensemaking.service.DBSettings")
    def test_reload_settings_with_changes(self, mock_db_settings_class):
        """Test reloading settings when database has changes."""
        # Store original value
        original_value = getattr(SETTINGS, "generate_inferences", None)

        # Mock database settings
        mock_db_settings = MagicMock()
        mock_db_settings.get_settings.return_value = {
            "generate_inferences": True,
            "detect_loiters": False,
        }
        mock_db_settings_class.return_value = mock_db_settings

        # Mock model_fields by setting it directly on the SETTINGS instance
        # This bypasses the class attribute lookup
        original_model_fields = getattr(SETTINGS.__class__, "model_fields", None)
        try:
            SETTINGS.__class__.model_fields = {
                "generate_inferences": None,
                "detect_loiters": None,
            }
            # Set initial values
            object.__setattr__(SETTINGS, "generate_inferences", False)
            object.__setattr__(SETTINGS, "detect_loiters", True)

            reload_settings_from_db()

            # Verify settings were updated
            assert SETTINGS.generate_inferences is True
            assert SETTINGS.detect_loiters is False

            mock_db_settings.get_settings.assert_called_once()
        finally:
            # Restore original model_fields
            if original_model_fields is not None:
                SETTINGS.__class__.model_fields = original_model_fields
            # Restore original value if it existed
            if original_value is not None:
                object.__setattr__(SETTINGS, "generate_inferences", original_value)

    @patch("oms_sensemaking.service.DBSettings")
    def test_reload_settings_no_changes(self, mock_db_settings_class):
        """Test reloading settings when values haven't changed."""
        mock_db_settings = MagicMock()
        mock_db_settings.get_settings.return_value = {
            "generate_inferences": True,
        }
        mock_db_settings_class.return_value = mock_db_settings

        # Set the value to match what's in DB
        original_model_fields = getattr(SETTINGS.__class__, "model_fields", None)
        try:
            SETTINGS.__class__.model_fields = {"generate_inferences": None}
            object.__setattr__(SETTINGS, "generate_inferences", True)

            reload_settings_from_db()

            # Value should still be True (no change)
            assert SETTINGS.generate_inferences is True
        finally:
            if original_model_fields is not None:
                SETTINGS.__class__.model_fields = original_model_fields

    @patch("oms_sensemaking.service.DBSettings")
    def test_reload_settings_empty_db(self, mock_db_settings_class):
        """Test reloading settings when database is empty."""
        mock_db_settings = MagicMock()
        mock_db_settings.get_settings.return_value = {}
        mock_db_settings_class.return_value = mock_db_settings

        original_value = getattr(SETTINGS, "generate_inferences", None)
        original_model_fields = getattr(SETTINGS.__class__, "model_fields", None)

        try:
            SETTINGS.__class__.model_fields = {"generate_inferences": None}
            object.__setattr__(SETTINGS, "generate_inferences", False)

            reload_settings_from_db()

            # Value should remain unchanged
            assert SETTINGS.generate_inferences is False
        finally:
            if original_model_fields is not None:
                SETTINGS.__class__.model_fields = original_model_fields
            if original_value is not None:
                object.__setattr__(SETTINGS, "generate_inferences", original_value)

    @patch("oms_sensemaking.service.DBSettings")
    def test_reload_settings_skips_invalid_fields(self, mock_db_settings_class):
        """Test that invalid fields are skipped during reload."""
        mock_db_settings = MagicMock()
        mock_db_settings.get_settings.return_value = {
            "valid_field": True,
            "invalid_field": False,  # Not in model_fields
            "field__with_double_underscore": True,  # Should be skipped
        }
        mock_db_settings_class.return_value = mock_db_settings

        original_model_fields = getattr(SETTINGS.__class__, "model_fields", None)
        try:
            SETTINGS.__class__.model_fields = {"valid_field": None}
            object.__setattr__(SETTINGS, "valid_field", False)

            reload_settings_from_db()

            # Only valid_field should be updated
            assert SETTINGS.valid_field is True
            # Invalid fields should not cause errors
        finally:
            if original_model_fields is not None:
                SETTINGS.__class__.model_fields = original_model_fields

    @patch("oms_sensemaking.service.DBSettings")
    @patch("oms_sensemaking.service.LOGGER")
    def test_reload_settings_handles_exception(self, mock_logger, mock_db_settings_class):
        """Test that exceptions during reload are handled gracefully."""
        mock_db_settings = MagicMock()
        mock_db_settings.get_settings.side_effect = Exception("Database error")
        mock_db_settings_class.return_value = mock_db_settings

        original_value = getattr(SETTINGS, "generate_inferences", None)

        # Should not raise exception
        reload_settings_from_db()

        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "Failed to reload settings" in str(mock_logger.warning.call_args[0][0])

        if original_value is not None:
            object.__setattr__(SETTINGS, "generate_inferences", original_value)


class TestRestartControllers:
    """Test class for restart_controllers function."""

    @patch("oms_sensemaking.service.get_controllers")
    @patch("oms_sensemaking.service.run_controller")
    @patch("oms_sensemaking.service.LOGGER")
    def test_restart_controllers_stops_and_starts(self, mock_logger, mock_run_controller, mock_get_controllers):
        """Test that controllers are stopped and restarted."""
        # Create mock controllers
        mock_controller1 = MagicMock(spec=SensemakerController)
        mock_controller2 = MagicMock(spec=SensemakerController)
        mock_controller1.__class__.__name__ = "MockController1"
        mock_controller2.__class__.__name__ = "MockController2"

        # Create mock threads
        mock_thread1 = MagicMock(spec=Thread)
        mock_thread1.is_alive.side_effect = [True, False]  # Alive first, then dead after join
        mock_thread2 = MagicMock(spec=Thread)
        mock_thread2.is_alive.side_effect = [True, False]  # Alive first, then dead after join

        # Set up existing controllers
        with _controller_lock:
            _controller_threads.clear()
            _controller_threads.append((mock_controller1, mock_thread1))
            _controller_threads.append((mock_controller2, mock_thread2))

        # Mock new controllers
        new_controller1 = MagicMock(spec=SensemakerController)
        new_controller2 = MagicMock(spec=SensemakerController)
        new_controller1.__class__.__name__ = "NewController1"
        new_controller2.__class__.__name__ = "NewController2"
        mock_get_controllers.return_value = [new_controller1, new_controller2]

        # Mock thread creation
        new_thread1 = MagicMock(spec=Thread)
        new_thread2 = MagicMock(spec=Thread)

        with (
            patch("oms_sensemaking.service.Thread") as mock_thread_class,
            patch("oms_sensemaking.service._controller_threads", _controller_threads),
        ):
            mock_thread_class.side_effect = [new_thread1, new_thread2]

            restart_controllers()

            # Verify old controllers were stopped
            mock_controller1.stop.assert_called_once()
            mock_controller2.stop.assert_called_once()

            # Verify threads were joined
            mock_thread1.join.assert_called_once_with(timeout=5.0)
            mock_thread2.join.assert_called_once_with(timeout=5.0)

            # Verify new controllers were created
            mock_get_controllers.assert_called_once()

            # Verify new threads were started
            assert mock_thread_class.call_count == 2
            new_thread1.start.assert_called_once()
            new_thread2.start.assert_called_once()

    @patch("oms_sensemaking.service.get_controllers")
    @patch("oms_sensemaking.service.run_controller")
    @patch("oms_sensemaking.service.LOGGER")
    def test_restart_controllers_handles_alive_thread(self, mock_logger, mock_run_controller, mock_get_controllers):
        """Test that alive threads are handled properly."""
        mock_controller = MagicMock(spec=SensemakerController)
        mock_controller.__class__.__name__ = "MockController"

        mock_thread = MagicMock(spec=Thread)
        mock_thread.is_alive.return_value = True  # Thread is still alive

        with _controller_lock:
            _controller_threads.clear()
            _controller_threads.append((mock_controller, mock_thread))

        new_controller = MagicMock(spec=SensemakerController)
        new_controller.__class__.__name__ = "NewController"
        mock_get_controllers.return_value = [new_controller]

        new_thread = MagicMock(spec=Thread)

        with (
            patch("oms_sensemaking.service.Thread", return_value=new_thread),
            patch("oms_sensemaking.service._controller_threads", _controller_threads),
        ):
            restart_controllers()

            # Verify thread join was called
            mock_thread.join.assert_called_once_with(timeout=5.0)

    @patch("oms_sensemaking.service.get_controllers")
    @patch("oms_sensemaking.service.run_controller")
    @patch("oms_sensemaking.service.LOGGER")
    def test_restart_controllers_handles_thread_timeout(self, mock_logger, mock_run_controller, mock_get_controllers):
        """Test that thread timeout is handled."""
        mock_controller = MagicMock(spec=SensemakerController)
        mock_controller.__class__.__name__ = "MockController"

        mock_thread = MagicMock(spec=Thread)
        mock_thread.is_alive.side_effect = [True, True]  # Still alive after join

        with _controller_lock:
            _controller_threads.clear()
            _controller_threads.append((mock_controller, mock_thread))

        new_controller = MagicMock(spec=SensemakerController)
        new_controller.__class__.__name__ = "NewController"
        mock_get_controllers.return_value = [new_controller]

        new_thread = MagicMock(spec=Thread)

        with (
            patch("oms_sensemaking.service.Thread", return_value=new_thread),
            patch("oms_sensemaking.service._controller_threads", _controller_threads),
        ):
            restart_controllers()

            # Verify warning was logged
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            assert any("did not stop in time" in str(call) for call in warning_calls)

    @patch("oms_sensemaking.service.get_controllers")
    @patch("oms_sensemaking.service.run_controller")
    def test_restart_controllers_with_no_existing_controllers(self, mock_run_controller, mock_get_controllers):
        """Test restarting when no controllers exist."""
        with _controller_lock:
            _controller_threads.clear()

        new_controller = MagicMock(spec=SensemakerController)
        new_controller.__class__.__name__ = "NewController"
        mock_get_controllers.return_value = [new_controller]

        new_thread = MagicMock(spec=Thread)

        with (
            patch("oms_sensemaking.service.Thread", return_value=new_thread),
            patch("oms_sensemaking.service._controller_threads", _controller_threads),
        ):
            restart_controllers()

            # Should still create new controllers
            mock_get_controllers.assert_called_once()
            new_thread.start.assert_called_once()


class TestReloadSettingsAndRestartControllers:
    """Test class for reload_settings_and_restart_controllers function."""

    @patch("oms_sensemaking.service.restart_controllers")
    @patch("oms_sensemaking.service.reload_settings_from_db")
    @patch("oms_sensemaking.service.LOGGER")
    def test_reload_and_restart_calls_both_functions(self, mock_logger, mock_reload, mock_restart):
        """Test that both reload and restart are called."""
        reload_settings_and_restart_controllers()

        mock_reload.assert_called_once()
        mock_restart.assert_called_once()

        # Verify logging
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Reloading settings and restarting controllers" in str(call) for call in info_calls)
        assert any("Settings reload and controller restart complete" in str(call) for call in info_calls)

    @patch("oms_sensemaking.service.restart_controllers")
    @patch("oms_sensemaking.service.reload_settings_from_db")
    def test_reload_and_restart_order(self, mock_reload, mock_restart):
        """Test that reload happens before restart."""
        call_order = []

        def track_reload():
            call_order.append("reload")

        def track_restart():
            call_order.append("restart")

        mock_reload.side_effect = track_reload
        mock_restart.side_effect = track_restart

        reload_settings_and_restart_controllers()

        assert call_order == ["reload", "restart"]
