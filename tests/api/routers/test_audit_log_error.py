"""Tests for the "audit_log_errors" router."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from oms_sensemaking.api.routers.audit_log_error import check_user_dn_in_whitelist, get_audit_log_errors
from oms_sensemaking.clients.audit_log_error_client import AuditLogErrorClient

MOCK_DATA = [{"id": 1, "message": "Sample error"}]


def mock_check_user_dn_in_whitelist():
    return "user_dn"


@pytest.fixture
def override_user_dn_check(sensemaking_app):
    sensemaking_app.dependency_overrides[check_user_dn_in_whitelist] = mock_check_user_dn_in_whitelist

    yield

    # reset the dependency override
    sensemaking_app.dependency_overrides[check_user_dn_in_whitelist] = {}


@patch("oms_sensemaking.api.routers.audit_log_error.AuditLogErrorClient.get_audit_log_errors", return_value=MOCK_DATA)
def test_get_audit_log_errors_direct_success(mock_get_audit_log_errors):
    result = get_audit_log_errors("user_dn", AuditLogErrorClient(), exception_name=None, page=1, pagesize=500)

    assert result == MOCK_DATA


@patch("oms_sensemaking.api.routers.audit_log_error.AuditLogErrorClient.get_audit_log_errors", return_value=MOCK_DATA)
def test_get_audit_log_errors(mock_get_audit_log_errors, override_user_dn_check, client: TestClient):
    params = {
        "exception_name": "TypeError",
        "created_at_start": "2026-01-01T00:00:00+00:00",
        "created_at_end": "2026-01-04T00:00:00+00:00",
    }

    response: Response = client.get("/audit", params=params)
    assert response.status_code == 200


@patch("oms_sensemaking.api.routers.audit_log_error.AuditLogErrorClient.delete_audit_log_errors", return_value=2)
def test_delete_audit_log_errors(mock_delete_audit_log_errors, override_user_dn_check, client: TestClient):
    params = {
        "exception_name": "TypeError",
        "created_at_start": "2026-01-01T00:00:00+00:00",
        "created_at_end": "2026-01-04T00:00:00+00:00",
    }

    response: Response = client.delete("/audit", params=params, headers={"user_dn": "test"})
    assert response.status_code == 200
    assert response.json() == {"deleted_count": 2}
