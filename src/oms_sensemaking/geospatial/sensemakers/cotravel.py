"""Cotravel Sensemakers."""
from oms_sensemaking.core.sensemakers import Sensemaker
from oms_sensemaking.models.geo import Track


class CotravelSensemaker(Sensemaker):
    """A sensemaker for analyzing tracks for cotravelers."""

    def __init__(self) -> None:
        super().__init__()

    def process_data(self, data: Track) -> Track:
        pass
