from pytest import raises

from oms_sensemaking.geospatial.track_weaver_factory import TrackWeaverFactory


def test_builds_valid_weaver():
    """
    Do a simple check to make sure it built a track weaver
    """
    factory = TrackWeaverFactory()
    track_weavers = ["extended_kalman_filter", "naive", "time_bin_weighted_average"]
    for track_weaver in track_weavers:
        strategy = factory.make_track_weaver(track_weaver)
        assert strategy is not None


def test_errors_on_unexpected_input():
    """
    Make sure that we throw an obvious error if the track weaver arg is incorrect
    """
    with raises(ValueError):
        factory = TrackWeaverFactory()
        factory.make_track_weaver("asdf")
