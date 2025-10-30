import logging
from itertools import groupby
from operator import attrgetter
from uuid import UUID, uuid4

from oms_sdk.generated.generated_graphql_client import NodeNode

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.dao.track import APITrack
from oms_sensemaking.models.geo import (
    CommonSenseFilter,
    Point,
    Track,
    TrackWeaverBase,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class TrackGenerator:
    def __init__(self, ontology_service: OntologyService) -> None:
        self._ontology_service = ontology_service

    def generate_track(
        self,
        track_uuid: UUID,
        track_weaver: TrackWeaverBase,
        common_sense_filters: list[CommonSenseFilter],
        track_node_buffer: dict[UUID, list[Point]],
        oms_crud_tool: OmsCrudTool,
    ) -> Track:
        """Generate Track object. Splits the full track into max_track_time_length_seconds time intervals.
        Then runs the common sense filters and track weaver.

        :param track_uuid: UUID of the track
        :return: Created Track object
        """

        track = None

        points = track_node_buffer[track_uuid]
        points.sort(key=attrgetter("detection_time"))

        # Get the IRI hierarchy for the node
        try:
            oms_node = oms_crud_tool.get_node(points[0].node_id)
        except IndexError as e:
            raise TrackLengthError(e) from e

        ancestor_iris = {oms_node.classIri}.union(self.get_node_ancestors_iris(oms_node))

        time_bins = self.bin_points_for_track(points)
        csf_funcs = GeoCSFTrackPointHelpers(cs_filters=common_sense_filters)
        for binned_points in time_bins.values():
            # since we split the track points into bins, each bin needs an id
            sub_track_id = uuid4()
            LOGGER.debug("Split bin %s from %s", sub_track_id, track_uuid)

            binned_points = csf_funcs.csf_single_track_points(ancestor_iris, binned_points, sub_track_id)
            # Execute a track weaver on the buffered Points
            # and save the new Track with the chosen UUID
            weaved_track = track_weaver.execute(binned_points)

            weaved_track = csf_funcs.csf_track_point_deltas(ancestor_iris, sub_track_id, weaved_track)
            # Abort and do not clear buffer if final track has less than 2 points
            if len(weaved_track.points) < 2:
                continue
            track_dict = {
                "points": weaved_track.points,
                "node_id": weaved_track.node_id,
                "algorithm": weaved_track.algorithm,
                "observation_ids": weaved_track.observation_ids,
                "acm": aac_client.get_acm_rollup([{"ACM": point.acm} for point in weaved_track.points]),
            }

            with db_session() as db:
                db.expire_on_commit = False
                track, _ = Track.get_or_create(
                    session=db,
                    defaults=track_dict,
                    track_uuid=sub_track_id,
                )

            LOGGER.info("Track completed: %s", sub_track_id)
            oms_track = APITrack(track).create_oms_track()
            LOGGER.info("OMS Track published: %s", oms_track.id)

        if not track:
            raise TrackLengthError("Not enough points for track.") from None

        return track

    def bin_points_for_track(self, points: list[Point]):
        """
        Put points into bins that correspond to a timerange
        Start with the most recent point when creating bins so if there'd be a bin with only one point on the end,
        the single point'd bin would be the oldest bin which would be the least important
        """
        points.reverse()
        time_bins = {
            k: list(g)
            for k, g in groupby(
                points,
                key=lambda x: x.detection_time.timestamp() // SETTINGS.max_track_time_length_seconds,
            )
        }
        for key in time_bins:
            time_bins[key].reverse()
        return time_bins

    def get_node_ancestors_iris(self, oms_node: NodeNode) -> set[str]:
        """
        Get ancestor's iris.

        :param oms_node: Node to grab the status for
        :return: The Node's ancestor's iri list
        """
        return self._ontology_service.geospatial_get_node_ancestors_iris(oms_node)


class GeoCSFTrackPointHelpers:
    def __init__(self, cs_filters: list[CommonSenseFilter]) -> None:
        self.common_sense_filters = cs_filters

    def csf_single_track_points(
        self, ancestor_iris: set[str], binned_points: list[Point], sub_track_id: UUID
    ) -> list[Point]:
        """
        Run commense sense filter on single point part of a track
        """
        for csf in self.common_sense_filters:
            if SETTINGS.apply_common_sense_filters and csf.iri in ancestor_iris:
                LOGGER.debug(
                    "Running common sense filter %s on single points in track %s",
                    csf.name,
                    sub_track_id,
                )
                binned_points = csf.filter_points(binned_points)
        return binned_points

    def csf_track_point_deltas(self, ancestor_iris: set[str], sub_track_id: UUID, weaved_track: Track) -> Track:
        for csf in self.common_sense_filters:
            if SETTINGS.apply_common_sense_filters and csf.iri in ancestor_iris:
                LOGGER.debug(
                    "Running common sense filter %s on point deltas in track %s",
                    csf.name,
                    sub_track_id,
                )
                weaved_track.points = csf.filter_point_deltas(weaved_track.points)
        return weaved_track
