import random
import uuid
from datetime import datetime

import shapely

from src.models.processed_point import ProcessedPoint
from src.models.track import Track
from src.services.cotravel import CotravelService


def test_cotravel_success():
    # Note these points/timestamps are set to match the base_track_service hard coded "DB"
    p1 = ProcessedPoint(51.484423, -0.148931, datetime.fromisoformat("2024-03-20T12:05:00-04:00"), True, False)
    p2 = ProcessedPoint(51.465229, -0.186849, datetime.fromisoformat("2024-03-20T12:15:00-04:00"), False, False)
    p3 = ProcessedPoint(51.476589, -0.225258, datetime.fromisoformat("2024-03-20T12:25:00-04:00"), False, True)

    # Create Track Object
    track = Track(uuid.uuid4(), [p1, p2, p3])

    cotravels = CotravelService.detect_cotravels(track)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.track1 == track.track_node_id
    assert cotravel.start_time1 == p1.timestamp
    assert cotravel.start_time2 == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time1 == p3.timestamp
    assert cotravel.last_time2 == datetime.fromisoformat("2024-03-20T12:20:00-04:00")
