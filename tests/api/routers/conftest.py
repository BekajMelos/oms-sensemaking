"""PyTest Configuration."""
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from oms_sensemaking.service import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yield a FastAPI TestClient."""
    yield TestClient(app)
