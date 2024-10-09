"""Geospatial sensemaker controller."""

import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Timer
from time import sleep
from typing import Optional
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from dateutil.parser import isoparse
from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.attribute import AttributeAttribute
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.enums import Action, AttributeType
from oms_sdk.generated.generated_graphql_client.input_types import IdQuery, RelationshipNodeQuery, RelationshipQuery
from oms_sdk.generated.generated_graphql_client.node import NodeNode
from sqlalchemy import select

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    EVENT_HANDLER,
    ObjectEvent,
    ObjectEventConsumer,
    ObjectType,
    SQSListener,
)
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.models.geo import Point, Track, get_track

LOGGER: logging.Logger = logging.getLogger(__name__)


class CSVFileParser(ObjectEventConsumer):
    """An ObjectEventConsumer based on a file as the data source."""

    def __init__(
            self,
            filename: str,
            default_acm: dict,
            default_user_dn: str,
            handle_event: Optional[EVENT_HANDLER] = None):
        """
        Create a new instance of CSVFileParser.

        :param filename: The CSV file to process.
        :param default_acm: The ACM to apply to all records in the CSV file.
        :param default_user_dn: The user DN to apply to all records in the CSV file.
        :param handle_event: A callback that will receive the processed tracks.
        """
        super().__init__(handle_event)
        self.filename: str = filename
        self.default_acm: dict = default_acm
        self.default_user_dn: str = default_user_dn

    def process_object_events(self) -> None:
        """Process a file into ObjectEvents."""
        input_file: Path = Path(self.filename)
        node_ids: dict[str, UUID] = {}

        if not callable(self.handle_event):
            raise ValueError(f"handle_event must be a callable object, got {type(self.handle_event)}")

        if not input_file.is_file():
            raise ValueError("%s does not exist", input_file)

        # 1. Initialize data source
        LOGGER.info("File consumer: %s", self.filename)
        with input_file.open("r", encoding="utf-8") as csv_file:
            reader: csv.DictReader = csv.DictReader(csv_file)

            with db_session() as db:
                for row in reader:
                    # , r, lat, lon, now, timestamp
                    try:
                        node_id: UUID = UUID(row["r"])
                    except ValueError:
                        node_id = node_ids.setdefault(row["r"], uuid4())

                    # 2. convert data from data source into a point in the db
                    #  - this is mimicking extracting the data from OMS and persisting the results
                    point, is_new = Point.get_or_create(db, defaults=dict(
                        acm=self.default_acm,
                        location=f"POINT({row['lon']} {row['lat']})",
                        altitude=None,
                        detection_time=datetime.fromtimestamp(float(row["now"]), tz=timezone.utc),
                        node_version=1,
                        attribute_version=1
                    ), node_id=node_id, attribute_id=uuid4(), source_id=uuid4())

                    db.add(point)
                    db.commit()
                    db.refresh(point)

                    success: bool = self.handle_event(
                        ObjectEvent(
                            self.default_user_dn,
                            point.attribute_id,
                            ObjectType.ATTRIBUTE,
                            Action.CREATE if is_new else Action.UPDATE
                        )
                    )

                    if success:
                        LOGGER.info("File-based attribute event [index=%s] was successfully processed.", row[""])
                    else:
                        LOGGER.warning("File-based attribute event [index=%s] was no processed.", row[""])


class GeoSQSListener(SQSListener):
    """An SQS ObjectEventConsumer that consumes geo-temporal OMS events."""

    def __init__(self, handle_event: Optional[EVENT_HANDLER] = None):
        """Create a new instance of GeoSqsObjectEventConsumer."""
        super().__init__(handle_event)

    def process_object_events(self) -> None:
        """Process geo-temporal object events from OMS."""
        if not callable(self.handle_event):
            raise ValueError(f"handle_event must be a callable object, got {type(self.handle_event)}")

        while not self.stopped.is_set():
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                if self.stopped.is_set():
                    LOGGER.debug("Shutting down GeoSQSListener")
                    break

                # Receive message from SQS queue
                try:
                    LOGGER.debug("Listening to %s", SETTINGS.sqs_queue_url)
                    response = self.sqs.receive_message(
                        QueueUrl=SETTINGS.sqs_queue_url,
                        AttributeNames=["SentTimestamp"],
                        MaxNumberOfMessages=10,
                        MessageAttributeNames=["All"],
                        VisibilityTimeout=0,
                        WaitTimeSeconds=0,
                    )
                except (BotoCoreError, self.sqs.exceptions.QueueDoesNotExist) as ex:
                    LOGGER.error(f"Unable to connect to SQS: {ex}. Trying again...")
                    break

                if "Messages" not in response:
                    LOGGER.debug("No Messages in response.")
                    sleep(SETTINGS.sqs_read_wait_seconds)
                    continue

                for message in response["Messages"]:
                    object_event: ObjectEvent = ObjectEvent.from_json((message["Body"]))

                    # ignore if not the right type of event
                    if ((object_event.objectType != ObjectType.ATTRIBUTE.value)
                            and (object_event.eventType != Action.CREATE.value)):
                        continue

                    if self.handle_event(object_event):
                        # Delete received message from queue - required, so you don't get the same message
                        self.sqs.delete_message(
                            QueueUrl=SETTINGS.sqs_queue_url,
                            ReceiptHandle=message["ReceiptHandle"]
                        )
                    else:
                        LOGGER.warning("object event was not processed successfully.")


class GeospatialSensemakerController(SensemakerController):
    """
    Geospatial sensemaker controller.

    This class manages a collection of geospatial sensemakers.
    """

    def __init__(self, event_consumer: ObjectEventConsumer, output_to_oms: bool = True) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer)

        # initialize buffer
        self.buffer: dict[UUID, Optional[datetime]] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)

        #: OMS GraphQL client
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )
        self.output_to_oms = output_to_oms

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.detect_cotravels:
            self.register("cotravel", CotravelSensemaker())

        if SETTINGS.detect_loiters:
            self.register("loiter", LoiterSensemaker(self.oms_client, self.output_to_oms))

        if SETTINGS.similar_tracks:
            self.register("similar_tracks", SimilarTracksSensemaker())

        self.autoflush_enabled.set()
        self.buffer_autoflush.start()
        super().start()

    def stop(self):
        """
        Stop the controller.

        This method handles stopping the buffer autoflush in addition to
        stopping the controller itself.
        """
        LOGGER.debug("Stopping track buffer autoflush.")
        self.autoflush_enabled.clear()

        if self.buffer_autoflush.is_alive():
            self.buffer_autoflush.cancel()
            self.buffer_autoflush.join()

        super().stop()

    def handle_event(self, event: ObjectEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        """
        now: datetime = datetime.now(tz=timezone.utc)
        point: Optional[Point] = None

        LOGGER.debug("Received ObjectEvent(objectId=%s)", event.objectId)

        if isinstance(self.event_consumer, CSVFileParser):
            # TODO: revisit this. Should the point be persisted here?
            with db_session() as db:
                point = db.execute(
                    select(Point).where(Point.attribute_id == event.objectId)
                ).scalars().one_or_none()
            pass
        elif isinstance(self.event_consumer, GeoSQSListener):
            # extract info from OMS via API calls
            oms_attr: Optional[AttributeAttribute] = self.get_oms_attribute(event.objectId)

            # we expect an observation node and a track node. If these don't exist, we can ignore the point.
            if not oms_attr:
                return True

            track_node: Optional[NodeNode] = self.get_track_node(oms_attr)
            if not track_node:
                return True

            with db_session() as db:
                # we're still using the point object for detections, so don't expire it
                db.expire_on_commit = False
                point, is_new = Point.get_or_create(db, defaults=dict(
                    acm=oms_attr.acm,
                    location=(f'Point({oms_attr.geo.geoJson["coordinates"][0]} '
                                f'{oms_attr.geo.geoJson["coordinates"][1]})'),
                    altitude=None,  # TODO include this
                    detection_time=isoparse(oms_attr.geo.startTime).replace(tzinfo=timezone.utc),
                    node_version=int(oms_attr.node.version),
                    attribute_version=int(oms_attr.version)
                ), node_id=track_node.id, attribute_id=oms_attr.id, source_id=oms_attr.sourceId)

            if not is_new:
                if point:
                    LOGGER.debug("Processing existing point: attribute_id=%s", point.attribute_id)
                else:
                    LOGGER.warning("Unable to process point.")

        if point:
            with self.lock:
                self.buffer[point.node_id] = now

            return True

        return False

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.debug("Checking buffer expirations")
        now: datetime = datetime.now(tz=timezone.utc)

        with self.lock:
            # purge stale keys
            self.buffer = {key: val for key, val in self.buffer.items() if val is not None}

            for node_id, last_updated_at in self.buffer.items():
                if last_updated_at is None:
                    LOGGER.warning("Skipping Node(id=%s)", node_id)
                    continue

                LOGGER.debug("Checking buffer for %s", node_id)
                if last_updated_at + timedelta(seconds=SETTINGS.cache_entry_expire_sec) < now:
                    LOGGER.debug("node_id=%s is expired, processing from buffer.", node_id)
                    with db_session() as db:
                        try:
                            track: Track = get_track(db, node_id)
                        except ValueError as e:
                            # Track doesn't have enough points. Ignore and remove from buffer until it gets more points
                            LOGGER.warn(e)
                            self.buffer[node_id] = None
                            continue
                        LOGGER.debug(track.to_linestring())

                    try:
                        with ThreadPoolExecutor() as executor:
                            futures = []
                            for sensemaker in self._registry.values():
                                future = executor.submit(sensemaker.execute, track)
                                futures.append(future)

                            # make sure errors are caught
                            for future in as_completed(futures):
                                _ = future.result()

                            executor.shutdown(wait=True)
                    except Exception:
                        LOGGER.exception("Error encountered while processing %s from buffer", node_id)
                    finally:
                        self.buffer[node_id] = None  # mark for removal
                else:
                    LOGGER.debug("node_id %s is still active in the buffer", node_id)

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()

    def get_oms_attribute(self, attribute_id: UUID) -> Optional[AttributeAttribute]:
        """
        Given an OMS Attribute ID, get the OMS Attribute.

        :param attribute_id: ID of the attribute
        :return: None if no attribute exists, or the OMS Attribute
        """
        # get attribute
        oms_attr: AttributeAttribute = self.oms_client.attribute(IdQuery(id=attribute_id))

        # Filter Attributes
        # Only process if there is a node ID
        if not oms_attr or oms_attr.nodeId is None:
            return None

        if oms_attr.attributeType != AttributeType.SPATIOTEMPORAL.value:
            return None

        if oms_attr.geo.geoJson["type"].lower() != "point":
            return None

        return oms_attr

    def get_track_node(self, oms_attr: AttributeAttribute) -> Optional[NodeNode]:
        """
        Given an OMS Observation Geo Attribute, get the associated Flight Activity Node - AKA Track Node ID.

        :param oms_attr: Attribute object
        :return: None if no relationship exists, or the Track Node id
        """
        # get relationship
        observation_node_id = oms_attr.nodeId
        rel = self.oms_client.relationships(
            query=RelationshipQuery(
                nodes=RelationshipNodeQuery(endNodeIds=[observation_node_id]),
                objectPropertyIris=[SETTINGS.operated_by_iri],
            )
        )

        if not len(rel.data) > 0:
            return None

        # ADSB Flight Activity Node. AKA Track Node ID
        track_node_id = rel.data[0].startNodeId

        node = self.oms_client.node(query=IdQuery(id=track_node_id))

        if not node:
            return None

        return node
