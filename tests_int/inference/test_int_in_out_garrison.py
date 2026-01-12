"""
Integration tests for InOrOutOfGarrison.
These tests validate:
- Geometry + buffer evaluation (inside vs outside garrison)
- Activity creation vs update behavior
- Timeframe overlap logic
- Idempotency (no duplicate writes)
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from oms_sdk import DEFAULT_ACM
from oms_sdk.generated.generated_graphql_client import (
    ActivitiesActivitiesData,
    UpdateActivityInput,
    UpdateUuidList,
)

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.inference.rules.in_out_garrison import InOrOutOfGarrison


# Helpers
def make_garrison_data(
    *,
    object_lat_lon: list[float],
    garrison_lat_lon: list[float],
    activities: list[ActivitiesActivitiesData] | None = None,
):
    """
    Minimal stand-in for GetGarrisonDataAllAtOnce result.
    """
    return SimpleNamespace(
        object_lat_lon=object_lat_lon,
        garrison_lat_lon=garrison_lat_lon,
        activities=activities or [],
    )


# Fixtures
@pytest.fixture
def mock_crud_tool():
    crud = MagicMock(spec=OmsCrudTool)
    crud.create_activity = MagicMock()
    crud.update_activity = MagicMock()
    return crud


@pytest.fixture
def observation_inside_garrison(mocker):
    """
    Observation inside the garrison buffer.
    """
    obs = mocker.Mock()
    obs.id = "obs_inside"
    obs.nodeId = "object_1"
    obs.acm = DEFAULT_ACM
    obs.geometry = {"type": "Point", "coordinates": [-155.6235, 19.7023]}
    obs.startTime = "2025-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"
    return obs


@pytest.fixture
def observation_outside_garrison(mocker):
    """
    Observation outside the garrison buffer.
    """
    obs = mocker.Mock()
    obs.id = "obs_outside"
    obs.nodeId = "object_1"
    obs.acm = DEFAULT_ACM
    obs.geometry = {"type": "Point", "coordinates": [-77.10218, 38.88589]}
    obs.startTime = "2025-01-01T00:00:00+00:00"
    obs.endTime = "2025-01-01T00:00:00+00:00"
    return obs


@pytest.fixture
def existing_in_garrison_activity(mocker):
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "in_garrison_1"
    activity.nodeId = "object_1"
    activity.name = SETTINGS.inference_in_garrison_activity_name
    activity.state = SETTINGS.inference_in_garrison_activity_state
    activity.startTime = "2024-12-01T00:00:00+00:00"
    activity.endTime = "2025-02-01T00:00:00+00:00"
    activity.observationIds = ["old_obs"]
    return activity


@pytest.fixture
def existing_out_garrison_activity(mocker):
    activity = mocker.Mock(spec=ActivitiesActivitiesData)
    activity.id = "out_garrison_1"
    activity.nodeId = "object_1"
    activity.name = SETTINGS.inference_out_of_garrison_activity_name
    activity.state = SETTINGS.inference_out_of_garrison_activity_state
    activity.startTime = "2024-12-01T00:00:00+00:00"
    activity.endTime = "2025-02-01T00:00:00+00:00"
    activity.observationIds = ["old_obs"]
    return activity


# Integration Tests
def test_int_creates_new_in_garrison_activity(
    mock_crud_tool,
    observation_inside_garrison,
    mocker,
):
    """
    Observation inside garrison → new In-Garrison activity created.
    """
    mocker.patch(
        "oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data",
        return_value=make_garrison_data(
            object_lat_lon=[19.7023, -155.6235],
            garrison_lat_lon=[19.7006, -155.6212],
            activities=[],
        ),
    )
    sensemaker = InOrOutOfGarrison(mock_crud_tool)
    sensemaker.process_data(obs=observation_inside_garrison)
    mock_crud_tool.create_activity.assert_called_once()
    mock_crud_tool.update_activity.assert_not_called()


def test_int_creates_new_out_garrison_activity(
    mock_crud_tool,
    observation_outside_garrison,
    mocker,
):
    """
    Observation outside garrison → new Out-of-Garrison activity created.
    """
    mocker.patch(
        "oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data",
        return_value=make_garrison_data(
            object_lat_lon=[38.88589, -77.10218],
            garrison_lat_lon=[19.7006, -155.6212],
            activities=[],
        ),
    )
    sensemaker = InOrOutOfGarrison(mock_crud_tool)
    sensemaker.process_data(obs=observation_outside_garrison)
    mock_crud_tool.create_activity.assert_called_once()
    mock_crud_tool.update_activity.assert_not_called()


def test_int_updates_existing_in_garrison_activity(
    mock_crud_tool,
    observation_inside_garrison,
    existing_in_garrison_activity,
    mocker,
):
    """
    Observation inside garrison overlapping existing activity → update.
    """
    mocker.patch(
        "oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data",
        return_value=make_garrison_data(
            object_lat_lon=[19.7023, -155.6235],
            garrison_lat_lon=[19.7006, -155.6212],
            activities=[existing_in_garrison_activity],
        ),
    )
    sensemaker = InOrOutOfGarrison(mock_crud_tool)
    sensemaker.process_data(obs=observation_inside_garrison)
    mock_crud_tool.update_activity.assert_called_once_with(
        UpdateActivityInput(
            id=existing_in_garrison_activity.id,
            startTime=existing_in_garrison_activity.startTime,
            endTime=existing_in_garrison_activity.endTime,
            observationIds=UpdateUuidList(add=[observation_inside_garrison.id]),
            nodeId=observation_inside_garrison.nodeId,
        )
    )
    mock_crud_tool.create_activity.assert_not_called()


def test_int_skips_when_observation_already_processed(
    mock_crud_tool,
    observation_inside_garrison,
    existing_in_garrison_activity,
    mocker,
):
    """
    Idempotency: observation already in activity → no-op.
    """
    existing_in_garrison_activity.observationIds = [observation_inside_garrison.id]
    mocker.patch(
        "oms_sensemaking.inference.rules.in_out_garrison.GetGarrisonDataAllAtOnce.get_all_garrison_data",
        return_value=make_garrison_data(
            object_lat_lon=[19.7023, -155.6235],
            garrison_lat_lon=[19.7006, -155.6212],
            activities=[existing_in_garrison_activity],
        ),
    )
    sensemaker = InOrOutOfGarrison(mock_crud_tool)
    sensemaker.process_data(obs=observation_inside_garrison)
    mock_crud_tool.create_activity.assert_not_called()
    mock_crud_tool.update_activity.assert_not_called()
