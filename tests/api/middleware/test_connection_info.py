from fastapi.datastructures import Headers
from pytest_mock import MockerFixture

from oms_sensemaking.api.middleware.connection_info import HeaderAddressConnectionInfo


class MockRequest:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers: Headers = Headers(headers)


def test_header_address_connection_info(mocker: MockerFixture):
    header_conn_info = HeaderAddressConnectionInfo()

    request = MockRequest({"X-Forwarded-For": "172.16.43.264,https://example.com"})
    conn_info = header_conn_info.get_connection_info(request)

    assert conn_info.host == "172.16.43.264"

    request = MockRequest({"X-Real-IP": "172.23.43.164"})
    conn_info = header_conn_info.get_connection_info(request)

    assert conn_info.host == "172.23.43.164"


def test_no_headers_connection():
    header_conn_info = HeaderAddressConnectionInfo()
    request = MockRequest({})
    conn_info = header_conn_info.get_connection_info(request)
    assert conn_info.host == "Unknown"
