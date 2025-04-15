"""Cotravel Sensemakers."""

import enum
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from geoalchemy2.shape import to_shape
from oms_sdk.generated.generated_graphql_client.client import (
    CreateAttributeInput,
    CreateNodeInput,
    CreateRelationshipInput,
)
from oms_sdk.generated.generated_graphql_client.enums import AttributeType, Confidence, ObjectTier
from shapely import LineString, MultiLineString
from sqlalchemy import func, join, select

from oms_sensemaking.clients.instances import aac_client, db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.core.sensemakers import FindingBase, Sensemaker
from oms_sensemaking.models.geo import Point, Track, get_track, track_points_table
from oms_sensemaking.models.sensemaking import FindingType

LOGGER = logging.getLogger(__name__)


class CotravelType(enum.Enum):
    potential_duplicate: str = "potential_duplicate"
    cotravel: str = "cotravel"
    lag_lead: str = "lag_lead"

    @classmethod
    def get_name(cls, cotravel_type: "CotravelType") -> str:
        if cotravel_type == cls.potential_duplicate:
            return SETTINGS.potential_duplicate_relationship_name
        if cotravel_type == cls.cotravel:
            return SETTINGS.cotravel_event_name
        if cotravel_type == cls.lag_lead:
            return SETTINGS.lag_lead_event_name

        raise ValueError("Invalid CotravelType")


@dataclass
class PotentialMatch:
    """Represents a potential co-travel match."""

    vehicle_id1: UUID
    vehicle_id2: UUID
    start_time1: datetime
    start_time2: datetime
    last_time1: datetime
    last_time2: datetime
    track_id1: UUID
    track_id2: UUID
    config: dict
    is_true_cotravel: bool = field(init=False)
    cotravel_type: CotravelType = field(init=False)
    total_time_diff: timedelta = field(default=timedelta(seconds=0), init=False)
    num_points: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Post init for Colocation"""

        diff = abs(self.start_time1 - self.start_time2)
        self.is_true_cotravel = False

        if diff <= timedelta(seconds=self.config["max_potential_duplicate_time_diff_seconds"]):
            self.cotravel_type = CotravelType.potential_duplicate
            self.is_true_cotravel = True
        elif diff <= timedelta(seconds=self.config["max_lag_lead_duration_seconds"]):
            self.cotravel_type = CotravelType.cotravel
            self.is_true_cotravel = True
        else:
            self.cotravel_type = CotravelType.lag_lead

    def tentative_add(self, time1: datetime, time2: datetime) -> bool:
        """
        Check if a new colocation can fit into a cotravel that is being created and adds it if so.

        :param time1:
        :param time2:
        :return: boolean indicating if the PotentialMatch was updated
        """
        valid_observation_threshold = timedelta(seconds=self.config["valid_observed_threshold_seconds"])
        if (
            abs(self.last_time1 - time1) <= valid_observation_threshold
            and abs(self.last_time2 - time2) <= valid_observation_threshold
        ):
            self.last_time1 = time1
            self.last_time2 = time2
            current_time_diff = abs(time1 - time2)

            self.num_points = self.num_points + 1
            self.total_time_diff = self.total_time_diff + current_time_diff
            avg_time_diff = self.total_time_diff.total_seconds() / self.num_points
            is_potential_duplicate = (timedelta(seconds=avg_time_diff) <=
                                      timedelta(seconds=self.config["max_potential_duplicate_time_diff_seconds"]))

            self.is_true_cotravel = (self.is_true_cotravel and
                                     (current_time_diff <=
                                      timedelta(seconds=self.config["min_lag_lead_duration_seconds"])))

            if is_potential_duplicate:
                self.cotravel_type = CotravelType.potential_duplicate
            elif self.is_true_cotravel:
                self.cotravel_type = CotravelType.cotravel
            else:
                self.cotravel_type = CotravelType.lag_lead

            return True

        return False

    def check_valid_cotravel_duration(self) -> bool:
        """Check whether a PotentialMatch has met the duration requirements."""
        min_duration = timedelta(seconds=self.config["min_cotravel_duration_seconds"])
        return (
            self.last_time1 - self.start_time1 >= min_duration
            and self.last_time2 - self.start_time2 >= min_duration
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
    cotravel_type: CotravelType
    geometry: MultiLineString = field(init=False)

    def __post_init__(self) -> None:
        """Post init for Cotravel"""
        ls1 = LineString([point.coordinates for point in self.track1.points])
        ls2 = LineString([point.coordinates for point in self.track2.points])
        self.geometry = MultiLineString([ls1, ls2])

    def __str__(self):
        return str(self.to_dict())

    def get_acm(self) -> dict:
        """Rollup the acm from the points"""
        track1_acms = [point.acm for point in self.track1.points]
        track2_acms = [point.acm for point in self.track2.points]
        return aac_client.get_acm_rollup([{"ACM": acm} for acm in (track1_acms + track2_acms)])

    def to_geojson(self) -> dict:
        """Geojson representation of the cotravel geometry"""

        return {
            "type": "MultiLineString",
            "coordinates": [
                [point.coordinates for point in self.track1.points],
                [point.coordinates for point in self.track2.points],
            ],
        }


@dataclass
class Colocation:
    """For CotravelService use, a Colocation stores the data for two tracks' intersection."""

    track1_node_id: UUID
    track2_node_id: UUID
    track1_id: UUID
    track2_id: UUID
    point: Point
    db_point: Point

    def __str__(self):
        loc1 = to_shape(self.point.location)
        loc2 = to_shape(self.db_point.location)
        return f"Colocation: {loc1} at {self.point.detection_time} and {loc2} at {self.db_point.detection_time}"


class CotravelSensemaker(Sensemaker):
    """
    A sensemaker for analyzing tracks for cotravelers.

    Algorithm ChangeLog
    ===================

    [1.0.0]

    - Added potential duplicate cotravel type to indicate the matched objects might be the same object
    - Initial "co-travel" algorithm implementation.

    """

    def __init__(self, oms_crud_tool: OmsCrudTool) -> None:
        """Create a new instance of CotravelSensemaker."""
        super().__init__()
        self.version = (1, 0, 0)
        self.config = {
            # "valid_observed_threshold_seconds": SETTINGS.valid_observed_threshold_seconds,
            # "min_cotravel_duration_seconds": SETTINGS.min_cotravel_duration_seconds,
            # "min_lag_lead_duration_seconds": SETTINGS.min_lag_lead_duration_seconds,
            # "max_lag_lead_duration_seconds": SETTINGS.max_lag_lead_duration_seconds,
            # "geohash_low": SETTINGS.geohash_low,
            "cotravel_event_node_attribute_iri": SETTINGS.cotravel_event_node_attribute_iri,
            "cotravel_relationship_iri": SETTINGS.cotravel_relationship_iri,
            "cotravel_track_to_event_relation_name": SETTINGS.cotravel_track_to_event_relation_name,
            "cotravel_event_node_iri": SETTINGS.cotravel_event_node_iri,
            "cotravel_event_name": SETTINGS.cotravel_event_name,
            "lag_lead_event_name": SETTINGS.lag_lead_event_name,
            "geo_sensemaker_event_tag": SETTINGS.geo_sensemaker_event_tag,
            # "max_potential_duplicate_time_diff_seconds": SETTINGS.max_potential_duplicate_time_diff_seconds
        }
        self.oms_crud_tool = oms_crud_tool

    def process_data(self, data: Track, config: dict) -> list[Cotravel]:
        """Run the *cotravel* algorithm on the given track.

        :param data: Track to run the sensemaker on
        :param config: Settings for this particular sensemaker run
        :return: List of discovered Cotravels
        """
        LOGGER.debug(f"Detecting Cotravels for {data.node_id}")

        # Update the config with specific geo settings
        # TODO configs will have some extra settings from other geo sensemakers. That okay?
        self.config.update(config)

        cotravels: list[Cotravel] = []
        matches: list[Colocation] = []

        # find matching points (colocations) for each point in the track
        for point in data.points:
            time = point.detection_time

            point_geohash_low = point.geohash[: self.config["geohash_low"]]

            db_points: list[tuple[UUID, Point]] = self.get_points(
                point_geohash_low,
                data.node_id,
                (time - timedelta(seconds=self.config["max_lag_lead_duration_seconds"])),
                (time + timedelta(seconds=self.config["max_lag_lead_duration_seconds"])),
                time,
            )

            # Create colocations from track entries
            match_points: list[Colocation] = [
                Colocation(
                    data.node_id,
                    db_point.node_id,
                    data.track_uuid,  # type: ignore
                    track2_uuid,
                    point,
                    db_point,
                )
                for track2_uuid, db_point in db_points
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
            track_uuid = data.track_uuid
            LOGGER.info(f"Found Cotravel(s) ({len(cotravels)}) in {track_uuid}")

        for cotravel in cotravels:
            LOGGER.debug(f"Cotravel ({cotravel.cotravel_type}) geometry: {cotravel.geometry.wkt}")
            self.publish(data, cotravel)

        return cotravels

    @classmethod
    def get_points(
        cls, geohash_low: str, vehicle_id: uuid.UUID, min_time: datetime, max_time: datetime, target_time: datetime
    ) -> list[tuple[UUID, Point]]:
        """
        Find points in other tracks that match the geohash of the given point within the time intervals.

        This query:

        SELECT DISTINCT ON (points.node_id) ST_GeoHash(points.location) AS "ST_GeoHash_1", points.track_id,
            points.observation_id, points.observation_version, points.node_id, points.node_version, points.source_id,
            ST_AsEWKB(points.location) AS location, points.altitude, points.detection_time, points.acm,
            points.created_at,points.updated_at
        FROM points
        WHERE ST_GeoHash(points.location) LIKE $1::VARCHAR
            AND points.node_id != $2::UUID
            AND points.detection_time > $3::TIMESTAMP WITHOUT TIME ZONE
            AND points.detection_time < $4::TIMESTAMP WITHOUT TIME ZONE
        ORDER BY points.node_id, abs(EXTRACT(epoch FROM points.detection_time - $5::TIMESTAMP WITHOUT TIME ZONE))

        :param geohash_low: Geohash to match in the DB
        :param vehicle_id: Track node to ignore
        :param min_time: Min allowed time to lag by
        :param max_time: Max allowed time to lag by
        :param target_time: time to sort the response by
        :return: List of cotravels

        """
        with db_session() as db:
            query = db.execute(
                select(Track.track_uuid, Point)
                .select_from(
                    join(
                        Point,
                        track_points_table,
                        track_points_table.c.point_id == Point.point_id,
                    ).join(Track, track_points_table.c.track_id == Track.track_id)
                )
                .filter(Point.geohash.like(f"{geohash_low}%"))  # type: ignore [attr-defined]
                .where(Point.node_id != vehicle_id, Point.detection_time > min_time, Point.detection_time < max_time)
                .order_by(Point.node_id, func.abs(func.extract("epoch", Point.detection_time - target_time)))
                .distinct(Point.node_id)
            )

            return list(tuple(row) for row in query.all())


    def determine_cotravels(self, track: Track, colocations: list[Colocation]) -> list[Cotravel]:
        """
        Given the list of colocations, that they meet the time requirements.

        :param colocations: List of colocations
        :return: List of cotravels
        """

        def create_cotravel_from_match(to_add_to: PotentialMatch) -> Cotravel:
            """Helper function to create Cotravel from PotentialMatch"""
            with db_session() as db:
                # db.expire_on_commit = False
                track2_id = to_add_to.track_id2
                track2: Track = get_track(db, track2_id)

                start_time = min(to_add_to.start_time1, to_add_to.start_time2)
                last_time = max(to_add_to.last_time1, to_add_to.last_time2)

            # Preserve original tracks' metadata for possible use in Finding
            return Cotravel(
                track1=Track(
                    points=CotravelSensemaker.extract_coordinate_track(track, start_time, last_time),
                    node_id=track.node_id,
                    algorithm=track.algorithm,
                    observation_ids=track.observation_ids,
                    track_uuid=uuid4(),  # type: ignore
                    acm=track.acm,
                ),
                track2=Track(
                    points=CotravelSensemaker.extract_coordinate_track(track2, start_time, last_time),
                    node_id=track2.node_id,
                    algorithm=track2.algorithm,
                    observation_ids=track2.observation_ids,
                    track_uuid=uuid4(),  # type: ignore
                    acm=track2.acm,
                ),
                start_time=start_time,
                last_time=last_time,
                cotravel_type=to_add_to.cotravel_type,
            )

        completed: list[Cotravel] = []
        to_add_to: PotentialMatch | None = None

        for colocation in colocations:
            if to_add_to:
                # if we have a potential match already, keep checking
                if (
                    not to_add_to.tentative_add(colocation.point.detection_time, colocation.db_point.detection_time)
                    and to_add_to.check_valid_cotravel_duration()
                ):
                    # the next colocation point doesn't meet the observation threshold but we still
                    # have a valid cotravel. Add the cotravel to the list and start over with a new
                    # potential match
                    cotravel = create_cotravel_from_match(to_add_to)
                    completed.append(cotravel)

                    to_add_to = PotentialMatch(
                        colocation.track1_node_id,
                        colocation.track2_node_id,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        colocation.point.detection_time,
                        colocation.db_point.detection_time,
                        colocation.track1_id,
                        colocation.track2_id,
                        self.config
                    )
            else:
                # if no potential match already exists, create and start checking

                to_add_to = PotentialMatch(
                    colocation.track1_node_id,
                    colocation.track2_node_id,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    colocation.point.detection_time,
                    colocation.db_point.detection_time,
                    colocation.track1_id,
                    colocation.track2_id,
                    self.config
                )

        # check the last point for a valid cotravel
        if to_add_to and to_add_to.check_valid_cotravel_duration():
            cotravel = create_cotravel_from_match(to_add_to)
            completed.append(cotravel)

        return completed

    # TODO maybe move to utility
    @staticmethod
    def extract_coordinate_track(track: Track, start_time: datetime, end_time: datetime) -> list[Point]:
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

    def publish(self, track: Track, cotravel: Cotravel) -> None:
        """Publish Potential Duplicate to OMS

        :param track: Original Track
        :param cotravel: Cotravel to publish
        :return: None
        """
        if cotravel.cotravel_type == CotravelType.potential_duplicate:
            self.publish_potential_duplicate(track, cotravel)
        else:
            self.publish_cotravel(track, cotravel)

    def publish_potential_duplicate(self, track: Track, cotravel: Cotravel) -> None:
        """Publish Potential Duplicate to OMS

        :param track: Original Track
        :param cotravel: Cotravel to publish
        :return: None
        """
        source_id = track.points[0].source_id

        # Resolution Relationship
        create_relationship_input = CreateRelationshipInput(
            tags=[SETTINGS.geo_sensemaker_event_tag],
            name=SETTINGS.resolution_relationship_name, # TODO deconflict with potential_duplicate_relationship_name
            startNodeId=cotravel.track1.node_id,
            endNodeId=cotravel.track2.node_id,
            confidence=Confidence.HIGH,
            acm=cotravel.get_acm(),
            objectPropertyIri=SETTINGS.resolution_relationship_iri,
            sourceId=source_id,
        )
        self.oms_crud_tool.publish_relationships([create_relationship_input])

    def publish_cotravel(self, track: Track, cotravel: Cotravel) -> None:
        """Publish Cotravel Events to OMS

        :param track: Original Track
        :param cotravel: Cotravel to publish
        :return: None
        """
        name = f"{CotravelType.get_name(cotravel.cotravel_type)}"
        source_id = track.points[0].source_id  # TODO thinking this similarly should be multiple sources
        tags = [SETTINGS.geo_sensemaker_event_tag]

        create_node_input = CreateNodeInput(
            acm=cotravel.get_acm(),
            name=name,
            tier=ObjectTier.DERIVATIVE,
            tags=[SETTINGS.geo_sensemaker_event_tag],
            classIri=SETTINGS.cotravel_event_node_iri,
            ifcCodes=set(),
            isNso=True,
        )
        published_node = self.oms_crud_tool.create_node(node_input=create_node_input)

        # vehicle 1 relationship
        create_relationship_input1 = CreateRelationshipInput(
            tags=tags,
            name=f"{name} {SETTINGS.cotravel_track_to_event_relation_name}",
            startNodeId=published_node.id,
            endNodeId=cotravel.track1.node_id,
            confidence=Confidence.HIGH,
            acm=cotravel.get_acm(),
            objectPropertyIri=SETTINGS.cotravel_relationship_iri,
            sourceId=source_id,
        )
        # vehicle 2 relationship
        create_relationship_input2 = CreateRelationshipInput(
            tags=tags,
            name=f"{name} {SETTINGS.cotravel_track_to_event_relation_name}",
            startNodeId=published_node.id,
            endNodeId=cotravel.track2.node_id,
            confidence=Confidence.HIGH,
            acm=cotravel.get_acm(),
            objectPropertyIri=SETTINGS.cotravel_relationship_iri,
            sourceId=source_id,
        )
        self.oms_crud_tool.publish_relationships([create_relationship_input1, create_relationship_input2])

        # attribute for geometry
        created_attribute_input = CreateAttributeInput(
            attributeIri=SETTINGS.cotravel_event_node_attribute_iri,
            attributeValue="geo",
            attributeDisplayValue="",
            attributeType=AttributeType.GEOSPATIAL,
            confidence=Confidence.HIGH,
            tags=[SETTINGS.geo_sensemaker_event_tag],
            sourceId=source_id,
            geometry=cotravel.to_geojson(),
            nodeId=published_node.id,
            acm=cotravel.get_acm(),
            valueStart=cotravel.start_time,
            valueEnd=cotravel.last_time,
        )
        self.oms_crud_tool.publish_attributes([created_attribute_input])
