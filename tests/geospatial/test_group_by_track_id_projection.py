import uuid

from oms_sensemaking.geospatial.models.group_by_track_id_projection import GroupByTrackIdProjection


def test_init_assigns_fields():
    track_id = uuid.uuid4()
    bookends = ["start", "end"]

    obj = GroupByTrackIdProjection(track_id, bookends)

    assert obj.track_uuid == track_id
    assert obj.track_bookends == bookends


def test_str_returns_dict_string():
    track_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    bookends = ["alpha", "omega"]

    obj = GroupByTrackIdProjection(track_id, bookends)

    # str() should equal the dict representation
    expected = str(
        {
            "track_uuid": track_id,
            "track_bookends": bookends,
        }
    )
    assert str(obj) == expected


def test_repr_matches_str():
    track_id = uuid.uuid4()
    bookends = ["foo", "bar"]

    obj = GroupByTrackIdProjection(track_id, bookends)

    assert repr(obj) == str(obj)
