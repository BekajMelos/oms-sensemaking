from unittest.mock import ANY, MagicMock, patch

from oms_sensemaking.clients.instances import ping_db, ping_db_host_wait  # adjust import


@patch("oms_sensemaking.clients.instances.db_session")
@patch("oms_sensemaking.clients.instances.LOGGER")
def test_ping_db_success(logger_mock, db_session_mock):
    mock_conn = MagicMock()
    db_session_mock.return_value.__enter__.return_value = mock_conn

    result = ping_db()

    assert result is True
    mock_conn.execute.assert_any_call(ANY)  # statement timeout + SELECT 1
    logger_mock.info.assert_called_once_with("DB connectivity check successful")


@patch("oms_sensemaking.clients.instances.db_session", side_effect=Exception("db down"))
@patch("oms_sensemaking.clients.instances.LOGGER")
def test_ping_db_failure(logger_mock, db_session_mock):
    result = ping_db()

    assert result is False
    logger_mock.warning.assert_called_once()
    assert "db down" in str(logger_mock.warning.call_args[0][1])


@patch("oms_sensemaking.clients.instances.BaseClient")
def test_ping_db_host_wait_success(base_client_mock):
    mock_client = MagicMock()
    mock_client.wait_until_ready.return_value = True
    base_client_mock.return_value = mock_client

    result = ping_db_host_wait()

    assert result is True
    mock_client.wait_until_ready.assert_called_once()


@patch("oms_sensemaking.clients.instances.BaseClient")
def test_ping_db_host_wait_failure(base_client_mock):
    mock_client = MagicMock()
    mock_client.wait_until_ready.return_value = False
    base_client_mock.return_value = mock_client

    result = ping_db_host_wait()

    assert result is False
    mock_client.wait_until_ready.assert_called_once()


@patch("oms_sensemaking.clients.instances.BaseClient", side_effect=Exception("network error"))
@patch("oms_sensemaking.clients.instances.LOGGER")
def test_ping_db_host_wait_exception(logger_mock, base_client_mock):
    result = ping_db_host_wait()

    assert result is False
    logger_mock.warning.assert_called_once()
    assert "network error" in str(logger_mock.warning.call_args[0][1])
