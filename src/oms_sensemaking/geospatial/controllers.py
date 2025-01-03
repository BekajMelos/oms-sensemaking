"""Geospatial sensemaker controller."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Event, Timer
from time import sleep
from typing import Optional
from uuid import UUID, uuid4

from botocore.exceptions import BotoCoreError
from dateutil.parser import isoparse
from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.enums import Action
from oms_sdk.generated.generated_graphql_client.input_types import IdQuery
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

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
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.models.geo import Point, Track, get_track

LOGGER: logging.Logger = logging.getLogger(__name__)


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
                    if ((object_event.objectType != ObjectType.OBSERVATION.value)
                            and (object_event.eventType != Action.CREATE.value)):
                        continue

                    LOGGER.info(f"Received Observation: {object_event.objectId}")

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

    def __init__(self, event_consumer: ObjectEventConsumer) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer)

        # initialize buffer
        self.buffer: dict[UUID, Optional[datetime]] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
        self.node_track_mapping: dict[UUID, UUID] = {}

        #: OMS GraphQL client
        self.oms_client: Client = get_generated_graphql_client(
            SETTINGS.omsb_url, SETTINGS.user_dn, SETTINGS.cert_path, SETTINGS.key_path
        )
        self.oms_crud_tool = OmsCrudTool()

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.detect_cotravels:
            self.register("cotravel", CotravelSensemaker(self.oms_crud_tool))

        if SETTINGS.detect_loiters:
            self.register("loiter", LoiterSensemaker(self.oms_crud_tool))

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

        if isinstance(self.event_consumer, GeoSQSListener):
            # extract info from OMS via API calls
            oms_obs: Optional[ObservationObservation] = self.get_oms_observation(event.objectId)

            # we expect an observation. If one doesn't exist, we can ignore the point.
            if not oms_obs:
                return True

            # if the vehicle node_id doesn't have a track linked to it, this is the first obs we received for it
            # we need to create a track_id for it so we can add future points for that vehicle/track
            if oms_obs.nodeId not in self.node_track_mapping:
                self.node_track_mapping[oms_obs.nodeId] = uuid4()
            # set the current track_id to the track linked to the node (vehicle) in question
            track_id = self.node_track_mapping[oms_obs.nodeId]

            with db_session() as db:
                # we're still using the point object for detections, so don't expire it
                db.expire_on_commit = False
                # create a point in the oms_sensemaking db, including the vehicle node_id and the track_id
                point, is_new = Point.get_or_create(db, defaults=dict(
                    acm=oms_obs.acm,
                    location=(f'Point({oms_obs.geometry["coordinates"][0]} '
                                f'{oms_obs.geometry["coordinates"][1]})'),
                    altitude=None,  # TODO include this
                    detection_time=isoparse(oms_obs.startTime).replace(tzinfo=timezone.utc),
                    node_version=int(oms_obs.node.version),
                    observation_version=int(oms_obs.version)
                ), node_id=oms_obs.nodeId, observation_id=oms_obs.id, source_id=oms_obs.sourceId, track_id=track_id)

            if not is_new:
                if point:
                    LOGGER.debug("Processing existing point: observation_id=%s", point.observation_id)
                else:
                    LOGGER.warning("Unable to process point.")
        else:
            LOGGER.warning("No ObjectEventConsumer found.")

        if point:
            with self.lock:
                # we just received the point, so set the point's track_id time to now in the buffer
                self.buffer[track_id] = now

            return True

        return False

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.info("Checking Track Buffer Expirations")
        now: datetime = datetime.now(tz=timezone.utc)

        with self.lock:
            # purge stale keys
            self.buffer = {key: val for key, val in self.buffer.items() if val is not None}

            for track_id, last_updated_at in self.buffer.items():
                if last_updated_at is None:
                    LOGGER.warning("Skipping Track(id=%s)", track_id)
                    continue

                LOGGER.debug("Checking buffer for %s", track_id)
                if last_updated_at + timedelta(seconds=SETTINGS.cache_entry_expire_sec) < now:
                    LOGGER.debug("track_id=%s is expired, processing from buffer.", track_id)
                    with db_session() as db:
                        try:
                            LOGGER.info(f"Track completed: {track_id}")
                            track: Track = get_track(db, track_id)
                        except ValueError as e:
                            # Track doesn't have enough points. Ignore and remove from buffer until it gets more points
                            LOGGER.warn(e)
                            self.buffer[track_id] = None
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
                        LOGGER.exception("Error encountered while processing %s from buffer", track_id)
                    finally:
                        self.buffer[track_id] = None  # mark for removal
                        for key, value in list(self.node_track_mapping.items()):
                            if value == track_id:
                                del self.node_track_mapping[key]
                else:
                    LOGGER.debug("track_id %s is still active in the buffer", track_id)

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()

    def get_oms_observation(self, observation_id: UUID) -> Optional[ObservationObservation]:
        """
        Given an OMS Observation ID, get the OMS Observation.

        :param observation_id: ID of the observation
        :return: None if no observation exists, or the OMS Observation
        """
        # get observation
        oms_obs: ObservationObservation = self.oms_client.observation(IdQuery(id=observation_id))

        # Filter observations
        # Only process if there is a nodeId
        if not oms_obs:
            return None

        # TODO: check this is right?
        can_handle_geometry = oms_obs.geometry["type"].lower() != "point"
        if can_handle_geometry:
            return None

        return oms_obs
