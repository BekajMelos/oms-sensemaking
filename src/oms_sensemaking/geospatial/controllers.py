"""Geospatial sensemaker controller."""

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Event, Timer
from typing import Optional
from uuid import UUID, uuid4

from dateutil.parser import isoparse
from oms_sdk import get_generated_graphql_client
from oms_sdk.generated.generated_graphql_client.client import Client
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from oms_sdk.generated.generated_graphql_client.input_types import IdQuery
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

from oms_sensemaking.clients import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import EventFilter, ObjectEvent, ObjectEventConsumer, SQSListener
from oms_sensemaking.core.oms_crud import OmsCrudTool
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.models.geo import Point, TimeBinTrackWeaver, Track, TrackWeaverBase

LOGGER: logging.Logger = logging.getLogger(__name__)


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
        self.node_track_mapping: dict[UUID, UUID] = defaultdict(uuid4)
        self.track_node_buffer: dict[UUID, list[Point]] = defaultdict(list)

        # track weaver to call on completed Tracks before publishing
        self.track_weaver: TrackWeaverBase = TimeBinTrackWeaver()
        self.confidence_weight_map = SETTINGS.confidence_weight_map

        # OMS GraphQL client
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
        :return: True if the object event was successfully processed, False otherwise.
        """
        now: datetime = datetime.now(tz=timezone.utc)
        point: Optional[Point] = None

        LOGGER.debug("Received ObjectEvent(objectId=%s)", event.objectId)

        if not isinstance(self.event_consumer, SQSListener):
            LOGGER.warning("No ObjectEventConsumer found.")
            return False

        # extract info from OMS via API calls
        oms_obs: Optional[ObservationObservation] = self.get_oms_observation(event.objectId)

        # we expect an observation. If one doesn't exist, we can ignore the point.
        if not oms_obs:
            return True

        # set the current track_uuid to the track linked to the node (vehicle) in question or a new track_uuid
        track_uuid = self.node_track_mapping[oms_obs.nodeId]

        try:
            node = self.oms_client.node(query=IdQuery(id=oms_obs.nodeId))
            node_version = node.version
        except AttributeError:
            LOGGER.warning("No node found. Unable to process observation.")
            return False

        with db_session() as db:
            # we're still using the point object for detections, so don't expire it
            db.expire_on_commit = False
            # create a point in the oms_sensemaking db, including the vehicle node_id
            point, is_new = Point.get_or_create(
                db,
                defaults=dict(
                    acm=oms_obs.acm,
                    location=(f'Point({oms_obs.geometry["coordinates"][0]} ' f'{oms_obs.geometry["coordinates"][1]})'),
                    altitude=None,  # TODO include this
                    detection_time=isoparse(oms_obs.startTime).replace(tzinfo=timezone.utc),
                    node_version=int(node_version),
                    observation_version=int(oms_obs.version),
                ),
                node_id=oms_obs.nodeId,
                observation_id=oms_obs.id,
                observation_confidence=oms_obs.confidence,
                source_id=oms_obs.sourceId,
                # TODO: Multiply by source weight if available
                weight=self.confidence_weight_map[oms_obs.confidence],
            )

        if not is_new:
            if point:
                LOGGER.debug("Processing existing point: observation_id=%s", point.observation_id)
            else:
                LOGGER.warning("Unable to process point.")
        if point:
            with self.lock:
                # we just received the point, so set the track_id time to now in the buffer
                self.buffer[track_uuid] = now
                self.track_node_buffer[track_uuid].append(point)
            return True

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.info("Checking Track Buffer Expirations")
        now: datetime = datetime.now(tz=timezone.utc)

        with self.lock:
            # purge stale keys
            self.buffer = {key: val for key, val in self.buffer.items() if val is not None}

            for track_uuid, last_updated_at in self.buffer.items():
                if last_updated_at is None:
                    LOGGER.warning("Skipping Track(track_uuid=%s)", track_uuid)
                    continue

                LOGGER.debug("Checking buffer for %s", track_uuid)
                if last_updated_at + timedelta(seconds=SETTINGS.cache_entry_expire_sec) < now:
                    LOGGER.debug("track_uuid=%s is expired, processing from buffer.", track_uuid)
                    with db_session() as db:
                        try:
                            LOGGER.info(f"Track completed: {track_uuid}")
                            # Execute a track weaver on the buffered Points and save the new Track with the chosen UUID
                            weaved_track = self.track_weaver.execute(self.track_node_buffer[track_uuid])
                            track_dict = {
                                "points": weaved_track.points,
                                "node_id": weaved_track.node_id,
                                "algorithm": weaved_track.algorithm,
                                "observation_ids": weaved_track.observation_ids,
                            }
                            track, _ = Track.get_or_create(session=db, defaults=track_dict, track_uuid=track_uuid)
                            LOGGER.debug(track.to_linestring())
                        except ValueError as e:
                            # Track doesn't have enough points. Ignore and remove from buffer until it gets more points
                            LOGGER.warning(e)
                            self.buffer[track_uuid] = None
                            continue

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
                        LOGGER.exception("Error encountered while processing %s from buffer", track_uuid)
                    finally:
                        self.buffer[track_uuid] = None  # mark for removal
                        for key, value in list(self.node_track_mapping.items()):
                            if value == track_uuid:
                                del self.node_track_mapping[key]
                else:
                    LOGGER.debug("track_uuid %s is still active in the buffer", track_uuid)

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
        # Only process if there is an observation and it has a geojson point
        if not oms_obs:
            return None

        can_handle_geometry = oms_obs.geometry["type"].lower() != "point"
        if can_handle_geometry:
            return None

        return oms_obs


class GeoQueueFilter(EventFilter):
    def passes_filter(self, object_event: ObjectEvent):
        return object_event.objectType == ObjectType.OBSERVATION.value and object_event.eventType == Action.CREATE.value
