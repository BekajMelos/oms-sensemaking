"""Unit tests for settings API router endpoints."""

from unittest.mock import MagicMock, patch

from fastapi import Response
from fastapi.testclient import TestClient

from oms_sensemaking.api.routers.settings import (
    create_or_update_setting,
    create_or_update_settings,
)
from oms_sensemaking.api.schemas.settings import SettingsBatchUpdate, SettingUpdate
from oms_sensemaking.models.settings import Setting


class TestCreateOrUpdateSetting:
    """Test class for create_or_update_setting endpoint."""

    def test_create_new_setting(self):
        """Test creating a new setting when it doesn't exist."""
        setting_update = SettingUpdate(field_name="test_setting", field_value=42)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None  # Setting doesn't exist

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_setting(setting=setting_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify database operations
            mock_db.query.assert_called_once_with(Setting)
            mock_query.filter.assert_called_once()
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify the added setting
            added_setting = mock_db.add.call_args[0][0]
            assert isinstance(added_setting, Setting)
            assert added_setting.field_name == "test_setting"
            assert added_setting.field_value == 42

            # Verify reload was called
            mock_reload.assert_called_once()

    def test_update_existing_setting(self):
        """Test updating an existing setting."""
        setting_update = SettingUpdate(field_name="existing_setting", field_value=100)

        mock_db = MagicMock()
        mock_query = MagicMock()
        existing_setting = Setting(field_name="existing_setting", field_value=50)
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = existing_setting

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_setting(setting=setting_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify database operations
            mock_db.query.assert_called_once_with(Setting)
            mock_query.filter.assert_called_once()
            assert existing_setting.field_value == 100
            mock_db.commit.assert_called_once()

            # Verify no new setting was added
            mock_db.add.assert_not_called()

            # Verify reload was called
            mock_reload.assert_called_once()

    def test_create_setting_with_complex_value(self):
        """Test creating a setting with an integer value."""
        setting_update = SettingUpdate(field_name="complex_setting", field_value=999)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_setting(setting=setting_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify the value was stored
            added_setting = mock_db.add.call_args[0][0]
            assert added_setting.field_value == 999

            mock_reload.assert_called_once()


class TestCreateOrUpdateSettings:
    """Test class for create_or_update_settings batch endpoint."""

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

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_settings(settings_update=settings_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify three settings were added
            assert mock_db.add.call_count == 3
            mock_db.commit.assert_called_once()

            # Verify reload was called
            mock_reload.assert_called_once()

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

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_settings(settings_update=settings_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify values were updated
            assert existing1.field_value == 200
            assert existing2.field_value == 300

            # Verify no new settings were added
            mock_db.add.assert_not_called()
            mock_db.commit.assert_called_once()

            mock_reload.assert_called_once()

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

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_settings(settings_update=settings_update, user_dn="test_user")

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
            mock_reload.assert_called_once()

    def test_empty_batch_update(self):
        """Test batch update with empty settings dict."""
        settings_update = SettingsBatchUpdate(settings={})

        mock_db = MagicMock()

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.check_user_dn_in_whitelist",
                return_value="test_user",
            ),
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db
            mock_db_session.return_value.__exit__.return_value = None

            response = create_or_update_settings(settings_update=settings_update, user_dn="test_user")

            assert isinstance(response, Response)
            assert response.status_code == 201

            # Verify no database operations when nothing to update
            mock_db_session.assert_not_called()
            mock_db.query.assert_not_called()
            mock_db.add.assert_not_called()
            mock_db.commit.assert_not_called()

            # Verify reload was not called when nothing changed
            mock_reload.assert_not_called()


class TestSettingsEndpointsIntegration:
    """Integration tests for settings endpoints using TestClient."""

    def test_create_setting_endpoint(self, client: TestClient):
        """Test POST /settings endpoint through TestClient."""
        from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
        from oms_sensemaking.service import app

        def mock_check_user_dn(user_dn: str = "test_user") -> str:
            return "test_user"

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            # Override the dependency
            app.dependency_overrides[check_user_dn_in_whitelist] = mock_check_user_dn

            try:
                mock_db = MagicMock()
                mock_query = MagicMock()
                mock_db.query.return_value = mock_query
                mock_query.filter.return_value.first.return_value = None
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings",
                    json={"field_name": "test_setting", "field_value": 42},
                    headers={"user_dn": "test_user"},
                )

                assert response.status_code == 201
                mock_reload.assert_called_once()
            finally:
                # Clean up dependency override
                app.dependency_overrides.clear()

    def test_batch_settings_endpoint(self, client: TestClient):
        """Test POST /settings/batch endpoint through TestClient."""
        from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
        from oms_sensemaking.service import app

        def mock_check_user_dn(user_dn: str = "test_user") -> str:
            return "test_user"

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch(
                "oms_sensemaking.api.routers.settings.service_module.reload_settings_and_restart_controllers"
            ) as mock_reload,
        ):
            # Override the dependency
            app.dependency_overrides[check_user_dn_in_whitelist] = mock_check_user_dn

            try:
                mock_db = MagicMock()
                mock_query = MagicMock()
                mock_db.query.return_value = mock_query
                mock_query.filter.return_value.first.return_value = None
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"setting1": 10, "setting2": 42}},
                    headers={"user_dn": "test_user"},
                )

                assert response.status_code == 201
                assert mock_db.add.call_count == 2
                mock_reload.assert_called_once()
            finally:
                # Clean up dependency override
                app.dependency_overrides.clear()
