"""Geospatial sensemaker controller."""

import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Timer
from typing import Optional
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from sqlalchemy import select

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import (
    EVENT_HANDLER,
    EventType,
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
                        node_id: UUID = node_ids.setdefault(row["r"], uuid4())

                    # 2. convert data from data source into a point in the db
                    #  - this is mimicking extracting the data from OMS and persisting the results
                    point, is_new = Point.get_or_create(db, defaults=dict(
                        acm=self.default_acm,
                        location=f"POINT({row['lon']} {row['lat']})",
                        altitude=None,
                        detection_time=datetime.fromtimestamp(float(row["now"]), tz=timezone.utc),
                        node_version=1,
                        attribute_version=1
                    ), node_id=node_id, attribute_id=uuid4())

                    db.add(point)
                    db.commit()
                    db.refresh(point)

                    success: bool = self.handle_event(
                        ObjectEvent(
                            self.default_user_dn,
                            point.attribute_id,
                            ObjectType.ATTRIBUTE,
                            EventType.CREATE if is_new else EventType.UPDATE
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
        while True:
            LOGGER.info("Waiting for events in SQS")

            for _ in range(0, SETTINGS.sqs_read_loops):
                # Receive message from SQS queue
                try:
                    response = self.sqs.receive_message(
                        QueueUrl=SETTINGS.sqs_queue_url,
                        AttributeNames=["SentTimestamp"],
                        MaxNumberOfMessages=10,
                        MessageAttributeNames=["All"],
                        VisibilityTimeout=0,
                        WaitTimeSeconds=0,
                    )
                except BotoCoreError as e:
                    LOGGER.error(f"Unable to connect to SQS: {e}. Trying again...")
                    break

                if "Messages" not in response:
                    LOGGER.debug("No Messages in response.")
                    continue

                for message in response["Messages"]:
                    object_event: dict = json.loads(message["Body"])  # TODO: convert to ObjectEvent

                    # TODO: convert dict to ObjectEvent
                    if self.handle_event(object_event):
                        # Delete received message from queue - required so you don't get the same message
                        self.sqs.delete_message(
                            QueueUrl=SETTINGS.sqs_queue_url,
                            ReceiptHandle=message["ReceiptHandle"]
                        )
                    else:
                        # TODO: deal with failed object events
                        LOGGER.warning("object event was not processed successfully.")

            # TODO: sleep?
            # await asyncio.sleep(SETTINGS.sqs_read_wait_seconds)


class GeospatialSensemakerController(SensemakerController):
    """
    Geospatial sensemaker controller.

    This class manages a collection of geospatial sensemakers.
    """

    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer)

        # initialize buffer
        self.buffer: dict[UUID, Optional[datetime]] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.detect_cotravels:
            self.register("cotravel", CotravelSensemaker())

        if SETTINGS.detect_loiters:
            self.register("loiter", LoiterSensemaker())

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

        if isinstance(self.event_consumer, CSVFileParser):
            with db_session() as db:
                point: Point = db.execute(
                    select(Point).where(Point.attribute_id == event.object_id)
                ).scalars().one_or_none()
            pass
        elif isinstance(self.event_consumer, GeoSQSListener):
            # TODO: extract info from OMS via API calls
            # TODO: convert OMS data to Point and persist in db
            # point = Point.get_or_create(...)
            pass
        else:
            return False

        if point:
            # this is the buffer/cache
            with self.lock:
                self.buffer[point.node_id] = now

        LOGGER.warning("GEO %s", event.object_id)
        return True

    def flush_buffer(self):
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.debug("Checking buffer expirations")
        now: datetime = datetime.now(tz=timezone.utc)

        with self.lock:
            # purge stale keys
            self.buffer = {key: val for key, val in self.buffer.items() if val is not None}

            for node_id, last_updated_at in self.buffer.items():
                LOGGER.debug("Checking buffer for %s", node_id)
                if last_updated_at + timedelta(seconds=SETTINGS.cache_entry_expire_sec) < now:
                    LOGGER.debug("node_id=%s is expired, processing from buffer.", node_id)
                    with db_session() as db:
                        track: Track = get_track(db, node_id)
                        LOGGER.debug(track.to_linestring())

                    try:
                        with ThreadPoolExecutor() as executor:
                            for sensemaker in self._registry.values():
                                executor.submit(sensemaker.execute, track)

                            executor.shutdown(wait=True)
                    except Exception:
                        LOGGER.exception("Error encountered while processing %s from buffer", node_id)
                    finally:
                        self.buffer[node_id] = None  # mark for removal
                else:
                    LOGGER.debug("node_id%s is still active in the buffer", node_id)

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()
