from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from oms_sensemaking.models.settings import Setting
from oms_sensemaking.service import app


def test_create_setting(client: TestClient):
    payload = {"settings": {"maximum_oms_api_calls": 5000}}

    # Setup app.state with mock controllers and threads
    mock_controller = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = False
    app.state.controllers = [mock_controller]
    app.state.controller_threads = [mock_thread]

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None  # new row

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
        patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
        patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db
        mock_app_settings_instance = MagicMock()
        mock_app_settings.return_value = mock_app_settings_instance
        mock_new_thread = MagicMock()
        mock_thread_class.return_value = mock_new_thread

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


def test_update_setting(client: TestClient):
    payload = {"settings": {"maximum_oms_api_calls": 5000}}

    # Setup app.state with mock controllers and threads
    mock_controller = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = False
    app.state.controllers = [mock_controller]
    app.state.controller_threads = [mock_thread]

    existing = Setting(field_name="maximum_oms_api_calls", field_value=100)

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = existing

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
        patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
        patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db
        mock_app_settings_instance = MagicMock()
        mock_app_settings.return_value = mock_app_settings_instance
        mock_new_thread = MagicMock()
        mock_thread_class.return_value = mock_new_thread

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        assert existing.field_value == 5000
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()


def test_batch_create_settings(client: TestClient):
    payload = {"settings": {"setting1": 10, "setting2": 42}}

    # Setup app.state with mock controllers and threads
    mock_controller = MagicMock()
    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = False
    app.state.controllers = [mock_controller]
    app.state.controller_threads = [mock_thread]

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value.first.return_value = None  # all new

    with (
        patch("oms_sensemaking.api.routers.settings.db_session") as mock_db_session,
        patch("oms_sensemaking.api.routers.settings.AppSettings") as mock_app_settings,
        patch("oms_sensemaking.api.routers.settings.Thread") as mock_thread_class,
    ):
        mock_db_session.return_value.__enter__.return_value = mock_db
        mock_app_settings_instance = MagicMock()
        mock_app_settings.return_value = mock_app_settings_instance
        mock_new_thread = MagicMock()
        mock_thread_class.return_value = mock_new_thread

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()


def test_batch_empty(client: TestClient):
    payload = {"settings": {}}

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
        mock_app_settings_instance = MagicMock()
        mock_app_settings.return_value = mock_app_settings_instance
        mock_new_thread = MagicMock()
        mock_thread_class.return_value = mock_new_thread

        response = client.post("/settings", json=payload)

        assert response.status_code == 201
        mock_db_session.assert_not_called()
