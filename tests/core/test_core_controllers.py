from threading import Event
from unittest.mock import MagicMock, patch

import pytest

from oms_sensemaking.core.controllers import SensemakerController


@pytest.fixture
def mock_event_consumer():
    consumer = MagicMock()
    consumer.handle_event = None
    return consumer


@pytest.fixture
def mock_err_logger():
    return MagicMock()


@pytest.fixture
def controller(mock_event_consumer, mock_err_logger):
    return SensemakerController(mock_event_consumer, mock_err_logger)


def test_init_sets_stopped(controller, mock_event_consumer):
    assert isinstance(controller.stopped, Event)
    assert controller.stopped.is_set()  # should start in stopped state
    assert mock_event_consumer.handle_event == controller.handle_event


def test_register_and_unregister(controller):
    sensemaker = MagicMock()
    assert controller.register("alpha", sensemaker) is True
    assert "alpha" in controller._registry

    # duplicate register
    assert controller.register("alpha", sensemaker) is False

    # unregister
    assert controller.unregister("alpha") is True
    assert "alpha" not in controller._registry
    assert controller.unregister("doesnotexist") is False


def test_start_and_stop(controller, mock_event_consumer):
    controller.start()
    assert controller.is_running is True
    mock_event_consumer.start.assert_called_once()

    controller.stop()
    assert controller.is_running is False
    mock_event_consumer.stop.assert_called_once()


def test_get_oms_data_calls_rehydrate(controller):
    with patch.object(controller.oms_crud_tool, "rehydrate_oms_obj", return_value="mock_obj") as mock_rehydrate:
        event = MagicMock()
        event.objectId = "123"
        event.objectType = "Node"
        result = controller.get_oms_data(event)
        assert result == "mock_obj"
        mock_rehydrate.assert_called_once_with("123", "Node")


def test_handle_event_success(controller):
    mock_oms_obj = MagicMock()
    controller.get_oms_data = MagicMock(return_value=mock_oms_obj)

    sensemaker = MagicMock()
    controller.register("alpha", sensemaker)

    event = MagicMock()
    event.objectId = "123"
    event.objectType = "Node"

    result = controller.handle_event(event)

    assert result is True
    sensemaker.execute.assert_called_once_with(mock_oms_obj)


def test_handle_event_object_not_found(controller, mock_err_logger):
    controller.get_oms_data = MagicMock(return_value=None)
    event = MagicMock()
    event.objectId = "123"
    event.objectType = "Node"

    result = controller.handle_event(event)

    assert result is False
    mock_err_logger.log_error.assert_not_called()


def test_handle_event_error_retrieving_object(controller, mock_err_logger):
    controller.get_oms_data = MagicMock(side_effect=Exception("API failure"))
    event = MagicMock()
    event.objectId = "123"
    event.objectType = "Node"

    result = controller.handle_event(event)

    assert result is False
    mock_err_logger.log_error.assert_called_once()
    args, kwargs = mock_err_logger.log_error.call_args
    assert "API failure" in str(args[3])  # check exception logged


def test_handle_event_error_during_execution(controller, mock_err_logger):
    mock_oms_obj = MagicMock()
    controller.get_oms_data = MagicMock(return_value=mock_oms_obj)

    bad_sensemaker = MagicMock()
    bad_sensemaker.execute.side_effect = Exception("Execution failed")
    controller.register("bad", bad_sensemaker)

    event = MagicMock()
    event.objectId = "123"
    event.objectType = "Node"

    result = controller.handle_event(event)

    assert result is True  # returns True even if execution fails
    mock_err_logger.log_error.assert_called_once()
