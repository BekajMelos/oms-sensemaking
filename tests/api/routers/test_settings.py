"""Unit tests for settings API router endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.service import app


class TestUpdateSettingsBatch:
    """Test class for batch settings update endpoint."""

    def test_create_multiple_new_settings(self, client: TestClient):
        """Test creating multiple new settings."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None  # All settings are new

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"setting1": 10, "setting2": 42, "setting3": 100}},
                )

                assert response.status_code == 201

                # Verify three settings were added
                assert mock_db.add.call_count == 3
                mock_db.commit.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_update_multiple_existing_settings(self, client: TestClient):
        """Test updating multiple existing settings."""
        existing1 = Setting(field_name="existing1", field_value=100)
        existing2 = Setting(field_name="existing2", field_value=150)

        mock_db = MagicMock()
        mock_query = MagicMock()

        # Mock query to return different settings based on filter call count
        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            filter_mock = MagicMock()
            call_count[0] += 1
            # Return existing1 for first call, existing2 for second
            if call_count[0] == 1:
                filter_mock.first.return_value = existing1
            else:
                filter_mock.first.return_value = existing2
            return filter_mock

        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = filter_side_effect

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"existing1": 200, "existing2": 300}},
                )

                assert response.status_code == 201

                # Verify values were updated
                assert existing1.field_value == 200
                assert existing2.field_value == 300

                # Verify no new settings were added
                mock_db.add.assert_not_called()
                mock_db.commit.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_mixed_create_and_update(self, client: TestClient):
        """Test batch update with mix of new and existing settings."""
        existing_setting = Setting(field_name="existing_setting", field_value=400)

        mock_db = MagicMock()
        mock_query = MagicMock()

        # Mock query to return existing setting for first call, None for second
        call_count = [0]

        def filter_side_effect(*args, **kwargs):
            filter_mock = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                filter_mock.first.return_value = existing_setting
            else:
                filter_mock.first.return_value = None
            return filter_mock

        mock_db.query.return_value = mock_query
        mock_query.filter.side_effect = filter_side_effect

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"existing_setting": 500, "new_setting": 600}},
                )

                assert response.status_code == 201

                # Verify existing setting was updated
                assert existing_setting.field_value == 500

                # Verify new setting was added
                assert mock_db.add.call_count == 1
                added_setting = mock_db.add.call_args[0][0]
                assert added_setting.field_name == "new_setting"
                assert added_setting.field_value == 600

                mock_db.commit.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_empty_batch_update(self, client: TestClient):
        """Test batch update with empty settings dict."""
        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                response = client.post(
                    "/settings/batch",
                    json={"settings": {}},
                )

                assert response.status_code == 201

                # Verify no database operations when nothing to update
                mock_db_session.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    def test_create_new_setting(self, client: TestClient):
        """Test creating a new setting when it doesn't exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None  # Setting doesn't exist

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"test_setting": 42}},
                )

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
        finally:
            app.dependency_overrides.clear()

    def test_update_existing_setting(self, client: TestClient):
        """Test updating an existing setting."""
        existing_setting = Setting(field_name="existing_setting", field_value=50)
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = existing_setting

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"existing_setting": 100}},
                )

                assert response.status_code == 201

                # Verify database operations
                assert existing_setting.field_value == 100
                mock_db.commit.assert_called_once()

                # Verify no new setting was added
                mock_db.add.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    def test_create_setting_with_integer_value(self, client: TestClient):
        """Test creating a setting with an integer value."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"complex_setting": 999}},
                )

                assert response.status_code == 201

                # Verify the value was stored
                added_setting = mock_db.add.call_args[0][0]
                assert added_setting.field_value == 999
        finally:
            app.dependency_overrides.clear()


class TestSettingsEndpointsIntegration:
    """Integration tests for settings endpoints using TestClient."""

    def test_update_settings_batch_endpoint(self, client: TestClient):
        """Test POST /settings/batch endpoint through TestClient."""
        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

        try:
            with patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session:
                mock_db = MagicMock()
                mock_query = MagicMock()
                mock_db.query.return_value = mock_query
                mock_query.filter.return_value.first.return_value = None
                mock_db_session.return_value.__enter__.return_value = mock_db
                mock_db_session.return_value.__exit__.return_value = None

                response = client.post(
                    "/settings/batch",
                    json={"settings": {"test_setting": 42}},
                )

                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()
