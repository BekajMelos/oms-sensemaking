"""Tests for the healthcheck API"""

from pytest_mock import MockerFixture

from oms_sensemaking.clients.aac_client import AacClient
from oms_sensemaking.clients.instances import health_checker
from oms_sensemaking.core.oms_crud import OmsCrudTool


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
