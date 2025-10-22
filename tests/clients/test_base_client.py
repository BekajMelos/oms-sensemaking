import pytest
from pytest_mock import MockerFixture

from oms_sensemaking.clients.base_client import BaseClient


def test_ping_success(mocker: MockerFixture):
    mocker.patch("oms_sensemaking.clients.base_client.BaseClient._resolve_host", return_value="1.1.1.1")
    client = BaseClient("host", 80, "TestService")

    mock_create_connection = mocker.patch("oms_sensemaking.clients.base_client.socket.create_connection")
    mock_socket = mocker.MagicMock()
    mock_create_connection.return_value = mock_socket

    assert client.ping()


def test_ping_failure(mocker: MockerFixture):
    mocker.patch("oms_sensemaking.clients.base_client.BaseClient._resolve_host", return_value="1.1.1.1")
    client = BaseClient("host", 80, "TestService")

    mock_create_connection = mocker.patch("oms_sensemaking.clients.base_client.socket.create_connection")
    mock_create_connection.side_effect = TimeoutError("Mocked timeout error")

    assert not client.ping(), "Expected socket create_connection to timeout"


@pytest.mark.parametrize("ping_result, expected_value", [(True, True), (False, False)])
def test_wait_until_ready_failure(ping_result: bool, expected_value: bool, mocker: MockerFixture):
    mocker.patch("oms_sensemaking.clients.base_client.BaseClient.ping", return_value=ping_result)
    mocker.patch("oms_sensemaking.clients.base_client.time.sleep", return_value=None)

    client = BaseClient("host", 80, "TestService")

    assert client.wait_until_ready() == expected_value
