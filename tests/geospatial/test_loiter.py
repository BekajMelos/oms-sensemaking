"""Tests for loiter sensemaker."""

import random
import uuid
from datetime import datetime

import shapely
from oms_sensemaking.geospatial.loiter import LoiterService
from oms_sensemaking.geospatial.models.processed_point import ProcessedPoint
from oms_sensemaking.geospatial.models.track import Track


def get_random_stamford_bridge_point() -> shapely.Point:
    #  Get point near Stamford Bridge - all within geohash5 gcpug
    lon_max = -0.189286
    lon_min = -0.192512
    lat_max = 51.482857
    lat_min = 51.480729

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max))


def get_random_emirates_stadium_point() -> shapely.Point:
    #  Get point near Emirates stadium - all within geohash5 gcpvm
    lon_max = -0.107211
    lon_min = -0.109761
    lat_max = 51.556461
    lat_min = 51.554000

    return shapely.Point(random.uniform(lon_min, lon_max), random.uniform(lat_min, lat_max))


def test_loiter_success():
    """Simple success track."""
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:04:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:08:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T12:12:00-04:00"), False, False)
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T12:16:00-04:00"), False, False)
    p6_point = get_random_stamford_bridge_point()
    p6 = ProcessedPoint(p6_point, datetime.fromisoformat("2024-03-20T12:20:00-04:00"), False, False)
    # West London way later
    p7 = ProcessedPoint(
        shapely.Point(-0.413890, 51.474942), datetime.fromisoformat("2024-03-20T12:44:00-04:00"), False, True
    )

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5, p6, p7])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    loiter_geometry = shapely.from_wkt(loiter.geometry)
    expected_linestring2 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points])
    assert loiter_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.timestamp
    assert loiter.end_time == p6.timestamp


def test_loiter_invalid_not_long_enough():
    """Loiter is only 8 minutes vs required 15."""
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:04:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:08:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T12:12:00-04:00"), False, False)
    # Still within stamford bridge but past the observation time
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T14:00:00-04:00"), False, True)

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold():
    """Failure. Unobserved for too long."""
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:20:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:40:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T13:00:00-04:00"), False, False)
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T13:20:00-04:00"), False, False)
    p6_point = get_random_stamford_bridge_point()
    p6 = ProcessedPoint(p6_point, datetime.fromisoformat("2024-03-20T13:40:00-04:00"), False, False)
    # West London
    p7 = ProcessedPoint(
        shapely.Point(-0.413890, 51.474942), datetime.fromisoformat("2024-03-20T14:00:00-04:00"), False, True
    )

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5, p6, p7])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold_within_geohash():
    """Don't remove valid loiters even if unobserved for too long."""
    # tests the find_prospective_loiters validity_time_diff
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:04:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:08:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T12:12:00-04:00"), False, False)
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T12:16:00-04:00"), False, False)
    p6_point = get_random_stamford_bridge_point()
    p6 = ProcessedPoint(p6_point, datetime.fromisoformat("2024-03-20T12:20:00-04:00"), False, False)
    # Still within stamford bridge but past the observation time
    p7_point = get_random_stamford_bridge_point()
    p7 = ProcessedPoint(p7_point, datetime.fromisoformat("2024-03-20T14:00:00-04:00"), False, True)

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5, p6, p7])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    loiter_geometry = shapely.from_wkt(loiter.geometry)
    expected_linestring2 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points])
    assert loiter_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.timestamp
    assert loiter.end_time == p6.timestamp


def test_loiter_success_multiple_in_same_geohash():
    """Two separate loiters in the same geohash."""
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:04:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:08:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T12:12:00-04:00"), False, False)
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T12:16:00-04:00"), False, False)
    p6_point = get_random_stamford_bridge_point()
    p6 = ProcessedPoint(p6_point, datetime.fromisoformat("2024-03-20T12:20:00-04:00"), False, False)
    # West London way later
    p7 = ProcessedPoint(
        shapely.Point(-0.413890, 51.474942), datetime.fromisoformat("2024-03-20T12:44:00-04:00"), False, False
    )
    # Loiter 2 Points
    p8_point = get_random_stamford_bridge_point()
    p8 = ProcessedPoint(p8_point, datetime.fromisoformat("2024-03-20T12:48:00-04:00"), False, False)
    p9_point = get_random_stamford_bridge_point()
    p9 = ProcessedPoint(p9_point, datetime.fromisoformat("2024-03-20T12:53:00-04:00"), False, False)
    p10_point = get_random_stamford_bridge_point()
    p10 = ProcessedPoint(p10_point, datetime.fromisoformat("2024-03-20T12:58:00-04:00"), False, False)
    p11_point = get_random_stamford_bridge_point()
    p11 = ProcessedPoint(p11_point, datetime.fromisoformat("2024-03-20T13:03:00-04:00"), False, True)

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    loiter1_geometry = shapely.from_wkt(loiter1.geometry)
    expected_linestring1 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points1])
    assert loiter1_geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.timestamp
    assert loiter1.end_time == p6.timestamp

    loiter2 = loiters[1]
    assert loiter2.geohash_low == "gcpug"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    loiter2_geometry = shapely.from_wkt(loiter2.geometry)
    expected_linestring2 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points2])
    assert loiter2_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.timestamp
    assert loiter2.end_time == p11.timestamp


def test_loiter_success_multiple_in_different_geohash():
    """Two separate loiters in different geohashes."""
    # East London
    p1 = ProcessedPoint(
        shapely.Point(-0.030890, 51.509420), datetime.fromisoformat("2024-03-20T12:00:00-04:00"), True, False
    )
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = ProcessedPoint(p2_point, datetime.fromisoformat("2024-03-20T12:04:00-04:00"), False, False)
    p3_point = get_random_stamford_bridge_point()
    p3 = ProcessedPoint(p3_point, datetime.fromisoformat("2024-03-20T12:08:00-04:00"), False, False)
    p4_point = get_random_stamford_bridge_point()
    p4 = ProcessedPoint(p4_point, datetime.fromisoformat("2024-03-20T12:12:00-04:00"), False, False)
    p5_point = get_random_stamford_bridge_point()
    p5 = ProcessedPoint(p5_point, datetime.fromisoformat("2024-03-20T12:16:00-04:00"), False, False)
    p6_point = get_random_stamford_bridge_point()
    p6 = ProcessedPoint(p6_point, datetime.fromisoformat("2024-03-20T12:20:00-04:00"), False, False)
    # West London way later
    p7 = ProcessedPoint(
        shapely.Point(-0.413890, 51.474942), datetime.fromisoformat("2024-03-20T12:44:00-04:00"), False, False
    )
    # Loiter 2 Points
    p8_point = get_random_emirates_stadium_point()
    p8 = ProcessedPoint(p8_point, datetime.fromisoformat("2024-03-20T12:48:00-04:00"), False, False)
    p9_point = get_random_emirates_stadium_point()
    p9 = ProcessedPoint(p9_point, datetime.fromisoformat("2024-03-20T12:53:00-04:00"), False, False)
    p10_point = get_random_emirates_stadium_point()
    p10 = ProcessedPoint(p10_point, datetime.fromisoformat("2024-03-20T12:58:00-04:00"), False, False)
    p11_point = get_random_emirates_stadium_point()
    p11 = ProcessedPoint(p11_point, datetime.fromisoformat("2024-03-20T13:03:00-04:00"), False, True)

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11])

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    loiter1_geometry = shapely.from_wkt(loiter1.geometry)
    expected_linestring1 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points1])
    assert loiter1_geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.timestamp
    assert loiter1.end_time == p6.timestamp

    loiter2 = loiters[1]
    assert loiter2.geohash_low == "gcpvm"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.geometry.y == point.geometry.y and p.geometry.x == point.geometry.x
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    loiter2_geometry = shapely.from_wkt(loiter2.geometry)
    expected_linestring2 = shapely.LineString([(p.geometry.x, p.geometry.y) for p in known_loiter_points2])
    assert loiter2_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.timestamp
    assert loiter2.end_time == p11.timestamp
