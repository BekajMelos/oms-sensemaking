import asyncio

from oms_sensemaking.geospatial.tracks import TrackCacheService


def test_track_cache_service():
    cache: TrackCacheService = TrackCacheService(asyncio.Queue())

    assert cache.is_running
    cache.stop()
