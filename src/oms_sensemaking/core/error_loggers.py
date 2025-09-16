"""Module defining Audit Error Logging classes"""

import logging
import traceback
from abc import ABC, abstractmethod
from types import TracebackType

import oms_sensemaking
from oms_sensemaking.clients.instances import db_session
from oms_sensemaking.config import SETTINGS
from oms_sensemaking.core.events import AuditLogEvent
from oms_sensemaking.models.logs import AuditLogError

LOGGER = logging.getLogger(__name__)

SENSEMAKING_MODULE = oms_sensemaking.__name__


class BaseErrorLogger(ABC):
    """Base class for Audit Log Event Error Handling"""

    @abstractmethod
    def log_error(self, event: AuditLogEvent, message: str, module: str, exc: Exception, acm: dict | None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param module: Name of the producing module.
        :param exc: Exception object
        :param acm: Classification for the event
        :return: None
        """
        raise NotImplementedError


class ErrorLogger(BaseErrorLogger):
    """Class for logging Audit Log Events to the Database"""

    def log_error(self, event: AuditLogEvent, message: str, module: str, exc: Exception, acm: dict | None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param module: Name of the producing module.
        :param exc: Exception object
        :param acm: Classification for the event
        :return: None
        """

        LOGGER.exception(message)

        if not SETTINGS.enable_audit_log_error_logging:
            return None

        tb = exc.__traceback__
        if tb is None:
            LOGGER.error("Unable to log error to the database. Not enough info in the exception.")
            return None

        error_frame_summary = self._get_sensemaking_error_frame(tb)

        exc_text: str | None = traceback.format_exc()[SETTINGS.audit_log_error_max_tb_chars * -1 :]

        # can't include everything without a proper acm
        if acm is None:
            acm = SETTINGS.audit_log_error_acm
            exc_text = None
            message = None  # type: ignore[assignment]

        log_record = AuditLogError(
            object_id=event.objectId,
            object_type=event.objectType,
            event_type=event.action,
            module_name=error_frame_summary.filename,
            line_no=error_frame_summary.lineno,
            function_name=error_frame_summary.name,
            code=error_frame_summary.line,
            exc_text=exc_text,
            message=message,
            acm=acm,
            exception_name=exc.__class__.__name__,
            version=oms_sensemaking.__version__,
        )

        with db_session() as db:
            db.add(log_record)
            db.commit()

        LOGGER.info("Created AuditLogError for %s", event.objectId)

    def _get_sensemaking_error_frame(self, tb: TracebackType) -> traceback.FrameSummary:
        """Get the last frame from within the sensemaking code that caused the exception
        Use last frame as backup

        :param tb: Traceback of the error
        :return: Traceback FrameSummary object
        """

        frame: traceback.FrameSummary | None = None
        frame_summaries = traceback.extract_tb(tb)
        for frame_summary in frame_summaries:
            if SENSEMAKING_MODULE in frame_summary.filename:
                frame = frame_summary

        if frame is None:
            frame = frame_summaries[-1]

        return frame


class RethrowErrorLogger(BaseErrorLogger):
    """Class for re raising AuditLogEvent Errors"""

    def __init__(self, err_logger: BaseErrorLogger):
        self.err_logger = err_logger

    def log_error(self, event: AuditLogEvent, message: str, module: str, exc: Exception, acm: dict | None) -> None:
        """Log errors with AuditLogEvent to the database. This method should be called within an exception handler.

        :param event: AuditLogEvent object being processed when the error occurred
        :param message: Log message for the error
        :param module: Name of the producing module.
        :param exc: Exception object
        :param acm: Classification for the event
        :return: None
        """
        self.err_logger.log_error(event, message, module, exc, acm)
        raise exc
