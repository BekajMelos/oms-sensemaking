"""Loiter Sensemakers."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from oms_sdk.generated.generated_graphql_client.client import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence, ObjectTier
from shapely import LineString

from oms_sensemaking.clients.instances import aac_client
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.models.geo import Point, Track
from oms_sensemaking.models.sensemaking import AtomsType, FindingType

LOGGER = logging.getLogger(__name__)


class PotentialLoiter:
    """Reprents a potential loiter event."""

    def __init__(self, start_time: datetime, latest_time: datetime):
        """
        Create a new instance of PotentialLoiter.

        :param start_time: The time potential loiter started.
        :param latest_time: The time the potential loiter ended.
        """
        self.start_time = start_time
        self.latest_time = latest_time

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


@dataclass
class Loiter(FindingBase):
    """Represents a loiter event."""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.GEO_LOITER)
    loiter_id: UUID = field(init=False, default_factory=uuid4)
    vehicle_id: UUID
    geohash: str
    start_time: datetime
    end_time: datetime
    processed_points: list[Point]
    geometry: LineString

    def get_acm(self) -> dict:
        """Rollup the acm from the points"""
        return aac_client.get_acm_rollup([{"ACM": point.acm} for point in self.processed_points])

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

    def to_geojson(self) -> dict:
        """Geojson representation of the loiter geometry"""

        return {"type": "LineString", "coordinates": [point.coordinates for point in self.processed_points]}


class LoiterSensemaker(Sensemaker):
    """
    A sensemaker for analyzing tracks for loiters.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "loiter" algorithm implementation.

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of LoiterSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.name = self.__class__.__name__
        self.config = {
            "loiter_event_node_iri": SETTINGS.loiter_event_node_iri,
            "loiter_relationship_iri": SETTINGS.loiter_relationship_iri,
            "loiter_event_node_attribute_iri": SETTINGS.loiter_event_node_attribute_iri,
        }
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, data: Track, config: dict) -> list[Loiter]:
        """
        Check for Loiter Events.

        Collect a list of prospective loiters. Check each of them to make sure
        they are long enough aka > LOITER_MIN_TIME. If not, it wasn't long
        enough. Ignore. If so, it's a valid loiter. Create a Loiter Object and
        add it to the list to be returned.

        :param data: The track to analyze.
        :return: list[Loiter] list of loiter events found
        """
        LOGGER.debug("Detecting Loiters in %s", data.node_id)

        # Update the config with specific geo settings
        self.config.update(config)

        confirmed_loiters: list[Loiter] = []
        prospective_loiters: dict[str, list[PotentialLoiter]] = self.find_prospective_loiters(data.points)

        # check for potential loiters that are long enough (> LOITER_MIN_TIME)
        # TODO could also check for loiters across geohashes that could be combined
        for point_geohash, potential_loiters in prospective_loiters.items():
            for potential_loiter in potential_loiters:
                time_diff = abs(potential_loiter.latest_time - potential_loiter.start_time)
                if time_diff >= timedelta(seconds=self.config["loiter_min_time"]):
                    # if craft loitered long enough
                    loiter_points = self._points_in_time_window(data, potential_loiter)
                    geometry = LineString([point.coordinates for point in loiter_points])
                    loiter = Loiter(
                        data.node_id,
                        point_geohash,
                        loiter_points[0].detection_time,
                        loiter_points[-1].detection_time,
                        loiter_points,
                        geometry,
                    )
                    confirmed_loiters.append(loiter)

        if confirmed_loiters:
            track_uuid = data.track_uuid
            # LOGGER.info(f"Found Loiters ({len(confirmed_loiters)}) in {track_uuid}")
            # LOGGER.info("Found Loiters (%d) in %s", (len(confirmed_loiters), track_uuid))
            LOGGER.info("Found Loiters (%d) in %s", len(confirmed_loiters), track_uuid)

        for loiter in confirmed_loiters:
            self.publish_loiter(data, loiter)

        return confirmed_loiters

    def _points_in_time_window(self, track: Track, potential_loiter: PotentialLoiter) -> list[Point]:
        """
        Check for points within the loiter time window
        """
        loiter_points_in_time_window = []
        for point in track.points:
            if (
                point.detection_time >= potential_loiter.start_time
                and point.detection_time <= potential_loiter.latest_time
            ):
                loiter_points_in_time_window.append(point)
        return loiter_points_in_time_window

    def find_prospective_loiters(self, points: list[Point]) -> dict[str, list[PotentialLoiter]]:
        """
        Find Prospective Loiters.

        Checks through the points and captures all points that are within a single geohash and
        within the VALID_OBSERVED_THRESHOLD_SECONDS to build a list of prospective loiters
        (PotentialLoiters). Keep adding points to a prospective loiter if they are within the
        geohash and the time threshold. Avoid accidentally removing valid loiters

        :param points: list of track points
        :return: Map of geohashes to a list of potential loiters within that geohash
        """
        prospective_loiters: dict[str, list[PotentialLoiter]] = {}
        # Find potential loiters - consecutive points within a geohash within a time threshold
        for point in points:
            point_geohash = point.geohash[: self.config["loiter_geohash"]]

            if point_geohash in prospective_loiters:
                # existing geohash
                last_loiters: list[PotentialLoiter] = prospective_loiters[point_geohash]
                last_loiter = last_loiters[-1]
                time_diff = abs((last_loiter.latest_time - point.detection_time))
                if time_diff <= timedelta(seconds=self.config["valid_observed_threshold_seconds"]):
                    # valid point, update the latest time for the last loiter for that geohash
                    last_loiter.latest_time = point.detection_time
                else:
                    # Points are too far apart - they've been unobserved for too long.
                    # Expire if it's not already a valid loiter
                    validity_time_diff = abs(last_loiter.latest_time - last_loiter.start_time)
                    if validity_time_diff < timedelta(seconds=self.config["loiter_min_time"]):
                        prospective_loiters.pop(point_geohash)
                    else:
                        # it must be a new loiter at the same location
                        potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                        last_loiters.append(potential_loiter)
            else:
                # new geohash
                potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                prospective_loiters[point_geohash] = [potential_loiter]

        return prospective_loiters

    def publish_loiter(self, track: Track, loiter: Loiter) -> None:
        """
        Publish Loiter to ATOMS

        :param loiter: Loiter Event to publish
        :return: None
        """
        source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources
        tags = [SETTINGS.geo_sensemaker_event_tag]

        create_node_input = CreateNodeInput(
            acm=loiter.get_acm(),
            name=SETTINGS.loiter_event_name,
            tier=ObjectTier.DERIVATIVE,
            tags=tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.geospatial_sm_label,
                SETTINGS.loiter_sm_label,
                self.version_string,
            ],
            classIri=SETTINGS.loiter_event_node_iri,
            ifcCodes=set(),
            isNso=True,
        )
        published_node = self.oms_crud_tool.create_node(node_input=create_node_input)

        loiter.atoms_id = published_node.id
        loiter.atoms_type = AtomsType.NODE

        create_relationship_input = CreateRelationshipInput(
            tags=tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.geospatial_sm_label,
                SETTINGS.loiter_sm_label,
                self.version_string,
            ],
            name=SETTINGS.loiter_event_name,
            startNodeId=published_node.id,
            endNodeId=loiter.vehicle_id,
            confidence=Confidence.HIGH,
            acm=loiter.get_acm(),
            objectPropertyIri=SETTINGS.loiter_relationship_iri,
            sourceId=source_id,
        )
        self.oms_crud_tool.publish_relationships([create_relationship_input])

        create_attribute_input = CreateAttributeInput(
            attributeIri=SETTINGS.loiter_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL.value,
            confidence=Confidence.HIGH.value,
            tags=tags,
            labels=[
                SETTINGS.sm_inferenced_label,
                SETTINGS.geospatial_sm_label,
                SETTINGS.loiter_sm_label,
                self.version_string,
            ],
            sourceId=source_id,
            geometry=loiter.to_geojson(),
            nodeId=published_node.id,
            acm=loiter.get_acm(),
            valueStart=loiter.start_time,
            valueEnd=loiter.end_time,
        )
        self.oms_crud_tool.publish_attributes([create_attribute_input])
