"""Similar Tracks Sensemakers."""
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.geo import Track


class SimilarTracksSensemaker(Sensemaker):
    """A sensemaker for detecting similar tracks."""

    def __init__(self) -> None:
        super().__init__()

    def process_data(self, data: Track) -> Track:
        pass
