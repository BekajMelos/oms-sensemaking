from datetime import datetime, timedelta, timezone

import pytest
from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client import ObservationObservation
from pytest_mock import MockerFixture

from oms_sensemaking.models.geo import decompose_observation_geometry


@pytest.fixture
def mock_observation(mocker: MockerFixture) -> ObservationObservation:
    oms_obs = mocker.Mock(spec=ObservationObservation)
    oms_obs.geometry = mocker.Mock()
    oms_obs.startTime = mocker.Mock()
    oms_obs.endTime = mocker.Mock()

    return oms_obs


def test_single_point(mock_observation: ObservationObservation):
    oms_obs = mock_observation
    oms_obs.geometry = {
        "type": "Point",
        "coordinates": [-77.04007, 38.85109],
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    }
    time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    oms_obs.startTime = time.isoformat()
    oms_obs.endTime = time.isoformat()

    timed_coords = decompose_observation_geometry(oms_obs)
    assert len(timed_coords) == 1
    assert timed_coords[0]["detection_time"] == time


def test_zero_time(mock_observation: ObservationObservation):
    oms_obs = mock_observation

    coordinates = [[-77.00000, 38.00000], [-77.00000, 38.50000], [-77.00000, 39.00000]]
    oms_obs.geometry = {
        "type": "LineString",
        "coordinates": coordinates,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    }

    time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    oms_obs.startTime = time.isoformat()
    oms_obs.endTime = time.isoformat()

    timed_coords = decompose_observation_geometry(oms_obs)
    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert all(tc["detection_time"] == time for tc in timed_coords)


def test_zero_distance(mock_observation: ObservationObservation):
    oms_obs = mock_observation
    coordinates = [[-77.00000, 38.00000], [-77.00000, 38.00000], [-77.00000, 38.00000]]
    oms_obs.geometry = {
        "type": "LineString",
        "coordinates": coordinates,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    }

    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=1)
    oms_obs.startTime = start_time.isoformat()
    oms_obs.endTime = end_time.isoformat()

    timed_coords = decompose_observation_geometry(oms_obs)
    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert [tc["detection_time"] for tc in timed_coords] == [start_time, start_time + timedelta(minutes=30), end_time]


def test_normal_linestring(mock_observation: ObservationObservation):
    oms_obs = mock_observation
    coordinates = [[-77.00000, 38.00000], [-77.00000, 39.00000], [-77.00000, 39.50000]]
    oms_obs.geometry = {
        "type": "LineString",
        "coordinates": coordinates,
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
    }

    start_time = isoparse("2022-12-01T00:20:14.000Z").replace(tzinfo=timezone.utc)
    end_time = start_time + timedelta(hours=1, minutes=30)
    oms_obs.startTime = start_time.isoformat()
    oms_obs.endTime = end_time.isoformat()

    timed_coords = decompose_observation_geometry(oms_obs)

    def round_time_seconds(dt: datetime) -> datetime:
        dt = dt.replace(second=int(round(dt.second + dt.microsecond / 1000000)), microsecond=0)
        return dt

    assert [tc["coordinates"] for tc in timed_coords] == coordinates
    assert [round_time_seconds(tc["detection_time"]) for tc in timed_coords] == [
        start_time,
        start_time + timedelta(hours=1),
        end_time,
    ]
