import pytest
from typing import Iterator
from fastapi.testclient import TestClient

from oms_sensemaking.service import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Yields a FastAPI TestClient."""
    yield TestClient(app)
