from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.service import app


class TestSettingsRouter:
    """Unit tests for settings API router endpoints."""

    def setup_method(self):
        app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "test_user"

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_empty_patch_no_db_no_runtime(self, client: TestClient):
        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.apply_settings_updates") as mock_runtime,
        ):
            response = client.patch("/settings", json={"settings": {}})

            assert response.status_code == 204
            mock_db_session.assert_not_called()
            mock_runtime.assert_not_called()

    def test_create_new_settings(self, client: TestClient):
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = None

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.apply_settings_updates") as mock_runtime,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db

            response = client.patch(
                "/settings",
                json={"settings": {"a": 1, "b": 2}},
            )

            assert response.status_code == 204
            assert mock_db.add.call_count == 2
            mock_db.commit.assert_called_once()
            mock_runtime.assert_called_once_with({"a": 1, "b": 2})

    def test_update_existing_settings(self, client: TestClient):
        existing = Setting(field_name="a", field_value=10)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = existing

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.apply_settings_updates") as mock_runtime,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db

            response = client.patch("/settings", json={"settings": {"a": 20}})

            assert response.status_code == 204
            assert existing.field_value == 20
            mock_db.add.assert_not_called()
            mock_db.commit.assert_called_once()
            mock_runtime.assert_called_once_with({"a": 20})

    def test_mixed_create_and_update(self, client: TestClient):
        existing = Setting(field_name="a", field_value=10)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query

        def filter_side_effect(*args, **kwargs):
            m = MagicMock()
            if filter_side_effect.calls == 0:
                m.first.return_value = existing
            else:
                m.first.return_value = None
            filter_side_effect.calls += 1
            return m

        filter_side_effect.calls = 0
        mock_query.filter.side_effect = filter_side_effect

        with (
            patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
            patch("oms_sensemaking.api.routers.settings.apply_settings_updates") as mock_runtime,
        ):
            mock_db_session.return_value.__enter__.return_value = mock_db

            response = client.patch("/settings", json={"settings": {"a": 20, "b": 30}})

            assert response.status_code == 204
            assert existing.field_value == 20
            assert mock_db.add.call_count == 1
            mock_db.commit.assert_called_once()
            mock_runtime.assert_called_once_with({"a": 20, "b": 30})

    def test_get_settings(self, client: TestClient):
        with patch("oms_sensemaking.api.routers.settings.fetch_settings_from_db") as mock_fetch:
            mock_fetch.return_value = {"a": "10", "b": "20"}

            response = client.get("/settings")

            assert response.status_code == 200
            assert response.json() == {"a": "10", "b": "20"}
