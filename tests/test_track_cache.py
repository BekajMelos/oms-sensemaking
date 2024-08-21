import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from oms_sensemaking.geospatial.tracks import PointAttribute, TrackCacheService


@pytest.mark.asyncio
async def test_track_cache_add_point():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = "test_identifier"
    point_identifier2 = "test_identifier2"

    # assertion errors shoudn't prevent cleanly exiting track cache
    try:
        # new point
        point1 = PointAttribute(point_identifier, 1, 2, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
        await tc.add_point(point1)
        assert len(tc._point_cache.items()) == 1
        assert len(tc._timestamp_cache.items()) == 1
        assert len(tc._point_cache[point_identifier].queue) == 1
        # make sure the latest time has been set to datetime.now()ish
        assert (datetime.now() - tc._timestamp_cache[point_identifier]).total_seconds() < 1

        # new point in same identifier
        point2 = PointAttribute(point_identifier, 2, 3, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
        await tc.add_point(point2)
        assert len(tc._point_cache.items()) == 1
        assert len(tc._timestamp_cache.items()) == 1
        # assert that two points went to the same identifier
        assert len(tc._point_cache[point_identifier].queue) == 2
        # make sure the latest time has been set to datetime.now()ish
        assert (datetime.now() - tc._timestamp_cache[point_identifier]).total_seconds() < 1

        # new point in with new identifier
        point3 = PointAttribute(point_identifier2, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))
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

    point_identifier = "test_identifier"
    other_identifier = "other_identifier"
    another_identifer = "another_identifier"

    point1 = PointAttribute(point_identifier, 1, 2, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
    point2 = PointAttribute(point_identifier, 2, 3, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
    point3 = PointAttribute(point_identifier, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))

    # assertion errors shoudn't prevent cleanly exiting track cache
    try:
        # random point
        await tc.add_point(PointAttribute(other_identifier, 3, 4, datetime.fromisoformat("2024-03-20T12:00:00-04:00")))

        # points we care about
        await tc.add_point(point1)
        await tc.add_point(point2)
        await tc.add_point(point3)
        # simulate that these points expired a minute ago
        tc._timestamp_cache[point_identifier] = datetime.now() - timedelta(minutes=1)

        # more random points
        await tc.add_point(PointAttribute(other_identifier, 3, 4, datetime.fromisoformat("2024-03-20T12:10:00-04:00")))
        await tc.add_point(PointAttribute(another_identifer, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00")))

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

    point1 = PointAttribute(point_identifier, 1, 4, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
    point2 = PointAttribute(point_identifier, 2, 5, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
    point3 = PointAttribute(point_identifier, 3, 6, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))

    # assertion errors shoudn't prevent cleanly exiting track cache
    try:
        # points in order
        await tc.add_point(point1)
        await tc.add_point(point2)
        await tc.add_point(point3)

        track = await tc.create_track(point_identifier, tc._point_cache[point_identifier])
        assert track.track_node_id == point_identifier
        assert len(track.points) == 3
        assert track.points[0].geometry.x == point1.lon
        assert track.points[0].geometry.y == point1.lat
        assert track.points[0].is_start
        assert not track.points[0].is_end
        assert track.points[2].geometry.x == point3.lon
        assert track.points[2].geometry.y == point3.lat
        assert not track.points[2].is_start
        assert track.points[2].is_end

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
        assert track.track_node_id == point_identifier
        assert len(track.points) == 3
        assert track.points[0].geometry.x == point1.lon
        assert track.points[0].geometry.y == point1.lat
        assert track.points[0].is_start
        assert not track.points[0].is_end
        assert track.points[2].geometry.x == point3.lon
        assert track.points[2].geometry.y == point3.lat
        assert not track.points[2].is_start
        assert track.points[2].is_end
        tc._point_cache.pop(point_identifier)
        tc._timestamp_cache.pop(point_identifier)
        assert tc.point_ingest_queue.empty()
    finally:
        tc.stop()
