"""Tests for the "about" router."""

from fastapi.testclient import TestClient
from httpx import Response


def test_aac_cache_clear_no_user_dn(client: TestClient):
    response: Response = client.post("/aac/clear")
    assert response.status_code == 401


def test_aac_cache_clear_invalid_user_dn(client: TestClient):
    response: Response = client.post("/aac/clear", headers={"user_dn": "invalid_user_dn"})
    assert response.status_code == 401


def test_aac_cache_clear_unauthorized_dn(client: TestClient):
    # real DN but not in whitelist
    response: Response = client.post(
        "/aac/clear", headers={"user_dn": "cn=test01,ou=jade,ou=meme,o=bia,st=maryland,c=us"}
    )
    assert response.status_code == 401


def test_aac_cache_clear_valid_user_dn(client: TestClient):
    response: Response = client.post(
        "/aac/clear", headers={"user_dn": "cn=test10,ou=jade,ou=meme,o=bia,st=maryland,c=us"}
    )
    assert response.status_code == 204
