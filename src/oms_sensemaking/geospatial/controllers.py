"""Geospatial sensemaker controller."""

import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Event, Lock, Timer
from typing import Callable
from uuid import UUID, uuid4

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import BaseErrorLogger
from oms_sensemaking.core.events import AuditLogEvent, AuditLogEventConsumer, EventFilter
from oms_sensemaking.core.exceptions import TrackLengthError
from oms_sensemaking.geospatial.schemas import GeospatialSensemakerConfig
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.geospatial.track_generator import TrackGenerator
from oms_sensemaking.geospatial.track_weaver_factory import TrackWeaverFactory
from oms_sensemaking.models.geo import (
    CommonSenseFilter,
    Point,
    Track,
    decompose_observation_geometry,
)
from oms_sensemaking.models.track_weavers import TrackWeaverBase

LOGGER: logging.Logger = logging.getLogger(__name__)


class Buffer:
    def __init__(self, flush_timer_seconds: float, callback_func: Callable) -> None:
        print("Calling buffer.__init__()")

        self.flush_timer_seconds = flush_timer_seconds
        self.callback_func = callback_func

        self.lock = Lock()
        self.expiration_times: dict[UUID, datetime | None] = {}
        self.id_mapping: dict[UUID, UUID] = defaultdict(uuid4)
        self.object_list_buffer: dict[UUID, list[Point]] = defaultdict(list)
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(flush_timer_seconds, self.flush_buffer)

    def add(self, obj_id: UUID, obj_to_add: Point) -> None:
        with self.lock:
            self.expiration_times[obj_id] = datetime.now(tz=timezone.utc)
            self.object_list_buffer[obj_id].append(obj_to_add)

    def get_list_id(self, initial_id: UUID):
        with self.lock:
            return self.id_mapping.setdefault(initial_id, uuid4())

    def start(self) -> None:
        print("Calling buffer.start()")
        self.autoflush_enabled.set()
        self.buffer_autoflush.start()

    def stop(self) -> None:

        self.autoflush_enabled.clear()

        if self.buffer_autoflush.is_alive():
            self.buffer_autoflush.cancel()
            self.buffer_autoflush.join()

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.debug("Checking for expired objects in the buffer cache.")
        now: datetime = datetime.now(tz=timezone.utc)
        expire_threshold = timedelta(seconds=SETTINGS.cache_entry_expire_sec)
        # TODO rename
        expired_tracks = []

        with self.lock:
            # Identify expired tracks in thread-safe snapshot
            self.expiration_times = {key: val for key, val in self.expiration_times.items() if val is not None}
            expired_tracks = [
                list_id
                for list_id, last_updated_at in self.expiration_times.items()
                if last_updated_at is not None and last_updated_at + expire_threshold < now
            ]

        if expired_tracks:
            LOGGER.info("Flushing %d expired tracks.", len(expired_tracks))

        for list_id in expired_tracks:
            # Process expired tracks
            # this may need a finally block after it
            self.execute_callback_func(list_id, self.object_list_buffer[list_id])

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()

    def execute_callback_func(self, list_id: UUID, object_list: list) -> None:
        try:
            self.callback_func(list_id, object_list)
            # self.restart_buffer()
        except Exception:
            LOGGER.exception("Unexpected error processing buffer %s", list_id)
        finally:
            with self.lock:
                self.expiration_times[list_id] = None
                # Thread-safe cleanup of expired track data
                self.object_list_buffer.pop(list_id, None)
                keys_to_delete = [k for k, v in self.id_mapping.items() if v == list_id]
                for k in keys_to_delete:
                    del self.id_mapping[k]

    # def restart_buffer(self) -> None:
    #     if self.autoflush_enabled:
    #         self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
    #         self.buffer_autoflush.start()


# class BufferedSensemakerController():
#     pass


class GeospatialSensemakerController(SensemakerController):
    """
    Geospatial sensemaker controller.

    This class manages a collection of geospatial sensemakers.
    """

    def __init__(
        self, event_consumer: AuditLogEventConsumer, err_logger: BaseErrorLogger, ontology_service: OntologyService
    ) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer, err_logger)

        # initialize buffer
        self.buffer = Buffer(SETTINGS.cache_entry_expire_sec, self.process_buffer)

        # track weaver to call on completed Tracks before publishing
        self.track_weaver: TrackWeaverBase = TrackWeaverFactory().make_track_weaver(SETTINGS.track_weaver_algorithm)
        self.confidence_weight_map = SETTINGS.confidence_weight_map
        self._track_generator = TrackGenerator(ontology_service)

        filter_path = SETTINGS.common_sense_filter_rules_file_path
        with open(filter_path, mode="r") as f:
            filter_configs: list[dict] = json.load(f)
        self.common_sense_filters = [CommonSenseFilter.model_validate(config) for config in filter_configs]
        LOGGER.info(
            "GeospatialSensemakerController succesfully loaded common sense filters: %s",
            [csf.name for csf in self.common_sense_filters],
        )

        with open(SETTINGS.geo_sensemaker_config_file_path) as fd:
            geo_config = json.load(fd)
        self.config: dict = geo_config

    def start(self) -> None:
        """Start the controller."""

        if SETTINGS.detect_cotravels:
            self.register("cotravel", CotravelSensemaker(self.oms_crud_tool))

        if SETTINGS.detect_loiters:
            self.register("loiter", LoiterSensemaker(self.oms_crud_tool))

        if SETTINGS.similar_tracks:
            self.register("similar_tracks", SimilarTracksSensemaker())

        self.buffer.start()
        super().start()

    def stop(self):
        """
        Stop the controller.

        This method handles stopping the buffer autoflush in addition to
        stopping the controller itself.
        """
        LOGGER.debug("Stopping track buffer autoflush.")
        self.buffer.stop()
        super().stop()

    def _ensure_uuid(self, id) -> UUID:
        """
        Function used to ensure that ids used
        in operations are of type UUID
        """
        if type(id) is UUID:
            return id
        else:
            return UUID(id)

    # TODO do we need a buffered_handle_event?
    # 1. move buffer logic out
    # 2. Then use in other sensemakers with bufferedcontroller or something
    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound ATOMS event.

        :param event: The event to process.
        :return: True if the audit log event was successfully processed, False otherwise.
        """
        LOGGER.debug("Received AuditLogEvent(objectId=%s)", event.objectId)

        # Retrieve observation
        oms_obs = self.get_oms_observation(event.objectId)
        if not oms_obs:
            return True

        # Skip generated tracks
        if self.is_generated_track(oms_obs):
            return True

        # Ensure node has associated track ID
        # move with self.lock to function
        # Why does this need a new uuid instead of the nodeid?
        list_id = self.buffer.get_list_id(oms_obs.nodeId)

        # Retrieve node version
        node = self.oms_crud_tool.get_node(oms_obs.nodeId)
        node_version = getattr(node, "version", None)
        if node_version is None:
            LOGGER.warning("No node found. Unable to process observation.")
            return False

        # Decompose geometry into point(s)
        obs_geo_data = decompose_observation_geometry(oms_obs)
        if not obs_geo_data:
            LOGGER.warning("No geometry found for observation %s", oms_obs.id)
            return False

        success = False
        with db_session() as db:
            db.expire_on_commit = False

            for point_data in obs_geo_data:
                LOGGER.debug("Parsed coordinates for %s", oms_obs.id)
                # NOTE: Altitude intentionally disabled: Shapely fails with mixed 2D/3D coordinate arrays.
                #   Enable once geometry normalization supports consistent altitude data.
                try:
                    print("\n\nnode_id: ", oms_obs.nodeId)
                    print("list_id: ", list_id)
                    point, is_new = Point.get_or_create(
                        db,
                        defaults={
                            "acm": oms_obs.acm,
                            "altitude": None,
                            "detection_time": point_data["detection_time"],
                            "node_version": int(node_version),
                            "observation_version": int(oms_obs.version),
                        },
                        location=f"Point({point_data['coordinates'][0]} {point_data['coordinates'][1]})",
                        node_id=self._ensure_uuid(oms_obs.nodeId),
                        observation_id=self._ensure_uuid(oms_obs.id),
                        observation_confidence=oms_obs.confidence,
                        source_id=self._ensure_uuid(oms_obs.sourceId),
                        weight=self.confidence_weight_map[oms_obs.confidence],
                    )
                except Exception:
                    LOGGER.exception("Unable to process point for observation %s", oms_obs.id)
                    continue

                if not point:
                    continue

                if not is_new:
                    LOGGER.debug("Processing existing point: observation_id=%s", point.observation_id)

                with self.lock:
                    self.buffer.add(list_id, point)
                    # self.expiration_times[track_uuid] = datetime.now(tz=timezone.utc)
                    # self.object_list_buffer[track_uuid].append(point)
                    success = True
        return success

    # def flush_buffer(self) -> None:
    #     """Check the buffer cache for data that can be flushed from it."""
    #     LOGGER.debug("Checking for expired tracks in the buffer cache.")
    #     now: datetime = datetime.now(tz=timezone.utc)
    #     expire_threshold = timedelta(seconds=SETTINGS.cache_entry_expire_sec)
    #     expired_tracks = []

    #     with self.lock:
    #         # Identify expired tracks in thread-safe snapshot
    #         self.expiration_times = {key: val for key, val in self.expiration_times.items() if val is not None}
    #         expired_tracks = [
    #             track_uuid
    #             for track_uuid, last_updated_at in self.expiration_times.items()
    #             if last_updated_at is not None and last_updated_at + expire_threshold < now
    #         ]

    #     if expired_tracks:
    #         LOGGER.info("Flushing %d expired tracks.", len(expired_tracks))

    #     for track_uuid in expired_tracks:
    #         # Process expired tracks
    #         # this may need a finally block after it
    #         self._process_buffer(track_uuid, self.object_list_buffer[track_uuid])

    #     if self.autoflush_enabled:
    #         self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
    #         self.buffer_autoflush.start()

    def process_buffer(self, track_uuid: UUID, track_points: list[Point]) -> bool:
        """
        Generate and process a completed track once its buffer has expired.
        Safely clean in-memory buffers.

        :param track_uuid: track ID
        :param track_points: list of points that make up the track
        """
        LOGGER.debug("Processing track %s", track_uuid)

        # TODO should we pass in the track_uuid or the list of points or both
        # generate_track doesn't need the entire object_list_buffer, just the points

        try:
            try:
                # Attempt to build the full track from buffered points
                tracks = self._track_generator.generate_track(
                    track_uuid,
                    self.track_weaver,
                    self.common_sense_filters,
                    track_points,
                    self.oms_crud_tool,
                )
            except TrackLengthError:
                LOGGER.warning("Track %s doesn't have enough points; removing from buffer.", track_uuid)
                # with self.lock:
                #     self.expiration_times[track_uuid] = None
                return False

            futures = []
            with ThreadPoolExecutor() as executor:
                for track in tracks:
                    geo_config = self._get_geo_config(track)
                    for sensemaker in self._registry.values():
                        future = executor.submit(sensemaker.execute, track, geo_config.model_dump())
                        futures.append(future)

                for future in as_completed(futures):
                    _ = future.result()
        except Exception:
            LOGGER.exception("Unexpected error processing track %s", track_uuid)
        # finally:
        #     with self.lock:
        #         # Thread-safe cleanup of expired track data
        #         self.expiration_times[track_uuid] = None
        #         self.object_list_buffer.pop(track_uuid, None)
        #         keys_to_delete = [k for k, v in self.id_mapping.items() if v == track_uuid]
        #         for k in keys_to_delete:
        #             del self.id_mapping[k]

        return True

    def _get_geo_config(self, track: Track) -> GeospatialSensemakerConfig:
        """Get the geo config for this track based on the provider and node type

        :param track: Track to process
        :return: GeospatialSensemakerConfig settings for this track and vehicle
        """

        node = self.oms_crud_tool.get_node(track.node_id)

        provider_id = None
        default_config = self.config.get(SETTINGS.geo_sensemaker_config_default_provider_id, {})

        # Fetch source/provider id from last (can be any) point in track
        if len(track.points):
            source_id = track.points[-1].source_id
            source = self.oms_crud_tool.get_source(source_id=str(source_id))
            if source:
                provider_id = source.providerId

        provider_config = self.config.get(provider_id, default_config) if provider_id else default_config

        return GeospatialSensemakerConfig(**provider_config.get(node.classIri, {}))

    def get_oms_observation(self, observation_id: UUID) -> ObservationObservation | None:
        """
        Given an ATOMS Observation ID, get the ATOMS Observation.
        Ensure it is an observation we can use to make a track

        :param observation_id: ID of the observation
        :return: None if no observation exists, or the ATOMS Observation
        """
        # get observation
        oms_obs: ObservationObservation = self.oms_crud_tool.get_observation(observation_id)

        # Filter observations
        # Only process if there is an observation and it has a geojson Point or LineString
        if not oms_obs:
            return None

        cannot_handle_geometry = oms_obs.geometry["type"].lower() not in ("point", "linestring")
        if cannot_handle_geometry:
            return None

        return oms_obs

    def is_generated_track(self, obs: ObservationObservation):
        return hasattr(obs, "labels") and obs.labels is not None and SETTINGS.sm_connected_track in obs.labels


class GeoQueueFilter(EventFilter):
    def passes_filter(self, audit_event: AuditLogEvent):
        handled_object_types = [ObjectType.OBSERVATION.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value]
        return (
            audit_event.objectType in handled_object_types
            and audit_event.action in handled_event_types
            and audit_event.headers.iri != SETTINGS.track_iri
        )
