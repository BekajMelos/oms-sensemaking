from httpx import AsyncHTTPTransport, BaseTransport, HTTPTransport


class SyncTransportStack(BaseTransport):
    def __init__(self, *args, **kwargs):
        self.transport = HTTPTransport(*args, **kwargs)


class AsyncTransportStack(BaseTransport):
    def __init__(self, *args, **kwargs):
        self.transport = AsyncHTTPTransport(*args, **kwargs)
