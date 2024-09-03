# Copyright {{ cookiecutter.copyright_year }} {{ cookiecutter.copyright_owner }}.
# Use of this software is governed by the LICENSE.md file.

"""Tests for the service application."""
import pytest
from fastapi import APIRouter, FastAPI, status
from fastapi.testclient import TestClient
from httpx import Response

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.service import create_app

router: APIRouter = APIRouter()


class DummyError(Exception):
    """
    A dummy error.

    This class can be used to test unexpected server exceptions.
    """
    pass


@router.get('/boom')
def raise_exception():
    raise DummyError('boom!')


def test_app_with_exception():
    app: FastAPI = create_app(SETTINGS)

    app.include_router(router)
    client: TestClient = TestClient(app)

    with pytest.raises(DummyError):
        response: Response = client.get('/boom')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.headers.get('content-type') == 'application/json'
