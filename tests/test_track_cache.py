import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
import shapely
from oms_sdk import DEFAULT_ACM

from oms_sensemaking.geospatial.tracks import TrackCacheService
from oms_sensemaking.models.geo import Point


@pytest.mark.asyncio
async def test_track_cache_add_point():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = uuid.uuid4()
    point_identifier2 = uuid.uuid4()

    # assertion errors shoudn't prevent cleanly exiting track cache
    try:
        # new point
        point1 = Point(
                    acm=DEFAULT_ACM,
                    location=shapely.Point(1, 2).wkt,
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                    node_id=point_identifier,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                )
        await tc.add_point(point1)
        assert len(tc._point_cache.items()) == 1
        assert len(tc._timestamp_cache.items()) == 1
        assert len(tc._point_cache[point_identifier].queue) == 1
        # make sure the latest time has been set to datetime.now()ish
        assert (datetime.now() - tc._timestamp_cache[point_identifier]).total_seconds() < 1

        # new point in same identifier
        point2 = Point(
                    acm=DEFAULT_ACM,
                    location=shapely.Point(2, 3).wkt,
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                    node_id=point_identifier,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                )
        await tc.add_point(point2)
        assert len(tc._point_cache.items()) == 1
        assert len(tc._timestamp_cache.items()) == 1
        # assert that two points went to the same identifier
        assert len(tc._point_cache[point_identifier].queue) == 2
        # make sure the latest time has been set to datetime.now()ish
        assert (datetime.now() - tc._timestamp_cache[point_identifier]).total_seconds() < 1

        # new point in with new identifier
        point3 = Point(
                    acm=DEFAULT_ACM,
                    location=shapely.Point(3, 4).wkt,
                    altitude=None,
                    detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
                    node_id=point_identifier2,
                    node_version=1,
                    attribute_id=uuid.uuid4(),
                    attribute_version=1
                )
        await tc.add_point(point3)
        assert len(tc._point_cache.items()) == 2
        assert len(tc._timestamp_cache.items()) == 2
        # assert that two points went to the same identifier
        assert len(tc._point_cache[point_identifier2].queue) == 1
        # make sure the latest time has been set to datetime.now()ish
        assert (datetime.now() - tc._timestamp_cache[point_identifier2]).total_seconds() < 1

        # get the points and make sure they're correct
        assert tc._point_cache[point_identifier].get() == point1
        assert tc._point_cache[point_identifier].get() == point2
        assert tc._point_cache[point_identifier2].get() == point3
    finally:
        tc.stop()


@pytest.mark.asyncio
async def test_track_cache_expiration():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = uuid.uuid4()
    other_identifier = uuid.uuid4()
    another_identifier = uuid.uuid4()

    point1 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(1, 2).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
    point2 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(2, 3).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
    point3 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(3, 4).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )

    # assertion errors shoudn't prevent cleanly exiting track cache
    try:
        # random point
        await tc.add_point(
            Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(3, 4).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                node_id=other_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
        )

        # points we care about
        await tc.add_point(point1)
        await tc.add_point(point2)
        await tc.add_point(point3)
        # simulate that these points expired a minute ago
        tc._timestamp_cache[point_identifier] = datetime.now() - timedelta(minutes=1)

        # more random points
        await tc.add_point(
            Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(3, 4).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                node_id=other_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
        )
        await tc.add_point(
            Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(3, 4).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
                node_id=another_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
        )

        tc.create_track = AsyncMock()
        await tc.check_expirations()

        tc.create_track.assert_called()
        assert tc.create_track.call_args[0][0] == point_identifier
        expected_point_queue_list = [point1, point2, point3]
        assert tc.create_track.call_args[0][1].queue == expected_point_queue_list
    finally:
        tc.stop()


@pytest.mark.asyncio
async def test_track_cache_create_track():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = "test_identifier"

    point1 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(1, 2).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:00:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
    point2 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(2, 3).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:10:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
    point3 = Point(
                acm=DEFAULT_ACM,
                location=shapely.Point(3, 4).wkt,
                altitude=None,
                detection_time=datetime.fromisoformat("2024-03-20T12:20:00-04:00"),
                node_id=point_identifier,
                node_version=1,
                attribute_id=uuid.uuid4(),
                attribute_version=1
            )
    # assertion errors shouldn't prevent cleanly exiting track cache
    try:
        # points in order
        await tc.add_point(point1)
        await tc.add_point(point2)
        await tc.add_point(point3)

        track = await tc.create_track(point_identifier, tc._point_cache[point_identifier])
        assert track.node_id == point_identifier
        assert len(track.points) == 3
        assert track.points[0].coordinates[0] == point1.coordinates[0]
        assert track.points[0].coordinates[1] == point1.coordinates[1]
        assert track.points[2].coordinates[0] == point3.coordinates[0]
        assert track.points[2].coordinates[1] == point3.coordinates[1]

        tc._point_cache.pop(point_identifier)
        tc._timestamp_cache.pop(point_identifier)
        assert tc.point_ingest_queue.empty()

        # points out of order
        await tc.add_point(point1)
        await tc.add_point(point3)
        await tc.add_point(point2)
        # Test that they are in the correct order
        # we might not need to do this if we switch to a different caching mechanism but it's good to have a unit
        # test that we can keep for even if we change that caching mechanism
        track = await tc.create_track(point_identifier, tc._point_cache[point_identifier])
        assert track.node_id == point_identifier
        assert len(track.points) == 3
        assert track.points[0].coordinates[0] == point1.coordinates[0]
        assert track.points[0].coordinates[1] == point1.coordinates[1]
        # assert track.points[0].is_start
        # assert not track.points[0].is_end
        assert track.points[2].coordinates[0] == point3.coordinates[0]
        assert track.points[2].coordinates[1] == point3.coordinates[1]
        # assert not track.points[2].is_start
        # assert track.points[2].is_end
        tc._point_cache.pop(point_identifier)
        tc._timestamp_cache.pop(point_identifier)
        assert tc.point_ingest_queue.empty()
    finally:
        tc.stop()
