from httpx import AsyncBaseTransport, BaseTransport
from oms_sdk.client_request_time_transport import AsyncClientRequestTimeTransport, ClientRequestTimeTransport
from oms_sdk.profiled_transport import ProfiledAsyncHTTPTransport, ProfiledHTTPTransport


def sync_transport_stack() -> type[BaseTransport]:
    class SyncStackTransport(ClientRequestTimeTransport):
        def __init__(self, *args, **kwargs):
            profiled_transport = ProfiledHTTPTransport(*args, **kwargs)
            super().__init__(transport=profiled_transport)

    return SyncStackTransport


def async_transport_stack() -> type[AsyncBaseTransport]:
    class AsyncStackTransport(AsyncClientRequestTimeTransport):
        def __init__(self, *args, **kwargs):
            profiled_transport = ProfiledAsyncHTTPTransport(*args, **kwargs)
            super().__init__(transport=profiled_transport)

    return AsyncStackTransport
