import asyncio
from collections import defaultdict
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

    # new point
    point1 = PointAttribute(point_identifier, 1, 2, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
    await tc.add_point(point1)
    assert len(tc.cache.items()) == 1
    assert len(tc.cache[point_identifier]) == 1
    # make sure the latest time has been set to datetime.now()ish
    assert (datetime.now() - tc.cache[point_identifier][0][0]).total_seconds() < 1
    assert tc.cache[point_identifier][0][1] == point1

    # new point in same identifier
    point2 = PointAttribute(point_identifier, 2, 3, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
    await tc.add_point(point2)
    assert len(tc.cache.items()) == 1
    # assert that two points went to the same identifier
    assert len(tc.cache[point_identifier]) == 2
    # make sure the latest time has been set to datetime.now()ish
    assert (datetime.now() - tc.cache[point_identifier][1][0]).total_seconds() < 1
    assert tc.cache[point_identifier][1][1] == point2

    # new point in with new identifier
    point3 = PointAttribute(point_identifier2, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))
    await tc.add_point(point3)
    assert len(tc.cache.items()) == 2
    # assert that two points went to the same identifier
    assert len(tc.cache[point_identifier2]) == 1
    # make sure the latest time has been set to datetime.now()ish
    assert (datetime.now() - tc.cache[point_identifier2][0][0]).total_seconds() < 1
    assert tc.cache[point_identifier2][0][1] == point3

    tc.stop()


@pytest.mark.asyncio
async def test_track_cache_expiration():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = "test_identifier"

    # 3 minutes ago
    three_min_ago = datetime.now() - timedelta(minutes=3)
    point1 = PointAttribute(point_identifier, 1, 2, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
    # 2 minutes ago
    two_min_ago = datetime.now() - timedelta(minutes=2)
    point2 = PointAttribute(point_identifier, 2, 3, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
    # 1 minute ago
    one_min_ago = datetime.now() - timedelta(minutes=1)
    point3 = PointAttribute(point_identifier, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))

    list_of_point_tuples = [
        (three_min_ago, point1),
        (two_min_ago, point2),
        (one_min_ago, point3),
    ]
    tc.cache = defaultdict(list, {point_identifier: list_of_point_tuples})

    # other random points
    await tc.add_point(PointAttribute("identifier", 3, 4, datetime.fromisoformat("2024-03-20T12:00:00-04:00")))
    await tc.add_point(PointAttribute("identifier", 3, 4, datetime.fromisoformat("2024-03-20T12:10:00-04:00")))
    await tc.add_point(PointAttribute("identifier2", 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00")))

    tc.create_track = AsyncMock()
    await tc.check_expirations()

    tc.create_track.assert_called_with(point_identifier, list_of_point_tuples)

    tc.stop()


@pytest.mark.asyncio
async def test_track_cache_create_track():
    q = asyncio.Queue()
    tc = TrackCacheService(q)

    point_identifier = "test_identifier"

    point1 = PointAttribute(point_identifier, 1, 2, datetime.fromisoformat("2024-03-20T12:00:00-04:00"))
    point2 = PointAttribute(point_identifier, 2, 3, datetime.fromisoformat("2024-03-20T12:10:00-04:00"))
    point3 = PointAttribute(point_identifier, 3, 4, datetime.fromisoformat("2024-03-20T12:20:00-04:00"))

    # other random points
    await tc.add_point(point1)
    await tc.add_point(point2)
    await tc.add_point(point3)

    track = await tc.create_track(point_identifier, tc.cache[point_identifier])
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

    tc.stop()
