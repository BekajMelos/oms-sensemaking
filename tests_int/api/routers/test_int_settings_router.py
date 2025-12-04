from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from oms_sensemaking.api.routers.utils import check_user_dn_in_whitelist
from oms_sensemaking.models.settings import Setting
from oms_sensemaking.service import app


def test_create_setting(client: TestClient):
    payload = {
        "field_name": "maximum_oms_api_calls",
        "field_value": 5000,
    }

    app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "mock-user"

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None  # new row

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


def test_update_setting(client: TestClient):
    payload = {
        "field_name": "maximum_oms_api_calls",
        "field_value": 5000,
    }

    app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "mock-user"

    existing = Setting(field_name="maximum_oms_api_calls", field_value=100)

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = existing

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        assert existing.field_value == 5000
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


def test_batch_create_settings(client: TestClient):
    payload = {"settings": {"setting1": 10, "setting2": 42}}

    app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "mock-user"

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None  # all new

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db

        response = client.post("/settings/batch", json=payload)

        assert response.status_code == 201
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    app.dependency_overrides.clear()


def test_batch_empty(client: TestClient):
    payload = {"settings": {}}

    app.dependency_overrides[check_user_dn_in_whitelist] = lambda: "mock-user"

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
    ):
        response = client.post("/settings/batch", json=payload)

        assert response.status_code == 201

        mock_db_session.assert_not_called()

    app.dependency_overrides.clear()
