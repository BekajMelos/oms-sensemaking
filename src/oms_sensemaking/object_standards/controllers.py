"""Object standards sensemaker controller."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import chain
from uuid import UUID

from oms_sdk.generated.generated_graphql_client.enums import Action

from oms_sensemaking.clients.instances import ontology_service
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.buffer import Buffer
from oms_sensemaking.core.controllers import SensemakerController
from oms_sensemaking.core.error_loggers import BaseErrorLogger
from oms_sensemaking.core.events import (
    AuditLogEvent,
    AuditLogEventConsumer,
    EventFilter,
    ObjectType,
)
from oms_sensemaking.object_standards.sensemaker import (
    ObjectStandards,
    ObjectStandardsDataRetriever,
    ObjectStandardsRubric,
)

LOGGER: logging.Logger = logging.getLogger(__name__)


class ObjStandardsDataProvider:
    def __init__(self, file_path=SETTINGS.object_standards_settings.rubrics_file_path) -> None:
        self.file_path = file_path
        self.entries = self._load_from_json()
        self.criteria = list(
            chain.from_iterable(
                entry.get(key, []) for entry in self.entries.values() for key in ("ATTRIBUTES", "RELATIONSHIPS")
            )
        )

    def _load_from_json(self):
        with open(self.file_path) as file:
            data = json.load(file)
        return data


class ObjectStandardsSensemakerController(SensemakerController):
    """
    Resolution sensemaker controller.

    This class manages a collection of resolution sensemakers.
    """

    def __init__(self, event_consumer: AuditLogEventConsumer, err_logger: BaseErrorLogger) -> None:
        """Create a new instance of GeospatialSensemakerController."""
        super().__init__(event_consumer, err_logger)

        # TODO config var
        self.buffer = Buffer("Object Standards Buffer", 30, self.process_buffer)

    def start(self) -> None:
        """Start the controller."""
        if SETTINGS.object_standards_settings.enable_object_standards_sensemaker:
            with open(SETTINGS.object_standards_settings.rubrics_file_path) as fd:
                rubric_criteria = json.load(fd)

            self.register(
                "object standards",
                ObjectStandards(
                    self.oms_crud_tool,
                    ontology_service,
                    ObjectStandardsDataRetriever(),
                    ObjectStandardsRubric(),
                    rubric_criteria,
                ),
            )
        self.buffer.start()
        super().start()

    def stop(self):
        """
        Stop the controller.

        This method handles stopping the buffer in addition to
        stopping the controller itself.
        """
        LOGGER.debug("Stopping buffer autoflush.")
        self.buffer.stop()
        super().stop()

    def handle_event(self, event: AuditLogEvent) -> bool:
        """
        Handle inbound ATOMS event.

        This function is intended as the entrypoint for controlling the flow of
        data to the sensemakers.

        :param event: The event to process.
        :return: Boolean of success or failure
        """
        LOGGER.debug("Received AuditLogEvent(objectId=%s)", event.objectId)

        try:
            # extract info from ATOMS via API calls
            oms_obj = self.get_oms_data(event)
        except Exception as e:
            message = f"Error retrieving object from omsb. {event.objectType}: {event.objectId}"
            self.err_logger.log_error(event, message, __name__, e, None)
            return False

        if not oms_obj:
            LOGGER.warning("Could not find %s with id: %s", event.objectType, event.objectId)
            return False

        # TODO does the oms_obj always have a nodeId?
        list_id = self.buffer.get_list_id(oms_obj.nodeId)
        self.buffer.add(list_id, oms_obj)

        return True

    def process_buffer(self, object_list_id: UUID, object_list: list) -> bool:
        """
        Execute the sensemaker on the last received object. The sensemaker will
        request for all other attributes, so no need to pass in every object in the list

        :param object_list_id: track ID
        :param object_list: list of points that make up the track
        """
        last_obj = object_list[-1]

        # try:
        with ThreadPoolExecutor() as sync_executor:
            futures = []
            for sensemaker in self._registry.values():
                future = sync_executor.submit(sensemaker.execute, last_obj)
                futures.append(future)

            # make sure errors are caught
            for future in as_completed(futures):
                _ = future.result()

            sync_executor.shutdown(wait=True)

        # TODO Should we pass the event into the buffer so that we can track these things for exceptions?

        # except Exception as e:
        #     message = f"Error encountered while processing object {last_obj}: {str(e)}"
        #     self.err_logger.log_error(
        #         event,
        #         message,
        #         __name__,
        #         e,
        #         oms_obj.acm,
        #     )

        return True


class ObjectStandardsQueueFilter(EventFilter):
    # Should we also do node creation as an event we care about to assign it a score of 0?
    def __init__(self, data_provider: ObjStandardsDataProvider) -> None:
        self.obj_standards_data = data_provider

    def passes_filter(self, audit_log_event: AuditLogEvent) -> bool:
        handled_object_types = [ObjectType.ATTRIBUTE.value, ObjectType.RELATIONSHIP.value]
        handled_event_types = [Action.CREATE.value, Action.RESTORE.value, Action.UPDATE.value, Action.DELETE.value]
        criteria = self.obj_standards_data.criteria
        return (
            audit_log_event.objectType in handled_object_types
            and audit_log_event.action in handled_event_types
            and audit_log_event.headers.iri in criteria
        )
