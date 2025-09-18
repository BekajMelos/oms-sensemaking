# Copyright {{ cookiecutter.copyright_year }} {{ cookiecutter.copyright_owner }}.
# Use of this software is governed by the LICENSE.md file.

"""Tests for the service application."""

from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, FastAPI, status
from fastapi.testclient import TestClient
from httpx import Response

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.service import check_aoi_file_path, create_app

router: APIRouter = APIRouter()


class DummyError(Exception):
    """
    A dummy error.

    This class can be used to test unexpected server exceptions.
    """

    pass


@router.get("/boom")
def raise_exception():
    raise DummyError("boom!")


def test_app_with_exception():
    app: FastAPI = create_app(SETTINGS)

    app.include_router(router)
    client: TestClient = TestClient(app)

    with pytest.raises(DummyError):
        response: Response = client.get("/boom")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.headers.get("content-type") == "application/json"


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("oms_sensemaking.config.SETTINGS", mock)
    return mock


def test_check_aoi_file_path_valid_dir(mock_settings, monkeypatch):
    mock_settings.toggle_incursion_rule = True
    mock_settings.inference_incursion_areas_of_interest_path = "/fake/path"

    monkeypatch.setattr("os.path.isdir", lambda _: True)

    # should not exit when path is valid
    check_aoi_file_path()


def test_check_aoi_file_path_invalid_dir_exits(mock_settings, monkeypatch):
    mock_settings.toggle_incursion_rule = True
    mock_settings.inference_incursion_areas_of_interest_path = "/bad/path"

    monkeypatch.setattr("os.path.isdir", lambda _: False)

    with pytest.raises(SystemExit) as e:
        check_aoi_file_path()

    assert "incorrect or does not exist" in str(e.value)


def test_check_aoi_file_path_skips_when_toggle_off(mock_settings, monkeypatch):
    mock_settings.toggle_incursion_rule = False
    mock_settings.inference_incursion_areas_of_interest_path = "/fake/path"

    monkeypatch.setattr("os.path.isdir", lambda _: True)

    # should silently pass because toggle is False
    check_aoi_file_path()
