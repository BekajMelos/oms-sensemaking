from httpx import AsyncBaseTransport, BaseTransport
from oms_sdk.client_request_time_transport import AsyncClientRequestTimeTransport, ClientRequestTimeTransport
from oms_sdk.profiled_transport import ProfiledAsyncHTTPTransport, ProfiledHTTPTransport


def sync_transport_stack() -> BaseTransport:
    profiled_transport = ProfiledHTTPTransport()
    stack = ClientRequestTimeTransport(transport=profiled_transport)
    return stack


async def async_transport_stack() -> AsyncBaseTransport:
    profiled_transport = ProfiledAsyncHTTPTransport()
    stack = AsyncClientRequestTimeTransport(transport=profiled_transport)
    return await stack
