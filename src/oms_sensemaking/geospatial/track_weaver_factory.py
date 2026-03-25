from oms_sensemaking.models.track_weavers import (
    ExtendedKalmanTrackWeaver,
    NaiveTrackWeaver,
    TimeBinTrackWeaver,
    TrackWeaverBase,
)


class TrackWeaverFactory:
    """
    Track Weaver Factory

    This class is responsible for producing a Track Weaver instance to use
    """

    def make_track_weaver(self, algorithm: str) -> TrackWeaverBase:
        """Build a new track weaver instance"""
        match algorithm:
            case "extended_kalman_filter":
                return ExtendedKalmanTrackWeaver()
            case "naive":
                return NaiveTrackWeaver()
            case "time_bin_weighted_average":
                return TimeBinTrackWeaver()
            case _:
                raise ValueError(f"Invalid Track Weaver algorithm: {algorithm}")
