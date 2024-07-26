"""Tests for similar tracks sensemaker."""
import uuid
from datetime import datetime

import pytest
import shapely
from oms_sensemaking.geospatial.models.processed_point import ProcessedPoint
from oms_sensemaking.geospatial.models.track import Track
from oms_sensemaking.geospatial.similar_tracks import MostSimilarTrackService


@pytest.mark.asyncio
async def test_most_similar_tracks_success():
    # Note these points/timestamps are set to match the base_track_service hard coded "DB"
    # first point is wayyy east of london
    p1 = ProcessedPoint(
        shapely.Point(0.226432, 51.479597), datetime.fromisoformat("2024-03-20T12:05:00-04:00"), True, False
    )
    p2 = ProcessedPoint(
        shapely.Point(-0.186849, 51.465229), datetime.fromisoformat("2024-03-20T12:15:00-04:00"), False, False
    )
    p3 = ProcessedPoint(
        shapely.Point(-0.225258, 51.476589), datetime.fromisoformat("2024-03-20T12:25:00-04:00"), False, True
    )

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3])

    similar_tracks = await MostSimilarTrackService.most_similar_track_node_ids(track)

    assert len(similar_tracks.top_similarities.queue) == 1
    assert similar_tracks.top_similarities.queue[0][0] == 0.75
