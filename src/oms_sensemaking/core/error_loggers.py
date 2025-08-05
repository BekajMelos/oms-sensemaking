"""Module defining Audit Error Logging classes"""

import logging
from abc import ABC, abstractmethod

from oms_sensemaking import __version__
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.core.events import AuditLogEvent
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)


class BaseErrorLogger(ABC):
    """Base class for Audit Log Event Error Handling"""

    @abstractmethod
    def log_error(self, event: AuditLogEvent, message: str, acm: dict, exc_text: None | str = None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param acm: Classification for the event
        :param exc_text: Optional exception text for the error
        :return: None
        """
        raise NotImplementedError


class ErrorLogger(BaseErrorLogger):
    """Class for logging Audit Log Events to the Database"""

    def log_error(self, event: AuditLogEvent, message: str, acm: dict, exc_text: None | str = None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param acm: Classification for the event
        :param exc_text: Optional exception text for the error
        :return: None
        """

        LOGGER.exception(message)

        log_record = AuditLogError(
            object_id=event.objectId,
            object_type=event.objectType,
            event_type=event.action,
            module_name=__name__,
            message=message,
            acm=acm,
            exc_text=exc_text,
            version=__version__,
        )

        with db_session() as db:
            db.add(log_record)
            db.commit()

        LOGGER.info("Created AuditLogError for %s", event.objectId)


class RethrowErrorLogger(BaseErrorLogger):
    """Class for re raising AuditLogEvent Errors"""

    def __init__(self, err_logger: BaseErrorLogger):
        self.err_logger = err_logger

    def log_error(self, event: AuditLogEvent, message: str, acm: dict, exc_text: None | str = None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param acm: Classification for the event
        :param exc_text: Optional exception text for the error
        :return: None
        """
        self.err_logger.log_error(event, message, acm, exc_text)
        raise
        # maybe raise e if just plain raise doesn't rethrow with helpful data
