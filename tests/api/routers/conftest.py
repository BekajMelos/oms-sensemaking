"""PyTest Configuration."""

from collections.abc import Iterator
from unittest import mock

import pytest
from fastapi.testclient import TestClient

with (
    mock.patch("oms_sensemaking.core.observability.initialize_observability"),
    mock.patch("oms_sensemaking.core.observability.instrument_fastapi"),
):
    from oms_sensemaking.service import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yield a FastAPI TestClient."""
    yield TestClient(app)
