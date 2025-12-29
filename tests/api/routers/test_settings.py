"""Unit tests for settings API router endpoints."""

from unittest.mock import MagicMock, patch

from fastapi import Response
from fastapi.testclient import TestClient

from oms_sensemaking.api.routers.settings import update_settings
from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate
from oms_sensemaking.models.settings import Setting


class TestUpdateSettings:
    """Test class for update_settings endpoint."""

    def _create_mock_request(self, controllers=None, controller_threads=None):
        """Helper to create a mock Request object with app.state."""
        mock_request = MagicMock()
        mock_app = MagicMock()
        mock_state = MagicMock()
        mock_state.controllers = controllers or []
        mock_state.controller_threads = controller_threads or []
        mock_app.state = mock_state
        mock_request.app = mock_app
        return mock_request

    def test_create_new_setting(self):
        """Test creating a new setting when it doesn't exist."""
        settings_update = SettingsBatchUpdate(settings={"test_setting": 42})

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None  # Setting doesn't exist

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify database operations
            mock_db.query.assert_called_with(Setting)
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify the added setting
            added_setting = mock_db.add.call_args[0][0]
            assert isinstance(added_setting, Setting)
            assert added_setting.field_name == "test_setting"
            assert added_setting.field_value == 42

            # Verify controller operations
            mock_controller.stop.assert_called_once()
            mock_controller.update_settings.assert_called_once_with(mock_app_settings_instance)

    def test_update_existing_setting(self):
        """Test updating an existing setting."""
        settings_update = SettingsBatchUpdate(settings={"existing_setting": 100})

        mock_db = MagicMock()
        mock_query = MagicMock()
        existing_setting = Setting(field_name="existing_setting", field_value=50)
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = existing_setting

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify database operations
            assert existing_setting.field_value == 100
            mock_db.commit.assert_called_once()

            # Verify no new setting was added
            mock_db.add.assert_not_called()

    def test_create_setting_with_complex_value(self):
        """Test creating a setting with an integer value."""
        settings_update = SettingsBatchUpdate(settings={"complex_setting": 999})

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify the value was stored
            added_setting = mock_db.add.call_args[0][0]
            assert added_setting.field_value == 999


class TestUpdateSettingsBatch:
    """Test class for update_settings batch functionality."""

    def _create_mock_request(self, controllers=None, controller_threads=None):
        """Helper to create a mock Request object with app.state."""
        mock_request = MagicMock()
        mock_app = MagicMock()
        mock_state = MagicMock()
        mock_state.controllers = controllers or []
        mock_state.controller_threads = controller_threads or []
        mock_app.state = mock_state
        mock_request.app = mock_app
        return mock_request

    def test_create_multiple_new_settings(self):
        """Test creating multiple new settings."""
        settings_update = SettingsBatchUpdate(
            settings={
                "setting1": 10,
                "setting2": 42,
                "setting3": 100,
            }
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None  # All settings are new

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify three settings were added
            assert mock_db.add.call_count == 3
            mock_db.commit.assert_called_once()

    def test_update_multiple_existing_settings(self):
        """Test updating multiple existing settings."""
        settings_update = SettingsBatchUpdate(
            settings={
                "existing1": 200,
                "existing2": 300,
            }
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        existing1 = Setting(field_name="existing1", field_value=100)
        existing2 = Setting(field_name="existing2", field_value=150)

        # Mock query to return different settings based on filter
        def filter_side_effect(*args, **kwargs):
            filter_mock = MagicMock()
            # Return existing1 for first call, existing2 for second
            if mock_query.filter.call_count == 1:
                filter_mock.first.return_value = existing1
            else:
                filter_mock.first.return_value = existing2
            return filter_mock

        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = filter_side_effect

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify values were updated
            assert existing1.field_value == 200
            assert existing2.field_value == 300

            # Verify no new settings were added
            mock_db.add.assert_not_called()
            mock_db.commit.assert_called_once()

    def test_mixed_create_and_update(self):
        """Test batch update with mix of new and existing settings."""
        settings_update = SettingsBatchUpdate(
            settings={
                "existing_setting": 500,
                "new_setting": 600,
            }
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        existing_setting = Setting(field_name="existing_setting", field_value=400)

        # Mock query to return existing setting for first call, None for second
        def filter_side_effect(*args, **kwargs):
            filter_mock = MagicMock()
            if mock_query.filter.call_count == 1:
                filter_mock.first.return_value = existing_setting
            else:
                filter_mock.first.return_value = None
            return filter_mock

        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = filter_side_effect

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify existing setting was updated
            assert existing_setting.field_value == 500

            # Verify new setting was added
            assert mock_db.add.call_count == 1
            added_setting = mock_db.add.call_args[0][0]
            assert added_setting.field_name == "new_setting"
            assert added_setting.field_value == 600

            mock_db.commit.assert_called_once()

    def test_empty_batch_update(self):
        """Test batch update with empty settings dict."""
        settings_update = SettingsBatchUpdate(settings={})

        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        mock_request = self._create_mock_request(controllers=[mock_controller], controller_threads=[mock_thread])

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = update_settings(request=mock_request, body=settings_update)

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify no database operations when nothing to update
            mock_db_session.assert_not_called()


class TestSettingsEndpointsIntegration:
    """Integration tests for settings endpoints using TestClient."""

    def test_update_settings_endpoint(self, client: TestClient):
        """Test POST /settings endpoint through TestClient."""
        from oms_sensemaking.service import app

        # Setup app.state with mock controllers and threads
        mock_controller = MagicMock()
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        app.state.controllers = [mock_controller]
        app.state.controller_threads = [mock_thread]

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
            patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
        ):
            mock_db = MagicMock()
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value.first.return_value = None
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None
            mock_app_settings_instance = MagicMock()
            mock_app_settings.return_value = mock_app_settings_instance
            mock_new_thread = MagicMock()
            mock_thread_class.return_value = mock_new_thread

            response = client.post(
                "/settings",
                json={"settings": {"test_setting": 42}},
            )

            assert response.status_code == 201
            assert response.text == "Settings updated"
