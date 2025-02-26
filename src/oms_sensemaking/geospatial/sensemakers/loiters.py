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
from oms_sensemaking.core.sensemakers import FindingBase, OmsPublisher, Sensemaker
from oms_sensemaking.models.geo import Point, Track
from oms_sensemaking.models.sensemaking import FindingType

LOGGER = logging.getLogger(__name__)

VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=SETTINGS.valid_observed_threshold_seconds)

LOITER_MIN_TIME = timedelta(seconds=SETTINGS.loiter_min_time)


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
    geohash_low: str
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


class LoiterOmsPublisher(OmsPublisher):
    def format_nodes(self, track: Track, loiters: list[Loiter]) -> list[CreateNodeInput]:
        """
        Format Node Objects to publish to OMS

        :param track: Track in which the loiter was found
        :param loiters: list of Loiter events
        :return: CreateNodeInput objects
        """
        formatted_nodes = []
        for loiter in loiters:
            create_event_node = CreateNodeInput(
                acm=loiter.get_acm(),
                name=SETTINGS.loiter_event_name,
                tier=ObjectTier.DERIVATIVE,
                tags=[SETTINGS.geo_sensemaker_event_tag],
                classIri=SETTINGS.loiter_event_node_iri,
                ifcCodes=set(),
                isNso=True,
            )

            self.node_uuid_list.append(str(loiter.loiter_id))
            formatted_nodes.append(create_event_node)

        return formatted_nodes

    def format_relationships(self, track: Track, loiters: list[Loiter]) -> list[CreateRelationshipInput]:
        """
        Format Relationship Objects to publish to OMS

        :param track: Track in which the loiter was found
        :param loiters: list of Loiter events
        :return: CreateRelationshipInput objects
        """

        formatted_relationships = []
        source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources

        for loiter in loiters:
            create_relationship_input = CreateRelationshipInput(
                tags=[SETTINGS.geo_sensemaker_event_tag],
                name=SETTINGS.loiter_event_name,
                startNodeId=self.node_id_mapping[str(loiter.loiter_id)],
                endNodeId=loiter.vehicle_id,
                confidence=Confidence.HIGH,
                acm=loiter.get_acm(),
                objectPropertyIri=SETTINGS.loiter_relationship_iri,
                sourceId=source_id,
            )
            formatted_relationships.append(create_relationship_input)

        return formatted_relationships

    def format_attributes(self, track: Track, loiters: list[Loiter]) -> list[CreateAttributeInput]:
        """
        Format Attribute Objects to publish to OMS

        :param track: Track in which the loiter was found
        :param loiters: list of Loiter events
        :return: CreateAttributeInput objects
        """
        formatted_attributes = []
        source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources

        for loiter in loiters:
            create_attribute_input = CreateAttributeInput(
                attributeIri=SETTINGS.loiter_event_node_attribute_iri,
                attributeValue="geo",
                attributeDisplayValue="",
                attributeType=AttributeType.GEOSPATIAL.value,
                confidence=Confidence.HIGH.value,
                tags=[SETTINGS.geo_sensemaker_event_tag],
                sourceId=source_id,
                geometry=loiter.to_geojson(),
                nodeId=self.node_id_mapping[str(loiter.loiter_id)],
                acm=loiter.get_acm(),
                valueStart=loiter.start_time,
                valueEnd=loiter.end_time,
            )
            formatted_attributes.append(create_attribute_input)
        return formatted_attributes


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
            "valid_observed_threshold_seconds": SETTINGS.valid_observed_threshold_seconds,
            "loiter_min_time": SETTINGS.loiter_min_time,
            "loiter_event_node_iri": SETTINGS.loiter_event_node_iri,
            "loiter_relationship_iri": SETTINGS.loiter_relationship_iri,
            "loiter_event_node_attribute_iri": SETTINGS.loiter_event_node_attribute_iri,
            "geohash_low": SETTINGS.geohash_low,
        }
        self.publisher = LoiterOmsPublisher(oms_crud_tool)

    def process_data(self, data: Track) -> list[Loiter]:
        """
        Check for Loiter Events.

        Collect a list of prospective loiters. Check each of them to make sure
        they are long enough aka > LOITER_MIN_TIME. If not, it wasn't long
        enough. Ignore. If so, it's a valid loiter. Create a Loiter Object and
        add it to the list to be returned.

        :param data: The track to analyze.
        :return: list[Loiter] list of loiter events found
        """
        LOGGER.debug(f"Detecting Loiters in {data.node_id}")
        confirmed_loiters: list[Loiter] = []
        prospective_loiters: dict[str, list[PotentialLoiter]] = self.find_prospective_loiters(data.points)

        # check for potential loiters that are long enough (> LOITER_MIN_TIME)
        # TODO could also check for loiters across geohashes that could be combined
        for point_geohash, potential_loiters in prospective_loiters.items():
            LOGGER.debug(f"Prospective Loiter: {point_geohash}: {potential_loiters}")
            for potential_loiter in potential_loiters:
                time_diff = abs(potential_loiter.latest_time - potential_loiter.start_time)
                if time_diff >= timedelta(seconds=self.config["loiter_min_time"]):
                    # if craft loitered long enough
                    loiter_points: list[Point] = []
                    for point in data.points:
                        # check for points within the loiter time window
                        if (
                            point.detection_time >= potential_loiter.start_time
                            and point.detection_time <= potential_loiter.latest_time
                        ):
                            loiter_points.append(point)

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
            LOGGER.info(f"Found Loiters ({len(confirmed_loiters)}) in {track_uuid}")

        for loiter in confirmed_loiters:
            LOGGER.debug("Loiter geometry: " + loiter.geometry.wkt)

        return confirmed_loiters

    @staticmethod
    def find_prospective_loiters(points: list[Point]) -> dict[str, list[PotentialLoiter]]:
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
            point_geohash_low = point.geohash[: SETTINGS.geohash_low]

            if point_geohash_low in prospective_loiters:
                # existing geohash
                last_loiters: list[PotentialLoiter] = prospective_loiters[point_geohash_low]
                last_loiter = last_loiters[-1]
                time_diff = abs((last_loiter.latest_time - point.detection_time))
                if time_diff <= VALID_OBSERVED_THRESHOLD_SECONDS:
                    # valid point, update the latest time for the last loiter for that geohash
                    last_loiter.latest_time = point.detection_time
                else:
                    # Points are too far apart - they've been unobserved for too long.
                    # Expire if it's not already a valid loiter
                    validity_time_diff = abs(last_loiter.latest_time - last_loiter.start_time)
                    if validity_time_diff < LOITER_MIN_TIME:
                        prospective_loiters.pop(point_geohash_low)
                    else:
                        # it must be a new loiter at the same location
                        potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                        last_loiters.append(potential_loiter)
            else:
                # new geohash
                potential_loiter = PotentialLoiter(point.detection_time, point.detection_time)
                prospective_loiters[point_geohash_low] = [potential_loiter]

        return prospective_loiters
