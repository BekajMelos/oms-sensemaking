from unittest.mock import MagicMock

import hishel
import httpx
import pytest

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.config import SETTINGS


@pytest.fixture
def client():
    # Basic client with caching disabled by default
    c = AacClient(
        cert_path=SETTINGS.cert_path,
        key_path=SETTINGS.key_path,
        ca_cert_path=SETTINGS.cacert_path,
        verification_mode=SETTINGS.aac_verification_mode,
    )
    return c


def test_dedup_acms(client):
    acms = [
        {"foo": "bar"},
        {"foo": "bar"},
        {"baz": "qux"},
    ]
    deduped = client._dedup_acms(acms)

    assert {"foo": "bar"} in deduped
    assert {"baz": "qux"} in deduped
    assert len(deduped) == 2


def test_get_new_caching_transport(client):
    transport = client._get_new_caching_transport()
    assert isinstance(transport, hishel.CacheTransport)


def test_get_acm_rollup_success(client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"RollupACM": {"foo": "rolled"}}

    client.client = MagicMock()
    client.client.post.return_value = mock_response

    result = client.get_acm_rollup([{"id": 1}])
    assert result == {"foo": "rolled"}
    client.client.post.assert_called_once()


def test_clear_cache_enabled(monkeypatch, client):
    monkeypatch.setattr(
        "oms_sensemaking.clients.aac_client.SETTINGS",
        type("S", (), {"aac_cache_enabled": True, "aac_cache_storage_ttl_seconds": 10}),
    )
    client.verify = True

    old_client = client.client
    client.clear_cache()

    # Should replace the client with a new one
    assert isinstance(client.client, httpx.Client)
    assert client.client is not old_client


def test_clear_cache_disabled(monkeypatch, client, caplog):
    monkeypatch.setattr("oms_sensemaking.clients.aac_client.SETTINGS", type("S", (), {"aac_cache_enabled": False}))
    old_client = client.client

    with caplog.at_level("INFO"):
        client.clear_cache()

    assert "Cache not enabled" in caplog.text
    assert client.client is old_client
