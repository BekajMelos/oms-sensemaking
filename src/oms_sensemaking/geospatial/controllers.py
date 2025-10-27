"""Geospatial sensemaker controller."""

import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from threading import Event, Timer
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
from oms_sensemaking.core.observability import with_metrics_collection
from oms_sensemaking.geospatial.schemas import GeospatialSensemakerConfig
from oms_sensemaking.geospatial.sensemakers import CotravelSensemaker, LoiterSensemaker, SimilarTracksSensemaker
from oms_sensemaking.geospatial.track_generator import TrackGenerator
from oms_sensemaking.geospatial.track_weaver_factory import TrackWeaverFactory
from oms_sensemaking.models.geo import (
    CommonSenseFilter,
    Point,
    Track,
    TrackWeaverBase,
    decompose_observation_geometry,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


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
        self.track_times: dict[UUID, datetime | None] = {}
        self.autoflush_enabled: Event = Event()
        self.buffer_autoflush: Timer = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
        self.node_track_mapping: dict[UUID, UUID] = defaultdict(uuid4)
        self.track_node_buffer: dict[UUID, list[Point]] = defaultdict(list)

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

    @with_metrics_collection
    def _ensure_uuid(self, id) -> UUID:
        """
        Function used to ensure that ids used
        in operations are of type UUID
        """
        if type(id) is UUID:
            return id
        else:
            return UUID(id)

    @with_metrics_collection
    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound OMS event.

        :param event: The event to process.
        :return: True if the audit log event was successfully processed, False otherwise.
        """
        LOGGER.debug(f"Received AuditLogEvent(objectId={event.objectId})")

        # Retrieve observation
        oms_obs = self.get_oms_observation(event.objectId)
        if not oms_obs:
            return True

        # Skip generated tracks
        if self.is_generated_track(oms_obs):
            return True

        # Ensure node has associated track ID
        track_uuid = self.node_track_mapping.setdefault(oms_obs.nodeId, uuid4())

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
                LOGGER.debug(f"Parsed coordinates for {oms_obs.id}")
                # NOTE: Altitude intentionally disabled: Shapely fails with mixed 2D/3D coordinate arrays.
                #   Enable once geometry normalization supports consistent altitude data.
                try:
                    point, is_new = Point.get_or_create(
                        db,
                        defaults={
                            "acm": oms_obs.acm,
                            "altitude": None,
                            "detection_time": point_data["detection_time"],
                            "node_version": int(node_version),
                            "observation_version": int(oms_obs.version),
                        },
                        location=f'Point({point_data["coordinates"][0]} {point_data["coordinates"][1]})',
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
                    self.track_times[track_uuid] = datetime.now(tz=timezone.utc)
                    self.track_node_buffer[track_uuid].append(point)
                    success = True
        return success

    def flush_buffer(self) -> None:
        """Check the buffer cache for data that can be flushed from it."""
        LOGGER.debug("Checking for expired tracks in the buffer cache.")
        now: datetime = datetime.now(tz=timezone.utc)
        expire_threshold = timedelta(seconds=SETTINGS.cache_entry_expire_sec)
        expired_tracks = []

        with self.lock:
            # Identify expired tracks in thread-safe snapshot
            self.track_times = {key: val for key, val in self.track_times.items() if val is not None}
            expired_tracks = [
                track_uuid
                for track_uuid, last_updated_at in self.track_times.items()
                if last_updated_at is not None and last_updated_at + expire_threshold < now
            ]

        if expired_tracks:
            LOGGER.info("Flushing %d expired tracks.", len(expired_tracks))

        for track_uuid in expired_tracks:
            # Process expired tracks
            self._process_track(track_uuid)

        if self.autoflush_enabled:
            self.buffer_autoflush = Timer(SETTINGS.cache_entry_expire_sec, self.flush_buffer)
            self.buffer_autoflush.start()

    def _process_track(self, track_uuid: UUID) -> bool:
        """
        Generate and process a completed track once its buffer has expired.
        Safely clean in-memory buffers.

        :param track_uuid: track ID
        """
        LOGGER.debug("Processing track %s", track_uuid)

        try:
            try:
                # Attempt to build the full track from buffered points
                tracks = self._track_generator.generate_track(
                    track_uuid,
                    self.track_weaver,
                    self.common_sense_filters,
                    self.track_node_buffer,
                    self.oms_crud_tool,
                )
            except TrackLengthError:
                LOGGER.warning("Track %s doesn't have enough points; removing from buffer.", track_uuid)
                with self.lock:
                    self.track_times[track_uuid] = None
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
        finally:
            with self.lock:
                # Thread-safe cleanup of expired track data
                self.track_times[track_uuid] = None
                self.track_node_buffer.pop(track_uuid)
                self.node_track_mapping = {k: v for k, v in self.node_track_mapping.items() if v != track_uuid}

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
        Given an OMS Observation ID, get the OMS Observation.  Ensure it is an observation we can use to make a track

        :param observation_id: ID of the observation
        :return: None if no observation exists, or the OMS Observation
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
        return audit_event.objectType in handled_object_types and audit_event.action in handled_event_types
