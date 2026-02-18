"""Tests for loiter sensemaker."""

import random
from unittest.mock import MagicMock
from uuid import uuid4

import shapely
from geoalchemy2.shape import to_shape
from oms_sdk.generated.generated_graphql_client.client import CreateActivityCreateActivity
from sqlalchemy import select
from sqlalchemy.orm import Session

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers.loiters import Loiter, LoiterSensemaker
from oms_sensemaking.models.geo import Track
from oms_sensemaking.models.sensemaking import AtomsType, Finding, FindingType
from tests_int.conftest import rollup_unclass_acm_3_0
from tests_int.geospatial.helper import TimeLocation

ROLLUP_DEFAULT_ACM = rollup_unclass_acm_3_0()


def get_random_stamford_bridge_point() -> str:
    #  Get point near Stamford Bridge - all within geohash5 gcpug
    lon_max = -0.189286
    lon_min = -0.192512
    lat_max = 51.482857
    lat_min = 51.480729

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def get_random_emirates_stadium_point() -> str:
    #  Get point near Emirates stadium - all within geohash5 gcpvm
    lon_max = -0.107211
    lon_min = -0.109761
    lat_max = 51.556461
    lat_min = 51.554000

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max)).wkt


def test_loiter_success(
    mock_oms_client: MagicMock, db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    """Simple success track."""
    node_id = uuid4()
    track_uuid = uuid4()
    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)

    # Loiter Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:04:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:08:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:12:00-04:00").create_node_point(node_id)
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:16:00-04:00").create_node_point(node_id)
    p6 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:20:00-04:00").create_node_point(node_id)
    # West London way later
    p7 = TimeLocation(shapely.Point(-0.413890, 51.474942).wkt, "2024-03-20T12:44:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5, p6, p7],
        node_id=node_id,
        algorithm="test_track",
        track_uuid=track_uuid,
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    loiter_activity_id = uuid4()
    mock_oms_client.create_activity = MagicMock(
        return_value=CreateActivityCreateActivity.model_construct(id=loiter_activity_id, acm=p1.acm)
    )
    sensemaker = LoiterSensemaker(mock_oms_crud_tool)
    loiters = sensemaker.execute(track, aircraft_geo_config)

    assert len(loiters) == 1
    loiter: Loiter = loiters[0]

    assert loiter.geohash == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time
    assert loiter.atoms_id == loiter_activity_id
    assert loiter.atoms_type == AtomsType.ACTIVITY

    tags = [SETTINGS.geo_sensemaker_event_tag]
    mock_oms_client.create_activity.assert_called_once()
    call_args = mock_oms_client.create_activity.call_args[0][0]
    assert call_args.classIri == SETTINGS.loiter_activity_iri
    assert call_args.name == SETTINGS.loiter_activity_name
    assert call_args.state == SETTINGS.loiter_activity_state
    assert call_args.nodeId == node_id
    assert call_args.sourceId == p1.source_id
    expected_obs_ids = {p2.observation_id, p3.observation_id, p4.observation_id, p5.observation_id, p6.observation_id}
    assert set(call_args.observationIds) == expected_obs_ids
    assert call_args.startTime == p2.detection_time
    assert call_args.endTime == p6.detection_time
    assert call_args.tags == tags
    assert call_args.acm == ROLLUP_DEFAULT_ACM

    # check that loiters exist in Findings table
    findings = db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_LOITER.value)).scalars().all()

    assert len(findings) == 1
    assert findings[0].finding_data["processed_points"][0]["location"] == to_shape(p2.location).wkt


def test_loiter_invalid_not_long_enough(
    mock_oms_client: MagicMock, db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    """Loiter is only 8 minutes vs required 15."""
    node_id = uuid4()
    track_uuid = uuid4()

    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)
    # Loiter Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:04:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:08:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:12:00-04:00").create_node_point(node_id)
    # Still within stamford bridge but past the observation time
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T14:00:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5],
        node_id=uuid4(),
        track_uuid=track_uuid,
        algorithm="test_loiter",
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    loiters = LoiterSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold(mock_oms_crud_tool, aircraft_geo_config: dict):
    """Failure. Unobserved for too long."""
    node_id = uuid4()
    track_uuid = uuid4()

    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)

    # Loiter Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:20:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:40:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T13:00:00-04:00").create_node_point(node_id)
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T13:20:00-04:00").create_node_point(node_id)
    p6 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T13:40:00-04:00").create_node_point(node_id)
    # West London
    p7 = TimeLocation(shapely.Point(-0.413890, 51.474942).wkt, "2024-03-20T14:00:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5, p6, p7],
        node_id=uuid4(),
        track_uuid=track_uuid,
        algorithm="test_loiter",
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    loiters = LoiterSensemaker(mock_oms_crud_tool).execute(track, aircraft_geo_config)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold_within_geohash(
    mock_oms_client: MagicMock, db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    """Don't remove valid loiters even if unobserved for too long."""
    # tests the find_prospective_loiters validity_time_diff

    node_id = uuid4()
    track_uuid = uuid4()

    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)

    # Loiter Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:04:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:08:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:12:00-04:00").create_node_point(node_id)
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:16:00-04:00").create_node_point(node_id)
    p6 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:20:00-04:00").create_node_point(node_id)
    # Still within stamford bridge but past the observation time
    p7 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T14:00:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5, p6, p7],
        node_id=uuid4(),
        track_uuid=track_uuid,
        algorithm="test_loiter",
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    loiter_node_id = uuid4()
    mock_oms_client.create_activity = MagicMock(
        return_value=CreateActivityCreateActivity.model_construct(id=loiter_node_id, acm=p1.acm)
    )
    sensemaker = LoiterSensemaker(mock_oms_crud_tool)
    loiters = sensemaker.execute(track, aircraft_geo_config)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time

    mock_oms_client.create_activity.assert_called_once()
    call_args = mock_oms_client.create_activity.call_args[0][0]
    assert call_args.classIri == SETTINGS.loiter_activity_iri
    assert call_args.name == SETTINGS.loiter_activity_name
    assert call_args.state == SETTINGS.loiter_activity_state
    assert call_args.nodeId == track.node_id

    # check that loiters exist in Findings table
    findings = db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_LOITER.value)).scalars().all()

    assert len(findings) == 1
    assert findings[0].finding_data["processed_points"][0]["location"] == to_shape(p2.location).wkt


def test_loiter_success_multiple_in_same_geohash(
    mock_oms_client: MagicMock, db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    """Two separate loiters in the same geohash."""
    node_id = uuid4()
    track_uuid = uuid4()

    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)

    # Loiter 1 Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:04:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:08:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:12:00-04:00").create_node_point(node_id)
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:16:00-04:00").create_node_point(node_id)
    p6 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:20:00-04:00").create_node_point(node_id)
    # West London way later
    p7 = TimeLocation(shapely.Point(-0.413890, 51.474942).wkt, "2024-03-20T12:44:00-04:00").create_node_point(node_id)

    # Loiter 2 Points
    p8 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:48:00-04:00").create_node_point(node_id)
    p9 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:53:00-04:00").create_node_point(node_id)
    p10 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:58:00-04:00").create_node_point(node_id)
    p11 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T13:03:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11],
        node_id=uuid4(),
        track_uuid=track_uuid,
        algorithm="test_loiter",
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    loiter_activity_id1 = uuid4()
    loiter_activity_id2 = uuid4()
    mock_oms_client.create_activity.side_effect = [
        CreateActivityCreateActivity.model_construct(id=loiter_activity_id1, acm=p1.acm),
        CreateActivityCreateActivity.model_construct(id=loiter_activity_id2, acm=p1.acm),
    ]
    sensemaker = LoiterSensemaker(mock_oms_crud_tool)
    loiters = sensemaker.execute(track, aircraft_geo_config)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1.geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2 = loiters[1]
    assert loiter2.geohash == "gcpug"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time

    assert mock_oms_client.create_activity.call_count == 2
    call_args_list = [c[0][0] for c in mock_oms_client.create_activity.call_args_list]
    assert all(
        c.classIri == SETTINGS.loiter_activity_iri and c.name == SETTINGS.loiter_activity_name for c in call_args_list
    )

    # check that loiters exist in Findings table
    findings = db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_LOITER.value)).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data["processed_points"][0]["location"] == to_shape(p2.location).wkt


def test_loiter_success_multiple_in_different_geohash(
    mock_oms_client: MagicMock, db: Session, mock_oms_crud_tool: OmsCrudTool, aircraft_geo_config: dict
):
    """Two separate loiters in different geohashes."""
    node_id = uuid4()
    track_uuid = uuid4()

    # East London
    p1 = TimeLocation(shapely.Point(-0.030890, 51.509420).wkt, "2024-03-20T12:00:00-04:00").create_node_point(node_id)

    # Loiter 1 Points
    p2 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:04:00-04:00").create_node_point(node_id)
    p3 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:08:00-04:00").create_node_point(node_id)
    p4 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:12:00-04:00").create_node_point(node_id)
    p5 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:16:00-04:00").create_node_point(node_id)
    p6 = TimeLocation(get_random_stamford_bridge_point(), "2024-03-20T12:20:00-04:00").create_node_point(node_id)
    # West London way later
    p7 = TimeLocation(shapely.Point(-0.413890, 51.474942).wkt, "2024-03-20T12:44:00-04:00").create_node_point(node_id)

    # Loiter 2 Points
    p8 = TimeLocation(get_random_emirates_stadium_point(), "2024-03-20T12:48:00-04:00").create_node_point(node_id)
    p9 = TimeLocation(get_random_emirates_stadium_point(), "2024-03-20T12:53:00-04:00").create_node_point(node_id)
    p10 = TimeLocation(get_random_emirates_stadium_point(), "2024-03-20T12:58:00-04:00").create_node_point(node_id)
    p11 = TimeLocation(get_random_emirates_stadium_point(), "2024-03-20T13:03:00-04:00").create_node_point(node_id)

    # Create Track Object
    track = Track(
        points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11],
        node_id=uuid4(),
        track_uuid=track_uuid,
        algorithm="test_loiter",
        acm=ROLLUP_DEFAULT_ACM,
        provider_id=uuid4(),
    )

    # Set up mocks
    loiter_activity_id1 = uuid4()
    loiter_activity_id2 = uuid4()
    mock_oms_client.create_activity.side_effect = [
        CreateActivityCreateActivity.model_construct(id=loiter_activity_id1, acm=p1.acm),
        CreateActivityCreateActivity.model_construct(id=loiter_activity_id2, acm=p1.acm),
    ]
    sensemaker = LoiterSensemaker(mock_oms_crud_tool)
    loiters = sensemaker.execute(track, aircraft_geo_config)
    assert len(loiters) == 2

    loiter1: Loiter = loiters[0]
    assert loiter1.geohash == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1.geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2: Loiter = loiters[1]
    assert loiter2.geohash == "gcpvm"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2.geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time

    assert mock_oms_client.create_activity.call_count == 2
    call_args_list = [c[0][0] for c in mock_oms_client.create_activity.call_args_list]
    assert all(
        c.classIri == SETTINGS.loiter_activity_iri and c.name == SETTINGS.loiter_activity_name for c in call_args_list
    )

    # check that loiters exist in Findings table
    findings = db.execute(select(Finding).filter(Finding.finding_type == FindingType.GEO_LOITER.value)).scalars().all()

    assert len(findings) == 2
    assert findings[0].finding_data["processed_points"][0]["location"] == to_shape(p2.location).wkt
