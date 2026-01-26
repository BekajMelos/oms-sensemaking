from fastapi.testclient import TestClient
from httpx import Response


def test_healthcheck_endpoint(client: TestClient):
    response: Response = client.get("/healthcheck")
    assert response.status_code == 200

    data: dict = response.json()

    # Basic structure validation
    assert "atoms" in data
    assert "aac" in data
    assert "db" in data
