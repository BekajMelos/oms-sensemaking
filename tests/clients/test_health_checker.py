"""Tests for the healthcheck API"""

import pytest
from pytest_mock import MockerFixture

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.instances import health_checker, parse_pool_status
from oms_sensemaking.core.oms_crud import OmsCrudTool


@pytest.fixture
def db_metrics():
    metrics = {
        "db_metrics": {
            "current_overflow": -9,
            "pool_status": {
                "Pool size": 10,
                "Connections in pool": 1,
                "Current Overflow": -9,
                "Current Checked out connections": 0,
            },
        }
    }
    return metrics


def test_services_healthy(mocker: MockerFixture):
    expected = "healthy"
    services = [
        {"test_spec": OmsCrudTool, "spec_attribute": "get_nodes", "health_method": health_checker.get_oms_health},
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


def test_services_unhealthy(mocker: MockerFixture):
    status_msg = "Unable to communicate with"
    services = [
        {
            "test_spec": OmsCrudTool,
            "spec_attribute": "get_nodes",
            "health_method": health_checker.get_oms_health,
            "expected": f"{status_msg} ATOMS",
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


def test_db_health(mocker: MockerFixture):
    # Healthy DB
    healthy_ping = mocker.Mock(return_value=True)
    result = health_checker.get_db_health(healthy_ping)
    assert result == "healthy"
    healthy_ping.assert_called_once()

    # Unhealthy DB (ping returns False)
    unhealthy_ping = mocker.Mock(return_value=False)
    result = health_checker.get_db_health(unhealthy_ping)
    assert result == "Unable to communicate with DB Service"
    unhealthy_ping.assert_called_once()

    # DB throws an exception
    error_ping = mocker.Mock(side_effect=Exception("db down"))
    result = health_checker.get_db_health(error_ping)
    assert result == "Unable to communicate with DB Service"
    error_ping.assert_called_once()


def test_get_db_metrics(mocker: MockerFixture):
    # DB Metrics
    metrics = mocker.Mock(return_value=db_metrics)
    result = health_checker.get_db_metrics(metrics)
    assert result == db_metrics
    metrics.assert_called_once()

    # DB throws an exception
    error_metrics = mocker.Mock(side_effect=Exception("error on metrics"))
    result = health_checker.get_db_metrics(error_metrics)
    assert result == "Unable to communicate with DB Metrics"
    error_metrics.assert_called_once()


def test_parse_pool_status():
    input_status = "Pool: 4 Checked out: 5 Overflow: 1"
    expected_result = {"Pool": 4, "Checked out": 5, "Overflow": 1}
    result = parse_pool_status(input_status)
    assert result == expected_result
