"""Cotravel Sensemaker."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.geospatial.models.processed_point import ProcessedPoint
from oms_sensemaking.geospatial.models.track import Track
from oms_sensemaking.geospatial.models.track_entry import TrackEntry
from oms_sensemaking.geospatial.tracks import BaseTrackService

LOGGER = logging.getLogger(__name__)


VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=SETTINGS.valid_observed_threshold_seconds)
MIN_COTRAVEL_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_cotravel_duration_seconds)
MIN_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_lag_lead_duration_seconds)
MAX_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.max_lag_lead_duration_seconds)


class PotentialMatch:
    def __init__(
        self,
        track1: UUID,
        track2: UUID,
        start_time1: datetime,
        start_time2: datetime,
        last_time1: datetime,
        last_time2: datetime,
        true_cotravel: bool,
    ):
        self.track1 = track1
        self.track2 = track2
        self.start_time1 = start_time1
        self.start_time2 = start_time2
        self.last_time1 = last_time1
        self.last_time2 = last_time2
        self.true_cotravel = true_cotravel

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def tentative_add(self, time1: datetime, time2: datetime) -> bool:
        """
        Checks if a new colocation can fit into a cotravel that is being created and adds it if so.

        :param time1:
        :param time2:
        :return: boolean indicating if the PotentialMatch was updated
        """
        if (
            abs(self.last_time1 - time1) <= VALID_OBSERVED_THRESHOLD_SECONDS
            and abs(self.last_time2 - time2) <= VALID_OBSERVED_THRESHOLD_SECONDS
        ):
            self.last_time1 = time1
            self.last_time2 = time2
            self.true_cotravel = self.true_cotravel and (abs(time1 - time2) <= MIN_LAG_LEAD_DURATION_SECONDS)
            return True
        return False

    def check_valid(self) -> bool:
        """Checks whether a PotentialMatch has met the duration requirements."""
        return (
            self.last_time1 - self.start_time1 >= MIN_COTRAVEL_DURATION_SECONDS
            and self.last_time2 - self.start_time2 >= MIN_COTRAVEL_DURATION_SECONDS
        )


class Colocation:
    """For CotravelService use, a Colocation stores the data for two tracks' intersection."""

    def __init__(self, track1: UUID, track2: UUID, processed_point: ProcessedPoint, track_entry):
        self.track1 = track1
        self.track2 = track2
        self.processed_point = processed_point
        self.track_entry = track_entry

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class CotravelService:
    """Service for detecting cotravel and lag/lead events."""

    @classmethod
    async def detect_cotravels(cls, track: Track) -> List[PotentialMatch]:
        """
        Takes a single track, queries for colocated observations

        :param Track object: Track object to detect cotravels on
        :return: List[PotentialMatch] list of CotravelEvents events found
        """
        LOGGER.info(f"Detecting Cotravels in {track}")

        cotravels: List[PotentialMatch] = []
        matches: List[Colocation] = []

        # find matching points (colocations) for each point in the track
        for point in track.points:
            time = point.timestamp
            track_entries: List[TrackEntry] = await cls.get_points(
                point.geohash_low,
                track.track_node_id,
                (time - MAX_LAG_LEAD_DURATION_SECONDS),
                (time + MAX_LAG_LEAD_DURATION_SECONDS),
                time,
            )

            # Create colocations from track entries
            match_points: List[Colocation] = [
                Colocation(track.track_node_id, entry.track_node_id, point, entry) for entry in track_entries
            ]

            if matches:
                matches.extend(match_points)
            else:
                matches = match_points

        if not matches:
            return []

        # group points (TrackEntrys) by track2
        groups = defaultdict(list)
        for entry in matches:
            groups[entry.track2].append(entry)

        # determine cotravels on each list
        for _, colocations in groups.items():
            sorted_entries = sorted(colocations, key=lambda colocation: colocation.track_entry.start_time)
            cotravels.extend(await CotravelService.determine_cotravels(sorted_entries))

        if cotravels:
            LOGGER.info(f"Found Cotravels: {cotravels}")
        return cotravels

    @staticmethod
    async def get_points(
        geohash_low: str, track_node_id: UUID, min_time: datetime, max_time: datetime, target_time: datetime
    ) -> List[TrackEntry]:
        """
        Find points in other tracks that match the geohash of the given point within the time
        intervals

        :param geohash_low: Geohash to match in the DB
        :param track_node_id: Track node to ignore
        :param min_time: Min allowed time to lag by
        :param max_time: Max allowed time to lag by
        :param target_time: time to sort the response by
        :return: List of cotravels
        """
        return BaseTrackService.find_location_by_geohash(geohash_low, track_node_id, min_time, max_time, target_time)

    @staticmethod
    async def determine_cotravels(colocations: List[Colocation]) -> List[PotentialMatch]:
        """
        Given the list of colocations, that they meet the time requirements

        :param colocations: List of colocations
        :return: List of cotravels
        """
        completed: List[PotentialMatch] = []
        to_add_to: Optional[PotentialMatch] = None

        for colocation in colocations:
            if to_add_to:
                # if we have a potential match already, keep checking
                if (
                    not to_add_to.tentative_add(colocation.processed_point.timestamp, colocation.track_entry.start_time)
                    and to_add_to.check_valid()
                ):
                    # the next colocation point doesn't meet the observation threshold but we still
                    # have a valid cotravel. Add the cotravel to the list and start over with a new
                    # potential match

                    # TODO this code path needs to be tested
                    completed.append(to_add_to)
                    true_cotravel = (
                        abs(colocation.processed_point.timestamp - colocation.track_entry.start_time)
                        <= MIN_LAG_LEAD_DURATION_SECONDS
                    )
                    to_add_to = PotentialMatch(
                        colocation.track1,
                        colocation.track2,
                        colocation.processed_point.timestamp,
                        colocation.track_entry.start_time,
                        colocation.processed_point.timestamp,
                        colocation.track_entry.start_time,
                        true_cotravel,
                    )
            else:
                # if no potential match already exists, create and start checking
                true_cotravel = (
                    abs(colocation.processed_point.timestamp - colocation.track_entry.start_time)
                    <= MIN_LAG_LEAD_DURATION_SECONDS
                )

                to_add_to = PotentialMatch(
                    colocation.track1,
                    colocation.track2,
                    colocation.processed_point.timestamp,
                    colocation.track_entry.start_time,
                    colocation.processed_point.timestamp,
                    colocation.track_entry.start_time,
                    true_cotravel,
                )

        # check the last point for a valid cotravel
        if to_add_to and to_add_to.check_valid():
            completed.append(to_add_to)

        return completed
