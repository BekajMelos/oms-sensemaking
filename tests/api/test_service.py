# Copyright {{ cookiecutter.copyright_year }} {{ cookiecutter.copyright_owner }}.
# Use of this software is governed by the LICENSE.md file.

"""Tests for the service application."""

from unittest import mock
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, FastAPI, status
from fastapi.testclient import TestClient
from httpx import Response

import oms_sensemaking.service as service_module
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.service import check_aoi_file_path, create_app, get_controllers

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


def test_get_controllers_builds_listeners_and_controllers(monkeypatch):
    fake_settings = mock.MagicMock()
    fake_settings.rethrow_errors_enabled = False
    fake_settings.rmq_geo_queue_name = "geo-q"
    fake_settings.rmq_inference_queue_name = "inf-q"
    fake_settings.rmq_res_queue_name = "res-q"
    fake_settings.queue_worker_threads = 3
    fake_settings.iw_settings.observable_query_interval = 5
    fake_settings.mil_symbol_settings.rmq_mil_symbol_queue_name = "mil-q"
    fake_settings.object_standards_settings.rmq_object_standards_queue_name = "obj-q"
    fake_settings.in_port_settings.rmq_in_port_queue_name = "inp-q"

    monkeypatch.setattr("oms_sensemaking.config.SETTINGS", fake_settings)
    monkeypatch.setattr("oms_sensemaking.core.runtime_settings.RUNTIME_SETTINGS.get", lambda k: 10)

    with (
        mock.patch.object(service_module, "RabbitMQListener") as mock_listener,
        mock.patch.object(service_module, "register_listener") as mock_register,
        mock.patch.object(service_module, "CronEventEmitter"),
        mock.patch.object(service_module, "GeospatialSensemakerController") as geospatial,
        mock.patch.object(service_module, "InferenceSensemakerController") as inference,
        mock.patch.object(service_module, "ResolutionSensemakerController") as resolution,
        mock.patch.object(service_module, "MilSymbolSensemakerController") as mil_symbol,
        mock.patch.object(service_module, "ObjectStandardsSensemakerController") as object_standards,
        mock.patch.object(service_module, "InPortSensemakerController") as in_port,
        mock.patch.object(service_module, "ObservableSensemakerController") as observable,
    ):
        # Each listener instance should be unique
        listener_instances = [mock.MagicMock() for _ in range(6)]
        mock_listener.side_effect = listener_instances

        controllers = get_controllers()

        # 5 RMQ listeners registered
        assert mock_register.call_count == 6

        # Prefetch applied to each listener
        for listener in listener_instances:
            listener.update_prefetch.assert_called_once_with(10)

        # controllers returned
        assert len(controllers) == 7

        # Controllers constructed
        geospatial.assert_called_once()
        inference.assert_called_once()
        resolution.assert_called_once()
        mil_symbol.assert_called_once()
        object_standards.assert_called_once()
        in_port.assert_called_once()
        observable.assert_called_once()
