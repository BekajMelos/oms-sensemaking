"""Geospatial sensemaker controller."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import UUID

from oms_sdk.generated.generated_graphql_client.enums import Action, ObjectType
from oms_sdk.generated.generated_graphql_client.observation import ObservationObservation

from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.clients.ontology_client import OntologyService
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.buffer import Buffer
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


# class BufferedSensemakerController():
# @abstractmethod
# def proces_buffer(self, list_id, object_list):
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

        self.buffer = Buffer("Geospatial Buffer", SETTINGS.geo_buffer_expire_sec, self.process_buffer)

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

                print("\n\nadding: ", oms_obs.nodeId, point)
                self.buffer.add(oms_obs.nodeId, point)

                # TODO maybe only return success if all points were processed properly
                success = True

        return success

    def process_buffer(self, track_uuid: UUID, track_points: list[Point]) -> bool:
        """
        Generate and process a completed track once its buffer has expired.
        Safely clean in-memory buffers.

        :param track_uuid: track ID
        :param track_points: list of points that make up the track
        """
        LOGGER.debug("Processing track %s", track_uuid)

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
