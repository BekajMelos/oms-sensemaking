"""Tests for the "about" router."""
from fastapi.testclient import TestClient
from httpx import Response


def test_version_json(client: TestClient):
    response: Response = client.get('/version.json')
    assert response.status_code == 200

    version_info: dict = response.json()
    assert len(version_info.get('title', ''))
    assert len(version_info.get('version', ''))
    assert len(version_info.get('description', ''))
