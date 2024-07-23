"""Provides "similar" sensemaker."""

import logging
import uuid
from queue import PriorityQueue
from typing import List, Set

from geolib import geohash

from oms_sensemaking.config import SETTINGS
from oms_sensemaking.geospatial.models.group_by_track_node_id_projection import GroupByTrackNodeIdProjection
from oms_sensemaking.geospatial.models.processed_point import ProcessedPoint
from oms_sensemaking.geospatial.models.track import Track
from oms_sensemaking.geospatial.tracks import BaseTrackService

LOGGER = logging.getLogger(__name__)


class ComparisonResult:
    def __init__(self, track_node_id: uuid.UUID, similarity_score: float):
        self.track_node_id = track_node_id
        self.similarity_score = similarity_score

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class TopSimilar:
    def __init__(self):
        self.top_similarities = PriorityQueue(maxsize=SETTINGS.n_tracks)

    def __str__(self):
        return str((self.top_similarities.maxsize, list(self.top_similarities.queue)))

    def __repr__(self):
        return self.__str__()

    def add_comparison_result(self, comparison_result: ComparisonResult) -> None:
        self.top_similarities.put((comparison_result.similarity_score, comparison_result.track_node_id))


class MostSimilarTrackService:
    """Service for discovering most similar tracks."""

    @classmethod
    def most_similar_track_node_ids(cls, track: Track) -> TopSimilar:
        """
        Primary method to obtain N-most similar track objects to the track provided.

        :param track: Track object to detect cotravels on
        :return: List[PotentialMatch] list of TopSimilar tracks
        """
        LOGGER.info(f"Looking for similar tracks to {track.track_node_id}")

        similar_results: TopSimilar = TopSimilar()

        first: ProcessedPoint = track.points[0]
        last: ProcessedPoint = track.points[-1]
        ref_track_geohash_set: Set[str] = cls.get_buffered_geohash_set(track.points)

        # query for tracks that start and end within the QUERY_DISTANCE
        LOGGER.debug(f"Reference track has first {first} and last {last} points")
        similar_track_groups: List[GroupByTrackNodeIdProjection] = BaseTrackService.query_for_similar_tracks(
            first.geometry, last.geometry, SETTINGS.within_meters
        )

        seen_groups = []
        for similar_track_group in similar_track_groups:
            # Remove any representations of the track of interest itself
            if similar_track_group.track_node_id == track.track_node_id:
                continue

            #
            if similar_track_group.track_node_id in seen_groups:
                continue
            seen_groups.append(similar_track_group.track_node_id)

            similar_track: Track = cls.get_track_from_group_projection(similar_track_group)
            # obtain buffered hashSet for prospective similar track
            eval_track_geohash_set = cls.get_buffered_geohash_set(similar_track.points)
            # calculate similarity by Jaccard measure of bufferedHashSets
            comparison_result: ComparisonResult = cls.determine_jaccard_similarity(
                ref_track_geohash_set, eval_track_geohash_set, similar_track.track_node_id
            )

            similar_results.add_comparison_result(comparison_result)

        return similar_results

    @staticmethod
    def determine_jaccard_similarity(
        ref_track_geohash_set: Set[str], eval_track_geohash_set: Set[str], eval_track_node_id: uuid.UUID
    ) -> ComparisonResult:
        # intersection of two sets
        intersection = len(ref_track_geohash_set.intersection(eval_track_geohash_set))
        # Unions of two sets
        union = len(ref_track_geohash_set.union(eval_track_geohash_set))
        score = intersection / union
        LOGGER.debug(f"Overall similarity for {eval_track_geohash_set}, {score}")
        return ComparisonResult(eval_track_node_id, score)

    @staticmethod
    def get_track_from_group_projection(group_projection: GroupByTrackNodeIdProjection) -> Track:
        """
        Obtain object for processing from groupBy query projection results.

        :param group_projection: GroupByTrackNodeIdProjection
        :return: Track object
        """
        return BaseTrackService.get_track(group_projection.track_node_id)

    @staticmethod
    def get_buffered_geohash_set(points: List[ProcessedPoint]) -> Set[str]:
        """
        Obtain a bufferedGeoHash set from the points provided.

        For each point, a reference geohash with one less character is added to
        the empty set. The neighbors of the reference hash are added to the set.

            Note: The lower precision geohash was used initially for test and
            evaluation purposes. This method should be tested with a more
            robust set of representative data in order to determine the most
            appropriate hash levels.

        :param points: list of track points
        :return: Set of geohashes
        """
        buffered_geohash_set: Set[str] = set()

        for point in points:
            # reduce precision of the geohash by one to generate set for comparison to expand range for 'similar' tracks
            base_geohash = point.geohash_low[0:-1]
            buffered_geohash_set.add(base_geohash)

            neighbors = geohash.neighbours(base_geohash)
            for neighbor in neighbors:
                buffered_geohash_set.add(neighbor)

        return buffered_geohash_set
