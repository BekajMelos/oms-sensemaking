"""Tests for loiter sensemaker."""

import random
import uuid
from datetime import datetime

import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.geospatial.loiter import LoiterService
from oms_sensemaking.models.geo import Point, Track


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


def test_loiter_success():
    """Simple success track."""
    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=node_id)

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    loiter_geometry = shapely.from_wkt(loiter.geometry)
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time


def test_loiter_invalid_not_long_enough():
    """Loiter is only 8 minutes vs required 15."""
    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Still within stamford bridge but past the observation time
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5], node_id=uuid.uuid4())

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold():
    """Failure. Unobserved for too long."""
    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:40:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:40:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # West London
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=uuid.uuid4())

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 0


def test_loiter_fails_valid_observed_threshold_within_geohash():
    """Don't remove valid loiters even if unobserved for too long."""
    # tests the find_prospective_loiters validity_time_diff

    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Still within stamford bridge but past the observation time
    p7_point = get_random_stamford_bridge_point()
    p7 = Point(acm=DEFAULT_ACM, location=p7_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T14:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7], node_id=uuid.uuid4())

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 1
    loiter = loiters[0]

    assert loiter.geohash_low == "gcpug"
    assert len(loiter.processed_points) == 5
    known_loiter_points = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points, loiter.processed_points, strict=False)
    )
    loiter_geometry = shapely.from_wkt(loiter.geometry)
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points])
    assert loiter_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter.start_time == p2.detection_time
    assert loiter.end_time == p6.detection_time


def test_loiter_success_multiple_in_same_geohash():
    """Two separate loiters in the same geohash."""
    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter 2 Points
    p8_point = get_random_stamford_bridge_point()
    p8 = Point(acm=DEFAULT_ACM, location=p8_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:48:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p9_point = get_random_stamford_bridge_point()
    p9 = Point(acm=DEFAULT_ACM, location=p9_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:53:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p10_point = get_random_stamford_bridge_point()
    p10 = Point(acm=DEFAULT_ACM, location=p10_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:58:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p11_point = get_random_stamford_bridge_point()
    p11 = Point(acm=DEFAULT_ACM, location=p11_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:03:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11], node_id=uuid.uuid4())

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    loiter1_geometry = shapely.from_wkt(loiter1.geometry)
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1_geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2 = loiters[1]
    assert loiter2.geohash_low == "gcpug"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    loiter2_geometry = shapely.from_wkt(loiter2.geometry)
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time


def test_loiter_success_multiple_in_different_geohash():
    """Two separate loiters in different geohashes."""
    node_id = uuid.uuid4()
    # East London
    p1 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.030890, 51.509420).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter 1 Points
    p2_point = get_random_stamford_bridge_point()
    p2 = Point(acm=DEFAULT_ACM, location=p2_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:04:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p3_point = get_random_stamford_bridge_point()
    p3 = Point(acm=DEFAULT_ACM, location=p3_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:08:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p4_point = get_random_stamford_bridge_point()
    p4 = Point(acm=DEFAULT_ACM, location=p4_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:12:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p5_point = get_random_stamford_bridge_point()
    p5 = Point(acm=DEFAULT_ACM, location=p5_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:16:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p6_point = get_random_stamford_bridge_point()
    p6 = Point(acm=DEFAULT_ACM, location=p6_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # West London way later
    p7 = Point(acm=DEFAULT_ACM, location=shapely.Point(-0.413890, 51.474942).wkt, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:44:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    # Loiter 2 Points
    p8_point = get_random_emirates_stadium_point()
    p8 = Point(acm=DEFAULT_ACM, location=p8_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:48:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p9_point = get_random_emirates_stadium_point()
    p9 = Point(acm=DEFAULT_ACM, location=p9_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:53:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p10_point = get_random_emirates_stadium_point()
    p10 = Point(acm=DEFAULT_ACM, location=p10_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:58:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)
    p11_point = get_random_emirates_stadium_point()
    p11 = Point(acm=DEFAULT_ACM, location=p11_point, altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:03:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid.uuid4(), attribute_version=1)

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11], node_id=uuid.uuid4())

    loiters = LoiterService.detect_loiters(track)
    assert len(loiters) == 2

    loiter1 = loiters[0]
    assert loiter1.geohash_low == "gcpug"
    assert len(loiter1.processed_points) == 5
    known_loiter_points1 = [p2, p3, p4, p5, p6]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points1, loiter1.processed_points, strict=False)
    )
    loiter1_geometry = shapely.from_wkt(loiter1.geometry)
    expected_linestring1 = shapely.LineString([p.coordinates for p in known_loiter_points1])
    assert loiter1_geometry.equals_exact(expected_linestring1, 1e-10)
    assert loiter1.start_time == p2.detection_time
    assert loiter1.end_time == p6.detection_time

    loiter2 = loiters[1]
    assert loiter2.geohash_low == "gcpvm"
    assert len(loiter2.processed_points) == 4
    known_loiter_points2 = [p8, p9, p10, p11]
    assert all(
        p.coordinates[0] == point.coordinates[0] and p.coordinates[1] == point.coordinates[1]
        for p, point in zip(known_loiter_points2, loiter2.processed_points, strict=False)
    )
    loiter2_geometry = shapely.from_wkt(loiter2.geometry)
    expected_linestring2 = shapely.LineString([p.coordinates for p in known_loiter_points2])
    assert loiter2_geometry.equals_exact(expected_linestring2, 1e-10)
    assert loiter2.start_time == p8.detection_time
    assert loiter2.end_time == p11.detection_time
