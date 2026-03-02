"""Test DB Logging"""

import logging
from unittest import mock

from oms_sensemaking.core import settings as core_settings
from oms_sensemaking.models.settings import Setting


@mock.patch("oms_sensemaking.core.settings.db_session")
def test_fetch_settings_from_db(mock_db_session):
    """Test DB fetch returns correct settings mapping"""

    mock_data = [
        Setting("rabbitmq_prefetch_count", 150),
        Setting("maximum_oms_api_calls", 500000),
    ]

    expected_output = {
        "rabbitmq_prefetch_count": 150,
        "maximum_oms_api_calls": 500000,
    }

    mock_db_session_instance = mock.MagicMock()
    mock_db_session_instance.query.return_value.all.return_value = mock_data
    mock_db_session.return_value.__enter__.return_value = mock_db_session_instance

    results = core_settings.fetch_settings_from_db()

    assert expected_output == results


@mock.patch("oms_sensemaking.core.settings.RUNTIME_SETTINGS")
@mock.patch("oms_sensemaking.core.settings.fetch_settings_from_db")
def test_load_runtime_settings_from_db_empty(mock_fetch, mock_runtime, caplog):
    """Ensure nothing happens when DB has no settings"""

    mock_fetch.return_value = {}

    caplog.set_level(logging.INFO)

    core_settings.load_runtime_settings_from_db()

    mock_runtime.bulk_set.assert_not_called()
    assert "No runtime settings found in DB" in caplog.text


@mock.patch("oms_sensemaking.core.settings.RUNTIME_SETTINGS")
@mock.patch("oms_sensemaking.core.settings.fetch_settings_from_db")
def test_load_runtime_settings_from_db_applies(mock_fetch, mock_runtime, caplog):
    """Ensure runtime settings are applied when DB has values"""

    mock_settings = {
        "rabbitmq_prefetch_count": 200,
        "maximum_oms_api_calls": 999999,
    }

    mock_fetch.return_value = mock_settings

    caplog.set_level(logging.INFO)

    core_settings.load_runtime_settings_from_db()

    mock_runtime.bulk_set.assert_called_once_with(mock_settings)
    assert "Applying runtime settings from DB" in caplog.text


@mock.patch("oms_sensemaking.core.settings.RUNTIME_SETTINGS")
@mock.patch("oms_sensemaking.core.settings.fetch_settings_from_db")
def test_load_runtime_settings_raw_values(mock_fetch, mock_runtime):
    """Ensure raw DB values are passed directly to runtime layer"""

    mock_settings = {"rabbitmq_prefetch_count": "250"}  # DB string

    mock_fetch.return_value = mock_settings

    core_settings.load_runtime_settings_from_db()

    mock_runtime.bulk_set.assert_called_once_with(mock_settings)


def test_apply_settings_updates_sets_state_and_triggers_handler():
    with (
        mock.patch.object(core_settings.RUNTIME_SETTINGS, "set") as mock_set,
        mock.patch.object(core_settings, "_handle_runtime_setting_change") as mock_handler,
    ):
        updates = {"a": 1, "b": 2}
        core_settings.apply_settings_updates(updates)

        mock_set.assert_any_call("a", 1)
        mock_set.assert_any_call("b", 2)
        assert mock_set.call_count == 2

        mock_handler.assert_any_call("a", 1)
        mock_handler.assert_any_call("b", 2)
        assert mock_handler.call_count == 2


def test_handle_runtime_setting_change_updates_listeners():
    mock_listener = mock.MagicMock()

    with mock.patch.object(core_settings, "LISTENERS", [mock_listener]):
        core_settings._handle_runtime_setting_change("rabbitmq_prefetch_count", 50)

        mock_listener.update_prefetch.assert_called_once_with(50)


def test_handle_runtime_setting_change_ignores_other_keys():
    mock_listener = mock.MagicMock()

    with mock.patch.object(core_settings, "LISTENERS", [mock_listener]):
        core_settings._handle_runtime_setting_change("other_setting", 10)

        mock_listener.update_prefetch.assert_not_called()


def test_handle_runtime_setting_change_handles_listener_exception():
    bad_listener = mock.MagicMock()
    bad_listener.update_prefetch.side_effect = Exception("boom")

    with (
        mock.patch.object(core_settings, "LISTENERS", [bad_listener]),
        mock.patch.object(core_settings.LOGGER, "exception") as mock_log,
    ):
        # Should not raise
        core_settings._handle_runtime_setting_change("rabbitmq_prefetch_count", 30)

        bad_listener.update_prefetch.assert_called_once_with(30)
        mock_log.assert_called_once()
