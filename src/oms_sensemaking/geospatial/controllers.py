"""Geospatial sensemaker controller."""

import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from operator import attrgetter
from threading import Event, Timer
from uuid import UUID, uuid4

from dateutil.parser import isoparse
from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer, EventFilter
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.models.geo import (
    Point,
    TimeBinTrackWeaver,
    Track,
    TrackWeaverBase,
    apply_common_sense_filters,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class GeospatialSensemakerController(SensemakerController):
    """
    Geospatial sensemaker controller.

    This class manages a collection of geospatial sensemakers.
    """

    def __init__(self, event_consumer: AuditLogEventConsumer) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer)

        # initialize buffer
        self.track_times: dict[UUID, datetime | None] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
        self.node_track_mapping: dict[UUID, UUID] = defaultdict(uuid4)
        self.track_node_buffer: dict[UUID, list[Point]] = defaultdict(list)

        # track weaver to call on completed Tracks before publishing
        self.track_weaver: TrackWeaverBase = TimeBinTrackWeaver()
        self.confidence_weight_map = SETTINGS.confidence_weight_map

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

    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        :return: True if the audit log event was successfully processed, False otherwise.
        """
        now: datetime = datetime.now(tz=timezone.utc)
        point: Point | None = None

        LOGGER.debug(f"Received AuditLogEvent(objectId={event.objectId})")

        # extract info from OMS via API calls
        oms_obs: ObservationObservation | None = self.get_oms_observation(event.objectId)

        # we expect an observation. If one doesn't exist, we can ignore the point.
        if not oms_obs:
            return True

        # if the vehicle node_id doesn't have a track linked to it, this is the first obs we received for it
        # we need to create a track_id for it so we can add future points for that vehicle/track
        if oms_obs.nodeId not in self.node_track_mapping:
            self.node_track_mapping[oms_obs.nodeId] = uuid4()
        # set the current track_id to the track linked to the node (vehicle) in question
        track_uuid = self.node_track_mapping[oms_obs.nodeId]

        try:
            node = self.oms_crud_tool.get_node(oms_obs.nodeId)
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
                    altitude=None,
                    # The below line can cause Shapely methods to fail if only some points have a Z coordinate.
                    #   Mismatched coordinate array lengths (2 vs 3) will break the LineString and MultiLineString
                    #   methods used by sensemakers to output results. This must be dealt with before we can handle
                    #   unreliable altitudes in OMS observations.
                    # altitude=oms_obs.geometry["coordinates"][2] if oms_obs.geometry["coordinates"][2:] else None,
                    detection_time=isoparse(oms_obs.startTime).replace(tzinfo=timezone.utc),
                    node_version=int(node_version),
                    observation_version=int(oms_obs.version),
                ),
                node_id=oms_obs.nodeId if type(oms_obs.nodeId) is UUID else UUID(oms_obs.nodeId),
                observation_id=oms_obs.id if type(oms_obs.id) is UUID else UUID(oms_obs.id),
                observation_confidence=oms_obs.confidence,
                source_id=oms_obs.sourceId if type(oms_obs.sourceId) is UUID else UUID(oms_obs.sourceId),
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
                self.track_times[track_uuid] = now
                self.track_node_buffer[track_uuid].append(point)
            return True
        return False

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.info("Checking Track Buffer Expirations")
        now: datetime = datetime.now(tz=timezone.utc)

        with self.lock:
            # purge stale keys
            self.track_times = {key: val for key, val in self.track_times.items() if val is not None}

            for track_uuid, last_updated_at in self.track_times.items():
                if last_updated_at is None:
                    LOGGER.warning("Skipping Track(track_uuid=%s)", track_uuid)
                    continue

                LOGGER.debug("Checking buffer for %s", track_uuid)
                if last_updated_at + timedelta(seconds=SETTINGS.cache_entry_expire_sec) < now:
                    LOGGER.debug("track_uuid=%s is expired, processing from buffer.", track_uuid)
                    with db_session() as db:
                        try:
                            points = self.track_node_buffer[track_uuid]
                            points.sort(key=attrgetter("detection_time"))
                            if SETTINGS.apply_common_sense_filters:
                                # Get the IRI for the node
                                iri = self.oms_crud_tool.get_node(points[0].node_id).classIri
                                points = apply_common_sense_filters(points, iri)
                            # Execute a track weaver on the buffered Points and save the new Track with the chosen UUID
                            weaved_track = self.track_weaver.execute(points)
                            track_dict = {
                                "points": weaved_track.points,
                                "node_id": weaved_track.node_id,
                                "algorithm": weaved_track.algorithm,
                                "observation_ids": weaved_track.observation_ids,
                            }
                            track, _ = Track.get_or_create(session=db, defaults=track_dict, track_uuid=track_uuid)
                            LOGGER.info(f"Track completed: {track_uuid}")
                        except ValueError as e:
                            # Track doesn't have enough points. Ignore and remove from buffer until it gets more points
                            LOGGER.warning(e)
                            self.track_times[track_uuid] = None
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
                    except Exception:
                        LOGGER.exception("Error encountered while processing %s from buffer", track_uuid)
                    finally:
                        self.track_times[track_uuid] = None  # mark for removal
                        for key, value in list(self.node_track_mapping.items()):
                            if value == track_uuid:
                                del self.node_track_mapping[key]
                else:
                    LOGGER.debug("track_uuid %s is still active in the buffer", track_uuid)

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()

    def get_oms_observation(self, observation_id: UUID) -> ObservationObservation | None:
        """
        Given an OMS Observation ID, get the OMS Observation.

        :param observation_id: ID of the observation
        :return: None if no observation exists, or the OMS Observation
        """
        # get observation
        oms_obs: ObservationObservation = self.oms_crud_tool.get_observation(observation_id)

        # Filter observations
        # Only process if there is an observation and it has a geojson point
        if not oms_obs:
            return None

        can_handle_geometry = oms_obs.geometry["type"].lower() != "point"
        if can_handle_geometry:
            return None

        return oms_obs


class GeoQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        handled_object_types = [ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value]
        return audit_event.objectType in handled_object_types and audit_event.action in handled_event_types
