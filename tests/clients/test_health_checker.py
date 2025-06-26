"""Tests for the healthcheck API"""
from unittest import mock

from pytest_mock import MockerFixture

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.instances import health_checker
from oms_sensemaking.core.logging.handlers import DatabaseHandler
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.nlp.corenlp_client import CoreNlpClient


@mock.patch("oms_sensemaking.core.logging.handlers.DatabaseHandler.emit")
def test_services_healthy(mock_database_logger: DatabaseHandler, mocker: MockerFixture):
    expected = "healthy"
    services = [
        {"test_spec": OmsCrudTool, "spec_attribute": "get_nodes", "health_method": health_checker.get_oms_health},
        {
            "test_spec": CoreNlpClient,
            "spec_attribute": "annotate_document_str",
            "health_method": health_checker.get_nlp_health,
        },
        {
            "test_spec": AacClient,
            "spec_attribute": "get_acm_rollup",
            "health_method": health_checker.get_aac_health,
        },
    ]

    for service in services:
        service_class = service.get("test_spec")
        mocked_service = mocker.Mock(spec=service_class)
        mock = mocker.patch.object(mocked_service, service.get("spec_attribute"), spec=service_class)
        actual = service.get("health_method")(mocked_service)

        assert actual == expected
        mock.assert_called_once()


@mock.patch("oms_sensemaking.core.logging.handlers.DatabaseHandler.emit")
def test_services_unhealthy(mock_database_logger: DatabaseHandler, mocker: MockerFixture):
    status_msg = "Unable to communicate with"
    services = [
        {
            "test_spec": OmsCrudTool,
            "spec_attribute": "get_nodes",
            "health_method": health_checker.get_oms_health,
            "expected": f"{status_msg} OMS",
        },
        {
            "test_spec": CoreNlpClient,
            "spec_attribute": "annotate_document_str",
            "health_method": health_checker.get_nlp_health,
            "expected": f"{status_msg} NLP Service",
        },
        {
            "test_spec": AacClient,
            "spec_attribute": "get_acm_rollup",
            "health_method": health_checker.get_aac_health,
            "expected": f"{status_msg} AAC Service",
        },
    ]

    for service in services:
        service_class = service.get("test_spec")
        mocked_service = mocker.Mock(spec=service_class)
        mock = mocker.patch.object(
            mocked_service, service.get("spec_attribute"), spec=service_class, side_effect=Exception("mocked error")
        )
        actual = service.get("health_method")(mocked_service)

        assert actual == service.get("expected")
        mock.assert_called_once()
