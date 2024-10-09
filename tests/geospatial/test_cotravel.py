"""Tests for co-travler sensemaker."""

from datetime import datetime
from typing import Iterator, List
from uuid import uuid4

import pytest
from oms_sdk import DEFAULT_ACM
from sqlalchemy.orm import Session

from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker
from oms_sensemaking.geospatial.sensemakers.cotravel import PotentialMatch
from oms_sensemaking.models.geo import Point, Track

NODE_UUID1 = uuid4()
NODE_UUID2 = uuid4()
NODE_UUID3 = uuid4()
SOURCE_ID = uuid4()
DATA: list = [  # Latitude, Longitude, Altitude (m), Description, Node ID, Attr ID, detection_time,
    # Track 1
    [51.482286, -0.165222, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:00:00-04:00")],
    [51.466103, -0.210562, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:10:00-04:00")],
    [51.487613, -0.229466, None, "London", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:20:00-04:00")],
    # point that shouldn't be included in the cotravel
    [50, 0, None, "English Channel", NODE_UUID1, uuid4(), datetime.fromisoformat("2024-03-20T12:30:00-04:00")],
    # Track 2
    [41.467810, 2.289575, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:00:00-04:00")],
    [41.399953, 2.217167, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:10:00-04:00")],
    [41.356069, 2.183748, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:20:00-04:00")],
    [41.296465, 2.130487, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-08-20T16:30:00-04:00")],
    # Track 3
    [41.467811, 2.289576, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:19:00-04:00")],
    [41.399954, 2.217168, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:29:00-04:00")],
    [41.356070, 2.183749, None, "Barcelona", NODE_UUID3, uuid4(), datetime.fromisoformat("2024-08-20T16:39:00-04:00")],
    # Track 4
    [38.252533, 15.650729, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-09-10T05:00:00-04:00")],
    [38.228556, 15.610534, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-09-10T05:10:00-04:00")],
    [38.185378, 15.594253, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-09-10T05:20:00-04:00")],
    [38.142175, 15.578989, None, "Barcelona", NODE_UUID2, uuid4(), datetime.fromisoformat("2024-09-10T05:30:00-04:00")],
]


@pytest.fixture
def tester_db(db: Session) -> Iterator[Session]:
    for row in DATA:
        point: Point = Point(
            node_id=row[4],
            node_version=1,
            attribute_id=row[5],
            attribute_version=1,
            location=f"POINT({row[1]} {row[0]})",  # lng lat
            altitude=row[2],
            detection_time=row[6],
            acm=DEFAULT_ACM,
            source_id=SOURCE_ID
        )

        db.add(point)

    db.commit()

    yield db


def test_cotravel_success(tester_db):

    node_id = uuid4()

    # 10 minutes behind fixture track
    p1 = Point(acm=DEFAULT_ACM, location="POINT (-0.148931 51.484423)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:05:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p2 = Point(acm=DEFAULT_ACM, location="POINT (-0.186849 51.465229)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:15:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p3 = Point(acm=DEFAULT_ACM, location="POINT (-0.225258 51.476589)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:25:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    cotravels: List[PotentialMatch] = CotravelSensemaker().execute(track)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.true_cotravel
    assert cotravel.track1 == track.node_id
    assert cotravel.start_time1 == p1.detection_time
    assert cotravel.start_time2 == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time1 == p3.detection_time
    assert cotravel.last_time2 == datetime.fromisoformat("2024-03-20T12:20:00-04:00")


def test_multiple_cotravel_success(tester_db):

    node_id = uuid4()

    # 10 minutes behind fixture track
    p1 = Point(acm=DEFAULT_ACM, location="POINT (2.289577 41.467812)", altitude=None,
               detection_time=datetime.fromisoformat("2024-08-20T16:39:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p2 = Point(acm=DEFAULT_ACM, location="POINT (2.217169 41.399955)", altitude=None,
               detection_time=datetime.fromisoformat("2024-08-20T16:49:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p3 = Point(acm=DEFAULT_ACM, location="POINT (2.183750 41.356071)", altitude=None,
               detection_time=datetime.fromisoformat("2024-08-20T16:59:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    cotravels: List[PotentialMatch] = CotravelSensemaker().execute(track)

    assert len(cotravels) == 2
    cotravels = sorted(cotravels, key=lambda cotravel: cotravel.true_cotravel)  # check lag_lead first
    lag_lead = cotravels[0]

    assert not lag_lead.true_cotravel
    assert lag_lead.track1 == track.node_id
    assert lag_lead.start_time1 == p1.detection_time
    assert lag_lead.start_time2 == datetime.fromisoformat("2024-08-20T16:00:00-04:00")
    assert lag_lead.last_time1 == p3.detection_time
    assert lag_lead.last_time2 == datetime.fromisoformat("2024-08-20T16:20:00-04:00")
    cotravel = cotravels[1]
    assert cotravel.true_cotravel
    assert cotravel.track1 == track.node_id
    assert cotravel.start_time1 == p1.detection_time
    assert cotravel.start_time2 == datetime.fromisoformat("2024-08-20T16:19:00-04:00")
    assert cotravel.last_time1 == p3.detection_time
    assert cotravel.last_time2 == datetime.fromisoformat("2024-08-20T16:39:00-04:00")


def test_lag_lead_success(tester_db):

    node_id = uuid4()

    # 35 minutes behind fixture track
    p1 = Point(acm=DEFAULT_ACM, location="POINT (-0.148931 51.484423)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:35:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p2 = Point(acm=DEFAULT_ACM, location="POINT (-0.186849 51.465229)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:45:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p3 = Point(acm=DEFAULT_ACM, location="POINT (-0.225258 51.476589)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T12:55:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    cotravels: List[PotentialMatch] = CotravelSensemaker().execute(track)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert not cotravel.true_cotravel
    assert cotravel.track1 == track.node_id
    assert cotravel.start_time1 == p1.detection_time
    assert cotravel.start_time2 == datetime.fromisoformat("2024-03-20T12:00:00-04:00")
    assert cotravel.last_time1 == p3.detection_time
    assert cotravel.last_time2 == datetime.fromisoformat("2024-03-20T12:20:00-04:00")


def test_cotravel_too_far_behind(tester_db):

    node_id = uuid4()

    # 95 minutes behind fixture track
    p1 = Point(acm=DEFAULT_ACM, location="POINT (-0.148931 51.484423)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:35:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p2 = Point(acm=DEFAULT_ACM, location="POINT (-0.186849 51.465229)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:45:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p3 = Point(acm=DEFAULT_ACM, location="POINT (-0.225258 51.476589)", altitude=None,
               detection_time=datetime.fromisoformat("2024-03-20T13:55:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3], node_id=uuid4())

    cotravels: List[PotentialMatch] = CotravelSensemaker().execute(track)

    assert len(cotravels) == 0


def test_cotravel_valid_before_observation_threshold_exceeded(tester_db):

    node_id = uuid4()

    # 10 minutes behind fixture track
    p1 = Point(acm=DEFAULT_ACM, location="POINT (15.650729 38.252533)", altitude=None,
               detection_time=datetime.fromisoformat("2024-09-10T05:10:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p2 = Point(acm=DEFAULT_ACM, location="POINT (15.610534 38.228556)", altitude=None,
               detection_time=datetime.fromisoformat("2024-09-10T05:20:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    p3 = Point(acm=DEFAULT_ACM, location="POINT (15.594253 38.185378)", altitude=None,
               detection_time=datetime.fromisoformat("2024-09-10T05:30:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # past observational threshold so shouldn't be added
    p4 = Point(acm=DEFAULT_ACM, location="POINT (15.578989 38.142175)", altitude=None,
               detection_time=datetime.fromisoformat("2024-09-10T05:46:00-04:00"), node_id=node_id, node_version=1,
               attribute_id=uuid4(), attribute_version=1, source_id=uuid4())

    # Create Track Object
    track = Track(points=[p1, p2, p3, p4], node_id=uuid4())

    cotravels: List[PotentialMatch] = CotravelSensemaker().execute(track)

    assert len(cotravels) == 1
    cotravel = cotravels[0]
    assert cotravel.true_cotravel
    assert cotravel.track1 == track.node_id
    assert cotravel.start_time1 == p1.detection_time
    assert cotravel.start_time2 == datetime.fromisoformat("2024-09-10T05:00:00-04:00")
    assert cotravel.last_time1 == p3.detection_time
    assert cotravel.last_time2 == datetime.fromisoformat("2024-09-10T05:20:00-04:00")
