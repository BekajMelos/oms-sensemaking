"""Cotravel Sensemakers."""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property
from typing import List, Optional
from uuid import UUID, uuid4

from geolib import geohash
from oms_sdk.generated.generated_graphql_client.client import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence, ObjectTier
from shapely import LineString, MultiLineString
from sqlalchemy import func, select
from sqlalchemy.orm import with_expression

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.acm import get_acm_rollup
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, OmsPublisher, Sensemaker
from oms_sensemaking.models.geo import Point, Track, get_track
from oms_sensemaking.models.sensemaking import FindingType

LOGGER = logging.getLogger(__name__)

VALID_OBSERVED_THRESHOLD_SECONDS = timedelta(seconds=SETTINGS.valid_observed_threshold_seconds)

MIN_COTRAVEL_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_cotravel_duration_seconds)

MIN_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.min_lag_lead_duration_seconds)

MAX_LAG_LEAD_DURATION_SECONDS = timedelta(seconds=SETTINGS.max_lag_lead_duration_seconds)


class PotentialMatch:
    """Represents a potential co-travel match."""

    def __init__(
        self,
        track1_node_id: UUID,
        track2_node_id: UUID,
        start_time1: datetime,
        start_time2: datetime,
        last_time1: datetime,
        last_time2: datetime,
        true_cotravel: bool,
    ):
        """Create a new instance of PotentialMatch."""
        self.track1_node_id = track1_node_id
        self.track2_node_id = track2_node_id
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
        Check if a new colocation can fit into a cotravel that is being created and adds it if so.

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
        """Check whether a PotentialMatch has met the duration requirements."""
        return (
            self.last_time1 - self.start_time1 >= MIN_COTRAVEL_DURATION_SECONDS
            and self.last_time2 - self.start_time2 >= MIN_COTRAVEL_DURATION_SECONDS
        )


@dataclass
class Cotravel(FindingBase):
    """Represents a Cotravel Event"""

    FINDING_TYPE: FindingType = field(init=False, default=FindingType.GEO_COTRAVEL)
    cotravel_id: UUID = field(init=False, default_factory=uuid4)
    track1: Track
    track2: Track
    start_time: datetime
    last_time: datetime
    true_cotravel: bool
    geometry: MultiLineString = field(init=False)

    def __post_init__(self) -> None:
        """Post init for Cotravel"""
        ls1 = LineString([point.coordinates for point in self.track1.points])
        ls2 = LineString([point.coordinates for point in self.track2.points])
        self.geometry = MultiLineString([ls1, ls2])

    def __str__(self):
        return str(self.to_dict())

    @cached_property
    def acm(self) -> dict:
        """Rollup the acm from the points"""
        track1_acms = [point.acm for point in self.track1.points]
        track2_acms = [point.acm for point in self.track2.points]
        return get_acm_rollup([{"ACM": acm} for acm in (track1_acms + track2_acms)])

    def to_geojson(self) -> dict:
        """Geojson representation of the cotravel geometry"""

        return {
            "type": "MultiLineString",
            "coordinates": [
                [point.coordinates for point in self.track1.points],
                [point.coordinates for point in self.track2.points],
            ],
        }


class Colocation:
    """For CotravelService use, a Colocation stores the data for two tracks' intersection."""

    def __init__(self, track1_node_id: UUID, track2_node_id: UUID, point: Point, db_point: Point):
        """Create a new instance of Colocation."""
        self.track1_node_id = track1_node_id
        self.track2_node_id = track2_node_id
        self.point = point
        self.db_point = db_point

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()


class CotravelOmsPublisher(OmsPublisher):
    def format_nodes(self, track: Track, cotravels: List[Cotravel]) -> list[CreateNodeInput]:
        """
        Format Node Objects to publish to OMS

        :param track: Track in which the cotravel was found
        :param cotravels: List of Cotravel events
        :return: None
        """

        formatted_nodes = []
        for cotravel in cotravels:
            name = SETTINGS.cotravel_event_name if cotravel.true_cotravel else SETTINGS.lag_lead_event_name

            create_node_input = CreateNodeInput(
                acm=cotravel.acm,
                name=name,
                tier=ObjectTier.DERIVATIVE,
                tags=[SETTINGS.geo_sensemaker_event_tag],
                classIri=SETTINGS.cotravel_event_node_iri,
                ifcCodes=set(),
                isNso=True,
            )
            self.node_uuid_list.append(str(cotravel.cotravel_id))
            formatted_nodes.append(create_node_input)

        return formatted_nodes

    def format_relationships(self, track: Track, cotravels: List[Cotravel]) -> list[CreateRelationshipInput]:
        """
        Format Relationships Objects to publish to OMS

        :param track: Track in which the cotravel was found
        :param cotravels: List of Cotravel events
        :return: None
        """

        formatted_relationships = []
        for cotravel in cotravels:
            name = SETTINGS.cotravel_event_name if cotravel.true_cotravel else SETTINGS.lag_lead_event_name
            source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources
            tags = [SETTINGS.geo_sensemaker_event_tag]

            # track 1 relationship
            create_relationship_input1 = CreateRelationshipInput(
                tags=tags,
                name=f"{name} {SETTINGS.cotravel_track_to_event_relation_name}",
                startNodeId=self.node_id_mapping[str(cotravel.cotravel_id)],
                endNodeId=cotravel.track1.node_id,
                confidence=Confidence.HIGH,
                acm=cotravel.acm,
                objectPropertyIri=SETTINGS.cotravel_relationship_iri,
                sourceId=source_id,
            )
            formatted_relationships.append(create_relationship_input1)

            # track 2 relationship
            create_relationship_input2 = CreateRelationshipInput(
                tags=tags,
                name=f"{name} {SETTINGS.cotravel_track_to_event_relation_name}",
                startNodeId=self.node_id_mapping[str(cotravel.cotravel_id)],
                endNodeId=cotravel.track2.node_id,
                confidence=Confidence.HIGH,
                acm=cotravel.acm,
                objectPropertyIri=SETTINGS.cotravel_relationship_iri,
                sourceId=source_id,
            )
            formatted_relationships.append(create_relationship_input2)

        return formatted_relationships

    def format_attributes(self, track: Track, cotravels: List[Cotravel]) -> list[CreateAttributeInput]:
        """
        Format Attribute Objects to publish to OMS

        :param track: Track in which the cotravel was found
        :param cotravels: List of Cotravel events
        :return: None
        """

        formatted_attributes = []
        for cotravel in cotravels:
            source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources

            created_attribute_input = CreateAttributeInput(
                attributeIri=SETTINGS.cotravel_event_node_attribute_iri,
                attributeValue="geo",
                attributeDisplayValue="",
                attributeType=AttributeType.SPATIOTEMPORAL,
                confidence=Confidence.HIGH,
                tags=[SETTINGS.geo_sensemaker_event_tag],
                sourceId=source_id,
                geometry=cotravel.to_geojson(),
                nodeId=self.node_id_mapping[str(cotravel.cotravel_id)],
                acm=cotravel.acm,
                valueStart=cotravel.start_time,
                valueEnd=cotravel.last_time,
            )
            formatted_attributes.append(created_attribute_input)

        return formatted_attributes


class CotravelSensemaker(Sensemaker):
    """
    A sensemaker for analyzing tracks for cotravelers.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Initial "co-travel" algorithm implementation.

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of CotravelSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.config = {
            "valid_observed_threshold_seconds": SETTINGS.valid_observed_threshold_seconds,
            "min_cotravel_duration_seconds": SETTINGS.min_cotravel_duration_seconds,
            "min_lag_lead_duration_seconds": SETTINGS.min_lag_lead_duration_seconds,
            "max_lag_lead_duration_seconds": SETTINGS.max_lag_lead_duration_seconds,
            "geohash_low": SETTINGS.geohash_low,
            "cotravel_event_node_attribute_iri": SETTINGS.cotravel_event_node_attribute_iri,
            "cotravel_relationship_iri": SETTINGS.cotravel_relationship_iri,
            "cotravel_track_to_event_relation_name": SETTINGS.cotravel_track_to_event_relation_name,
            "cotravel_event_node_iri": SETTINGS.cotravel_event_node_iri,
            "cotravel_event_name": SETTINGS.cotravel_event_name,
            "lag_lead_event_name": SETTINGS.lag_lead_event_name,
            "geo_sensemaker_event_tag": SETTINGS.geo_sensemaker_event_tag,
        }
        self.publisher = CotravelOmsPublisher(oms_crud_tool)

    def process_data(self, data: Track) -> list[Cotravel]:
        """Run the *cotravel* algorithm on the given track."""
        LOGGER.debug(f"Detecting Cotravels in {data.node_id}")

        cotravels: list[Cotravel] = []
        matches: list[Colocation] = []

        # find matching points (colocations) for each point in the track
        for point in data.points:
            time = point.detection_time

            point_geohash_low = geohash.encode(
                lat=point.coordinates[1], lon=point.coordinates[0], precision=SETTINGS.geohash_low
            )

            db_points: List[Point] = self.get_points(
                point_geohash_low,
                data.node_id,
                (time - MAX_LAG_LEAD_DURATION_SECONDS),
                (time + MAX_LAG_LEAD_DURATION_SECONDS),
                time,
            )

            # Create colocations from track entries
            match_points: List[Colocation] = [
                Colocation(data.node_id, db_point.node_id, point, db_point) for db_point in db_points
            ]

            if matches:
                matches.extend(match_points)
            else:
                matches = match_points

        if not matches:
            return []

        # group points by track2_node_id
        groups = defaultdict(list)
        for entry in matches:
            groups[entry.track2_node_id].append(entry)

        # determine cotravels on each list
        for _, colocations in groups.items():
            sorted_entries = sorted(colocations, key=lambda colocation: colocation.db_point.detection_time)
            cotravels.extend(self.determine_cotravels(data, sorted_entries))

        if cotravels:
            LOGGER.info(f"Found Cotravel(s) ({len(cotravels)}) in {data.node_id}")

        for cotravel in cotravels:
            LOGGER.debug("Cotravel geometry: " + cotravel.geometry.wkt)

        return cotravels

    @classmethod
    def get_points(
        cls, geohash_low: str, track_node_id: uuid.UUID, min_time: datetime, max_time: datetime, target_time: datetime
    ) -> List[Point]:
        """
        Find points in other tracks that match the geohash of the given point within the time intervals.

        This query:

        SELECT DISTINCT ST_GeoHash(points.location) AS "ST_GeoHash_1", points.node_id, points.node_version,
            points.attribute_id, points.attribute_version, ST_AsEWKB(points.location) AS location,
            points.altitude, points.detection_time, points.acm, points.created_at, points.updated_at
        FROM points
        WHERE ST_GeoHash(points.location) LIKE :ST_GeoHash_2
            AND points.node_id != :node_id_1
            AND points.detection_time > :detection_time_1
            AND points.detection_time < :detection_time_2
        ORDER BY points.node_id, abs(EXTRACT(epoch FROM points.detection_time - :detection_time_3))

        :param geohash_low: Geohash to match in the DB
        :param track_node_id: Track node to ignore
        :param min_time: Min allowed time to lag by
        :param max_time: Max allowed time to lag by
        :param target_time: time to sort the response by
        :return: List of cotravels

        """
        with db_session() as db:
            query = db.execute(
                select(Point)
                .filter(Point.location.ST_Geohash().like(f"{geohash_low}%"))
                .where(Point.node_id != track_node_id, Point.detection_time > min_time, Point.detection_time < max_time)
                .order_by(Point.node_id, func.abs(func.extract("epoch", Point.detection_time - target_time)))
                .options(with_expression(Point.geohash, func.ST_GeoHash(Point.location)))
                .distinct(Point.node_id)
            )

            return list(query.scalars().all())

    @staticmethod
    def determine_cotravels(track: Track, colocations: list[Colocation]) -> list[Cotravel]:
        """
        Given the list of colocations, that they meet the time requirements.

        :param colocations: List of colocations
        :return: List of cotravels
        """

        def create_cotravel_from_match(to_add_to: PotentialMatch) -> Cotravel:
            """Helper function to create Cotravel from PotentialMatch"""
            with db_session() as db:
                track2: Track = get_track(db, to_add_to.track2_node_id)

            start_time = min(to_add_to.start_time1, to_add_to.start_time2)
            last_time = max(to_add_to.last_time1, to_add_to.last_time2)

            return Cotravel(
                track1=Track(
                    points=CotravelSensemaker.extract_coordinate_track(track, start_time, last_time),
                    node_id=track.node_id,
                ),
                track2=Track(
                    points=CotravelSensemaker.extract_coordinate_track(track2, start_time, last_time),
                    node_id=track2.node_id,
                ),
                start_time=start_time,
                last_time=last_time,
                true_cotravel=to_add_to.true_cotravel,
            )

        completed: list[Cotravel] = []
        to_add_to: Optional[PotentialMatch] = None

        for colocation in colocations:
            if to_add_to:
                # if we have a potential match already, keep checking
                if (
                    not to_add_to.tentative_add(colocation.point.detection_time, colocation.db_point.detection_time)
                    and to_add_to.check_valid()
                ):
                    # the next colocation point doesn't meet the observation threshold but we still
                    # have a valid cotravel. Add the cotravel to the list and start over with a new
                    # potential match
                    cotravel = create_cotravel_from_match(to_add_to)
                    completed.append(cotravel)
                    true_cotravel = (
                        abs(colocation.point.detection_time - colocation.db_point.detection_time)
                        <= MIN_LAG_LEAD_DURATION_SECONDS
                    )
                    to_add_to = PotentialMatch(
                        colocation.track1_node_id,
                        colocation.track2_node_id,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        true_cotravel,
                    )
            else:
                # if no potential match already exists, create and start checking
                true_cotravel = (
                    abs(colocation.point.detection_time - colocation.db_point.detection_time)
                    <= MIN_LAG_LEAD_DURATION_SECONDS
                )

                to_add_to = PotentialMatch(
                    colocation.track1_node_id,
                    colocation.track2_node_id,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    true_cotravel,
                )

        # check the last point for a valid cotravel
        if to_add_to and to_add_to.check_valid():
            cotravel = create_cotravel_from_match(to_add_to)
            completed.append(cotravel)

        return completed

    # TODO maybe move to utility
    @staticmethod
    def extract_coordinate_track(track: Track, start_time: datetime, end_time: datetime) -> List[Point]:
        """
        Return points within provided time bounds.

        :param track: Track to extract points from
        :param start_time: earliest point timestamp
        :param end_time: latest point timestamp
        :return: List of valid points
        """
        points = []
        for point in track.points:
            if point.detection_time >= start_time and point.detection_time <= end_time:
                points.append(point)
        return points
